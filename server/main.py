from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json
import logging
from .pdf_generator import create_pdf
from model.process_image import process_image, setup_model, last_prediction_results
from .model import Base, User
from .database import engine, SessionLocal
from .schemas import UserCreate, UserOut

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Определение путей
UPLOAD_DIR = "/app/server/images"
REPORTS_DIR = "/app/server/reports"

# Создание директорий, если они не существуют
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Инициализация модели
try:
    model_path = "/app/model/utils/model.pth"
    predictor = setup_model(model_path)
    logger.info("Модель успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка при инициализации модели: {e}")
    raise

# Глобальная переменная для хранения последних результатов предсказания
last_prediction_results = None

app = FastAPI()

# Настройка CORS
origins = [
    "https://spark-radex.vercel.app",  # Продакшн домен
    "http://localhost:3000",             # Локальная разработка
    "http://localhost:5173",
    "https://spark-radex-ai.vercel.app",
    "https://radex-spark-ai.vercel.app"             # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Кэширование preflight запросов на 1 час
)

# Добавляем middleware для работы с прокси
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Разрешаем все хосты, так как используем прокси
)

# Кастомный класс для обработки CORS в статических файлах
class CORSMiddlewareStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

# Монтирование статических файлов с CORS
app.mount("/images", CORSMiddlewareStaticFiles(directory=UPLOAD_DIR), name="images")
app.mount("/reports", CORSMiddlewareStaticFiles(directory=REPORTS_DIR), name="reports")

# Создание таблиц в базе
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.post("/users/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        fullName=user.fullName,
        status=user.status,
        email=user.email,
        password=user.password,
        images=user.images,
        reports=user.reports,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.delete("/users/{user_id}", response_model=UserOut)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        if user.images:
            for filename in user.images:
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Удален файл изображения: {file_path}")

        if user.reports:
            for filename in user.reports:
                file_path = os.path.join(REPORTS_DIR, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Удален файл отчета: {file_path}")

        db.delete(user)
        db.commit()
        return user
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя")

@app.post("/upload")
async def upload_image(
        file: UploadFile = File(...),
        userId: int = Form(...),
        db: Session = Depends(get_db)
):
    # Проверка типа файла
    if file.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Разрешены только PNG изображения")

    # Проверка размера файла (максимум 100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB

    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Размер файла превышает 100MB")

    # Сброс позиции файла для повторного чтения
    await file.seek(0)

    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    filename = f"{user.fullName}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Сохранение файла
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Обработка изображения для поиска дефектов
        global last_prediction_results
        try:
            last_prediction_results = process_image(predictor, file_path, None)
            logger.info(f"Изображение успешно обработано: {filename}")
            logger.info(f"Результаты анализа: {json.dumps(last_prediction_results, indent=2)}")
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            last_prediction_results = None

        # Обновление списка изображений пользователя
        if user.images is None:
            user.images = []
        user.images = (user.images or []) + [filename]

        db.commit()
        db.refresh(user)

        response_data = {
            "filename": filename,
            "defects": last_prediction_results
        }
        logger.info(f"Отправляем ответ: {json.dumps(response_data, indent=2)}")
        return response_data

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")

@app.get("/defects")
def get_example_defects():
    global last_prediction_results
    if last_prediction_results is None:
        raise HTTPException(status_code=404, detail="Нет доступных результатов предсказания")
    
    return {
        "user": {
            "defects": last_prediction_results
        }
    }

@app.post("/replace-image")
async def replace_image(
    file: UploadFile = File(...),
    userId: int = Form(...),
    filename: str = Form(...),
    rects: str = Form(...),
    db: Session = Depends(get_db),
):
    if file.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Разрешены только PNG изображения")

    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if not user.images or filename not in user.images:
        raise HTTPException(status_code=400, detail="Файл не принадлежит пользователю")

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл для замены не найден")

    try:
        # Перезапись файла
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        logger.info(f"Файл успешно заменен: {filename}")

        # Обработка прямоугольников и создание PDF
        try:
            rect_data = json.loads(rects)
            base_filename = filename.replace('.png', '')
            create_pdf(base_filename, REPORTS_DIR, rect_data)
            
            pdf_filename = f"{base_filename}.pdf"
            if user.reports is None:
                user.reports = []
            user.reports = (user.reports or []) + [pdf_filename]

            db.commit()
            db.refresh(user)
            logger.info(f"PDF отчет создан: {pdf_filename}")

        except Exception as e:
            logger.error(f"Ошибка при создании PDF отчета: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка создания PDF отчета: {str(e)}")

        return {
            "user": {
                "images": user.images,
                "reports": user.reports
            }
        }

    except Exception as e:
        logger.error(f"Ошибка при замене файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при замене файла: {str(e)}")