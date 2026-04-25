"""
Модуль базы данных частей тела (Body Parts Database)
Позволяет сохранять и загружать индивидуальные части и поддеревья
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class PartsDatabase:
    """База данных частей тела для хранения шаблонов частей и поддеревьев"""
    
    def __init__(self, db_path: str = "body_parts_db.json"):
        self.db_path = Path(db_path)
        self.data = {
            "individual_parts": [],  # Отдельные части с тегами
            "tree_templates": []     # Шаблоны поддеревьев
        }
        self.load()
    
    def load(self):
        """Загрузка базы данных из файла"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    # Убедимся, что есть оба раздела
                    if "individual_parts" not in self.data:
                        self.data["individual_parts"] = []
                    if "tree_templates" not in self.data:
                        self.data["tree_templates"] = []
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading database: {e}")
                self.data = {"individual_parts": [], "tree_templates": []}
    
    def save(self):
        """Сохранение базы данных в файл"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving database: {e}")
            return False
    
    # === Индивидуальные части ===
    
    def add_individual_part(self, name: str, tags: List[str], 
                           size_min: float = 0.0, size_max: float = 0.0,
                           description: str = "") -> Dict:
        """Добавить индивидуальную часть в базу"""
        part = {
            "id": len(self.data["individual_parts"]) + 1,
            "name": name.strip(),
            "tags": [tag.strip() for tag in tags if tag.strip()],
            "size_min": size_min,
            "size_max": size_max,
            "description": description.strip()
        }
        
        # Проверка на дубликаты
        for existing in self.data["individual_parts"]:
            if existing["name"].lower() == part["name"].lower():
                raise ValueError(f"Part with name '{name}' already exists")
        
        self.data["individual_parts"].append(part)
        self.save()
        return part
    
    def get_individual_parts(self, search_term: str = "", 
                            tag_filter: str = "") -> List[Dict]:
        """Получить список частей с фильтрацией"""
        results = []
        
        for part in self.data["individual_parts"]:
            # Поиск по имени
            if search_term and search_term.lower() not in part["name"].lower():
                continue
            
            # Фильтр по тегам
            if tag_filter:
                tag_lower = tag_filter.lower()
                if not any(tag_lower in tag.lower() for tag in part["tags"]):
                    continue
            
            results.append(part)
        
        return results
    
    def delete_individual_part(self, part_id: int) -> bool:
        """Удалить часть по ID"""
        for i, part in enumerate(self.data["individual_parts"]):
            if part["id"] == part_id:
                del self.data["individual_parts"][i]
                self.save()
                return True
        return False
    
    def update_individual_part(self, part_id: int, **kwargs) -> Optional[Dict]:
        """Обновить параметры части"""
        for part in self.data["individual_parts"]:
            if part["id"] == part_id:
                if "name" in kwargs:
                    part["name"] = kwargs["name"].strip()
                if "tags" in kwargs:
                    part["tags"] = [tag.strip() for tag in kwargs["tags"] if tag.strip()]
                if "size_min" in kwargs:
                    part["size_min"] = kwargs["size_min"]
                if "size_max" in kwargs:
                    part["size_max"] = kwargs["size_max"]
                if "description" in kwargs:
                    part["description"] = kwargs["description"].strip()
                
                self.save()
                return part
        return None
    
    # === Шаблоны деревьев ===
    
    def add_tree_template(self, name: str, tree_data: Dict, 
                         description: str = "") -> Dict:
        """Добавить шаблон дерева частей"""
        template = {
            "id": len(self.data["tree_templates"]) + 1,
            "name": name.strip(),
            "tree_data": tree_data,  # Структура дерева
            "description": description.strip(),
            "part_count": self._count_parts_in_tree(tree_data)
        }
        
        # Проверка на дубликаты
        for existing in self.data["tree_templates"]:
            if existing["name"].lower() == template["name"].lower():
                raise ValueError(f"Template with name '{name}' already exists")
        
        self.data["tree_templates"].append(template)
        self.save()
        return template
    
    def _count_parts_in_tree(self, tree_data: Dict) -> int:
        """Подсчитать количество частей в дереве"""
        count = 1  # Сам корень
        if "children" in tree_data:
            for child in tree_data["children"]:
                count += self._count_parts_in_tree(child)
        return count
    
    def get_tree_templates(self, search_term: str = "") -> List[Dict]:
        """Получить список шаблонов с фильтрацией"""
        results = []
        
        for template in self.data["tree_templates"]:
            if search_term and search_term.lower() not in template["name"].lower():
                continue
            results.append(template)
        
        return results
    
    def delete_tree_template(self, template_id: int) -> bool:
        """Удалить шаблон по ID"""
        for i, template in enumerate(self.data["tree_templates"]):
            if template["id"] == template_id:
                del self.data["tree_templates"][i]
                self.save()
                return True
        return False
    
    def get_tree_template(self, template_id: int) -> Optional[Dict]:
        """Получить шаблон по ID"""
        for template in self.data["tree_templates"]:
            if template["id"] == template_id:
                return template
        return None
    
    # === Статистика ===
    
    def get_stats(self) -> Dict:
        """Получить статистику базы данных"""
        return {
            "individual_parts_count": len(self.data["individual_parts"]),
            "tree_templates_count": len(self.data["tree_templates"]),
            "total_parts_in_templates": sum(
                t["part_count"] for t in self.data["tree_templates"]
            )
        }
    
    # === Методы для работы с тегами (для менеджера тегов) ===
    
    def add_or_update_tag(self, name: str, category: str = "General", description: str = ""):
        """Добавляет или обновляет тег в базе данных"""
        if not hasattr(self, 'tags'):
            self.tags = {}
        
        name = name.strip()
        category = category.strip() if category else "General"
        description = description.strip()
        
        self.tags[name] = {
            "name": name,
            "category": category,
            "description": description
        }
        self._save_tags()
    
    def get_all_tags(self) -> List[Dict]:
        """Возвращает список всех тегов"""
        if not hasattr(self, 'tags'):
            self.tags = {}
            self._load_tags()
        return list(self.tags.values())
    
    def get_tag_by_name(self, name: str) -> Optional[Dict]:
        """Возвращает информацию о теге по имени"""
        if not hasattr(self, 'tags'):
            self._load_tags()
        return self.tags.get(name)
    
    def delete_tag(self, name: str) -> bool:
        """Удаляет тег по имени"""
        if not hasattr(self, 'tags'):
            self._load_tags()
        
        if name in self.tags:
            del self.tags[name]
            self._save_tags()
            return True
        return False
    
    def _load_tags(self):
        """Загружает теги из файла"""
        tags_file = self.db_path.parent / "tags_db.json"
        if tags_file.exists():
            try:
                with open(tags_file, 'r', encoding='utf-8') as f:
                    self.tags = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.tags = {}
        else:
            self.tags = {}
    
    def _save_tags(self):
        """Сохраняет теги в файл"""
        if not hasattr(self, 'tags'):
            self.tags = {}
        
        tags_file = self.db_path.parent / "tags_db.json"
        try:
            with open(tags_file, 'w', encoding='utf-8') as f:
                json.dump(self.tags, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving tags: {e}")
            return False
    
    def import_tags_from_json(self, file_path: str):
        """Импортирует теги из JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            imported_tags = json.load(f)
        
        if not hasattr(self, 'tags'):
            self.tags = {}
        
        # merged_tags может быть списком или словарём
        if isinstance(imported_tags, list):
            for tag in imported_tags:
                if isinstance(tag, dict) and "name" in tag:
                    self.tags[tag["name"]] = tag
        elif isinstance(imported_tags, dict):
            self.tags.update(imported_tags)
        
        self._save_tags()
    
    def export_tags_to_json(self, file_path: str):
        """Экспортирует теги в JSON файл"""
        if not hasattr(self, 'tags'):
            self._load_tags()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(self.tags.values()), f, indent=2, ensure_ascii=False)
