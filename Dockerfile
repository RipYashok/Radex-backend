FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # Пакеты для PostgreSQL
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование только requirements.txt сначала для лучшего кэширования слоев
COPY requirements.txt .

# Установка Python пакетов
RUN pip3 install --no-cache-dir torch==2.2.1+cu121 torchvision==0.17.1+cu121 -f https://download.pytorch.org/whl/torch_stable.html && \
    pip3 install --no-cache-dir opencv-python matplotlib && \
    pip3 install --no-cache-dir 'git+https://github.com/facebookresearch/detectron2.git' && \
    pip3 install --no-cache-dir -r requirements.txt

# Создание необходимых директорий
RUN mkdir -p /app/model/utils \
    /app/server/images \
    /app/server/reports

# Копирование файлов проекта
COPY model/ /app/model/
COPY server/ /app/server/

# Копирование конфигурационных файлов
COPY model/utils/cascade_mask_rcnn_R_50_FPN_3x.yaml /app/model/utils/
COPY model/utils/Base-RCNN-FPN.yaml /app/model/utils/

# Установка переменных окружения
ENV PYTHONPATH=/app

# Открываем порт для сервера
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose.yml)
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"] 