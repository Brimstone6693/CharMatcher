# file: module_loader.py
import os
import importlib.util
from components import BaseComponent
from body import AbstractBody # Импортируем базовый класс тела

def load_available_modules_and_bodies(components_dir="modules", bodies_dir="bodies"):
    """
    Сканирует директории components_dir и bodies_dir и загружает все классы,
    наследующиеся от BaseComponent или AbstractBody соответственно.
    Возвращает два словаря: {имя_компонента: класс}, {имя_тела: класс}.
    """
    available_components = {}
    available_bodies = {}

    print(f"Scanning directories: {components_dir}, {bodies_dir}")

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

    # Загрузка тел
    for filename in os.listdir(bodies_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(bodies_dir, filename)
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and
                            issubclass(obj, AbstractBody) and
                            obj != AbstractBody):
                                print(f"  Found body class: {obj.__name__}")
                                available_bodies[obj.__name__] = obj
                except Exception as e:
                    print(f"  Error loading body module {filename}: {e}")

    return available_components, available_bodies

# Пример использования:
# loaded_components, loaded_bodies = load_available_modules_and_bodies()
# print("Loaded components:", list(loaded_components.keys()))
# print("Loaded bodies:", list(loaded_bodies.keys()))