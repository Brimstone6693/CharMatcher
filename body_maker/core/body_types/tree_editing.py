# file: body_type_manager/tree_editing.py
"""
Миксин для операций редактирования дерева частей тела.
Включает: переименование, inline-редактирование тегов, обработку кликов.
"""

import tkinter as tk
from tkinter import messagebox, ttk


class TreeEditingMixin:
    """Предоставляет операции редактирования дерева частей тела."""
    
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
                self._save_action_state("edit_tags", {
                    "part_name": part_name, 
                    "old_tags": self._get_part_tags(part_name), 
                    "new_tags": new_tags
                })
                
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
