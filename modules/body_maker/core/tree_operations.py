# file: body_type_manager/tree_operations.py
"""
Миксин для базовых операций с деревом частей тела.
Включает: обновление дерева, добавление/удаление частей.
"""

import uuid
from tkinter import messagebox


class TreeOperationsMixin:
    """Предоставляет базовые операции с деревом частей тела."""
    
    def update_body_parts_tree(self):
        """Обновляет дерево частей тела на основе current_body_structure с сохранением состояния раскрытия."""
        # Сохраняем текущее состояние раскрытия узлов по их именам
        expanded_items = set()
        for item in self.body_parts_tree.get_children(""):
            if self.body_parts_tree.item(item, "open"):
                item_text = self.body_parts_tree.item(item)["text"].split(" [")[0]
                expanded_items.add(item_text)
                for child_item in self.body_parts_tree.get_children(item):
                    if self.body_parts_tree.item(child_item, "open"):
                        child_text = self.body_parts_tree.item(child_item)["text"].split(" [")[0]
                        expanded_items.add(f"{item_text}::{child_text}")
        
        # Очищаем дерево
        for item in self.body_parts_tree.get_children():
            self.body_parts_tree.delete(item)
        
        # Рекурсивно добавляем узлы
        def add_children(parent_node_id, parent_key, visited=None):
            if visited is None:
                visited = set()
            
            # Защита от циклических ссылок
            if parent_key in visited:
                return
            visited.add(parent_key)
            
            children = self.current_body_structure.get(parent_key, [])
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                child_tags = child.get("tags", []) if isinstance(child, dict) else []
                child_id = child.get("part_id", "") if isinstance(child, dict) else ""
                
                # Формируем текст для отображения с тегами
                display_text = child_name
                tags_display = f"[{', '.join(child_tags)}]" if child_tags else ""
                
                # Добавляем узел в дерево: text - имя, values - (теги, part_id)
                node_id = self.body_parts_tree.insert(parent_node_id, "end", text=display_text, values=(tags_display, child_id))
                
                # Проверяем, нужно ли раскрыть этот узел
                parent_path = ""
                if parent_key:
                    parent_path = f"{parent_key}::"
                item_path = f"{parent_path}{child_name}"
                if item_path in expanded_items or (not parent_key and child_name in expanded_items):
                    self.body_parts_tree.item(node_id, open=True)
                
                # Рекурсивно добавляем детей этого узла
                add_children(node_id, child_name, visited.copy())
        
        # Начинаем с корневых элементов (ключ None)
        root_parts = self.current_body_structure.get(None, [])
        for part in root_parts:
            part_name = part["name"] if isinstance(part, dict) else part
            part_tags = part.get("tags", []) if isinstance(part, dict) else []
            part_id = part.get("part_id", "") if isinstance(part, dict) else ""
            
            display_text = part_name
            tags_display = f"[{', '.join(part_tags)}]" if part_tags else ""
            
            node_id = self.body_parts_tree.insert("", "end", text=display_text, values=(tags_display, part_id))
            # Раскрываем корневые узлы по умолчанию
            self.body_parts_tree.item(node_id, open=True)
            add_children(node_id, part_name)
    
    def on_add_root_part(self):
        """Добавляет корневую часть тела (к ключу None) как дочернюю к Body с плейсхолдером вместо имени."""
        # Проверяем, существует ли корневой элемент "Body"
        root_parts = self.current_body_structure.get(None, [])
        body_exists = any((isinstance(p, dict) and p.get("name") == "Body") or p == "Body" for p in root_parts)
        
        if not body_exists:
            messagebox.showwarning("Error", "Root 'Body' part is missing. Please reinitialize the structure.", parent=self.parent)
            return
        
        # Генерируем уникальный ID для части
        part_id = str(uuid.uuid4())
        
        # Находим уникальное имя с плейсхолдером
        base_name = "New_Part"
        counter = 1
        new_name = base_name
        
        existing_names = set()
        for existing in self.current_body_structure.get("Body", []):
            existing_name = existing["name"] if isinstance(existing, dict) else existing
            existing_names.add(existing_name)
        
        while new_name in existing_names:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        # Добавляем как словарь с именем-плейсхолдером, пустыми тегами и ID в список детей "Body"
        if "Body" not in self.current_body_structure:
            self.current_body_structure["Body"] = []
        self.current_body_structure["Body"].append({"name": new_name, "tags": [], "part_id": part_id})
        if new_name not in self.current_body_structure:
            self.current_body_structure[new_name] = []
        
        # Сохраняем состояние для Undo
        self._save_action_state("add_root", {"name": new_name, "tags": [], "parent": "Body", "part_id": part_id})
        
        self.update_body_parts_tree()
        
        # Автоматически переходим в режим редактирования имени
        self._start_rename_mode(new_name)
    
    def _start_rename_mode(self, part_name):
        """Запускает режим переименования для указанной части."""
        # Находим элемент дерева по имени
        for item in self.body_parts_tree.get_children(""):
            text = self.body_parts_tree.item(item)["text"].split(" [")[0]
            if text == part_name:
                self.body_parts_tree.selection_set(item)
                self.body_parts_tree.focus(item)
                # Запускаем переименование
                self.on_rename_part()
                break
    
    def on_add_child_part(self):
        """Добавляет дочернюю часть к выбранному элементу с плейсхолдером вместо имени."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parent part first.", parent=self.parent)
            return
        
        # Получаем имя выбранной части
        selected_item = selection[0]
        parent_name = self.body_parts_tree.item(selected_item)["text"].split(" [")[0]
        
        # Генерируем уникальный ID для части
        part_id = str(uuid.uuid4())
        
        # Находим уникальное имя с плейсхолдером
        base_name = "New_Child"
        counter = 1
        new_name = base_name
        
        existing_names = set()
        for existing in self.current_body_structure.get(parent_name, []):
            existing_name = existing["name"] if isinstance(existing, dict) else existing
            existing_names.add(existing_name)
        
        while new_name in existing_names:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        # Добавляем как словарь с именем-плейсхолдером, пустыми тегами и ID
        if parent_name not in self.current_body_structure:
            self.current_body_structure[parent_name] = []
        
        self.current_body_structure[parent_name].append({"name": new_name, "tags": [], "part_id": part_id})
        if new_name not in self.current_body_structure:
            self.current_body_structure[new_name] = []
        
        # Сохраняем состояние для Undo
        self._save_action_state("add_child", {"name": new_name, "tags": [], "parent": parent_name, "part_id": part_id})
        
        self.update_body_parts_tree()
        
        # Автоматически переходим в режим редактирования имени
        self._start_rename_mode(new_name)
    
    def on_delete_part(self):
        """Удаляет выбранную часть тела и все её дочерние элементы."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a part to delete.", parent=self.parent)
            return
        
        # Нельзя удалить корневой элемент "Body"
        for item in selection:
            part_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
            if part_name == "Body":
                messagebox.showwarning("Cannot Delete", "Cannot delete the root 'Body' part.", parent=self.parent)
                return
        
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected part(s)?", parent=self.parent):
            return
        
        # Сохраняем состояние для Undo перед удалением
        self._save_action_state("delete", list(selection))
        
        # Удаляем выбранные части
        for item in selection:
            part_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
            
            # Находим родителя и удаляем из его списка детей
            for parent, children in self.current_body_structure.items():
                self.current_body_structure[parent] = [
                    c for c in children 
                    if not (isinstance(c, dict) and c.get("name") == part_name) and c != part_name
                ]
            
            # Удаляем сам ключ из структуры
            if part_name in self.current_body_structure:
                del self.current_body_structure[part_name]
        
        self.update_body_parts_tree()
    
