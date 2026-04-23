# file: bodies/ghost_body.py
from body import AbstractBody

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium"):
        super().__init__(race, size)
        # Инициализируем иерархическую структуру частей тела
        self.body_structure = {
            None: ["form"],
            "form": []
        }

    def describe_appearance(self):
        return f"A translucent {self.race} of {self.size} size."
