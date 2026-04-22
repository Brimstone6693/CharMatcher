# file: bodies/quadrupedal_body.py
from body import AbstractBody

class QuadrupedalBody(AbstractBody):
    def __init__(self, race="Wolf", size="Medium", gender="Male"):
        super().__init__(race, size)
        self.gender = gender
        self.body_parts = ["head", "torso", "front_left_leg", "front_right_leg", "rear_left_leg", "rear_right_leg", "tail"]

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a quadrupedal body."