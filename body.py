# file: body.py
from abc import ABC, abstractmethod

class AbstractBody(ABC):
    def __init__(self, race="Unknown", size="Medium"):
        self.race = race
        self.size = size
        # Иерархическая структура частей тела с тегами:
        # Формат: {parent: [{"name": "child1", "tags": ["tag1", "tag2"]}, ...], None: [...]}
        # Пример: {None: [{"name": "head", "tags": []}, {"name": "torso", "tags": ["core"]}], 
        #          "head": [{"name": "eyes", "tags": ["sensory", "vision"]}, {"name": "mouth", "tags": ["eating"]}], 
        #          "mouth": [{"name": "teeth", "tags": ["weapon", "bone"]}, {"name": "tongue", "tags": ["sensory", "taste"]}]}
        self.body_structure = {None: []}

    @abstractmethod
    def describe_appearance(self):
        """Возвращает строку с описанием тела."""
        pass

    def _normalize_part(self, part):
        """Нормализует часть тела до формата словаря {name, tags}."""
        if isinstance(part, str):
            return {"name": part, "tags": []}
        elif isinstance(part, dict):
            return {"name": part.get("name", ""), "tags": list(part.get("tags", []))}
        return part

    def get_all_parts(self):
        """Возвращает плоский список всех частей тела (словари)."""
        all_parts = []
        for children in self.body_structure.values():
            for child in children:
                all_parts.append(self._normalize_part(child))
        return all_parts

    def get_part_names(self):
        """Возвращает плоский список имен всех частей тела."""
        return [p["name"] for p in self.get_all_parts()]

    def get_children(self, part_name):
        """Возвращает список дочерних частей для указанной части тела (словари)."""
        children = self.body_structure.get(part_name, [])
        return [self._normalize_part(c) for c in children]

    def get_children_names(self, part_name):
        """Возвращает список имен дочерних частей."""
        return [c["name"] if isinstance(c, dict) else c for c in self.body_structure.get(part_name, [])]

    def add_part(self, part_name, parent=None, tags=None):
        """Добавляет новую часть тела к указанному родителю с опциональными тегами."""
        if tags is None:
            tags = []
        
        if parent is not None and parent not in self.body_structure:
            # Если родитель существует как часть, но не имеет записи в словаре
            if parent not in self.get_part_names():
                raise ValueError(f"Parent part '{parent}' does not exist.")
            self.body_structure[parent] = []

        # Добавляем часть к родителю
        if parent not in self.body_structure:
            self.body_structure[parent] = []

        # Проверяем, существует ли уже такая часть у этого родителя
        existing_names = [self._normalize_part(c)["name"] for c in self.body_structure[parent]]
        if part_name not in existing_names:
            new_part = {"name": part_name, "tags": list(tags)}
            self.body_structure[parent].append(new_part)
            # Инициализируем запись для новой части (она может стать родителем)
            if part_name not in self.body_structure:
                self.body_structure[part_name] = []

        return True

    def remove_part(self, part_name):
        """Удаляет часть тела и все её дочерние части."""
        # Сначала удаляем из списка родителя
        for parent, children in list(self.body_structure.items()):
            normalized_children = [self._normalize_part(c) for c in children]
            names_to_remove = [i for i, c in enumerate(normalized_children) if c["name"] == part_name]
            for i in reversed(names_to_remove):
                children.pop(i)

        # Удаляем запись о детях этой части
        if part_name in self.body_structure:
            del self.body_structure[part_name]

        return True

    def add_tag_to_part(self, part_name, tag):
        """Добавляет тег к указанной части тела."""
        for parent, children in self.body_structure.items():
            for i, child in enumerate(children):
                normalized = self._normalize_part(child)
                if normalized["name"] == part_name:
                    if isinstance(child, dict):
                        if "tags" not in child:
                            child["tags"] = []
                        if tag not in child["tags"]:
                            child["tags"].append(tag)
                    else:
                        children[i] = {"name": part_name, "tags": [tag]}
                    return True
        return False

    def remove_tag_from_part(self, part_name, tag):
        """Удаляет тег из указанной части тела."""
        for parent, children in self.body_structure.items():
            for i, child in enumerate(children):
                normalized = self._normalize_part(child)
                if normalized["name"] == part_name:
                    if isinstance(child, dict) and "tags" in child:
                        if tag in child["tags"]:
                            child["tags"].remove(tag)
                    return True
        return False

    def get_tags_for_part(self, part_name):
        """Возвращает список тегов для указанной части тела."""
        for parent, children in self.body_structure.items():
            for child in children:
                normalized = self._normalize_part(child)
                if normalized["name"] == part_name:
                    return normalized.get("tags", [])
        return []

    def has_tag(self, part_name, tag):
        """Проверяет, есть ли у части тела указанный тег."""
        return tag in self.get_tags_for_part(part_name)

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
