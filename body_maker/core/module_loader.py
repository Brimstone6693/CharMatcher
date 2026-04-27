# file: module_loader.py
import os
import importlib.util
import json

# Получаем директорию проекта (родительскую от директории этого файла)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(PROJECT_ROOT, "modules")
BODIES_DATA_DIR = os.path.join(PROJECT_ROOT, "bodies_data")

def load_available_modules_and_bodies(components_dir=None, bodies_dir=None, base_component_class=None, body_classes_module=None):
    """
    Сканирует директории components_dir и bodies_data_dir для JSON файлов,
    и загружает все классы, наследующиеся от BaseComponent или AbstractBody соответственно.
    Возвращает два словаря: {имя_компонента: класс}, {имя_тела: экземпляр DynamicBody}.
    
    Args:
        components_dir: Директория с компонентами
        bodies_dir: Директория с телами
        base_component_class: Базовый класс компонентов (для проверки issubclass)
        body_classes_module: Модуль с классами тел (AbstractBody, DynamicBody)
    """
    # Импортируем классы по умолчанию если не переданы
    if base_component_class is None:
        from core.components import BaseComponent
        base_component_class = BaseComponent
    
    if body_classes_module is None:
        from core.body_types import body_classes
        body_classes_module = body_classes
    
    AbstractBody = body_classes_module.AbstractBody
    DynamicBody = body_classes_module.DynamicBody
        
    # Используем переданные пути или пути по умолчанию (относительно корня проекта)
    if components_dir is None:
        components_dir = MODULES_DIR
    if bodies_dir is None:
        bodies_dir = BODIES_DATA_DIR
        
    available_components = {}
    available_bodies = {}

    print(f"Scanning directories: {components_dir}, {bodies_dir}")

    # Загрузка компонентов
    if os.path.exists(components_dir):
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
                                issubclass(obj, base_component_class) and
                                obj != base_component_class):
                                    print(f"  Found component class: {obj.__name__}")
                                    available_components[obj.__name__] = obj
                    except Exception as e:
                        print(f"  Error loading component module {filename}: {e}")
    else:
        print(f"  Warning: Components directory '{components_dir}' does not exist.")

    # Добавляем DynamicBody как доступный класс для загрузки сохранений
    # Это нужно чтобы Character.from_dict мог восстановить DynamicBody из JSON
    available_bodies["DynamicBody"] = DynamicBody  # Сам класс, а не экземпляр

    # Загрузка тел из JSON файлов
    if os.path.exists(bodies_dir):
        for filename in os.listdir(bodies_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(bodies_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    class_name = data.get("class_name")
                    if class_name:
                        # Сохраняем ДИНАМИЧЕСКИЙ КЛАСС (callable), а не экземпляр
                        # Создаём фабрику которая будет создавать экземпляры при вызове
                        def make_body_factory(body_data):
                            def factory(**kwargs):
                                return DynamicBody.from_dict(body_data)
                            return factory
                        
                        available_bodies[class_name] = make_body_factory(data)
                        print(f"  Found body class (JSON): {class_name}")
                except Exception as e:
                    print(f"  Error loading body JSON {filename}: {e}")
    else:
        print(f"  Warning: Bodies data directory '{bodies_dir}' does not exist.")

    return available_components, available_bodies

# Пример использования:
# loaded_components, loaded_bodies = load_available_modules_and_bodies()
# print("Loaded components:", list(loaded_components.keys()))
# print("Loaded bodies:", list(loaded_bodies.keys()))