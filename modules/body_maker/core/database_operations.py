# file: body_type_manager/database_operations.py
"""
Миксин для операций с базой данных частей тела.
"""

import copy
import tkinter as tk
from tkinter import messagebox, ttk


class DatabaseOperationsMixin:
    """Предоставляет операции сохранения/загрузки из базы данных."""
    
    def on_save_part_to_db(self):
        """Сохраняет выбранную часть тела в базу данных"""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a part to save.", parent=self.parent)
            return
        
        item = selection[0]
        part_name = self.body_parts_tree.item(item, "text")
        tags_str = self.body_parts_tree.item(item, "values")[0] if self.body_parts_tree.item(item, "values") else ""
        tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()] if tags_str else []
        
        # Диалог для сохранения части
        dialog = tk.Toplevel(self.parent)
        dialog.title("Save Part to Database")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Part Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.insert(0, part_name)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Tags (comma-separated):").pack(pady=5)
        tags_entry = ttk.Entry(dialog, width=40)
        tags_entry.insert(0, ", ".join(tags))
        tags_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description (optional):").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=40)
        desc_entry.pack(pady=5)
        
        def confirm():
            name = name_entry.get().strip()
            tags_str = tags_entry.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            desc = desc_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            
            try:
                self.parts_db.add_individual_part(name=name, tags=tags, description=desc)
                messagebox.showinfo("Success", f"Part '{name}' saved to database!", parent=dialog)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        ttk.Button(dialog, text="Save", command=confirm).pack(pady=10)
    
    def on_load_part_from_db(self):
        """Загружает часть из базы данных и вставляет её как дочернюю к выбранной"""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parent part.", parent=self.parent)
            return
        
        parent_item = selection[0]
        parent_name = self.body_parts_tree.item(parent_item, "text").split(" [")[0]  # Убираем теги из имени
        
        # Диалог выбора части из базы
        dialog = tk.Toplevel(self.parent)
        dialog.title("Load Part from Database")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Search:").pack(pady=5)
        search_entry = ttk.Entry(dialog, width=50)
        search_entry.pack(pady=5)
        
        # Список частей
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        parts_listbox = tk.Listbox(list_frame, width=60, height=10)
        parts_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=parts_listbox.yview)
        parts_listbox.configure(yscrollcommand=parts_scrollbar.set)
        
        parts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        parts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Загрузка начального списка
        parts = self.parts_db.get_individual_parts()
        for part in parts:
            tags_str = ", ".join(part.get("tags", []))
            display = f"{part['name']} [{tags_str}]" if tags_str else part['name']
            parts_listbox.insert(tk.END, display)
        
        def on_search(event=None):
            search_term = search_entry.get().strip()
            parts_listbox.delete(0, tk.END)
            parts = self.parts_db.get_individual_parts(search_term=search_term)
            for part in parts:
                tags_str = ", ".join(part.get("tags", []))
                display = f"{part['name']} [{tags_str}]" if tags_str else part['name']
                parts_listbox.insert(tk.END, display)
        
        search_entry.bind("<KeyRelease>", on_search)
        
        def confirm():
            sel = parts_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a part.", parent=dialog)
                return
            
            display_text = parts_listbox.get(sel[0])
            part_name = display_text.split(" [")[0]
            
            # Находим часть в базе
            parts = self.parts_db.get_individual_parts()
            part_data = next((p for p in parts if p["name"] == part_name), None)
            
            if not part_data:
                messagebox.showerror("Error", "Part not found in database.", parent=dialog)
                return
            
            # Используем общую логику для добавления части
            new_name = self._add_part_to_body(part_data, parent_name)
            
            # Сохраняем состояние для Undo
            self._save_action_state("add_child", {
                "name": new_name,
                "tags": part_data.get("tags", []),
                "parent": parent_name
            })
            
            self.update_body_parts_tree()
            messagebox.showinfo("Success", f"Part '{part_name}' loaded and added to '{parent_name}'!", parent=dialog)
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Load", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_save_tree_to_db(self):
        """Сохраняет всё дерево или выбранное поддерево в базу данных как шаблон"""
        if not self.current_body_structure.get(None):
            messagebox.showwarning("Empty Structure", "No body structure to save.", parent=self.parent)
            return
        
        selection = self.body_parts_tree.selection()
        
        # Диалог для сохранения дерева
        dialog = tk.Toplevel(self.parent)
        dialog.title("Save Tree Template to Database")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Template Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description (optional):").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=40)
        desc_entry.pack(pady=5)
        
        def confirm():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Invalid Input", "Template name cannot be empty.", parent=dialog)
                return
            
            # Формируем структуру дерева
            def build_tree_dict(part_name, visited=None):
                if visited is None:
                    visited = set()
                
                # Detect cycles to prevent infinite recursion
                if part_name in visited:
                    return {"name": part_name, "tags": [], "children": [], "_cycle_detected": True}
                
                visited.add(part_name)
                
                # Извлекаем теги части
                tags = []
                for parent_key, children in self.current_body_structure.items():
                    for child in children:
                        child_name = child["name"] if isinstance(child, dict) else child
                        if child_name == part_name and isinstance(child, dict):
                            tags = child.get("tags", [])
                            break
                
                result = {"name": part_name, "tags": tags, "children": []}
                children = self.current_body_structure.get(part_name, [])
                for child in children:
                    child_name = child["name"] if isinstance(child, dict) else child
                    result["children"].append(build_tree_dict(child_name, visited.copy()))
                return result
            
            # Если есть выделение, сохраняем только поддерево
            if selection:
                item = selection[0]
                root_name = self.body_parts_tree.item(item, "text").split(" [")[0]  # Убираем теги из имени
                tree_data = build_tree_dict(root_name)
            else:
                # Сохраняем всё дерево от корня
                root_parts = self.current_body_structure.get(None, [])
                tree_data = {"name": "Body", "children": []}
                for part in root_parts:
                    part_name = part["name"] if isinstance(part, dict) else part
                    if part_name != "Body":
                        tree_data["children"].append(build_tree_dict(part_name))
            
            try:
                self.parts_db.add_tree_template(name=name, tree_data=tree_data, description=desc)
                messagebox.showinfo("Success", f"Tree template '{name}' saved to database!", parent=dialog)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        ttk.Button(dialog, text="Save", command=confirm).pack(pady=10)
    
    def on_load_tree_from_db(self):
        """Загружает шаблон дерева из базы данных"""
        # Диалог выбора шаблона
        dialog = tk.Toplevel(self.parent)
        dialog.title("Load Tree Template from Database")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Search:").pack(pady=5)
        search_entry = ttk.Entry(dialog, width=50)
        search_entry.pack(pady=5)
        
        # Список шаблонов
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        templates_listbox = tk.Listbox(list_frame, width=60, height=10)
        templates_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=templates_listbox.yview)
        templates_listbox.configure(yscrollcommand=templates_scrollbar.set)
        
        templates_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        templates_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Загрузка начального списка
        templates = self.parts_db.get_tree_templates()
        for template in templates:
            display = f"{template['name']} ({template['part_count']} parts)"
            templates_listbox.insert(tk.END, display)
        
        def on_search(event=None):
            search_term = search_entry.get().strip()
            templates_listbox.delete(0, tk.END)
            templates = self.parts_db.get_tree_templates(search_term=search_term)
            for template in templates:
                display = f"{template['name']} ({template['part_count']} parts)"
                templates_listbox.insert(tk.END, display)
        
        search_entry.bind("<KeyRelease>", on_search)
        
        def confirm():
            sel = templates_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a template.", parent=dialog)
                return
            
            display_text = templates_listbox.get(sel[0])
            template_name = display_text.split(" (")[0]
            
            # Находим шаблон в базе
            templates = self.parts_db.get_tree_templates()
            template_data = next((t for t in templates if t["name"] == template_name), None)
            
            if not template_data:
                messagebox.showerror("Error", "Template not found in database.", parent=dialog)
                return
            
            # Получаем корневой элемент для вставки
            selection = self.body_parts_tree.selection()
            if selection:
                parent_item = selection[0]
                parent_name = self.body_parts_tree.item(parent_item, "text").split(" [")[0]  # Убираем теги из имени
            else:
                # Если нет выделения, добавляем к Body
                parent_name = "Body"
                if "Body" not in self.current_body_structure:
                    self.current_body_structure["Body"] = []
            
            # Добавляем дерево используя общую рекурсивную функцию
            tree_data = template_data["tree_data"]
            self._add_tree_to_body_recursive(tree_data, parent_name)
            
            # Сохраняем состояние для Undo
            self._save_action_state("paste_tree", {
                "tree_data": copy.deepcopy(tree_data),
                "parent": parent_name
            })
            
            self.update_body_parts_tree()
            messagebox.showinfo("Success", f"Tree template '{template_name}' loaded!", parent=dialog)
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Load", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_tree_to_body_recursive(self, tree_data, parent_key, visited=None):
        """
        Рекурсивно добавляет части дерева с защитой от дублирования имен и генерацией новых ID.
        Сохраняет теги из загружаемого дерева.
        """
        import uuid
        
        if visited is None:
            visited = set()
            
        part_name = tree_data["name"]
        
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
        
        # Извлекаем теги из tree_data (сохраняются при загрузке из базы)
        tags = tree_data.get("tags", [])
        # Генерируем новый уникальный ID для добавляемой части
        new_part_id = str(uuid.uuid4())
        self.current_body_structure[parent_key].append({"name": new_name, "tags": tags, "part_id": new_part_id})
        
        # Добавляем новое имя в посещенные
        visited.add(new_name)
        
        if "children" in tree_data:
            for child in tree_data["children"]:
                self._add_tree_to_body_recursive(child, new_name, visited.copy())
