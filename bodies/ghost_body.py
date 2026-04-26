# file: bodies/ghost_body.py
from bodies import AbstractBody, generate_short_id

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium"):
        super().__init__(race, size)
        # Инициализируем иерархическую структуру частей тела с короткими ID
        
        form_id = generate_short_id()
        
        self.body_structure = {
            None: [
                {"part_id": form_id, "name": "form", "tags": []}
            ],
            form_id: []
        }
        self._rebuild_name_cache()

    def describe_appearance(self):
        return f"A translucent {self.race} of {self.size} size."
