# file: module_generator.py
import os

# Шаблоны для генерации
COMPONENT_TEMPLATE = '''# file: {filename}
from core.components import BaseComponent

class {class_name}(BaseComponent):
    def __init__(self, placeholder_param="default_value"):
        # Добавьте сюда атрибуты вашего компонента
        self.placeholder_attr = placeholder_param
        # Пример: self.health = 100
        # Пример: self.skills = []

    # Добавьте сюда методы вашего компонента
    # Пример: def take_damage(self, amount): ...

    def to_dict(self):
        # Верните словарь с состоянием компонента
        return {{
            "type": "{class_name}",
            "placeholder_attr": self.placeholder_attr, # Замените на реальные атрибуты
            # "health": self.health,
            # "skills": self.skills,
        }}

    @classmethod
    def from_dict(cls, data):
        # Создайте экземпляр из словаря
        return cls(
            placeholder_param=data.get("placeholder_attr", "default_value") # Замените на реальные атрибуты
            # health=data.get("health", 100),
            # skills=data.get("skills", []),
        )

'''

BODY_TEMPLATE = '''# file: {filename}
from core.body_types.body_classes import AbstractBody

class {class_name}(AbstractBody):
    def __init__(self, race="Custom_{class_name_base}", size="Medium", gender="N/A", **kwargs):
        # Вызовите родительский конструктор
        super().__init__(race, size)
        # Добавьте сюда атрибуты вашего тела
        self.gender = gender
        # Инициализируем иерархическую структуру частей тела
        # Формат: {{parent: [child1, child2, ...], None: [корневые части]}}
        # Пример: {{None: ["head", "torso"], "head": ["eyes", "mouth"], "mouth": ["teeth"]}}
        self.body_structure = {{
            None: ["custom_part1", "custom_part2"],
            "custom_part1": []
        }}
        # Пример: self.wingspan = kwargs.get("wingspan", 0)
        # Пример: self.has_fur = kwargs.get("has_fur", False)

    def describe_appearance(self):
        # Верните строку с описанием тела
        return f"A {{self.size}} {{self.gender}} {{self.race}} with a custom {{self.__class__.__name__.lower()}} body plan, featuring {{len(self.get_all_parts())}} distinct parts."

    # Методы to_dict и from_dict наследуются из AbstractBody, если не переопределяете специфичное поведение
    # def to_dict(self):
    #     # Если нужно добавить специфичные поля, расширьте родительскую реализацию
    #     data = super().to_dict()
    #     data.update({{
    #         "gender": self.gender,
    #         # "wingspan": self.wingspan,
    #         # "has_fur": self.has_fur,
    #     }})
    #     return data

    # @classmethod
    # def from_dict(cls, data, available_body_classes):
    #     # Если нужно обработать специфичные поля, расширьте родительскую реализацию
    #     # Этот метод уже переопределён в AbstractBody, вызывающий эту реализацию
    #     # Просто вызовите super() с переданными аргументами, если не добавляете логику
    #     return super().from_dict(data, available_body_classes)

'''


def main():
    print("=== Module Generator ===")

    module_type = input("Generate a new (C)omponent or (B)ody? ").lower()
    if module_type not in ['c', 'b']:
        print("Invalid choice.")
        return

    class_name = input("Enter the name for your new class (e.g., HealthSystem, DragonBody): ").strip()
    if not class_name:
        print("Name cannot be empty.")
        return

    # Убираем "Body" или "Component" из имени класса для имени файла, если есть
    class_name_base = class_name.replace("Body", "").replace("Component", "")
    if module_type == 'c':
        filename = f"{class_name_base.lower()}_component.py"
        template = COMPONENT_TEMPLATE
        target_dir = "modules"
    elif module_type == 'b':
        filename = f"{class_name_base.lower()}_body.py"
        template = BODY_TEMPLATE
        target_dir = "bodies"

    filepath = os.path.join(target_dir, filename)

    # Проверяем, существует ли файл
    if os.path.exists(filepath):
        overwrite = input(f"File {filepath} already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Generation cancelled.")
            return

    # Генерируем содержимое
    content = template.format(class_name=class_name, filename=filename, class_name_base=class_name_base)

    # Создаём директорию, если не существует
    os.makedirs(target_dir, exist_ok=True)

    # Записываем файл
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully generated {filepath}")
        print("\n--- Generated Content Preview ---")
        print(content)
        print("-------------------------------")
    except Exception as e:
        print(f"Error writing file {filepath}: {e}")


if __name__ == "__main__":
    main()
