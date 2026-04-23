# file: module_loader.py
import os
import importlib.util
import json
from components import BaseComponent
from body import AbstractBody, DynamicBody # Импортируем базовый класс тела и динамический класс

BODIES_DATA_DIR = "bodies_data"

def load_available_modules_and_bodies(components_dir="modules", bodies_dir="bodies"):
    """
    Сканирует директории components_dir и bodies_data_dir для JSON файлов,
    и загружает все классы, наследующиеся от BaseComponent или AbstractBody соответственно.
    Возвращает два словаря: {имя_компонента: класс}, {имя_тела: экземпляр DynamicBody}.
    """
    available_components = {}
    available_bodies = {}

    print(f"Scanning directories: {components_dir}, {BODIES_DATA_DIR}")

    # Загрузка компонентов
    for filename in os.listdir(components_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(components_dir, filename)
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and
                            issubclass(obj, BaseComponent) and
                            obj != BaseComponent):
                                print(f"  Found component class: {obj.__name__}")
                                available_components[obj.__name__] = obj
                except Exception as e:
                    print(f"  Error loading component module {filename}: {e}")

    # Загрузка тел из JSON файлов
    if os.path.exists(BODIES_DATA_DIR):
        for filename in os.listdir(BODIES_DATA_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(BODIES_DATA_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    class_name = data.get("class_name")
                    if class_name:
                        # Создаем динамический экземпляр тела
                        body_instance = DynamicBody.from_dict(data)
                        print(f"  Found body class (JSON): {class_name}")
                        available_bodies[class_name] = body_instance
                except Exception as e:
                    print(f"  Error loading body JSON {filename}: {e}")
    else:
        print(f"  Warning: Bodies data directory '{BODIES_DATA_DIR}' does not exist.")

    return available_components, available_bodies

# Пример использования:
# loaded_components, loaded_bodies = load_available_modules_and_bodies()
# print("Loaded components:", list(loaded_components.keys()))
# print("Loaded bodies:", list(loaded_bodies.keys()))