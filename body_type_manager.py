# file: body_type_manager.py
"""
Модуль для управления типами тел (Body Type Manager).
Инкапсулирует всю логику создания, редактирования, удаления и отображения типов тел.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR


class BodyTypeManager:
    """
    Класс для управления типами тел в GUI.
    Инкапсулирует всю логику работы с формами, деревьями частей тела и файлами JSON.
    """
    
    # Пороги размеров для standing height (человеческий стандарт)
    STANDING_SIZE_THRESHOLDS = [
        (30, "Tiny"),
        (100, "Small"),
        (180, "Medium"),
        (400, "Large"),
        (700, "Huge"),
        (float('inf'), "Gargantuan")
    ]
    
    # Пороги размеров для withers height (высота в холке)
    WITHERS_SIZE_THRESHOLDS = [
        (20, "Tiny"),
        (60, "Small"),
        (120, "Medium"),
        (250, "Large"),
        (450, "Huge"),
        (float('inf'), "Gargantuan")
    ]
    
    def __init__(self, parent_window):
        """
        Инициализирует менеджер типов тел.
        
        Args:
            parent_window: Родительское окно Tkinter
        """
        self.parent = parent_window
        self.available_components = {}
        self.available_bodies = {}
        
        # Переменные формы
        self.height_type_var = None
        self.auto_size_label = None
        self.current_body_structure = {}
        self.tree_expanded_items = set()
        self.body_parts_tree = None
        self.bodies_listbox = None
        self.body_list_menu = None
        
        # Буфер для копирования/вставки частей
        self.clipboard_parts = None
        
        # Загружаем доступные модули и тела
        self._reload_available_bodies()
    
    def _reload_available_bodies(self):
        """Перезагружает список доступных компонентов и тел."""
        self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
    
    def create_manage_bodies_screen(self):
        """
        Создает и показывает экран управления типами тел.
        Возвращает корневой фрейм экрана.
        """
        # Очищаем предыдущее содержимое
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Настраиваем основное окно с прокруткой
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(main_frame)
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set)
        
        # Привязка изменения размера окна для обновления ширины canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Привязка колесика мыши для прокрутки
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        frame = scrollable_frame
        
        ttk.Label(frame, text="Manage Body Types", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Форма добавления нового типа тела
        form_frame = ttk.LabelFrame(frame, text="Add New Body Type")
        form_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Имя класса
        ttk.Label(form_frame, text="Class Name (e.g., Insectoid):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.new_body_class_name_entry = ttk.Entry(form_frame)
        self.new_body_class_name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        ttk.Label(form_frame, text="('Body' will be added automatically)").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Отображаемое имя
        ttk.Label(form_frame, text="Display Name (e.g., Insectoid):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.new_body_display_name_entry = ttk.Entry(form_frame)
        self.new_body_display_name_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Размер - диапазон высоты/роста
        size_frame = ttk.LabelFrame(form_frame, text="Size Range")
        size_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        # Переключатель типа измерения
        self.height_type_var = tk.StringVar(value="standing")
        height_type_frame = ttk.Frame(size_frame)
        height_type_frame.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(height_type_frame, text="Standing Height", variable=self.height_type_var, value="standing").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(height_type_frame, text="Withers Height", variable=self.height_type_var, value="withers").pack(side=tk.LEFT)
        
        # Привязка события для обновления размера при переключении типа высоты
        self.height_type_var.trace_add('write', lambda *args: self.update_auto_size())
        
        # Поля ввода диапазона
        ttk.Label(size_frame, text="Min (cm):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(5, 0))
        self.new_body_height_min_entry = ttk.Entry(size_frame, width=10)
        self.new_body_height_min_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(0, 15))
        self.new_body_height_min_entry.insert(0, "150")
        
        ttk.Label(size_frame, text="Max (cm):").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(5, 0))
        self.new_body_height_max_entry = ttk.Entry(size_frame, width=10)
        self.new_body_height_max_entry.grid(row=1, column=3, sticky=tk.W, pady=5)
        self.new_body_height_max_entry.insert(0, "200")
        
        # Автоматическое описание размера (только для чтения)
        ttk.Label(size_frame, text="Auto Size Category:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(5, 0))
        self.auto_size_label = ttk.Label(size_frame, text="Medium", font=("Arial", 10, "bold"))
        self.auto_size_label.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(0, 15), columnspan=2)
        
        # Привязка событий для авто-обновления размера
        self.new_body_height_min_entry.bind('<KeyRelease>', self.update_auto_size)
        self.new_body_height_max_entry.bind('<KeyRelease>', self.update_auto_size)
        
        # Пол - выпадающий список + custom поле
        gender_frame = ttk.Frame(form_frame)
        gender_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(gender_frame, text="Gender:").pack(side=tk.LEFT, padx=(0, 10))
        self.new_body_gender_var = tk.StringVar(value="N/A")
        gender_combo = ttk.Combobox(gender_frame, textvariable=self.new_body_gender_var, 
                                    values=["Male", "Female", "Herm", "N/A", "Other"], state="readonly", width=12)
        gender_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(gender_frame, text="Custom (optional):").pack(side=tk.LEFT, padx=(10, 5))
        self.new_body_gender_custom_entry = ttk.Entry(gender_frame, width=20)
        self.new_body_gender_custom_entry.pack(side=tk.LEFT)
        
        # Части тела (интерактивное дерево)
        ttk.Label(form_frame, text="Body Parts Hierarchy:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Фрейм для дерева и кнопок
        tree_frame = ttk.Frame(form_frame)
        tree_frame.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0), rowspan=3)
        
        # Дерево для отображения иерархии с поддержкой множественного выбора
        columns = ("tags",)
        self.body_parts_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=8, selectmode="extended")
        self.body_parts_tree.heading("#0", text="Bodypart")
        self.body_parts_tree.column("#0", width=200)
        self.body_parts_tree.heading("tags", text="Tags")
        self.body_parts_tree.column("tags", width=150)
        
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient="vertical", command=self.body_parts_tree.yview)
        self.body_parts_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        self.body_parts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для дерева частей тела
        self.tree_menu = tk.Menu(self.parent, tearoff=0)
        self.tree_menu.add_command(label="Copy", command=self.on_copy_parts)
        self.tree_menu.add_command(label="Paste", command=self.on_paste_parts)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Add Child Part", command=self.on_add_child_part)
        self.tree_menu.add_command(label="Rename Part", command=self.on_rename_part)
        self.tree_menu.add_command(label="Delete Part", command=self.on_delete_part)
        
        # Привязка контекстного меню и горячих клавиш к дереву
        self.body_parts_tree.bind("<Button-3>", self.on_tree_right_click)
        self.body_parts_tree.bind("<Control-c>", lambda e: self.on_copy_parts())
        self.body_parts_tree.bind("<Control-v>", lambda e: self.on_paste_parts())
        self.body_parts_tree.bind("<Delete>", lambda e: self.on_delete_part())
        self.body_parts_tree.bind("<F2>", lambda e: self.on_rename_part())
        
        # Легенда убрана - она мешала и была избыточна
        
        # Кнопки управления деревом
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=8, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        add_root_btn = ttk.Button(btn_frame, text="Add Root Part", command=self.on_add_root_part)
        add_root_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        add_child_btn = ttk.Button(btn_frame, text="Add Child Part", command=self.on_add_child_part)
        add_child_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_part_btn = ttk.Button(btn_frame, text="Delete Part", command=self.on_delete_part)
        delete_part_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        rename_part_btn = ttk.Button(btn_frame, text="Rename Part", command=self.on_rename_part)
        rename_part_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        copy_part_btn = ttk.Button(btn_frame, text="Copy", command=self.on_copy_parts)
        copy_part_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        paste_part_btn = ttk.Button(btn_frame, text="Paste", command=self.on_paste_parts)
        paste_part_btn.pack(side=tk.LEFT)
        
        # Хранилище для структуры частей тела (словарь)
        self.current_body_structure = {None: []}
        # Хранилище состояния раскрытия дерева
        self.tree_expanded_items = set()
        
        # Описание внешности (шаблон)
        ttk.Label(form_frame, text="Appearance Description Template (use {size}, {gender}, {race}):").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.new_body_desc_template_entry = ttk.Entry(form_frame, width=60)
        self.new_body_desc_template_entry.grid(row=9, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        ttk.Label(form_frame, text="Example: A {size} {gender} {race} with an insectoid body.").grid(row=10, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        ttk.Label(form_frame, text="(Leave empty for default template)").grid(row=11, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Кнопка создания
        create_btn = ttk.Button(form_frame, text="Create Body Type", command=self.on_create_body_type_clicked)
        create_btn.grid(row=12, column=0, columnspan=2, pady=15)
        
        # Список существующих типов тел
        list_frame = ttk.LabelFrame(frame, text="Existing Body Types (Right-click for options)")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        self.bodies_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bodies_listbox.yview)
        self.bodies_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.bodies_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для списка тел
        self.body_list_menu = tk.Menu(self.parent, tearoff=0)
        self.body_list_menu.add_command(label="Load into Editor", command=self.on_load_body_to_editor)
        self.body_list_menu.add_command(label="Rename", command=self.on_rename_body_type)
        self.body_list_menu.add_command(label="Copy", command=self.on_copy_body_type)
        self.body_list_menu.add_command(label="Delete", command=self.on_delete_body_type)
        
        # Привязка контекстного меню к списку и горячих клавиш
        self.bodies_listbox.bind("<Button-3>", self.on_body_list_right_click)
        self.bodies_listbox.bind("<Double-Button-1>", lambda e: self.on_load_body_to_editor())
        self.bodies_listbox.bind("<Control-c>", lambda e: self.on_copy_body_type())
        self.bodies_listbox.bind("<Control-v>", lambda e: messagebox.showinfo("Info", "Paste is not available for body types list.", parent=self.parent))
        self.bodies_listbox.bind("<Delete>", lambda e: self.on_delete_body_type())
        
        # Заполняем список
        self.refresh_bodies_list()
        
        # Инициализируем дерево с обязательной корневой частью "Body"
        self.init_body_structure_with_root()
        
        # Кнопка назад
        back_btn = ttk.Button(frame, text="Back to Start", command=self.show_start_screen)
        back_btn.pack(pady=5)
        
        return main_frame
    
    def show_start_screen(self):
        """Возвращает к начальному экрану (делегирование родительскому окну)."""
        if hasattr(self.parent, 'show_start_screen'):
            self.parent.show_start_screen()
    
    def update_auto_size(self, event=None):
        """Автоматически определяет категорию размера на основе диапазона высоты."""
        try:
            min_height_str = self.new_body_height_min_entry.get().strip()
            max_height_str = self.new_body_height_max_entry.get().strip()
            
            # Защита от пустых значений и некорректного ввода
            if not min_height_str or not max_height_str:
                self.auto_size_label.config(text="Enter values")
                return
                
            min_height = float(min_height_str)
            max_height = float(max_height_str)
            
            # Защита от отрицательных чисел
            if min_height < 0 or max_height < 0:
                self.auto_size_label.config(text="No negatives")
                return
            
            # Защита от min > max
            if min_height > max_height:
                self.auto_size_label.config(text="Min > Max error")
                return
            
            # Используем среднее значение для определения категории
            avg_height = (min_height + max_height) / 2
            
            # Получаем тип измерения (standing или withers)
            height_type = self.height_type_var.get()
            
            # Определяем категорию размера на основе средней высоты
            if height_type == "standing":
                thresholds = self.STANDING_SIZE_THRESHOLDS
            else:  # withers
                thresholds = self.WITHERS_SIZE_THRESHOLDS
            
            size_category = "Unknown"
            for threshold, category in thresholds:
                if avg_height < threshold:
                    size_category = category
                    break
            
            self.auto_size_label.config(text=size_category)
        except ValueError:
            self.auto_size_label.config(text="Invalid input")
    
    def get_final_gender(self):
        """Возвращает итоговое значение пола с учётом custom поля."""
        base_gender = self.new_body_gender_var.get()
        custom_gender = self.new_body_gender_custom_entry.get().strip()
        
        if custom_gender:
            return custom_gender
        return base_gender if base_gender else "N/A"
    
    def init_body_structure_with_root(self):
        """Инициализирует структуру тела с обязательной корневой частью 'Body'."""
        self.current_body_structure = {None: ["Body"], "Body": []}
        self.update_body_parts_tree()
    
    def refresh_bodies_list(self):
        """Обновляет список отображаемых типов тел в ListBox."""
        self.bodies_listbox.delete(0, tk.END)
        for body_name in sorted(self.available_bodies.keys()):
            self.bodies_listbox.insert(tk.END, body_name)
    
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
        def add_children(parent_node_id, parent_key):
            children = self.current_body_structure.get(parent_key, [])
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                child_tags = child.get("tags", []) if isinstance(child, dict) else []
                
                # Формируем текст для отображения с тегами
                display_text = child_name
                tags_display = f"[{', '.join(child_tags)}]" if child_tags else ""
                
                # Добавляем узел в дерево: text - имя, values - теги
                node_id = self.body_parts_tree.insert(parent_node_id, "end", text=display_text, values=(tags_display,))
                
                # Проверяем, нужно ли раскрыть этот узел
                parent_path = ""
                if parent_key:
                    parent_path = f"{parent_key}::"
                item_path = f"{parent_path}{child_name}"
                if item_path in expanded_items or (not parent_key and child_name in expanded_items):
                    self.body_parts_tree.item(node_id, open=True)
                
                # Рекурсивно добавляем детей этого узла
                add_children(node_id, child_name)
        
        # Начинаем с корневых элементов (ключ None)
        root_parts = self.current_body_structure.get(None, [])
        for part in root_parts:
            part_name = part["name"] if isinstance(part, dict) else part
            part_tags = part.get("tags", []) if isinstance(part, dict) else []
            
            display_text = part_name
            tags_display = f"[{', '.join(part_tags)}]" if part_tags else ""
            
            node_id = self.body_parts_tree.insert("", "end", text=display_text, values=(tags_display,))
            # Раскрываем корневые узлы по умолчанию
            self.body_parts_tree.item(node_id, open=True)
            add_children(node_id, part_name)
    
    def on_add_root_part(self):
        """Добавляет корневую часть тела (к ключу None) как дочернюю к Body."""
        # Проверяем, существует ли корневой элемент "Body"
        root_parts = self.current_body_structure.get(None, [])
        body_exists = any((isinstance(p, dict) and p.get("name") == "Body") or p == "Body" for p in root_parts)
        
        if not body_exists:
            messagebox.showwarning("Error", "Root 'Body' part is missing. Please reinitialize the structure.", parent=self.parent)
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Root Body Part")
        dialog.geometry("350x180")
        # Центрируем диалог относительно родительского окна
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=5)
        entry.focus()
        
        ttk.Label(dialog, text="Tags (comma-separated, optional):").pack(pady=5)
        tags_entry = ttk.Entry(dialog, width=40)
        tags_entry.pack(pady=5)
        
        def confirm():
            name = entry.get().strip()
            tags_str = tags_entry.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            
            # Добавляем как словарь с именем и тегами в список детей "Body"
            if "Body" not in self.current_body_structure:
                self.current_body_structure["Body"] = []
            self.current_body_structure["Body"].append({"name": name, "tags": tags})
            if name not in self.current_body_structure:
                self.current_body_structure[name] = []
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=confirm).pack(pady=10)
    
    def on_add_child_part(self):
        """Добавляет дочернюю часть к выбранному элементу."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parent part first.", parent=self.parent)
            return
        
        # Получаем имя выбранной части
        selected_item = selection[0]
        parent_name = self.body_parts_tree.item(selected_item)["text"].split(" [")[0]
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Add Child to '{parent_name}'")
        dialog.geometry("350x180")
        # Центрируем диалог относительно родительского окна
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Child Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=5)
        entry.focus()
        
        ttk.Label(dialog, text="Tags (comma-separated, optional):").pack(pady=5)
        tags_entry = ttk.Entry(dialog, width=40)
        tags_entry.pack(pady=5)
        
        def confirm():
            name = entry.get().strip()
            tags_str = tags_entry.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            
            # Добавляем как словарь с именем и тегами
            if parent_name not in self.current_body_structure:
                self.current_body_structure[parent_name] = []
            
            self.current_body_structure[parent_name].append({"name": name, "tags": tags})
            if name not in self.current_body_structure:
                self.current_body_structure[name] = []
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=confirm).pack(pady=10)
    
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
    
    def on_rename_part(self):
        """Переименовывает выбранную часть тела."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a part to rename.", parent=self.parent)
            return
        
        old_name = self.body_parts_tree.item(selection[0])["text"].split(" [")[0]
        
        # Нельзя переименовать корневой элемент "Body"
        if old_name == "Body":
            messagebox.showwarning("Cannot Rename", "Cannot rename the root 'Body' part.", parent=self.parent)
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Rename '{old_name}'")
        dialog.geometry("350x150")
        # Центрируем диалог относительно родительского окна
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Name:").pack(pady=5)
        entry = ttk.Entry(dialog, width=40)
        entry.insert(0, old_name)
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Name cannot be empty.", parent=dialog)
                return
            
            if new_name == old_name:
                dialog.destroy()
                return
            
            # Проверяем на дубликат
            for parent, children in self.current_body_structure.items():
                for child in children:
                    child_name = child["name"] if isinstance(child, dict) else child
                    if child_name == new_name:
                        messagebox.showwarning("Duplicate", f"A part with name '{new_name}' already exists.", parent=dialog)
                        return
            
            # Переименовываем во всех местах
            # 1. В списках детей у родителей
            for parent, children in self.current_body_structure.items():
                for i, child in enumerate(children):
                    if isinstance(child, dict) and child.get("name") == old_name:
                        children[i]["name"] = new_name
                    elif child == old_name:
                        children[i] = new_name
            
            # 2. Ключ структуры (если есть)
            if old_name in self.current_body_structure:
                self.current_body_structure[new_name] = self.current_body_structure.pop(old_name)
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=10)
    
    def on_copy_parts(self):
        """Копирует выбранные части тела в буфер обмена."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select part(s) to copy.", parent=self.parent)
            return
        
        # Копируем выбранные части и их дочерние элементы
        self.clipboard_parts = []
        for item in selection:
            part_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
            part_tags = []
            tags_val = self.body_parts_tree.item(item)["values"]
            if tags_val and len(tags_val) > 0 and tags_val[0]:
                tags_str = tags_val[0].strip("[]")
                if tags_str:
                    part_tags = [t.strip() for t in tags_str.split(",")]
            
            # Копируем структуру части с детьми
            part_data = {"name": part_name, "tags": part_tags, "children": []}
            self._copy_subtree(part_name, part_data["children"])
            self.clipboard_parts.append(part_data)
        
        messagebox.showinfo("Copy", f"Copied {len(self.clipboard_parts)} part(s) to clipboard.", parent=self.parent)
    
    def _copy_subtree(self, part_name, children_list):
        """Рекурсивно копирует поддерево части."""
        children = self.current_body_structure.get(part_name, [])
        for child in children:
            child_name = child["name"] if isinstance(child, dict) else child
            child_tags = child.get("tags", []) if isinstance(child, dict) else []
            child_data = {"name": child_name, "tags": child_tags, "children": []}
            children_list.append(child_data)
            self._copy_subtree(child_name, child_data["children"])
    
    def on_paste_parts(self):
        """Вставляет части из буфера обмена к выбранному родителю или как корневые."""
        if not self.clipboard_parts:
            messagebox.showwarning("Clipboard Empty", "No parts to paste. Please copy parts first.", parent=self.parent)
            return
        
        selection = self.body_parts_tree.selection()
        if not selection:
            # Если ничего не выбрано, спрашиваем куда вставлять
            result = messagebox.askquestion("Paste Location", "No part selected. Paste as children of 'Body'?", parent=self.parent)
            if result == 'yes':
                parent_name = "Body"
            else:
                return
        else:
            parent_name = self.body_parts_tree.item(selection[0])["text"].split(" [")[0]
        
        # Вставляем скопированные части
        if parent_name not in self.current_body_structure:
            self.current_body_structure[parent_name] = []
        
        def add_part_with_children(part_data, parent_key):
            """Рекурсивно добавляет часть и её детей."""
            name = part_data["name"]
            tags = part_data.get("tags", [])
            
            # Проверяем на дубликат имени у родителя
            existing_names = set()
            for existing in self.current_body_structure.get(parent_key, []):
                existing_name = existing["name"] if isinstance(existing, dict) else existing
                existing_names.add(existing_name)
            
            # Если имя уже существует, добавляем суффикс
            base_name = name
            counter = 1
            while name in existing_names:
                name = f"{base_name}_{counter}"
                counter += 1
            
            self.current_body_structure[parent_key].append({"name": name, "tags": tags})
            if name not in self.current_body_structure:
                self.current_body_structure[name] = []
            
            # Добавляем детей
            for child_data in part_data.get("children", []):
                add_part_with_children(child_data, name)
        
        for part_data in self.clipboard_parts:
            add_part_with_children(part_data, parent_name)
        
        self.update_body_parts_tree()
        messagebox.showinfo("Paste", "Parts pasted successfully.", parent=self.parent)
    
    def on_create_body_type_clicked(self):
        """Обработчик создания нового типа тела через интерфейс."""
        class_name = self.new_body_class_name_entry.get().strip()
        display_name = self.new_body_display_name_entry.get().strip()
        
        # Получаем размер из авто-категории
        default_size = self.auto_size_label.cget("text")
        
        # Получаем пол с учётом custom поля
        default_gender = self.get_final_gender()
        
        desc_template = self.new_body_desc_template_entry.get().strip()
        
        # Валидация
        if not class_name:
            messagebox.showwarning("Invalid Input", "Class Name is required.")
            return
        
        if not display_name:
            display_name = class_name
        
        # Добавляем "Body" к имени класса если нет
        if not class_name.endswith("Body"):
            class_name = class_name + "Body"
        
        # Проверка на дубликат
        if class_name in self.available_bodies:
            messagebox.showwarning("Duplicate", f"A body type with class name '{class_name}' already exists.")
            return
        
        # Проверяем, есть ли корневые части
        if not self.current_body_structure[None]:
            messagebox.showwarning("Invalid Input", "Please add at least one root body part.")
            return
        
        # Шаблон описания теперь опционален - если пустой, будет использован дефолтный
        
        # Используем текущую структуру напрямую
        body_structure = dict(self.current_body_structure)
        
        # Конвертируем ключ None в строку "null" для JSON совместимости
        if None in body_structure:
            body_structure["null"] = body_structure.pop(None)
        
        # Если шаблон пустой, используем дефолтный
        if not desc_template:
            desc_template = f"A {{size}} {{gender}} {display_name}."
        
        # Получаем тип высоты (standing или withers)
        height_type = self.height_type_var.get()
        
        # Получаем диапазон высоты
        try:
            height_min = float(self.new_body_height_min_entry.get().strip())
            height_max = float(self.new_body_height_max_entry.get().strip())
        except ValueError:
            height_min = 150.0
            height_max = 200.0
        
        # Создаем словарь данных для JSON
        body_data = {
            "class_name": class_name,
            "race": "Custom",
            "size": default_size,
            "gender": default_gender if default_gender else "N/A",
            "display_name": display_name,
            "description_template": desc_template,
            "body_structure": body_structure,
            "height_type": height_type,
            "height_min_cm": height_min,
            "height_max_cm": height_max
        }
        
        # Сохранение файла JSON
        filename = f"{class_name.lower()}.json"
        filepath = os.path.join(BODIES_DATA_DIR, filename)
        
        # Создаем директорию bodies_data если нет
        os.makedirs(BODIES_DATA_DIR, exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(body_data, f, indent=4, ensure_ascii=False)
            print(f"GUI: Created new body type file: {filepath}")
            
            # Перезагрузка списка доступных тел
            self._reload_available_bodies()
            print(f"GUI: Reloaded modules. Now have {len(self.available_bodies)} bodies.")
            
            # Обновляем список в интерфейсе
            self.refresh_bodies_list()
            
            # Очищаем поля формы и дерево
            self.new_body_class_name_entry.delete(0, tk.END)
            self.new_body_display_name_entry.delete(0, tk.END)
            self.new_body_gender_var.set("N/A")
            self.new_body_gender_custom_entry.delete(0, tk.END)
            self.new_body_desc_template_entry.delete(0, tk.END)
            self.new_body_height_min_entry.delete(0, tk.END)
            self.new_body_height_min_entry.insert(0, "150")
            self.new_body_height_max_entry.delete(0, tk.END)
            self.new_body_height_max_entry.insert(0, "200")
            self.update_auto_size()  # Обновить авто-размер
            
            # Сбрасываем структуру и дерево
            self.current_body_structure = {None: []}
            self.update_body_parts_tree()
            
            messagebox.showinfo("Success", f"Successfully created new body type '{class_name}'!\nIt is now available for selection.")
            
        except Exception as e:
            messagebox.showerror("Creation Error", f"Failed to create body type file:\n{e}")
    
    def on_tree_right_click(self, event):
        """Обработчик правого клика по дереву частей тела."""
        # Выбираем элемент под курсором
        item = self.body_parts_tree.identify_row(event.y)
        if item:
            self.body_parts_tree.selection_set(item)
        
        # Показываем контекстное меню
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()
    
    def on_body_list_right_click(self, event):
        """Обработчик правого клика по списку типов тел."""
        # Выбираем элемент под курсором
        index = self.bodies_listbox.nearest(event.y)
        self.bodies_listbox.selection_clear(0, tk.END)
        self.bodies_listbox.selection_set(index)
        self.bodies_listbox.activate(index)
        
        # Показываем контекстное меню
        try:
            self.body_list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.body_list_menu.grab_release()
    
    def on_load_body_to_editor(self):
        """Загружает выбранный тип тела в редактор для просмотра/редактирования."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            return
        
        body_name = self.bodies_listbox.get(selection[0])
        # Получаем путь к файлу тела (JSON)
        filename = f"{body_name.lower()}.json"
        filepath = os.path.join(BODIES_DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File for '{body_name}' not found at {filepath}.")
            return
        
        try:
            # Загружаем данные из JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Заполняем поля формы
            self.new_body_class_name_entry.delete(0, tk.END)
            # Убираем "Body" из конца имени класса для отображения
            class_name = data.get("class_name", body_name)
            if class_name.endswith("Body"):
                class_name = class_name[:-4]
            self.new_body_class_name_entry.insert(0, class_name)
            
            display_name = data.get("display_name", body_name.replace("Body", ""))
            self.new_body_display_name_entry.delete(0, tk.END)
            self.new_body_display_name_entry.insert(0, display_name)
            
            # Размер и тип высоты - загружаем из данных или используем дефолтные значения
            height_type = data.get('height_type', 'standing')
            self.height_type_var.set(height_type)
            
            # Загружаем диапазон высот если есть, иначе определяем по размеру
            if 'height_min_cm' in data and 'height_max_cm' in data:
                min_h = data['height_min_cm']
                max_h = data['height_max_cm']
            else:
                # Для обратной совместимости используем примерные значения на основе категории размера
                size_category = data.get('size', 'Medium')
                height_ranges = {
                    "Tiny": (20, 50),
                    "Small": (50, 100),
                    "Medium": (150, 200),
                    "Large": (200, 350),
                    "Huge": (350, 600)
                }
                min_h, max_h = height_ranges.get(size_category, (150, 200))
            
            self.new_body_height_min_entry.delete(0, tk.END)
            self.new_body_height_min_entry.insert(0, str(min_h))
            self.new_body_height_max_entry.delete(0, tk.END)
            self.new_body_height_max_entry.insert(0, str(max_h))
            self.update_auto_size()  # Обновить авто-категорию
            
            # Пол - разбираем и устанавливаем в соответствующие поля
            gender = data.get('gender', 'N/A')
            standard_genders = ["Male", "Female", "Herm", "N/A", "Other"]
            if gender in standard_genders:
                self.new_body_gender_var.set(gender)
                self.new_body_gender_custom_entry.delete(0, tk.END)
            else:
                self.new_body_gender_var.set("Other")
                self.new_body_gender_custom_entry.delete(0, tk.END)
                self.new_body_gender_custom_entry.insert(0, gender)
            
            # Загружаем структуру частей тела
            body_structure = data.get('body_structure', {})
            # Конвертируем ключ "null" или "None" из строки обратно в None
            for null_key in ["null", "None"]:
                if null_key in body_structure:
                    body_structure[None] = body_structure.pop(null_key)
                    break
            
            # Также нужно нормализовать все части в списках до словарей {name, tags}
            for key in body_structure:
                normalized_list = []
                for item in body_structure[key]:
                    if isinstance(item, str):
                        normalized_list.append({"name": item, "tags": []})
                    elif isinstance(item, dict) and "name" in item:
                        # Убеждаемся что tags есть
                        if "tags" not in item:
                            item["tags"] = []
                        normalized_list.append(item)
                    else:
                        normalized_list.append(item)
                body_structure[key] = normalized_list
            
            self.current_body_structure = body_structure
            self.update_body_parts_tree()
            
            # Загружаем шаблон описания
            desc_template = data.get('description_template', '')
            self.new_body_desc_template_entry.delete(0, tk.END)
            self.new_body_desc_template_entry.insert(0, desc_template)
            
            print(f"GUI: Loaded body type '{body_name}' into editor.")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load body type:\n{e}")
    
    def on_rename_body_type(self):
        """Переименовывает выбранный тип тела (создает копию с новым именем и удаляет старый)."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to rename.")
            return
        
        old_name = self.bodies_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Rename '{old_name}'")
        dialog.geometry("400x150")
        # Центрируем диалог относительно родительского окна
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Class Name (e.g., Insectoid):").pack(pady=5)
        ttk.Label(dialog, text="('Body' will be added automatically)").pack(pady=0)
        entry = ttk.Entry(dialog, width=50)
        entry.insert(0, old_name.replace("Body", ""))
        
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            base_name = entry.get().strip()
            if not base_name:
                messagebox.showwarning("Invalid Input", "Class name cannot be empty.", parent=dialog)
                return
            
            # Автоматически добавляем "Body" если нет
            new_name = base_name if base_name.endswith("Body") else base_name + "Body"
            
            if new_name == old_name:
                dialog.destroy()
                return
            if new_name in self.available_bodies:
                messagebox.showwarning("Duplicate", f"A body type with class name '{new_name}' already exists.", parent=dialog)
                return
            
            # Загружаем данные старого тела из JSON файла
            filename = f"{old_name.lower()}.json"
            filepath = os.path.join(BODIES_DATA_DIR, filename)
            
            if not os.path.exists(filepath):
                messagebox.showerror("Error", f"File for '{old_name}' not found at {filepath}.")
                return
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Обновляем имя класса
                data["class_name"] = new_name
                
                # Сохраняем новый файл
                filename = f"{new_name.lower()}.json"
                filepath = os.path.join(BODIES_DATA_DIR, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                # Удаляем старый файл
                old_filename = f"{old_name.lower()}.json"
                old_filepath = os.path.join(BODIES_DATA_DIR, old_filename)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
                
                # Перезагружаем список тел
                self._reload_available_bodies()
                self.refresh_bodies_list()
                
                messagebox.showinfo("Success", f"Successfully renamed '{old_name}' to '{new_name}'.")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Rename Error", f"Failed to rename body type:\n{e}")
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=10)
    
    def on_copy_body_type(self):
        """Копирует выбранный тип тела с новым именем."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to copy.")
            return
        
        old_name = self.bodies_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Copy '{old_name}'")
        dialog.geometry("400x150")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        new_default_name = old_name.replace("Body", "") + " Copy"
        ttk.Label(dialog, text="New Class Name (e.g., Insectoid):").pack(pady=5)
        ttk.Label(dialog, text="('Body' will be added automatically)").pack(pady=0)
        
        entry = ttk.Entry(dialog, width=50)
        entry.insert(0, new_default_name)
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            base_name = entry.get().strip()
            if not base_name:
                messagebox.showwarning("Invalid Input", "Class name cannot be empty.", parent=dialog)
                return
            
            # Автоматически добавляем "Body" если нет
            new_name = base_name if base_name.endswith("Body") else base_name + "Body"
            
            if new_name in self.available_bodies:
                messagebox.showwarning("Duplicate", f"A body type with class name '{new_name}' already exists.", parent=dialog)
                return
            
            # Загружаем данные старого тела из JSON файла
            filename = f"{old_name.lower()}.json"
            filepath = os.path.join(BODIES_DATA_DIR, filename)
            
            if not os.path.exists(filepath):
                messagebox.showerror("Error", f"File for '{old_name}' not found at {filepath}.")
                return
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Обновляем имя класса и display_name
                data["class_name"] = new_name
                data["display_name"] = new_name.replace("Body", "")
                
                # Сохраняем новый файл
                filename = f"{new_name.lower()}.json"
                filepath = os.path.join(BODIES_DATA_DIR, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                # Перезагружаем список тел
                self._reload_available_bodies()
                self.refresh_bodies_list()
                
                messagebox.showinfo("Success", f"Successfully copied '{old_name}' to '{new_name}'.")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy body type:\n{e}")
        
        ttk.Button(dialog, text="Copy", command=confirm).pack(pady=10)
    
    def on_delete_body_type(self):
        """Удаляет выбранный тип тела."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to delete.")
            return
        
        body_name = self.bodies_listbox.get(selection[0])
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{body_name}'?\nThis will permanently remove the file.", parent=self.parent):
            return
        
        try:
            # Удаляем файл JSON
            filename = f"{body_name.lower()}.json"
            filepath = os.path.join(BODIES_DATA_DIR, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
                # Перезагружаем список тел
                self._reload_available_bodies()
                self.refresh_bodies_list()
                
                messagebox.showinfo("Success", f"Successfully deleted '{body_name}'.")
            else:
                messagebox.showerror("Error", f"File for '{body_name}' not found at {filepath}.")
                
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete body type:\n{e}")
