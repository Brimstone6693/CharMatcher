# file: bodies/__init__.py
"""
Базовые классы для системы тел.
Заменяет удалённый модуль body.
"""

import uuid

def generate_short_id(length=6):
    """
    Генерирует короткий уникальный ID.
    
    Args:
        length: Длина ID (по умолчанию 6 символов)
        
    Returns:
        Строка с уникальным ID
    """
    return uuid.uuid4().hex[:length]


class AbstractBody:
    """
    Базовый абстрактный класс для всех типов тел.
    Определяет общий интерфейс и базовую функциональность.
    """
    
    def __init__(self, race="Unknown", size="Medium"):
        """
        Инициализирует базовое тело.
        
        Args:
            race: Раса существа
            size: Размер существа
        """
        self.race = race
        self.size = size
        self.body_structure = {}  # {parent_id: [{"part_id": id, "name": name, "tags": []}, ...]}
        self._name_to_id_cache = {}
        self._id_to_part_cache = {}
    
    def _rebuild_name_cache(self):
        """Перестраивает кэш имя->ID и ID->часть."""
        self._name_to_id_cache = {}
        self._id_to_part_cache = {}
        
        def traverse(parent_id):
            children = self.body_structure.get(parent_id, [])
            for child in children:
                part_id = child["part_id"]
                name = child["name"]
                self._name_to_id_cache[name] = part_id
                self._id_to_part_cache[part_id] = child
                traverse(part_id)
        
        traverse(None)
    
    def get_part_id_by_name(self, name):
        """Получает ID части по имени."""
        return self._name_to_id_cache.get(name)
    
    def get_part_by_id(self, part_id):
        """Получает часть по ID."""
        return self._id_to_part_cache.get(part_id)
    
    def get_part_children(self, part_id):
        """Получает дочерние части для данной части."""
        return self.body_structure.get(part_id, [])
    
    def add_part(self, parent_id, part_id, name, tags=None):
        """
        Добавляет новую часть тела.
        
        Args:
            parent_id: ID родительской части (None для корневых)
            part_id: Уникальный ID новой части
            name: Имя части
            tags: Список тегов
        """
        if tags is None:
            tags = []
        
        if parent_id not in self.body_structure:
            self.body_structure[parent_id] = []
        
        new_part = {"part_id": part_id, "name": name, "tags": tags}
        self.body_structure[parent_id].append(new_part)
        self.body_structure[part_id] = []  # Инициализируем список детей
        
        # Обновляем кэш
        self._name_to_id_cache[name] = part_id
        self._id_to_part_cache[part_id] = new_part
    
    def remove_part(self, part_id):
        """
        Удаляет часть тела и все её дочерние части.
        
        Args:
            part_id: ID удаляемой части
        """
        # Сначала рекурсивно удаляем всех потомков
        def collect_all_descendants(pid):
            descendants = []
            children = self.body_structure.get(pid, [])
            for child in children:
                descendants.append(child["part_id"])
                descendants.extend(collect_all_descendants(child["part_id"]))
            return descendants
        
        all_to_remove = collect_all_descendants(part_id)
        
        # Удаляем из кэша
        for pid in all_to_remove:
            part = self._id_to_part_cache.get(pid)
            if part:
                self._name_to_id_cache.pop(part["name"], None)
            self._id_to_part_cache.pop(pid, None)
            self.body_structure.pop(pid, None)
        
        # Удаляем саму часть из списка детей родителя
        for parent_id, children in self.body_structure.items():
            self.body_structure[parent_id] = [c for c in children if c["part_id"] != part_id]
        
        # Удаляем из кэша саму часть
        part = self._id_to_part_cache.get(part_id)
        if part:
            self._name_to_id_cache.pop(part["name"], None)
        self._id_to_part_cache.pop(part_id, None)
    
    def describe_appearance(self):
        """Возвращает описание внешности. Должен быть переопределён в подклассах."""
        return f"A {self.size} {self.race}."
    
    def to_dict(self):
        """Сериализует тело в словарь."""
        return {
            "race": self.race,
            "size": self.size,
            "body_structure": self.body_structure,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        """Десериализует тело из словаря."""
        body = cls(race=data.get("race", "Unknown"), size=data.get("size", "Medium"))
        body.body_structure = data.get("body_structure", {})
        body._rebuild_name_cache()
        return body