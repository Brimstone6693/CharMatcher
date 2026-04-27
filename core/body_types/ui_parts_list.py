# file: body_type_manager/ui_parts_list.py
"""
Миксин для управления списком всех частей тела (All Body Parts).
"""

import copy
from tkinter import messagebox, ttk


class PartsListMixin:
    """Предоставляет функциональность списка всех частей тела."""
    
    def toggle_parts_list(self):
        """Показывает или скрывает панель списка частей тела."""
        if self.parts_list_visible:
            self.hide_parts_list()
        else:
            self.show_parts_list()
    
    def show_parts_list(self):
        """Создает и показывает панель списка частей тела."""
        # Показываем левый контейнер если скрыт
        self.left_panel_container.grid()
        
        if self.parts_list_frame is not None:
            # Если фрейм уже создан, просто показываем его
            self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
            # Скрываем теги если они были видны (только одна вкладка активна)
            if self.tags_manager_visible:
                self.tags_manager_frame.grid_remove()
            self._update_left_panel_layout()
            self.parts_list_visible = True
            self.toggle_parts_list_btn.config(text="📋 Hide List")
            self.update_parts_list_tree()  # Обновляем данные при каждом показе
            return
        
        # Создаем новую панель для списка частей в левом контейнере
        self.parts_list_frame = ttk.LabelFrame(self.left_panel_container, text="All Body Parts (Multiple Roots)", padding=5)
        self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
        self.parts_list_frame.grid_columnconfigure(0, weight=1)
        self.parts_list_frame.grid_rowconfigure(0, weight=1)
        
        # Дерево со всеми частями (поддержка нескольких корневых узлов)
        columns = ("tags", "path")
        self.parts_list_tree = ttk.Treeview(self.parts_list_frame, columns=columns, show="tree headings", selectmode="extended")
        self.parts_list_tree.heading("#0", text="Bodypart")
        self.parts_list_tree.column("#0", width=200, minwidth=150)
        self.parts_list_tree.heading("tags", text="Tags")
        self.parts_list_tree.column("tags", width=150, minwidth=100)
        self.parts_list_tree.heading("path", text="Full Path")
        self.parts_list_tree.column("path", width=300, minwidth=200)
        
        # Вертикальный скроллбар
        vsb = ttk.Scrollbar(self.parts_list_frame, orient="vertical", command=self.parts_list_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        
        # Горизонтальный скроллбар
        hsb = ttk.Scrollbar(self.parts_list_frame, orient="horizontal", command=self.parts_list_tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.parts_list_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.parts_list_tree.grid(row=0, column=0, sticky="nsew")
        
        # Заполняем дерево всеми частями
        self.update_parts_list_tree()
        
        # Двойной клик для редактирования
        self.parts_list_tree.bind("<Double-1>", self.on_parts_list_double_click)
        
        # Настраиваем Drag and Drop для списка частей
        self._setup_parts_list_drag_and_drop()
        
        self.parts_list_visible = True
        self.toggle_parts_list_btn.config(text="📋 Hide List")
    
    def hide_parts_list(self):
        """Скрывает панель списка частей тела."""
        if self.parts_list_frame is not None:
            self.parts_list_frame.grid_remove()
        
        # Скрываем левый контейнер если теги тоже скрыты
        if not self.tags_manager_visible:
            self.left_panel_container.grid_remove()
        
        self.parts_list_visible = False
        self.toggle_parts_list_btn.config(text="📋 List")
    
    def update_parts_list_tree(self):
        """Обновляет дерево списка всех частей тела из базы данных."""
        if not hasattr(self, 'parts_list_tree') or self.parts_list_tree is None:
            return
        
        # Очищаем дерево
        for item in self.parts_list_tree.get_children():
            self.parts_list_tree.delete(item)
        
        # Получаем все индивидуальные части из базы
        individual_parts = self.parts_db.get_individual_parts()
        for part in individual_parts:
            tags_display = f"[{', '.join(part.get('tags', []))}]" if part.get('tags') else ""
            full_path = part['name']
            display_text = part['name']
            
            node_id = self.parts_list_tree.insert("", "end", text=display_text, values=(tags_display, full_path))
            self.parts_list_tree.item(node_id, open=True)
        
        # Получаем все шаблоны деревьев из базы
        tree_templates = self.parts_db.get_tree_templates()
        for tree in tree_templates:
            tags_display = f"[{', '.join(tree.get('tags', []))}]" if tree.get('tags') else ""
            full_path = tree['name']
            display_text = f"🌳 {tree['name']}"
            
            node_id = self.parts_list_tree.insert("", "end", text=display_text, values=(tags_display, full_path))
            self.parts_list_tree.item(node_id, open=True)
    
    def on_parts_list_double_click(self, event):
        """Обрабатывает двойной клик по списку частей для загрузки части в текущее тело."""
        selection = self.parts_list_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        display_text = self.parts_list_tree.item(item, "text")
        
        # Проверяем, является ли элемент составной частью (деревом)
        if display_text.startswith("🌳 "):
            # Это составная часть (дерево) - используем общую логику из on_load_tree_from_db
            tree_name = display_text[3:]  # Убираем эмодзи
            
            # Получаем данные дерева из базы
            trees = self.parts_db.get_tree_templates()
            tree_data = next((t for t in trees if t["name"] == tree_name), None)
            
            if not tree_data:
                messagebox.showerror("Error", "Tree template not found in database.", parent=self.parent)
                return
            
            # Проверяем выделение в основном дереве
            tree_selection = self.body_parts_tree.selection()
            if not tree_selection:
                messagebox.showwarning("No Selection", "Please select a parent part in the main tree first.", parent=self.parent)
                return
            
            parent_item = tree_selection[0]
            parent_name = self.body_parts_tree.item(parent_item, "text")
            
            # Используем общую рекурсивную функцию для добавления дерева
            self._add_tree_to_body_recursive(tree_data["tree_data"], parent_name)
            
            # Сохраняем состояние для Undo
            self._save_action_state("paste_tree", {
                "tree_data": copy.deepcopy(tree_data["tree_data"]),
                "parent": parent_name
            })
            
            self.update_body_parts_tree()
            self.update_parts_list_tree()  # Обновляем список частей после добавления
        else:
            # Это индивидуальная часть - используем общую логику из on_load_part_from_db
            part_name = display_text
            
            # Получаем данные части из базы
            parts = self.parts_db.get_individual_parts()
            part_data = next((p for p in parts if p["name"] == part_name), None)
            
            if not part_data:
                messagebox.showerror("Error", "Part not found in database.", parent=self.parent)
                return
            
            # Проверяем выделение в основном дереве
            tree_selection = self.body_parts_tree.selection()
            if not tree_selection:
                messagebox.showwarning("No Selection", "Please select a parent part in the main tree first.", parent=self.parent)
                return
            
            parent_item = tree_selection[0]
            parent_name = self.body_parts_tree.item(parent_item, "text")
            
            # Используем общую логику для добавления части
            new_name = self._add_part_to_body(part_data, parent_name)
            
            # Сохраняем состояние для Undo
            self._save_action_state("add_child", {
                "name": new_name,
                "tags": part_data.get("tags", []),
                "parent": parent_name
            })
            
            self.update_body_parts_tree()
            self.update_parts_list_tree()  # Обновляем список частей после добавления
    
    def _add_part_to_body(self, part_data, parent_name):
        """
        Добавляет часть к родителю с уникальным именем.
        Возвращает новое имя части.
        """
        import uuid
        
        # Проверяем на дубликат имени у родителя и добавляем суффикс если нужно
        existing_names = set()
        for existing in self.current_body_structure.get(parent_name, []):
            existing_name = existing["name"] if isinstance(existing, dict) else existing
            existing_names.add(existing_name)
        
        base_name = part_data["name"]
        counter = 1
        new_name = part_data["name"]
        while new_name in existing_names:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        # Генерируем новый уникальный ID для добавляемой части
        new_part_id = str(uuid.uuid4())
        
        # Добавляем часть к родителю с уникальным именем
        if parent_name not in self.current_body_structure:
            self.current_body_structure[parent_name] = []
        
        self.current_body_structure[parent_name].append({
            "name": new_name,
            "tags": part_data.get("tags", []),
            "part_id": new_part_id
        })
        
        return new_name
    
    def _setup_parts_list_drag_and_drop(self):
        """Настраивает Drag and Drop для списка частей тела."""
        # Инициализация переменных для drag-and-drop
        self._drag_data = {"item": None, "target": None}
        
        def on_drag_start(event):
            widget = event.widget
            item = widget.identify_row(event.y)
            if item:
                self._drag_data["item"] = item
                widget.selection_set(item)
        
        def on_drag_drop(event):
            widget = event.widget
            target_item = widget.identify_row(event.y)
            if target_item and self._drag_data["item"]:
                # Определяем тип элемента (часть или дерево)
                source_display = widget.item(self._drag_data["item"], "text")
                
                # Проверяем выделение в основном дереве
                tree_selection = self.body_parts_tree.selection()
                if not tree_selection:
                    messagebox.showwarning("No Selection", "Please select a parent part in the main tree first.", parent=self.parent)
                    return
                
                parent_item = tree_selection[0]
                parent_name = self.body_parts_tree.item(parent_item, "text")
                
                if source_display.startswith("🌳 "):
                    # Это дерево
                    tree_name = source_display[3:]
                    trees = self.parts_db.get_tree_templates()
                    tree_data = next((t for t in trees if t["name"] == tree_name), None)
                    
                    if tree_data:
                        self._add_tree_to_body_recursive(tree_data["tree_data"], parent_name)
                        self._save_action_state("paste_tree", {
                            "tree_data": copy.deepcopy(tree_data["tree_data"]),
                            "parent": parent_name
                        })
                else:
                    # Это индивидуальная часть
                    part_name = source_display
                    parts = self.parts_db.get_individual_parts()
                    part_data = next((p for p in parts if p["name"] == part_name), None)
                    
                    if part_data:
                        new_name = self._add_part_to_body(part_data, parent_name)
                        self._save_action_state("add_child", {
                            "name": new_name,
                            "tags": part_data.get("tags", []),
                            "parent": parent_name
                        })
                
                self.update_body_parts_tree()
                self.update_parts_list_tree()
            
            self._drag_data["item"] = None
        
        self.parts_list_tree.bind("<ButtonPress-1>", on_drag_start)
        self.parts_list_tree.bind("<ButtonRelease-1>", on_drag_drop)
