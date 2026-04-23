# file: bodies/quadrupedal_body.py
from body import AbstractBody

class QuadrupedalBody(AbstractBody):
    def __init__(self, race="Wolf", size="Medium", gender="Male"):
        super().__init__(race, size)
        self.gender = gender
        # Инициализируем иерархическую структуру частей тела
        self.body_structure = {
            None: ["head", "torso", "front_left_leg", "front_right_leg", "rear_left_leg", "rear_right_leg", "tail"],
            "head": ["eyes", "ears", "mouth", "nose"],
            "mouth": ["teeth", "tongue"],
            "tail": []
        }

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a quadrupedal body."