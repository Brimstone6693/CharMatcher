# file: components.py
from abc import ABC, abstractmethod

class BaseComponent(ABC):
    """Базовый класс для всех компонентов персонажа."""

    @abstractmethod
    def to_dict(self):
        """Преобразует состояние компонента в словарь для сохранения."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """Создает экземпляр компонента из словаря (для загрузки)."""
        pass

# --- Примеры компонентов ---
class Stats(BaseComponent):
    def __init__(self, strength=10, dexterity=10, intelligence=10):
        self.attributes = {
            "strength": strength,
            "dexterity": dexterity,
            "intelligence": intelligence
        }

    def modify(self, attr_name, value):
        if attr_name in self.attributes:
            self.attributes[attr_name] += value

    def to_dict(self):
        return {"type": "Stats", "attributes": self.attributes}

    @classmethod
    def from_dict(cls, data):
        return cls(**data["attributes"])

class Inventory(BaseComponent):
    def __init__(self, items=None):
        self.items = items or []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def to_dict(self):
        return {"type": "Inventory", "items": self.items}

    @classmethod
    def from_dict(cls, data):
        return cls(data["items"])

class Personality(BaseComponent):
    def __init__(self, traits=None):
        self.traits = traits or {"brave": False, "shy": True}

    def set_trait(self, trait, value):
        self.traits[trait] = value

    def get_trait(self, trait):
        return self.traits.get(trait, None)

    def to_dict(self):
        return {"type": "Personality", "traits": self.traits}

    @classmethod
    def from_dict(cls, data):
        return cls(data["traits"])

# Пример "странного" компонента
class GhostlyFeatures(BaseComponent):
    def __init__(self, transparency=0.0, can_pass_through_walls=False):
        self.transparency = transparency
        self.can_pass_through_walls = can_pass_through_walls

    def haunt(self):
        print("Boo!")

    def to_dict(self):
        return {"type": "GhostlyFeatures", "transparency": self.transparency, "can_pass_through_walls": self.can_pass_through_walls}

    @classmethod
    def from_dict(cls, data):
        return cls(data["transparency"], data["can_pass_through_walls"])

# --- Не забудьте добавить новые компоненты в module_loader.py ---