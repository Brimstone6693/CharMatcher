# file: bodies/legasy2dragonbody.py
from body import AbstractBody

class Legasy2DragonBody(AbstractBody):
    def __init__(self, race="Custom", size="Huge", gender="Male"):
        super().__init__(race, size)
        self.gender = gender
        self.body_structure = {None: ["Body"], "Body": ["Torso"], "Torso": ["Wings", "Tail", "Paws"], "Wings": ["R Wing", "L Wing"], "R Wing": [], "L Wing": [], "Tail": [], "Paws": []}

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race}"
