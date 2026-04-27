# file: body_type_manager/ui_tags_manager.py
"""
Миксин для управления менеджером тегов.
"""

import json
import tkinter as tk
from tkinter import messagebox, ttk, filedialog


class TagsManagerMixin:
    """Предоставляет функциональность менеджера тегов."""
    
    def toggle_tags_manager(self):
        """Показывает или скрывает панель менеджера тегов."""
        if self.tags_manager_visible:
            self.hide_tags_manager()
        else:
            self.show_tags_manager()
    
    def show_tags_manager(self):
        """Создает и показывает панель менеджера тегов."""
        # Показываем левый контейнер если скрыт
        self.left_panel_container.grid()
        
        if self.tags_manager_frame is not None:
            # Если фрейм уже создан, просто показываем его
            self.tags_manager_visible = True
            self.toggle_tags_manager_btn.config(text="🏷️ Hide Tags")
            # Скрываем список частей если он был виден (только одна вкладка активна)
            if self.parts_list_frame and self.parts_list_frame.winfo_viewable():
                self.parts_list_frame.grid_remove()
                self.parts_list_visible = False
                self.toggle_parts_list_btn.config(text="📋 List")
            self._update_left_panel_layout()
            self.update_tags_manager_tree()
            return
        
        # Создаем новую панель для менеджера тегов в левом контейнере
        self.tags_manager_frame = ttk.LabelFrame(self.left_panel_container, text="Tags Manager (Drag & Drop to Tree)", padding=5)
        self.tags_manager_frame.grid(row=0, column=0, sticky="nsew")
        self.tags_manager_frame.grid_columnconfigure(0, weight=1)
        self.tags_manager_frame.grid_rowconfigure(0, weight=1)
        
        # Настраиваем веса строк контейнера сразу после создания
        self.left_panel_container.grid_rowconfigure(0, weight=1)
        
        # Дерево с тегами
        columns = ("category", "description")
        self.tags_tree = ttk.Treeview(self.tags_manager_frame, columns=columns, show="tree headings", selectmode="extended")
        self.tags_tree.heading("#0", text="Tag Name")
        self.tags_tree.column("#0", width=200, minwidth=150)
        self.tags_tree.heading("category", text="Category")
        self.tags_tree.column("category", width=150, minwidth=100)
        self.tags_tree.heading("description", text="Description")
        self.tags_tree.column("description", width=300, minwidth=200)
        
        # Вертикальный скроллбар
        vsb = ttk.Scrollbar(self.tags_manager_frame, orient="vertical", command=self.tags_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        
        # Горизонтальный скроллбар
        hsb = ttk.Scrollbar(self.tags_manager_frame, orient="horizontal", command=self.tags_tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.tags_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tags_tree.grid(row=0, column=0, sticky="nsew")
        
        # Кнопки управления тегами
        tags_btn_frame = ttk.Frame(self.tags_manager_frame)
        tags_btn_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        ttk.Button(tags_btn_frame, text="➕ Add Tag", command=self.on_add_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(tags_btn_frame, text="✏️ Edit Tag", command=self.on_edit_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(tags_btn_frame, text="🗑️ Delete Tag", command=self.on_delete_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(tags_btn_frame, text="📁 Import Tags", command=self.on_import_tags).pack(side=tk.LEFT, padx=2)
        ttk.Button(tags_btn_frame, text="💾 Export Tags", command=self.on_export_tags).pack(side=tk.LEFT, padx=2)
        
        # Заполняем дерево тегами
        self.update_tags_manager_tree()
        
        # Drag and Drop поддержка
        self._setup_tags_drag_and_drop()
        
        self.tags_manager_visible = True
        self.toggle_tags_manager_btn.config(text="🏷️ Hide Tags")
        self._update_left_panel_layout()
    
    def hide_tags_manager(self):
        """Скрывает панель менеджера тегов."""
        if self.tags_manager_frame is not None:
            self.tags_manager_frame.grid_remove()
        
        # Показываем список частей если он был скрыт
        if self.parts_list_visible and self.parts_list_frame is not None:
            self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
            self._update_left_panel_layout()
        
        # Скрываем левый контейнер если список частей тоже скрыт
        if not self.parts_list_visible:
            self.left_panel_container.grid_remove()
        
        self.tags_manager_visible = False
        self.toggle_tags_manager_btn.config(text="🏷️ Tags")
    
    def _update_left_panel_layout(self):
        """Обновляет layout левой панели в зависимости от видимых элементов."""
        # Сначала сбрасываем все row weights
        self.left_panel_container.grid_rowconfigure(0, weight=0)
        self.left_panel_container.grid_rowconfigure(1, weight=0)
        
        # Определяем какие элементы фактически видны (не скрыты через grid_remove)
        parts_list_is_visible = (self.parts_list_visible and 
                                  self.parts_list_frame is not None and 
                                  self.parts_list_frame.winfo_viewable())
        tags_manager_is_visible = (self.tags_manager_visible and 
                                    self.tags_manager_frame is not None and 
                                    self.tags_manager_frame.winfo_viewable())
        
        # Если оба элемента видны, показываем их один под другим с равным весом
        if parts_list_is_visible and tags_manager_is_visible:
            self.left_panel_container.grid_rowconfigure(0, weight=1)
            self.left_panel_container.grid_rowconfigure(1, weight=1)
            if self.parts_list_frame:
                self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
            if self.tags_manager_frame:
                self.tags_manager_frame.grid(row=1, column=0, sticky="nsew")
        # Если только список частей виден - он занимает всё пространство
        elif parts_list_is_visible and not tags_manager_is_visible:
            self.left_panel_container.grid_rowconfigure(0, weight=1)
            if self.parts_list_frame:
                self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
            if self.tags_manager_frame:
                self.tags_manager_frame.grid_remove()
        # Если только теги видны - они занимают всё пространство
        elif not parts_list_is_visible and tags_manager_is_visible:
            self.left_panel_container.grid_rowconfigure(0, weight=1)
            if self.parts_list_frame:
                self.parts_list_frame.grid_remove()
            if self.tags_manager_frame:
                self.tags_manager_frame.grid(row=0, column=0, sticky="nsew")
        # Если ничего не видно - скрываем контейнер
        else:
            self.left_panel_container.grid_remove()
    
    def update_tags_manager_tree(self):
        """Обновляет дерево менеджера тегов."""
        if not hasattr(self, 'tags_tree') or self.tags_tree is None:
            return
        
        # Очищаем дерево
        for item in self.tags_tree.get_children():
            self.tags_tree.delete(item)
        
        # Получаем все теги из базы данных
        all_tags = self.parts_db.get_all_tags()
        
        # Группируем теги по категориям
        categories = {}
        for tag_data in all_tags:
            category = tag_data.get("category", "Uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(tag_data)
        
        # Добавляем узлы для каждой категории
        for category, tags in sorted(categories.items()):
            cat_id = self.tags_tree.insert("", "end", text=category, values=(category, ""), open=True)
            for tag_data in tags:
                self.tags_tree.insert(cat_id, "end", 
                                     text=tag_data["name"], 
                                     values=(category, tag_data.get("description", "")))
    
    def on_add_tag(self):
        """Добавляет новый тег через диалоговое окно."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Tag")
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
                self.parts_db.add_or_update_tag(name=name, category=category, description=description)
                messagebox.showinfo("Success", f"Tag '{name}' created!", parent=dialog)
                dialog.destroy()
                self.update_tags_manager_tree()
                # Обновляем меню тегов если оно открыто
                if hasattr(self, 'tree_menu'):
                    self._update_add_tag_menu()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        ttk.Button(dialog, text="Create", command=confirm).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def on_edit_tag(self):
        """Редактирует выбранный тег."""
        selection = self.tags_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tag to edit.", parent=self.parent)
            return
        
        item = selection[0]
        # Проверяем, что это не категория
        parent = self.tags_tree.parent(item)
        if not parent:
            messagebox.showwarning("Invalid Selection", "Please select a specific tag, not a category.", parent=self.parent)
            return
        
        tag_name = self.tags_tree.item(item, "text")
        category = self.tags_tree.item(item, "values")[0]
        description = self.tags_tree.item(item, "values")[1]
        
        # Получаем полные данные тега из базы
        all_tags = self.parts_db.get_all_tags()
        tag_data = next((t for t in all_tags if t["name"] == tag_name), None)
        
        if not tag_data:
            messagebox.showerror("Error", "Tag not found in database.", parent=self.parent)
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Tag")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tag Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.insert(0, tag_name)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Category:").pack(pady=5)
        category_entry = ttk.Entry(dialog, width=40)
        category_entry.insert(0, category)
        category_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description:").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=40)
        desc_entry.insert(0, description)
        desc_entry.pack(pady=5)
        
        def confirm():
            new_name = name_entry.get().strip()
            new_category = category_entry.get().strip() or "Custom"
            new_description = desc_entry.get().strip()
            
            if not new_name:
                messagebox.showwarning("Invalid Input", "Tag name cannot be empty.", parent=dialog)
                return
            
            try:
                self.parts_db.update_tag(old_name=tag_name, name=new_name, category=new_category, description=new_description)
                messagebox.showinfo("Success", f"Tag '{new_name}' updated!", parent=dialog)
                dialog.destroy()
                self.update_tags_manager_tree()
                if hasattr(self, 'tree_menu'):
                    self._update_add_tag_menu()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        ttk.Button(dialog, text="Save", command=confirm).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def on_delete_tag(self):
        """Удаляет выбранный тег."""
        selection = self.tags_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tag to delete.", parent=self.parent)
            return
        
        item = selection[0]
        # Проверяем, что это не категория
        parent = self.tags_tree.parent(item)
        if not parent:
            messagebox.showwarning("Invalid Selection", "Please select a specific tag, not a category.", parent=self.parent)
            return
        
        tag_name = self.tags_tree.item(item, "text")
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete tag '{tag_name}'?", parent=self.parent):
            return
        
        try:
            self.parts_db.delete_tag(tag_name)
            messagebox.showinfo("Success", f"Tag '{tag_name}' deleted!", parent=self.parent)
            self.update_tags_manager_tree()
            if hasattr(self, 'tree_menu'):
                self._update_add_tag_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self.parent)
    
    def on_import_tags(self):
        """Импортирует теги из JSON файла."""
        filepath = filedialog.askopenfilename(
            title="Import Tags",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
            
            count = 0
            for tag_data in tags_data:
                try:
                    self.parts_db.add_tag(
                        name=tag_data.get("name", ""),
                        category=tag_data.get("category", "Imported"),
                        description=tag_data.get("description", "")
                    )
                    count += 1
                except ValueError:
                    pass  # Пропускаем дубликаты
            
            messagebox.showinfo("Success", f"Imported {count} tags from file.", parent=self.parent)
            self.update_tags_manager_tree()
            if hasattr(self, 'tree_menu'):
                self._update_add_tag_menu()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import tags: {str(e)}", parent=self.parent)
    
    def on_export_tags(self):
        """Экспортирует теги в JSON файл."""
        filepath = filedialog.asksaveasfilename(
            title="Export Tags",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            all_tags = self.parts_db.get_all_tags()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_tags, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Exported {len(all_tags)} tags to file.", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export tags: {str(e)}", parent=self.parent)
    
    def _setup_tags_drag_and_drop(self):
        """Настраивает Drag and Drop для менеджера тегов."""
        self._drag_data = {"item": None}
        
        def on_drag_start(event):
            widget = event.widget
            item = widget.identify_row(event.y)
            if item:
                self._drag_data["item"] = item
                widget.selection_set(item)
        
        def on_drag_drop(event):
            widget = event.widget
            target_item = widget.identify_row(event.y)
            
            if self._drag_data["item"]:
                source_item = self._drag_data["item"]
                parent = widget.parent(source_item)
                
                # Проверяем, что это тег, а не категория
                if parent:
                    tag_name = widget.item(source_item, "text")
                    
                    # Применяем тег к выбранной части в дереве
                    tree_selection = self.body_parts_tree.selection()
                    if tree_selection:
                        self._apply_tag_to_selected_part(tag_name)
                    else:
                        messagebox.showwarning("No Selection", "Please select a part in the main tree first.", parent=self.parent)
            
            self._drag_data["item"] = None
        
        self.tags_tree.bind("<ButtonPress-1>", on_drag_start)
        self.tags_tree.bind("<ButtonRelease-1>", on_drag_drop)
