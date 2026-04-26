# file: character.py
from core.body_types.body_classes import AbstractBody
from core.components import BaseComponent

class Character:
    def __init__(self, name="Unnamed", body: AbstractBody = None):
        self.name = name
        # Требуем, чтобы тело было передано явно.
        if body is None:
            raise ValueError("A 'body' object must be provided when creating a Character.")
        self.body = body
        # Словарь для хранения компонентов: {type(component_class): component_instance}
        self.components = {}

    def add_component(self, component: BaseComponent):
        """Добавляет компонент к персонажу. Перезаписывает, если компонент этого типа уже существует."""
        comp_type = type(component)
        self.components[comp_type] = component
        print(f"Added component: {comp_type.__name__}")

    def remove_component(self, component_type: type):
        """Удаляет компонент указанного типа."""
        if component_type in self.components:
            del self.components[component_type]
            print(f"Removed component: {component_type.__name__}")
        else:
            print(f"No component of type {component_type.__name__} found.")

    def has_component(self, component_type: type) -> bool:
        """Проверяет, есть ли компонент указанного типа."""
        return component_type in self.components

    def get_component(self, component_type: type):
        """Возвращает компонент указанного типа или None."""
        return self.components.get(component_type)

    def to_dict(self):
        return {
            "name": self.name,
            "body": self.body.to_dict(),
            "components": {comp_type.__name__: comp.to_dict() for comp_type, comp in self.components.items()}
        }

    @classmethod
    def from_dict(cls, data, available_component_classes, available_body_classes):
        # available_component_classes: {'Stats': Stats, ...}
        # available_body_classes: {'HumanoidBody': HumanoidBody, ...}
        name = data["name"]
        # !!! Передаём доступные тела в from_dict тела !!!
        body = AbstractBody.from_dict(data["body"], available_body_classes)
        # Теперь передаём созданное тело в конструктор
        char = cls(name=name, body=body)

        for comp_name, comp_data in data["components"].items():
            comp_class = available_component_classes.get(comp_name)
            if comp_class:
                comp_instance = comp_class.from_dict(comp_data)
                char.add_component(comp_instance)
                print(f"  Loaded component: {comp_name}")
            else:
                print(f"  WARNING: Component type '{comp_name}' not found during load. Skipping.")
                print(f"           Character will be loaded without this part of its functionality.")
        return char

    def describe(self):
        desc = f"Character: {self.name}\n"
        desc += f"Body: {self.body.describe_appearance()}\n"
        desc += "Components:\n"
        for comp_type, comp_instance in self.components.items():
            desc += f"  - {comp_type.__name__}: {comp_instance.to_dict()}\n"
        return desc