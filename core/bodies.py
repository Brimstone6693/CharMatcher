# file: body.py
from abc import ABC, abstractmethod
import uuid

def generate_short_id():
    """Генерирует короткий уникальный ID (8 символов)."""
    return uuid.uuid4().hex[:8]

class AbstractBody(ABC):
    def __init__(self, race="Unknown", size="Medium"):
        self.race = race
        self.size = size
        # Иерархическая структура частей тела с тегами и ID:
        # Формат: {parent_id: [{ "part_id": "short_id", "name": "child1", "tags": [ "tag1", "tag2"]}, ...], None: [...]}
        # Ключи словаря - это part_id родителей (или None для корневых элементов)
        # Пример: {None: [{"part_id": "a1b2c3d4", "name": "head", "tags": []}, {"part_id": "e5f6g7h8", "name": "torso", "tags": ["core"]}], 
        #          "a1b2c3d4": [{"part_id": "i9j0k1l2", "name": "eyes", "tags": ["sensory", "vision"]}]}
        self.body_structure = {None: []}
        # Маппинг name -> part_id для быстрого поиска (кэш)
        self._name_to_id_cache = {}
        self._rebuild_name_cache()

    @abstractmethod
    def describe_appearance(self):
        """Возвращает строку с описанием тела."""
        pass

    def _normalize_part(self, part):
        """Нормализует часть тела до формата словаря {part_id, name, tags}."""
        if isinstance(part, str):
            part_id = generate_short_id()
            return {"part_id": part_id, "name": part, "tags": []}
        elif isinstance(part, dict):
            return {
                "part_id": part.get("part_id", generate_short_id()),
                "name": part.get("name", ""),
                "tags": list(part.get("tags", []))
            }
        return part

    def _rebuild_name_cache(self):
        """Перестраивает кэш name -> part_id."""
        self._name_to_id_cache = {}
        for children in self.body_structure.values():
            for child in children:
                normalized = self._normalize_part(child)
                name = normalized["name"]
                part_id = normalized["part_id"]
                # Если имя встречается несколько раз, сохраняем первый ID
                if name not in self._name_to_id_cache:
                    self._name_to_id_cache[name] = part_id

    def _get_part_by_id(self, part_id):
        """Находит часть по ID и возвращает (parent_id, part_dict, index)."""
        for parent_id, children in self.body_structure.items():
            for i, child in enumerate(children):
                normalized = self._normalize_part(child)
                if normalized["part_id"] == part_id:
                    return parent_id, normalized, i
        return None, None, -1

    def _get_part_id_by_name(self, part_name):
        """Получает ID части по имени (возвращает первый найденный)."""
        return self._name_to_id_cache.get(part_name)

    def _get_parts_by_name(self, part_name):
        """Находит все части с указанным именем и возвращает список (parent_id, part_dict, index)."""
        results = []
        for parent_id, children in self.body_structure.items():
            for i, child in enumerate(children):
                normalized = self._normalize_part(child)
                if normalized["name"] == part_name:
                    results.append((parent_id, normalized, i))
        return results

    def get_all_parts(self):
        """Возвращает плоский список всех частей тела (словари с part_id, name, tags)."""
        all_parts = []
        for children in self.body_structure.values():
            for child in children:
                all_parts.append(self._normalize_part(child))
        return all_parts

    def get_part_names(self):
        """Возвращает плоский список имен всех частей тела."""
        return [p["name"] for p in self.get_all_parts()]

    def get_part_ids(self):
        """Возвращает плоский список ID всех частей тела."""
        return [p["part_id"] for p in self.get_all_parts()]

    def get_children(self, parent_id):
        """Возвращает список дочерних частей для указанной части тела по ID (словари)."""
        children = self.body_structure.get(parent_id, [])
        return [self._normalize_part(c) for c in children]

    def get_children_by_name(self, parent_name):
        """Возвращает список дочерних частей для указанной части тела по имени."""
        parent_id = self._get_part_id_by_name(parent_name)
        if parent_id:
            return self.get_children(parent_id)
        return []

    def get_children_names(self, parent_id):
        """Возвращает список имен дочерних частей по ID родителя."""
        return [c["name"] for c in self.get_children(parent_id)]

    def add_part(self, part_name, parent=None, tags=None, part_id=None):
        """Добавляет новую часть тела к указанному родителю с опциональными тегами и ID.
        
        Args:
            part_name: Имя новой части
            parent: ID родителя или None для корневых элементов
            tags: Список тегов
            part_id: Опциональный ID (если не указан, генерируется автоматически)
        """
        if tags is None:
            tags = []
        if part_id is None:
            part_id = generate_short_id()
        
        # Проверяем существует ли родитель по ID
        if parent is not None and parent not in self.body_structure:
            # Если родителя нет в структуре, проверяем существует ли он как часть
            found_parent = False
            for children in self.body_structure.values():
                for child in children:
                    normalized = self._normalize_part(child)
                    if normalized["part_id"] == parent:
                        found_parent = True
                        break
                if found_parent:
                    break
            if not found_parent:
                raise ValueError(f"Parent part with ID '{parent}' does not exist.")
            # Инициализируем запись для родителя
            self.body_structure[parent] = []

        # Добавляем часть к родителю
        if parent not in self.body_structure:
            self.body_structure[parent] = []

        # Проверяем, существует ли уже такая часть с таким именем у этого родителя
        existing_names = [self._normalize_part(c)["name"] for c in self.body_structure[parent]]
        if part_name not in existing_names:
            new_part = {"part_id": part_id, "name": part_name, "tags": list(tags)}
            self.body_structure[parent].append(new_part)
            # Инициализируем запись для новой части (она может стать родителем)
            if part_id not in self.body_structure:
                self.body_structure[part_id] = []
            # Обновляем кэш
            if part_name not in self._name_to_id_cache:
                self._name_to_id_cache[part_name] = part_id

        return True

    def remove_part(self, part_id):
        """Удаляет часть тела по ID и все её дочерние части."""
        # Находим часть по ID
        parent_id, part, index = self._get_part_by_id(part_id)
        if part is None:
            return False
        
        # Рекурсивно удаляем всех потомков
        children_to_remove = list(self.body_structure.get(part_id, []))
        for child in children_to_remove:
            child_normalized = self._normalize_part(child)
            self.remove_part(child_normalized["part_id"])
        
        # Удаляем из списка родителя
        if parent_id in self.body_structure:
            self.body_structure[parent_id] = [
                c for c in self.body_structure[parent_id]
                if self._normalize_part(c)["part_id"] != part_id
            ]
        
        # Удаляем запись о детях этой части
        if part_id in self.body_structure:
            del self.body_structure[part_id]
        
        # Перестраиваем кэш
        self._rebuild_name_cache()
        
        return True

    def remove_part_by_name(self, part_name):
        """Удаляет все части с указанным именем."""
        parts = self._get_parts_by_name(part_name)
        for parent_id, part, index in parts:
            self.remove_part(part["part_id"])
        return len(parts) > 0

    def add_tag_to_part(self, part_id, tag):
        """Добавляет тег к указанной части тела по ID."""
        parent_id, part, index = self._get_part_by_id(part_id)
        if part is None:
            return False
        
        # Находим оригинальный элемент в структуре
        original_child = self.body_structure[parent_id][index]
        if isinstance(original_child, dict):
            if "tags" not in original_child:
                original_child["tags"] = []
            if tag not in original_child["tags"]:
                original_child["tags"].append(tag)
        else:
            # Заменяем строку на словарь
            self.body_structure[parent_id][index] = {
                "part_id": part["part_id"],
                "name": part["name"],
                "tags": [tag]
            }
        return True

    def add_tag_to_part_by_name(self, part_name, tag):
        """Добавляет тег ко всем частям с указанным именем."""
        parts = self._get_parts_by_name(part_name)
        success = False
        for parent_id, part, index in parts:
            if self.add_tag_to_part(part["part_id"], tag):
                success = True
        return success

    def remove_tag_from_part(self, part_id, tag):
        """Удаляет тег из указанной части тела по ID."""
        parent_id, part, index = self._get_part_by_id(part_id)
        if part is None:
            return False
        
        original_child = self.body_structure[parent_id][index]
        if isinstance(original_child, dict) and "tags" in original_child:
            if tag in original_child["tags"]:
                original_child["tags"].remove(tag)
                return True
        return False

    def remove_tag_from_part_by_name(self, part_name, tag):
        """Удаляет тег из всех частей с указанным именем."""
        parts = self._get_parts_by_name(part_name)
        success = False
        for parent_id, part, index in parts:
            if self.remove_tag_from_part(part["part_id"], tag):
                success = True
        return success

    def get_tags_for_part(self, part_id):
        """Возвращает список тегов для указанной части тела по ID."""
        parent_id, part, index = self._get_part_by_id(part_id)
        if part is None:
            return []
        return part.get("tags", [])

    def get_tags_for_part_by_name(self, part_name):
        """Возвращает список тегов для первой найденной части с указанным именем."""
        part_id = self._get_part_id_by_name(part_name)
        if part_id:
            return self.get_tags_for_part(part_id)
        return []

    def has_tag(self, part_id, tag):
        """Проверяет, есть ли у части тела указанный тег (по ID)."""
        return tag in self.get_tags_for_part(part_id)

    def has_tag_by_name(self, part_name, tag):
        """Проверяет, есть ли у части тела указанный тег (по имени)."""
        part_id = self._get_part_id_by_name(part_name)
        if part_id:
            return self.has_tag(part_id, tag)
        return False

    def get_part_by_id(self, part_id):
        """Возвращает полную информацию о части по ID."""
        parent_id, part, index = self._get_part_by_id(part_id)
        return part

    def get_part_by_name(self, part_name):
        """Возвращает первую найденную часть по имени."""
        part_id = self._get_part_id_by_name(part_name)
        if part_id:
            return self.get_part_by_id(part_id)
        return None

    def to_dict(self):
        # Общая логика для всех тел
        return {"race": self.race, "size": self.size, "__class__": self.__class__.__name__, "body_structure": self.body_structure}

    @classmethod
    def from_dict(cls, data, available_body_classes):
        # available_body_classes: {'HumanoidBody': HumanoidBody, 'GhostBody': GhostBody, ...}
        # Восстановление конкретного типа тела из словаря доступных классов
        # Используем class_name вместо __class__ для JSON совместимости
        class_name = data.pop("class_name", None) or data.pop("__class__", None)
        if not class_name:
            raise ValueError("Body data must contain 'class_name' or '__class__' field")
        
        body_class = available_body_classes.get(class_name)
        if body_class:
            instance = body_class(**{k: v for k, v in data.items() if k != "body_structure"})
            # Восстанавливаем структуру частей тела
            if "body_structure" in data:
                raw_structure = data["body_structure"]
                # Конвертируем ключ "null" или "None" из строки обратно в None
                for null_key in ["null", "None"]:
                    if null_key in raw_structure:
                        raw_structure[None] = raw_structure.pop(null_key)
                        break
                
                # Нормализуем все части в списках до словарей {part_id, name, tags}
                normalized_structure = {}
                for key, parts_list in raw_structure.items():
                    normalized_list = []
                    for item in parts_list:
                        if isinstance(item, str):
                            # Старый формат без ID - генерируем новый
                            normalized_list.append({"part_id": generate_short_id(), "name": item, "tags": []})
                        elif isinstance(item, dict) and "name" in item:
                            # Поддерживаем оба формата: с part_id и без
                            normalized_item = {
                                "part_id": item.get("part_id", generate_short_id()),
                                "name": item["name"],
                                "tags": list(item.get("tags", []))
                            }
                            normalized_list.append(normalized_item)
                        else:
                            normalized_list.append(item)
                    normalized_structure[key] = normalized_list
                
                instance.body_structure = normalized_structure
                instance._rebuild_name_cache()
            return instance
        else:
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
            raw_structure = data["body_structure"]
            # Конвертируем ключ "null" или "None" из строки обратно в None
            for null_key in ["null", "None"]:
                if null_key in raw_structure:
                    raw_structure[None] = raw_structure.pop(null_key)
                    break
            
            # Нормализуем все части в списках до словарей {part_id, name, tags}
            normalized_structure = {}
            for key, parts_list in raw_structure.items():
                normalized_list = []
                for item in parts_list:
                    if isinstance(item, str):
                        # Старый формат без ID - генерируем новый
                        normalized_list.append({"part_id": generate_short_id(), "name": item, "tags": []})
                    elif isinstance(item, dict) and "name" in item:
                        # Поддерживаем оба формата: с part_id и без
                        normalized_item = {
                            "part_id": item.get("part_id", generate_short_id()),
                            "name": item["name"],
                            "tags": list(item.get("tags", []))
                        }
                        normalized_list.append(normalized_item)
                    else:
                        normalized_list.append(item)
                normalized_structure[key] = normalized_list
            
            instance.body_structure = normalized_structure
            instance._rebuild_name_cache()
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
        # Конвертируем ключ None в строку "null" для JSON совместимости
        if None in base_dict.get("body_structure", {}):
            base_dict["body_structure"]["null"] = base_dict["body_structure"].pop(None)
        # Удаляем __class__ так как мы используем class_name для JSON
        base_dict.pop("__class__", None)
        return base_dict


