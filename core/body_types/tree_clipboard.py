# file: body_type_manager/tree_clipboard.py
"""
Миксин для операций буфера обмена с деревом частей тела.
Включает: копирование, вставку, извлечение структур.
"""

import copy
import uuid
from tkinter import messagebox


class TreeClipboardMixin:
    """Предоставляет операции буфера обмена для дерева частей тела."""
    
    def on_copy_parts(self):
        """Копирует выбранные части тела в буфер обмена."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select parts to copy.", parent=self.parent)
            return False
        
        # Извлекаем структуру выбранных частей
        self.clipboard_parts = []
        for item in selection:
            part_name = self.body_parts_tree.item(item, "text").split(" [")[0]
            part_structure = self._extract_part_structure(part_name)
            self.clipboard_parts.append(part_structure)
        
        return True
    
    def _extract_part_structure(self, part_name):
        """Извлекает полную структуру части включая всех потомков, теги и ID."""
        # Находим часть в структуре чтобы получить её теги и ID
        tags = []
        part_id = ""
        for parent_key, children in self.current_body_structure.items():
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == part_name:
                    if isinstance(child, dict):
                        tags = child.get("tags", [])
                        part_id = child.get("part_id", "")
                    break
        
        result = {"name": part_name, "tags": tags, "part_id": part_id, "children": []}
        
        children = self.current_body_structure.get(part_name, [])
        for child in children:
            child_name = child["name"] if isinstance(child, dict) else child
            child_structure = self._extract_part_structure(child_name)
            result["children"].append(child_structure)
        
        return result
    
    def on_paste_parts(self):
        """Вставляет скопированные части под выбранный элемент."""
        if not self.clipboard_parts:
            messagebox.showwarning("Clipboard Empty", "No parts copied to clipboard.", parent=self.parent)
            return
        
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parent part to paste to.", parent=self.parent)
            return
        
        parent_item = selection[0]
        parent_name = self.body_parts_tree.item(parent_item, "text").split(" [")[0]
        
        # Сохраняем состояние для Undo
        self._save_action_state("paste", {
            "parts": copy.deepcopy(self.clipboard_parts),
            "parent": parent_name
        })
        
        # Вставляем каждую скопированную часть
        for part_structure in self.clipboard_parts:
            self._paste_part_recursive(part_structure, parent_name)
        
        self.update_body_parts_tree()
    
    def _paste_part_recursive(self, part_structure, parent_key, visited=None):
        """Рекурсивно вставляет часть и её потомков с сохранением тегов и генерацией новых ID."""
        if visited is None:
            visited = set()
        
        part_name = part_structure["name"]
        
        # Проверяем на дубликат имени у родителя и добавляем суффикс если нужно
        existing_names = set()
        for existing in self.current_body_structure.get(parent_key, []):
            existing_name = existing["name"] if isinstance(existing, dict) else existing
            existing_names.add(existing_name)
        
        base_name = part_name
        counter = 1
        new_name = part_name
        while new_name in existing_names:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        if parent_key not in self.current_body_structure:
            self.current_body_structure[parent_key] = []
        
        # Извлекаем теги из структуры если они есть
        tags = part_structure.get("tags", [])
        
        # Генерируем новый уникальный ID для вставляемой части
        new_part_id = str(uuid.uuid4())
        
        self.current_body_structure[parent_key].append({"name": new_name, "tags": tags, "part_id": new_part_id})
        
        # Добавляем новое имя в посещенные
        visited.add(new_name)
        
        # Рекурсивно добавляем детей
        for child in part_structure.get("children", []):
            self._paste_part_recursive(child, new_name, visited.copy())
    
    def _apply_tag_to_selected_part(self, tag_name):
        """Применяет указанный тег к выбранной части."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a part first.", parent=self.parent)
            return
        
        item = selection[0]
        part_name = self.body_parts_tree.item(item, "text").split(" [")[0]
        
        # Получаем текущие теги
        current_tags = self._get_part_tags(part_name)
        
        # Добавляем тег если его еще нет
        if tag_name not in current_tags:
            new_tags = current_tags + [tag_name]
            # Сохраняем состояние для Undo
            self._save_action_state("edit_tags", {
                "part_name": part_name, 
                "old_tags": current_tags, 
                "new_tags": new_tags
            })
            self._update_part_tags(part_name, new_tags)
            self.update_body_parts_tree()
    
    def _update_add_tag_menu(self):
        """Обновляет подменю для добавления тегов."""
        import tkinter as tk
        from tkinter import ttk
        
        # Очищаем существующие пункты
        self.add_tag_menu.delete(0, 'end')
        
        # Получаем все теги из базы данных
        all_tags = self.parts_db.get_all_tags()
        
        # Группируем теги по категориям
        categories = {}
        for tag_data in all_tags:
            category = tag_data.get("category", "Uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(tag_data)
        
        # Создаем пункты меню для каждой категории
        for category, tags in sorted(categories.items()):
            if len(tags) <= 5:
                # Если тегов мало, показываем напрямую
                for tag_data in tags:
                    tag_name = tag_data["name"]
                    self.add_tag_menu.add_command(
                        label=tag_name, 
                        command=lambda t=tag_name: self._apply_tag_to_selected_part(t)
                    )
            else:
                # Если тегов много, создаем подменю
                category_menu = tk.Menu(self.add_tag_menu, tearoff=0)
                self.add_tag_menu.add_cascade(label=category, menu=category_menu)
                for tag_data in tags:
                    tag_name = tag_data["name"]
                    category_menu.add_command(
                        label=tag_name, 
                        command=lambda t=tag_name: self._apply_tag_to_selected_part(t)
                    )
        
        # Добавляем пункт для создания своего тега
        self.add_tag_menu.add_separator()
        self.add_tag_menu.add_command(label="➕ Create Custom Tag...", command=self.on_add_custom_tag)
    
    def on_tree_right_click(self, event):
        """Обрабатывает правый клик по дереву частей тела."""
        import tkinter as tk
        
        # Выбираем элемент под курсором
        item = self.body_parts_tree.identify_row(event.y)
        if item:
            self.body_parts_tree.selection_set(item)
        
        # Обновляем подменю тегов
        self._update_add_tag_menu()
        
        try:
            self.tree_menu.post(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()
