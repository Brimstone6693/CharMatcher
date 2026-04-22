# file: modules/example_component.py
from components import BaseComponent

class ExampleComponent(BaseComponent):
    def __init__(self, special_value=42):
        self.special_value = special_value

    def activate(self):
        print(f"ExampleComponent activated! Value: {self.special_value}")

    def to_dict(self):
        return {"type": "ExampleComponent", "special_value": self.special_value}

    @classmethod
    def from_dict(cls, data):
        return cls(data["special_value"])