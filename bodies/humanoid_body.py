# file: bodies/humanoid_body.py
from body import AbstractBody

class HumanoidBody(AbstractBody):
    def __init__(self, race="Human", size="Medium", gender="Male"):
        super().__init__(race, size)
        self.gender = gender
        # Инициализируем иерархическую структуру частей тела
        # Формат: {parent: [child1, child2, ...], None: [корневые части]}
        self.body_structure = {
            None: ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
            "head": ["eyes", "ears", "mouth", "nose"],
            "mouth": ["teeth", "tongue"],
            "torso": []
        }

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a humanoid body."