# Добавляем DynamicBody в доступные классы тел для загрузки
# Это нужно чтобы Character.from_dict мог загрузить DynamicBody из сохранений
AbstractBody._dynamic_body_class = DynamicBody


# --- Пример конкретных тел ---
# Примечание: Эти классы оставлены для обратной совместимости.
# Для новых типов тел рекомендуется использовать JSON файлы в bodies_data/

class HumanoidBody(AbstractBody):
    def __init__(self, race="Human", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        self.gender = kwargs.get('gender', gender)
        # Инициализируем иерархическую структуру частей тела с короткими ID
        # Формат: {parent_id: [{"part_id": "...", "name": "...", "tags": [...]}, ...], None: [...]}
        
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

class QuadrupedalBody(AbstractBody):
    def __init__(self, race="Wolf", size="Medium", gender="Male", **kwargs):
        super().__init__(race, size)
        self.gender = kwargs.get('gender', gender)
        # Инициализируем иерархическую структуру частей тела с короткими ID
        
        # Генерируем ID для всех частей
        head_id = generate_short_id()
        torso_id = generate_short_id()
        fl_leg_id = generate_short_id()
        fr_leg_id = generate_short_id()
        rl_leg_id = generate_short_id()
        rr_leg_id = generate_short_id()
        tail_id = generate_short_id()
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
                {"part_id": fl_leg_id, "name": "front_left_leg", "tags": []},
                {"part_id": fr_leg_id, "name": "front_right_leg", "tags": []},
                {"part_id": rl_leg_id, "name": "rear_left_leg", "tags": []},
                {"part_id": rr_leg_id, "name": "rear_right_leg", "tags": []},
                {"part_id": tail_id, "name": "tail", "tags": []}
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
            tail_id: []
        }
        self._rebuild_name_cache()

    def describe_appearance(self):
        return f"A {self.size} {self.gender} {self.race} with a quadrupedal body."

class GhostBody(AbstractBody):
    def __init__(self, race="Spirit", size="Medium", **kwargs):
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

# Убедитесь, что новые классы тел добавлены в папку bodies/ и загружаются module_loader
# Примечание: HumanoidBody, QuadrupedalBody, GhostBody оставлены для обратной совместимости
# Рекомендуется использовать JSON файлы в bodies_data/ для новых типов тел
