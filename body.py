# file: body.py
from abc import ABC, abstractmethod

class AbstractBody(ABC):
    def __init__(self, race="Unknown", size="Medium"):
        self.race = race
        self.size = size
        # Иерархическая структура частей тела: {parent: [child1, child2, ...], None: [root_parts]}
        # Пример: {None: ["head", "torso"], "head": ["eyes", "mouth", "ears"], "mouth": ["teeth", "tongue"]}
        self.body_structure = {None: []}

    @abstractmethod
    def describe_appearance(self):
        """Возвращает строку с описанием тела."""
        pass

    def get_all_parts(self):
        """Возвращает плоский список всех частей тела."""
        all_parts = []
        for children in self.body_structure.values():
            all_parts.extend(children)
        return all_parts

    def get_children(self, part_name):
        """Возвращает список дочерних частей для указанной части тела."""
        return self.body_structure.get(part_name, [])

    def add_part(self, part_name, parent=None):
        """Добавляет новую часть тела к указанному родителю."""
        if parent is not None and parent not in self.body_structure:
            # Если родитель существует как часть, но не имеет записи в словаре
            if parent not in self.get_all_parts():
                raise ValueError(f"Parent part '{parent}' does not exist.")
            self.body_structure[parent] = []

        # Добавляем часть к родителю
        if parent not in self.body_structure:
            self.body_structure[parent] = []

        if part_name not in self.body_structure[parent]:
            self.body_structure[parent].append(part_name)
            # Инициализируем запись для новой части (она может стать родителем)
            if part_name not in self.body_structure:
                self.body_structure[part_name] = []

        return True

    def remove_part(self, part_name):
        """Удаляет часть тела и все её дочерние части."""
        # Сначала удаляем из списка родителя
        for parent, children in list(self.body_structure.items()):
            if part_name in children:
                children.remove(part_name)

        # Удаляем запись о детях этой части
        if part_name in self.body_structure:
            del self.body_structure[part_name]

        # Рекурсивно удаляем всех потомков
        # (они уже были удалены из списков детей при удалении part_name)
        return True

    def to_dict(self):
        # Общая логика для всех тел
        return {"race": self.race, "size": self.size, "__class__": self.__class__.__name__, "body_structure": self.body_structure}

    @classmethod
    def from_dict(cls, data, available_body_classes):
        # available_body_classes: {'HumanoidBody': HumanoidBody, 'GhostBody': GhostBody, ...}
        # Восстановление конкретного типа тела из словаря доступных классов
        class_name = data.pop("__class__")
        body_class = available_body_classes.get(class_name)
        if body_class:
            instance = body_class(**{k: v for k, v in data.items() if k != "body_structure"})
            # Восстанавливаем структуру частей тела
            if "body_structure" in data:
                instance.body_structure = data["body_structure"]
            return instance
        else:
            # Если тело не найдено, можно попробовать загрузить базовое тело или вызвать ошибку
            # Пока бросим ошибку, как в предыдущей версии
            raise ValueError(f"Unknown Body type: {class_name}")


class DynamicBody(AbstractBody):
    """Класс для динамической загрузки тел из JSON файлов."""
    
    def __init__(self, race="Unknown", size="Medium", gender="N/A", display_name="Unknown", description_template=None, **kwargs):
        super().__init__(race, size)
        self.gender = gender
        self.display_name = display_name
        self.description_template = description_template
        # body_structure будет установлен через from_dict
    
    def describe_appearance(self):
        if self.description_template:
            try:
                return self.description_template.format(size=self.size, gender=self.gender, race=self.race, display_name=self.display_name)
            except KeyError:
                return f"A {self.size} {self.gender} {self.display_name}."
        return f"A {self.size} {self.gender} {self.display_name}."
    
    @classmethod
    def from_dict(cls, data):
        """Создает экземпляр DynamicBody из словаря данных JSON."""
        instance = cls(
            race=data.get("race", "Unknown"),
            size=data.get("size", "Medium"),
            gender=data.get("gender", "N/A"),
            display_name=data.get("display_name", "Unknown"),
            description_template=data.get("description_template")
        )
        if "body_structure" in data:
            instance.body_structure = data["body_structure"]
        return instance
    
    def to_dict(self):
        """Сериализует тело в словарь для сохранения в JSON."""
        base_dict = super().to_dict()
        base_dict.update({
            "gender": self.gender,
            "display_name": self.display_name,
            "description_template": self.description_template,
            "class_name": self.__class__.__name__
        })
        # Удаляем __class__ так как мы используем class_name для JSON
        base_dict.pop("__class__", None)
        return base_dict


# --- Пример конкретных тел ---
class HumanoidBody(AbstractBody):
    def __init__(self, race="Human", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе используем значение по умолчанию
        self.gender = kwargs.get('gender', gender)
        # Или просто self.gender = gender, если передаём напрямую
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

class QuadrupedalBody(AbstractBody):
    def __init__(self, race="Wolf", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе используем значение по умолчанию
        self.gender = kwargs.get('gender', gender)
        # Или просто self.gender = gender, если передаём напрямую
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

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium", **kwargs):
        super().__init__(race, size)
        # Извлекаем gender из kwargs, если передан, иначе игнорируем
        # self.gender = kwargs.get('gender', "N/A") # Если хотим добавить gender и тут
        # Инициализируем иерархическую структуру частей тела
        self.body_structure = {
            None: ["form"],
            "form": []
        }

    def describe_appearance(self):
        return f"A translucent {self.race} of {self.size} size."

# Убедитесь, что новые классы тел добавлены в папку bodies/ и загружаются module_loader
