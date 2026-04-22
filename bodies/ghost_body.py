# file: bodies/ghost_body.py
from body import AbstractBody

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium"):
        super().__init__(race, size)
        self.body_parts = ["form"] # Условно

    def describe_appearance(self):
        return f"A translucent {self.race} of {self.size} size."
