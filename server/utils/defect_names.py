import os
import yaml

class DefectNames:
    def __init__(self):
        # Путь к YAML-файлу относительно текущего скрипта
        yaml_path = os.path.join(os.path.dirname(__file__), 'classes.yaml')

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.names = data.get('names', {})

        # Преобразуем ключи в int, если они были строками
        self.names = {int(k): v for k, v in self.names.items()}

    def get(self, code):
        return self.names.get(code, f"Неизвестный код: {code}")
