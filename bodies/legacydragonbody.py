from body import AbstractBody

class LegacyDragonBody(AbstractBody):
    def __init__(self, race="Legacy Dragon", size="Huge", gender="male"):
        super().__init__(race, size)
        self.gender = gender
        
        # Иерархическая структура частей тела (Вариант В)
        # Формат: { Родитель: [Список_Детей] }
        # None обозначает корневые элементы
        self.body_structure = {
            None: ["Torso"],
            "Torso": ["Wings", "Paws", "Head"],
            "Paws": ["Claws"],
            "Head": ["Maw"],
            "Maw": ["Teeth"],
            "Wings": [],
            "Claws": [],
            "Teeth": []
        }

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race}"
