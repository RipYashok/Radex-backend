import os
import cv2
import torch
import numpy as np
import json
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
# from skimage.exposure import match_histograms
import glob

# Глобальная переменная для хранения последних результатов
last_prediction_results = None

def setup_model(model_path):
    """
    Инициализация модели Detectron2
    """
    cfg = get_cfg()
    cfg.merge_from_file("/app/model/utils/cascade_mask_rcnn_R_50_FPN_3x.yaml")
    
    # Настройка модели под ваши классы
    # cfg.MODEL.ROI_HEADS.NUM_CLASSES = 13  # Количество классов в вашей модели
    cfg.MODEL.ROI_HEADS.NAME = "StandardROIHeads"
    cfg.MODEL.MASK_ON = False
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 13
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.35
    cfg.MODEL.WEIGHTS = model_path
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Создаем метаданные для ваших классов
    MetadataCatalog.get("custom_dataset").set(thing_classes= [
                                                                "pora", "vkl", "podrez", "projog", "crack",
                                                                "napliv", "etalon1", "etalon2", "etalon3",
                                                                "pora-concealed", "utjazhina", "nesplavlenie", "neprovar-kornja"
                                                            ])
    
    return DefaultPredictor(cfg)

def match_histogram(image, reference):
    """
    Приводит гистограмму image к гистограмме reference.
    """
    # Применим match_histograms для grayscale изображений
    matched = match_histograms(image, reference, channel_axis=None)
    return matched

def convert_to_uint8(image):
    """
    Приводит изображение к формату uint8.
    """
    # Ограничиваем диапазон значений [0, 255]
    image = np.clip(image, 0, 255)

    # Преобразуем к uint8
    return image.astype(np.uint8)

def process_images_histogram_matching(input_dir, output_dir, reference_path):
    """
    Приводит яркость всех изображений в input_dir к яркости reference_path
    с использованием гистограмменого выравнивания.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Загрузим эталонное изображение
    reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    if reference_image is None:
        print(f"[Ошибка] Не удалось загрузить эталонное изображение: {reference_path}")
        return

    print(f"[INFO] Применение гистограмменого выравнивания к {reference_path}")

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # Загрузим изображение
            image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print(f"[Ошибка] Не удалось загрузить: {input_path}")
                continue

            # Применим гистограмменое выравнивание
            matched = match_histogram(image, reference_image)

            # Преобразуем к uint8 для сохранения
            matched_uint8 = convert_to_uint8(matched)


    
    return matched_uint8



def process_image(predictor, image_path, output_path):
    """
    Обработка одного изображения
    """
    global last_prediction_results
    img = cv2.imread(image_path)

    if img is None:
        print(f"Не удалось загрузить изображение: {image_path}")
        return
    
    # Получение предсказаний
    outputs = predictor(img)
    
    # Получаем размеры изображения
    height, width = img.shape[:2]
    
    # Формируем словарь в нужном формате
    outputs_dict = {
        "instances": {
            "num_instances": len(outputs["instances"]),
            "image_height": height,
            "image_width": width,
            "pred_boxes": outputs["instances"].pred_boxes.tensor.cpu().numpy().tolist(),
            "scores": outputs["instances"].scores.cpu().numpy().tolist(),
            "pred_classes": outputs["instances"].pred_classes.cpu().numpy().tolist()
        }
    }
    
    # Сохраняем результаты в глобальную переменную
    last_prediction_results = outputs_dict
    
    print(f"Обработано изображение: {image_path}")
    
    return outputs_dict
