# file: body.py
from abc import ABC, abstractmethod

class AbstractBody(ABC):
    def __init__(self, race="Unknown", size="Medium"):
        self.race = race
        self.size = size

    @abstractmethod
    def describe_appearance(self):
        """Возвращает строку с описанием тела."""
        pass

    def to_dict(self):
        # Общая логика для всех тел
        return {"race": self.race, "size": self.size, "__class__": self.__class__.__name__}

    @classmethod
    def from_dict(cls, data, available_body_classes):
        # available_body_classes: {'HumanoidBody': HumanoidBody, 'GhostBody': GhostBody, ...}
        # Восстановление конкретного типа тела из словаря доступных классов
        class_name = data.pop("__class__")
        body_class = available_body_classes.get(class_name)
        if body_class:
            return body_class(**{k: v for k, v in data.items()})
        else:
            # Если тело не найдено, можно попробовать загрузить базовое тело или вызвать ошибку
            # Пока бросим ошибку, как в предыдущей версии
            raise ValueError(f"Unknown Body type: {class_name}")

# --- Пример конкретных тел ---
class HumanoidBody(AbstractBody):
    def __init__(self, race="Human", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе используем значение по умолчанию
        self.gender = kwargs.get('gender', gender)
        # Или просто self.gender = gender, если передаём напрямую
        self.gender = gender
        self.body_parts = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a humanoid body."

class QuadrupedalBody(AbstractBody):
    def __init__(self, race="Wolf", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе используем значение по умолчанию
        self.gender = kwargs.get('gender', gender)
        # Или просто self.gender = gender, если передаём напрямую
        self.gender = gender
        self.body_parts = ["head", "torso", "front_left_leg", "front_right_leg", "rear_left_leg", "rear_right_leg", "tail"]

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a quadrupedal body."

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе игнорируем
        # self.gender = kwargs.get('gender', "N/A") # Если хотим добавить gender и тут
        self.body_parts = ["form"] # Условно

    def describe_appearance(self):
        return f"A translucent {self.race} of {self.size} size."

# Убедитесь, что новые классы тел добавлены в папку bodies/ и загружаются module_loader