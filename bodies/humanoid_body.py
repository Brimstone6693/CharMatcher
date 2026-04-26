# file: bodies/humanoid_body.py
from bodies import AbstractBody, generate_short_id

class HumanoidBody(AbstractBody):
    def __init__(self, race="Human", size="Medium", gender="Male"):
        super().__init__(race, size)
        self.gender = gender
        # Инициализируем иерархическую структуру частей тела с короткими ID
        
        # Генерируем ID для всех частей
        head_id = generate_short_id()
        torso_id = generate_short_id()
        left_arm_id = generate_short_id()
        right_arm_id = generate_short_id()
        left_leg_id = generate_short_id()
        right_leg_id = generate_short_id()
        eyes_id = generate_short_id()
        ears_id = generate_short_id()
        mouth_id = generate_short_id()
        nose_id = generate_short_id()
        teeth_id = generate_short_id()
        tongue_id = generate_short_id()
        
        self.body_structure = {
            None: [
                {"part_id": head_id, "name": "head", "tags": []},
                {"part_id": torso_id, "name": "torso", "tags": []},
                {"part_id": left_arm_id, "name": "left_arm", "tags": []},
                {"part_id": right_arm_id, "name": "right_arm", "tags": []},
                {"part_id": left_leg_id, "name": "left_leg", "tags": []},
                {"part_id": right_leg_id, "name": "right_leg", "tags": []}
            ],
            head_id: [
                {"part_id": eyes_id, "name": "eyes", "tags": []},
                {"part_id": ears_id, "name": "ears", "tags": []},
                {"part_id": mouth_id, "name": "mouth", "tags": []},
                {"part_id": nose_id, "name": "nose", "tags": []}
            ],
            mouth_id: [
                {"part_id": teeth_id, "name": "teeth", "tags": []},
                {"part_id": tongue_id, "name": "tongue", "tags": []}
            ],
            torso_id: []
        }
        self._rebuild_name_cache()

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a humanoid body."