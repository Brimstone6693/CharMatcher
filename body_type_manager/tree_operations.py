# file: body_type_manager/tree_operations.py
"""
Миксин для операций с деревом частей тела.
"""

import copy
import uuid
import tkinter as tk
from tkinter import messagebox, ttk


class TreeOperationsMixin:
    """Предоставляет операции с деревом частей тела."""
    
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
    
    def on_rename_part(self, item=None):
        """Переименовывает выбранную часть тела."""
        if item is None:
            selection = self.body_parts_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a part to rename.", parent=self.parent)
                return
            item = selection[0]
        
        old_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
        
        # Нельзя переименовать корневой элемент "Body"
        if old_name == "Body":
            messagebox.showwarning("Cannot Rename", "Cannot rename the root 'Body' part.", parent=self.parent)
            return
        
        # Создаем Entry прямо в дереве для inline редактирования
        name_entry = ttk.Entry(self.body_parts_tree)
        name_entry.insert(0, old_name)
        name_entry.select_range(0, 'end')
        
        # Размещаем Entry поверх текста элемента
        bbox = self.body_parts_tree.bbox(item, column="#0")
        if bbox:
            x, y, width, height = bbox
            name_entry.place(x=x, y=y, width=width + 50, height=height)
            name_entry.focus()
        
        def save_rename(event=None):
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=self.parent)
                name_entry.destroy()
                return
            
            if new_name == old_name:
                name_entry.destroy()
                return
            
            # Проверяем на дубликат у родителя
            parent_key = None
            for key, children in self.current_body_structure.items():
                for child in children:
                    child_name = child["name"] if isinstance(child, dict) else child
                    if child_name == old_name:
                        parent_key = key
                        break
                if parent_key:
                    break
            
            if parent_key:
                existing_names = set()
                for existing in self.current_body_structure.get(parent_key, []):
                    existing_name = existing["name"] if isinstance(existing, dict) else existing
                    existing_names.add(existing_name)
                
                if new_name in existing_names:
                    messagebox.showwarning("Duplicate Name", f"A part named '{new_name}' already exists under this parent.", parent=self.parent)
                    name_entry.destroy()
                    return
            
            # Сохраняем состояние для Undo
            self._save_action_state("rename", {"old_name": old_name, "new_name": new_name})
            
            # Обновляем структуру
            for key, children in self.current_body_structure.items():
                for i, child in enumerate(children):
                    child_name = child["name"] if isinstance(child, dict) else child
                    if child_name == old_name:
                        if isinstance(child, dict):
                            self.current_body_structure[key][i]["name"] = new_name
                        else:
                            self.current_body_structure[key][i] = new_name
                        break
            
            # Если у старого имени были дети, создаем запись для нового имени
            if old_name in self.current_body_structure:
                self.current_body_structure[new_name] = self.current_body_structure.pop(old_name)
            
            name_entry.destroy()
            self.update_body_parts_tree()
        
        name_entry.bind("<Return>", save_rename)
        name_entry.bind("<Escape>", lambda e: name_entry.destroy())
    
    def on_tree_double_click(self, event):
        """Обрабатывает двойной клик по дереву частей тела для переименования."""
        # Получаем элемент под курсором
        item = self.body_parts_tree.identify_row(event.y)
        if not item:
            return
        
        # Проверяем, что клик был по колонке с именем (#0)
        region = self.body_parts_tree.identify_element(event.x, event.y)
        if region and "text" in region or "tree" in region:
            self.on_rename_part(item)
    
    def on_edit_tags_inline(self):
        """Редактирует теги выбранной части через inline редактор."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a part to edit tags.", parent=self.parent)
            return
        
        item = selection[0]
        self._start_inline_edit(self.body_parts_tree, item, "tags")
    
    def _start_inline_edit(self, tree, item, field_type):
        """Запускает inline редактирование для указанного поля."""
        if field_type == "tags":
            # Получаем текущие теги
            values = tree.item(item, "values")
            current_tags_str = values[0] if values else ""
            # Преобразуем из "[tag1, tag2]" в "tag1, tag2"
            if current_tags_str.startswith("[") and current_tags_str.endswith("]"):
                current_tags_str = current_tags_str[1:-1]
            
            # Создаем Entry
            tags_entry = ttk.Entry(tree)
            tags_entry.insert(0, current_tags_str)
            tags_entry.select_range(0, 'end')
            
            # Размещаем Entry поверх колонки tags
            bbox = tree.bbox(item, column="tags")
            if bbox:
                x, y, width, height = bbox
                tags_entry.place(x=x, y=y, width=width, height=height)
                tags_entry.focus()
            
            def save_tags(event=None):
                new_tags_str = tags_entry.get().strip()
                # Преобразуем строку в список тегов
                new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()] if new_tags_str else []
                
                # Получаем имя части
                part_name = tree.item(item, "text").split(" [")[0]
                
                # Сохраняем состояние для Undo
                self._save_action_state("edit_tags", {"part_name": part_name, "old_tags": self._get_part_tags(part_name), "new_tags": new_tags})
                
                # Обновляем теги в структуре
                self._update_part_tags(part_name, new_tags)
                
                tags_entry.destroy()
                self.update_body_parts_tree()
            
            tags_entry.bind("<Return>", save_tags)
            tags_entry.bind("<Escape>", lambda e: tags_entry.destroy())
    
    def _get_part_tags(self, part_name):
        """Получает текущие теги указанной части."""
        for key, children in self.current_body_structure.items():
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == part_name:
                    if isinstance(child, dict):
                        return child.get("tags", [])
                    else:
                        return []
        return []
    
    def _update_part_tags(self, part_name, new_tags):
        """Обновляет теги указанной части."""
        for key, children in self.current_body_structure.items():
            for i, child in enumerate(children):
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == part_name:
                    if isinstance(child, dict):
                        self.current_body_structure[key][i]["tags"] = new_tags
                    else:
                        # Преобразуем строку в словарь с тегами
                        self.current_body_structure[key][i] = {"name": child_name, "tags": new_tags}
                    return
    
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
        """Извлекает полную структуру части включая всех потомков."""
        result = {"name": part_name, "children": []}
        
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
        """Рекурсивно вставляет часть и её потомков."""
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
        
        self.current_body_structure[parent_key].append({"name": new_name, "tags": []})
        
        # Добавляем новое имя в посещенные
        visited.add(new_name)
        
        # Рекурсивно добавляем детей
        for child in part_structure.get("children", []):
            self._paste_part_recursive(child, new_name, visited.copy())
    
    def on_tree_right_click(self, event):
        """Обрабатывает правый клик по дереву частей тела."""
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
    
    def _update_add_tag_menu(self):
        """Обновляет подменю для добавления тегов."""
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
                    self.add_tag_menu.add_command(label=tag_name, command=lambda t=tag_name: self._apply_tag_to_selected_part(t))
            else:
                # Если тегов много, создаем подменю
                category_menu = tk.Menu(self.add_tag_menu, tearoff=0)
                self.add_tag_menu.add_cascade(label=category, menu=category_menu)
                for tag_data in tags:
                    tag_name = tag_data["name"]
                    category_menu.add_command(label=tag_name, command=lambda t=tag_name: self._apply_tag_to_selected_part(t))
        
        # Добавляем пункт для создания своего тега
        self.add_tag_menu.add_separator()
        self.add_tag_menu.add_command(label="➕ Create Custom Tag...", command=self.on_add_custom_tag)
    
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
            self._save_action_state("edit_tags", {"part_name": part_name, "old_tags": current_tags, "new_tags": new_tags})
            self._update_part_tags(part_name, new_tags)
            self.update_body_parts_tree()
    
    def on_add_custom_tag(self):
        """Создает новый пользовательский тег."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create Custom Tag")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tag Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Category:").pack(pady=5)
        category_entry = ttk.Entry(dialog, width=40)
        category_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description:").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=40)
        desc_entry.pack(pady=5)
        
        def confirm():
            name = name_entry.get().strip()
            category = category_entry.get().strip() or "Custom"
            description = desc_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Invalid Input", "Tag name cannot be empty.", parent=dialog)
                return
            
            try:
                self.parts_db.add_tag(name=name, category=category, description=description)
                messagebox.showinfo("Success", f"Tag '{name}' created!", parent=dialog)
                dialog.destroy()
                # Обновляем меню тегов если оно открыто
                if hasattr(self, 'tree_menu'):
                    self._update_add_tag_menu()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        ttk.Button(dialog, text="Create", command=confirm).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
