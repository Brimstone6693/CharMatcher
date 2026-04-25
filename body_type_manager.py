# file: body_type_manager.py
"""
Модуль для управления типами тел (Body Type Manager).
Инкапсулирует всю логику создания, редактирования, удаления и отображения типов тел.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import copy  # Импортируем модуль для глубокого копирования
from module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR
from parts_database import PartsDatabase


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
        
        # История действий для Undo/Redo
        self.action_history = []
        self.redo_stack = []
        self.max_history_size = 50
        
        # База данных частей тела
        self.parts_db = PartsDatabase()
        
        # Состояние видимости панели списка частей
        self.parts_list_visible = False
        self.parts_list_frame = None
        self.parts_list_tree = None
        
        # Менеджер тегов
        self.tags_manager_frame = None
        self.tags_manager_visible = False
        
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
        
        # Устанавливаем заголовок окна
        self.parent.title("Body Master")
        
        # Основной контейнер с grid layout для лучшего контроля
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # --- Top Bar (Профессиональная панель инструментов) ---
        top_bar = ttk.Frame(main_frame)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Группа: История
        history_frame = ttk.LabelFrame(top_bar, text="History", padding=2)
        history_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.undo_btn = ttk.Button(history_frame, text="↶ Undo", command=self.on_undo, width=8)
        self.undo_btn.pack(side=tk.LEFT, padx=2)
        
        self.redo_btn = ttk.Button(history_frame, text="↷ Redo", command=self.on_redo, width=8)
        self.redo_btn.pack(side=tk.LEFT, padx=2)
        
        # Группа: Файл
        file_frame = ttk.LabelFrame(top_bar, text="File", padding=2)
        file_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(file_frame, text="📂 New", command=self.new_body, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="💾 Save", command=self.save_body, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="📁 Open", command=self.on_load_body_to_editor, width=8).pack(side=tk.LEFT, padx=2)
        
        # Группа: Части тела
        parts_frame = ttk.LabelFrame(top_bar, text="Parts", padding=2)
        parts_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(parts_frame, text="➕ Root", command=self.on_add_root_part, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(parts_frame, text="🌱 Child", command=self.on_add_child_part, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(parts_frame, text="✏️ Rename", command=self.on_rename_part, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(parts_frame, text="🗑️ Delete", command=self.on_delete_part, width=8).pack(side=tk.LEFT, padx=2)
        
        # Кнопка показа/скрытия списка частей
        self.toggle_parts_list_btn = ttk.Button(parts_frame, text="📋 List", command=self.toggle_parts_list, width=8)
        self.toggle_parts_list_btn.pack(side=tk.LEFT, padx=2)
        
        # Кнопка показа/скрытия менеджера тегов
        self.toggle_tags_manager_btn = ttk.Button(parts_frame, text="🏷️ Tags", command=self.toggle_tags_manager, width=8)
        self.toggle_tags_manager_btn.pack(side=tk.LEFT, padx=2)
        
        # Группа: База данных
        db_frame = ttk.LabelFrame(top_bar, text="Database", padding=2)
        db_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(db_frame, text="💾 Save Part", command=self.on_save_part_to_db, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(db_frame, text="📂 Load Part", command=self.on_load_part_from_db, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(db_frame, text="🌳 Save Tree", command=self.on_save_tree_to_db, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(db_frame, text="📁 Load Tree", command=self.on_load_tree_from_db, width=10).pack(side=tk.LEFT, padx=2)
        
        # Кнопка назад справа
        ttk.Button(top_bar, text="← Back", command=self.show_start_screen).pack(side=tk.RIGHT, padx=5)
        
        # --- Основная рабочая область ---
        workspace = ttk.Frame(main_frame)
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)  # Центральная колонка растягивается
        workspace.grid_rowconfigure(0, weight=1)     # Верхняя строка (дерево) растягивается
        workspace.grid_rowconfigure(1, weight=0)     # Нижняя строка (левая панель) фиксирована
        
        # Центральная часть: Дерево частей тела (занимает всю ширину по умолчанию)
        tree_container = ttk.LabelFrame(workspace, text="Body Parts Structure", padding=5)
        tree_container.grid(row=0, column=0, sticky="nsew", columnspan=2)
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
        # Дерево с вертикальным и горизонтальным скроллбарами
        columns = ("tags",)
        self.body_parts_tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", selectmode="extended")
        self.body_parts_tree.heading("#0", text="Bodypart")
        self.body_parts_tree.column("#0", width=200, minwidth=150)
        self.body_parts_tree.heading("tags", text="Tags")
        self.body_parts_tree.column("tags", width=150, minwidth=100)
        
        # Вертикальный скроллбар
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.body_parts_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        
        # Горизонтальный скроллбар
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.body_parts_tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.body_parts_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.body_parts_tree.grid(row=0, column=0, sticky="nsew")
        
        # Контекстное меню для дерева
        self.tree_menu = tk.Menu(self.parent, tearoff=0)
        self.tree_menu.add_command(label="Copy", command=self.on_copy_parts)
        self.tree_menu.add_command(label="Paste", command=self.on_paste_parts)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Add Child Part", command=self.on_add_child_part)
        self.tree_menu.add_command(label="Rename Part", command=self.on_rename_part)
        self.tree_menu.add_command(label="Delete Part", command=self.on_delete_part)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Undo", command=self.on_undo)
        self.tree_menu.add_command(label="Redo", command=self.on_redo)
        
        self.body_parts_tree.bind("<Button-3>", self.on_tree_right_click)
        # Двойной клик по названию части (колонка #0) - переименование
        self.body_parts_tree.bind("<Double-1>", self.on_tree_double_click)
        
        # Привязка горячих клавиш
        self._bind_shortcuts()
        
        # Правая панель: Свойства и список тел (теперь в нижней строке)
        right_panel = ttk.Frame(workspace)
        right_panel.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        right_panel.grid_rowconfigure(0, weight=1)  # Список тел растягивается
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Форма свойств тела
        props_frame = ttk.LabelFrame(right_panel, text="Body Type Properties", padding=10)
        props_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        props_frame.grid_columnconfigure(1, weight=1)
        
        # Имя класса
        ttk.Label(props_frame, text="Class Name:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.new_body_class_name_entry = ttk.Entry(props_frame)
        self.new_body_class_name_entry.grid(row=0, column=1, sticky="ew", pady=3)
        
        # Отображаемое имя
        ttk.Label(props_frame, text="Display Name:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.new_body_display_name_entry = ttk.Entry(props_frame)
        self.new_body_display_name_entry.grid(row=1, column=1, sticky="ew", pady=3)
        
        # Тип высоты
        ttk.Label(props_frame, text="Height Type:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.height_type_var = tk.StringVar(value="standing")
        height_combo = ttk.Combobox(props_frame, textvariable=self.height_type_var, 
                                    values=["standing", "withers"], state="readonly")
        height_combo.grid(row=2, column=1, sticky="ew", pady=3)
        self.height_type_var.trace_add('write', lambda *args: self.update_auto_size())
        
        # Диапазон высоты
        size_frame = ttk.Frame(props_frame)
        size_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=3)
        
        ttk.Label(size_frame, text="Min (cm):").pack(side=tk.LEFT, padx=(0, 5))
        self.new_body_height_min_entry = ttk.Entry(size_frame, width=8)
        self.new_body_height_min_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.new_body_height_min_entry.insert(0, "150")
        self.new_body_height_min_entry.bind('<KeyRelease>', self.update_auto_size)
        
        ttk.Label(size_frame, text="Max (cm):").pack(side=tk.LEFT, padx=(0, 5))
        self.new_body_height_max_entry = ttk.Entry(size_frame, width=8)
        self.new_body_height_max_entry.pack(side=tk.LEFT)
        self.new_body_height_max_entry.insert(0, "200")
        self.new_body_height_max_entry.bind('<KeyRelease>', self.update_auto_size)
        
        # Авто-размер
        ttk.Label(props_frame, text="Auto Size:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.auto_size_label = ttk.Label(props_frame, text="Medium", font=("Arial", 10, "bold"), foreground="blue")
        self.auto_size_label.grid(row=4, column=1, sticky=tk.W, pady=3)
        
        # Пол
        gender_frame = ttk.Frame(props_frame)
        gender_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=3)
        
        ttk.Label(gender_frame, text="Gender:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_body_gender_var = tk.StringVar(value="N/A")
        gender_combo = ttk.Combobox(gender_frame, textvariable=self.new_body_gender_var, 
                                    values=["Male", "Female", "Herm", "N/A", "Other"], state="readonly", width=10)
        gender_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(gender_frame, text="Custom:").pack(side=tk.LEFT, padx=(5, 2))
        self.new_body_gender_custom_entry = ttk.Entry(gender_frame, width=15)
        self.new_body_gender_custom_entry.pack(side=tk.LEFT)
        
        # Шаблон описания
        ttk.Label(props_frame, text="Description Template:").grid(row=6, column=0, sticky=tk.W, pady=3)
        self.new_body_desc_template_entry = ttk.Entry(props_frame)
        self.new_body_desc_template_entry.grid(row=6, column=1, sticky="ew", pady=3)
        self.new_body_desc_template_entry.insert(0, "A {size} {gender} {display_name}.")
        
        # Список сохраненных тел
        list_frame = ttk.LabelFrame(right_panel, text="Saved Body Types", padding=5)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.bodies_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.bodies_listbox.grid(row=0, column=0, sticky="nsew")
        
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.bodies_listbox.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.bodies_listbox.config(yscrollcommand=list_scroll.set)
        
        self.bodies_listbox.bind("<<ListboxSelect>>", lambda e: None)  # Убрано, т.к. используется только двойной клик
        self.bodies_listbox.bind("<Double-Button-1>", lambda e: self.on_load_body_to_editor())
        
        # Кнопки списка
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(list_btn_frame, text="Load", command=self.on_load_body_to_editor).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_btn_frame, text="Delete", command=self.on_delete_body_type).pack(side=tk.LEFT, padx=2)
        
        # Контейнер для левой панели (список частей/теги) - скрыт по умолчанию
        self.left_panel_container = ttk.Frame(workspace)
        self.left_panel_container.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.left_panel_container.grid_remove()  # Скрываем по умолчанию
        self.left_panel_container.grid_rowconfigure(0, weight=1)
        self.left_panel_container.grid_columnconfigure(0, weight=1)
        
        # Привязка горячих клавиш
        self._bind_shortcuts()
        
        # Загрузка списка тел
        self.refresh_bodies_list()
        
        # Инициализация авто-размера
        self.update_auto_size()
        self.refresh_bodies_list()
        
        # Инициализируем дерево с обязательной корневой частью "Body"
        self.init_body_structure_with_root()
        
        # Кнопка назад
        back_btn = ttk.Button(main_frame, text="Back to Start", command=self.show_start_screen)
        back_btn.grid(row=2, column=0, pady=5, sticky="ew")
        
        return main_frame
    
    def show_start_screen(self):
        """Возвращает к начальному экрану (делегирование родительскому окну)."""
        if hasattr(self.parent, 'show_start_screen'):
            self.parent.show_start_screen()
    
    def toggle_parts_list(self):
        """Показывает или скрывает панель списка частей тела."""
        if self.parts_list_visible:
            self.hide_parts_list()
        else:
            self.show_parts_list()
    
    def toggle_tags_manager(self):
        """Показывает или скрывает панель менеджера тегов."""
        if self.tags_manager_visible:
            self.hide_tags_manager()
        else:
            self.show_tags_manager()
    
    def show_parts_list(self):
        """Создает и показывает панель списка частей тела."""
        # Показываем левый контейнер если скрыт
        self.left_panel_container.grid()
        
        if self.parts_list_frame is not None:
            # Если фрейм уже создан, просто показываем его
            self.parts_list_frame.grid(row=0, column=0, sticky="nsew")
            self.parts_list_visible = True
            self.toggle_parts_list_btn.config(text="📋 Hide List")
            self.update_parts_list_tree()
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
    
    def show_tags_manager(self):
        """Создает и показывает панель менеджера тегов."""
        # Показываем левый контейнер если скрыт
        self.left_panel_container.grid()
        
        if self.tags_manager_frame is not None:
            # Если фрейм уже создан, просто показываем его
            self.tags_manager_frame.grid(row=0, column=0, sticky="nsew")
            self.tags_manager_visible = True
            self.toggle_tags_manager_btn.config(text="🏷️ Hide Tags")
            self.update_tags_manager_tree()
            return
        
        # Создаем новую панель для менеджера тегов в левом контейнере
        self.tags_manager_frame = ttk.LabelFrame(self.left_panel_container, text="Tags Manager (Drag & Drop to Tree)", padding=5)
        self.tags_manager_frame.grid(row=0, column=0, sticky="nsew")
        self.tags_manager_frame.grid_columnconfigure(0, weight=1)
        self.tags_manager_frame.grid_rowconfigure(0, weight=1)
        
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
    
    def hide_tags_manager(self):
        """Скрывает панель менеджера тегов."""
        if self.tags_manager_frame is not None:
            self.tags_manager_frame.grid_remove()
        
        # Скрываем левый контейнер если список частей тоже скрыт
        if not self.parts_list_visible:
            self.left_panel_container.grid_remove()
        
        self.tags_manager_visible = False
        self.toggle_tags_manager_btn.config(text="🏷️ Tags")
    
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
        for tag_info in all_tags:
            category = tag_info.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(tag_info)
        
        # Добавляем категории и теги в дерево
        for category, tags in sorted(categories.items()):
            cat_id = self.tags_tree.insert("", "end", text=category, values=("", ""))
            for tag_info in sorted(tags, key=lambda x: x['name']):
                tag_name = tag_info['name']
                description = tag_info.get('description', '')
                self.tags_tree.insert(cat_id, "end", text=tag_name, values=(category, description))
    
    def on_add_tag(self):
        """Открывает диалог добавления нового тега."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Tag")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tag Name:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        tag_name_entry = ttk.Entry(dialog, width=30)
        tag_name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        ttk.Label(dialog, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        tag_category_entry = ttk.Entry(dialog, width=30)
        tag_category_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        tag_category_entry.insert(0, "General")
        
        ttk.Label(dialog, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        tag_desc_entry = ttk.Entry(dialog, width=30)
        tag_desc_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)
        
        def save_tag():
            name = tag_name_entry.get().strip()
            category = tag_category_entry.get().strip()
            description = tag_desc_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Tag name cannot be empty!")
                return
            
            # Сохраняем тег в базу данных
            self.parts_db.add_or_update_tag(name, category, description)
            self.update_tags_manager_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_tag).grid(row=3, column=0, columnspan=2, pady=10)
        
        dialog.wait_window()
    
    def on_edit_tag(self):
        """Открывает диалог редактирования выбранного тега."""
        selection = self.tags_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a tag to edit.")
            return
        
        item = selection[0]
        tag_name = self.tags_tree.item(item, "text")
        
        # Проверяем, не категория ли это
        if self.tags_tree.parent(item) == "":
            messagebox.showinfo("Info", "Please select a specific tag, not a category.")
            return
        
        # Получаем информацию о теге
        tag_info = self.parts_db.get_tag_by_name(tag_name)
        if not tag_info:
            messagebox.showerror("Error", f"Tag '{tag_name}' not found in database.")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit Tag: {tag_name}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tag Name:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        tag_name_entry = ttk.Entry(dialog, width=30)
        tag_name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        tag_name_entry.insert(0, tag_name)
        
        ttk.Label(dialog, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        tag_category_entry = ttk.Entry(dialog, width=30)
        tag_category_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        tag_category_entry.insert(0, tag_info.get('category', 'General'))
        
        ttk.Label(dialog, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        tag_desc_entry = ttk.Entry(dialog, width=30)
        tag_desc_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)
        tag_desc_entry.insert(0, tag_info.get('description', ''))
        
        def save_tag():
            new_name = tag_name_entry.get().strip()
            category = tag_category_entry.get().strip()
            description = tag_desc_entry.get().strip()
            
            if not new_name:
                messagebox.showerror("Error", "Tag name cannot be empty!")
                return
            
            # Обновляем тег в базе данных
            self.parts_db.add_or_update_tag(new_name, category, description, old_name=tag_name)
            self.update_tags_manager_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_tag).grid(row=3, column=0, columnspan=2, pady=10)
        
        dialog.wait_window()
    
    def on_delete_tag(self):
        """Удаляет выбранный тег."""
        selection = self.tags_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a tag to delete.")
            return
        
        item = selection[0]
        tag_name = self.tags_tree.item(item, "text")
        
        # Проверяем, не категория ли это
        if self.tags_tree.parent(item) == "":
            messagebox.showinfo("Info", "Please select a specific tag, not a category.")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete tag '{tag_name}'?"):
            self.parts_db.delete_tag(tag_name)
            self.update_tags_manager_tree()
    
    def on_import_tags(self):
        """Импортирует теги из JSON файла."""
        file_path = filedialog.askopenfilename(
            title="Import Tags from JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.parts_db.import_tags_from_json(file_path)
                self.update_tags_manager_tree()
                messagebox.showinfo("Success", "Tags imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import tags: {str(e)}")
    
    def on_export_tags(self):
        """Экспортирует теги в JSON файл."""
        file_path = filedialog.asksaveasfilename(
            title="Export Tags to JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.parts_db.export_tags_to_json(file_path)
                messagebox.showinfo("Success", "Tags exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export tags: {str(e)}")
    
    def _setup_tags_drag_and_drop(self):
        """Настраивает Drag and Drop для перетаскивания тегов на части тела."""
        # Переменная для хранения перетаскиваемого элемента
        self.dragged_tag_item = None
        
        def on_drag_start(event):
            """Начало перетаскивания."""
            item = self.tags_tree.identify_row(event.y)
            if item and self.tags_tree.parent(item) != "":  # Только теги, не категории
                self.dragged_tag_item = item
                self.tags_tree.selection_set(item)
        
        def on_drag_drop(event):
            """Завершение перетаскивания - бросок на дерево частей тела."""
            # Проверяем, был ли бросок на дерево частей тела
            widget = self.parent.winfo_containing(event.x_root, event.y_root)
            
            # Ищем, является ли виджет частью дерева body_parts_tree
            current_widget = widget
            while current_widget:
                if current_widget == self.body_parts_tree:
                    # Бросок на дерево частей тела
                    if self.dragged_tag_item:
                        tag_name = self.tags_tree.item(self.dragged_tag_item, "text")
                        self._apply_tag_to_selected_part(tag_name)
                    self.dragged_tag_item = None
                    return
                
                current_widget = current_widget.master
        
        def on_drag_end(event):
            """Очистка после перетаскивания."""
            self.dragged_tag_item = None
        
        # Привязываем события к дереву тегов
        self.tags_tree.bind("<ButtonPress-1>", on_drag_start)
        self.tags_tree.bind("<ButtonRelease-1>", on_drag_drop)
        self.tags_tree.bind("<B1-Motion>", lambda e: None)  # Для визуальной обратной связи можно добавить
    
    def _apply_tag_to_selected_part(self, tag_name):
        """Применяет тег к выбранной части тела."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a body part in the tree first.")
            return
        
        item = selection[0]
        part_name = self.body_parts_tree.item(item, "text").split(" [")[0]
        
        # Находим часть в структуре
        def find_and_update(part_key, parent_key=None):
            if part_key == part_name:
                # Находим часть в структуре
                if parent_key is None:
                    parts_list = self.current_body_structure.get(None, [])
                else:
                    parts_list = self.current_body_structure.get(parent_key, [])
                
                for i, part in enumerate(parts_list):
                    if isinstance(part, dict) and part.get("name") == part_name:
                        if "tags" not in part:
                            part["tags"] = []
                        if tag_name not in part["tags"]:
                            part["tags"].append(tag_name)
                        return True
                    elif part == part_name:
                        # Конвертируем строку в словарь с тегами
                        parts_list[i] = {"name": part_name, "tags": [tag_name]}
                        return True
            
            # Рекурсивный поиск в детях
            children = self.current_body_structure.get(part_key, [])
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                if find_and_update(child_name, part_key):
                    return True
            
            return False
        
        # Поиск с корневых элементов
        root_parts = self.current_body_structure.get(None, [])
        for part in root_parts:
            part_name_check = part["name"] if isinstance(part, dict) else part
            if find_and_update(part_name_check):
                break
        
        # Обновляем дерево
        self.update_body_parts_tree()
        if self.parts_list_visible:
            self.update_parts_list_tree()

    
    def update_parts_list_tree(self):
        """Обновляет дерево списка всех частей с поддержкой нескольких корней."""
        if self.parts_list_tree is None:
            return
        
        # Очищаем дерево
        for item in self.parts_list_tree.get_children():
            self.parts_list_tree.delete(item)
        
        # Рекурсивно добавляем узлы с полным путем
        def add_children(parent_node_id, parent_key, current_path, visited=None):
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
                
                # Формируем полный путь
                if current_path:
                    full_path = f"{current_path} > {child_name}"
                else:
                    full_path = child_name
                
                # Формируем текст для отображения с тегами
                display_text = child_name
                tags_display = f"[{', '.join(child_tags)}]" if child_tags else ""
                
                # Добавляем узел в дерево
                node_id = self.parts_list_tree.insert(parent_node_id, "end", text=display_text, values=(tags_display, full_path))
                
                # Рекурсивно добавляем детей
                add_children(node_id, child_name, full_path, visited.copy())
        
        # Начинаем с корневых элементов (ключ None) - поддержка нескольких корней
        root_parts = self.current_body_structure.get(None, [])
        for part in root_parts:
            part_name = part["name"] if isinstance(part, dict) else part
            part_tags = part.get("tags", []) if isinstance(part, dict) else []
            
            display_text = part_name
            tags_display = f"[{', '.join(part_tags)}]" if part_tags else ""
            full_path = part_name
            
            node_id = self.parts_list_tree.insert("", "end", text=display_text, values=(tags_display, full_path))
            self.parts_list_tree.item(node_id, open=True)
            add_children(node_id, part_name, full_path)
    
    def on_parts_list_double_click(self, event):
        """Обрабатывает двойной клик по списку частей для inline-редактирования."""
        selection = self.parts_list_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        column = self.parts_list_tree.identify_column(event.x)
        
        # Определяем, какая колонка была клинута
        if column == "#0":
            # Редактирование названия
            self._start_inline_edit(self.parts_list_tree, item, "name")
        elif column == "tags":
            # Редактирование тегов
            self._start_inline_edit(self.parts_list_tree, item, "tags")
    
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
                add_children(node_id, child_name, visited.copy())
        
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
            
            # Проверяем на дубликат имени у родителя (Body) и добавляем суффикс если нужно
            existing_names = set()
            for existing in self.current_body_structure.get("Body", []):
                existing_name = existing["name"] if isinstance(existing, dict) else existing
                existing_names.add(existing_name)
            
            base_name = name
            counter = 1
            new_name = name
            while new_name in existing_names:
                new_name = f"{base_name}_{counter}"
                counter += 1
            
            # Добавляем как словарь с именем и тегами в список детей "Body" (с уникальным именем)
            if "Body" not in self.current_body_structure:
                self.current_body_structure["Body"] = []
            self.current_body_structure["Body"].append({"name": new_name, "tags": tags})
            if new_name not in self.current_body_structure:
                self.current_body_structure[new_name] = []
            
            # Сохраняем состояние для Undo
            self._save_action_state("add_root", {"name": new_name, "tags": tags, "parent": "Body"})
            
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
            
            # Проверяем на дубликат имени у родителя и добавляем суффикс если нужно
            existing_names = set()
            for existing in self.current_body_structure.get(parent_name, []):
                existing_name = existing["name"] if isinstance(existing, dict) else existing
                existing_names.add(existing_name)
            
            base_name = name
            counter = 1
            new_name = name
            while new_name in existing_names:
                new_name = f"{base_name}_{counter}"
                counter += 1
            
            # Добавляем как словарь с именем и тегами (с уникальным именем)
            if parent_name not in self.current_body_structure:
                self.current_body_structure[parent_name] = []
            
            self.current_body_structure[parent_name].append({"name": new_name, "tags": tags})
            if new_name not in self.current_body_structure:
                self.current_body_structure[new_name] = []
            
            # Сохраняем состояние для Undo
            self._save_action_state("add_child", {"name": new_name, "tags": tags, "parent": parent_name})
            
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
        
        # Размещаем Entry в позиции ячейки названия
        bbox = self.body_parts_tree.bbox(item, "#0")
        if bbox:
            x, y, width, height = bbox
            name_entry.place(x=x, y=y, width=width, height=height)
            name_entry.focus()
            name_entry.select_range(0, tk.END)
            
            def confirm(event=None):
                new_name = name_entry.get().strip()
                if not new_name:
                    messagebox.showwarning("Invalid Input", "Name cannot be empty.", parent=self.parent)
                    name_entry.focus()
                    return
                
                if new_name == old_name:
                    name_entry.destroy()
                    return
                
                # Проверяем на дубликат
                for parent, children in self.current_body_structure.items():
                    for child in children:
                        child_name = child["name"] if isinstance(child, dict) else child
                        if child_name == new_name:
                            messagebox.showwarning("Duplicate", f"A part with name '{new_name}' already exists.", parent=self.parent)
                            name_entry.focus()
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
                
                # Сохраняем состояние для Undo
                self._save_action_state("rename", {"old_name": old_name, "new_name": new_name})
                
                self.update_body_parts_tree()
                name_entry.destroy()
            
            name_entry.bind("<Return>", confirm)
            name_entry.bind("<FocusOut>", confirm)
            name_entry.bind("<Escape>", lambda e: name_entry.destroy())
            return
        
        # Fallback: если bbox не получен, используем старый диалог
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
            
            # Сохраняем состояние для Undo
            self._save_action_state("rename", {"old_name": old_name, "new_name": new_name})
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=10)
    
    def on_tree_double_click(self, event):
        """Обработчик двойного клика по дереву - определяет колонку и вызывает соответствующее редактирование."""
        # Определяем элемент и колонку
        item = self.body_parts_tree.identify_row(event.y)
        column = self.body_parts_tree.identify_column(event.x)
        
        if not item:
            return
        
        # Выбираем элемент
        self.body_parts_tree.selection_set(item)
        
        if column == "#0":
            # Двойной клик по названию части - inline редактирование
            self.on_rename_part(item=item)
        elif column == "#1":
            # Двойной клик по колонке тегов - inline редактирование
            self.on_edit_tags_inline()
    
    def on_edit_tags_inline(self):
        """Редактирование тегов прямо в дереве (inline)."""
        selection = self.body_parts_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        current_tags_str = self.body_parts_tree.item(item)["values"][0] if self.body_parts_tree.item(item)["values"] else ""
        current_tags = [t.strip() for t in current_tags_str.strip("[]").split(",") if t.strip()] if current_tags_str else []
        
        # Создаем Entry прямо в дереве для inline редактирования
        tags_entry = ttk.Entry(self.body_parts_tree)
        tags_entry.insert(0, ", ".join(current_tags))
        
        # Размещаем Entry в позиции ячейки тегов
        bbox = self.body_parts_tree.bbox(item, "tags")
        if bbox:
            x, y, width, height = bbox
            tags_entry.place(x=x, y=y, width=width, height=height)
            tags_entry.focus()
            tags_entry.select_range(0, tk.END)
            
            def save_tags(event=None):
                new_tags_str = tags_entry.get().strip()
                new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()] if new_tags_str else []
                
                # Обновляем структуру
                part_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
                self._update_part_tags(part_name, new_tags)
                
                # Обновляем дерево
                self.update_body_parts_tree()
                tags_entry.destroy()
            
            tags_entry.bind("<Return>", save_tags)
            tags_entry.bind("<FocusOut>", save_tags)
            tags_entry.bind("<Escape>", lambda e: tags_entry.destroy())
    
    def _start_inline_edit(self, tree, item, field_type):
        """Универсальная функция для inline-редактирования в любом дереве."""
        if field_type == "name":
            # Редактирование названия
            old_name = tree.item(item)["text"]
            
            # Нельзя переименовать корневой элемент "Body"
            if old_name == "Body":
                messagebox.showwarning("Cannot Rename", "Cannot rename the root 'Body' part.", parent=self.parent)
                return
            
            name_entry = ttk.Entry(tree)
            name_entry.insert(0, old_name)
            
            bbox = tree.bbox(item, "#0")
            if bbox:
                x, y, width, height = bbox
                name_entry.place(x=x, y=y, width=width, height=height)
                name_entry.focus()
                name_entry.select_range(0, tk.END)
                
                def confirm(event=None):
                    new_name = name_entry.get().strip()
                    if not new_name:
                        messagebox.showwarning("Invalid Input", "Name cannot be empty.", parent=self.parent)
                        name_entry.focus()
                        return
                    
                    if new_name == old_name:
                        name_entry.destroy()
                        return
                    
                    # Проверяем на дубликат
                    for parent, children in self.current_body_structure.items():
                        for child in children:
                            child_name = child["name"] if isinstance(child, dict) else child
                            if child_name == new_name:
                                messagebox.showwarning("Duplicate", f"A part with name '{new_name}' already exists.", parent=self.parent)
                                name_entry.focus()
                                return
                    
                    # Переименовываем во всех местах
                    for parent, children in self.current_body_structure.items():
                        for i, child in enumerate(children):
                            if isinstance(child, dict) and child.get("name") == old_name:
                                children[i]["name"] = new_name
                            elif child == old_name:
                                children[i] = new_name
                    
                    # Ключ структуры (если есть)
                    if old_name in self.current_body_structure:
                        self.current_body_structure[new_name] = self.current_body_structure.pop(old_name)
                    
                    # Сохраняем состояние для Undo
                    self._save_action_state("rename", {"old_name": old_name, "new_name": new_name})
                    
                    self.update_body_parts_tree()
                    if self.parts_list_visible:
                        self.update_parts_list_tree()
                    name_entry.destroy()
                
                name_entry.bind("<Return>", confirm)
                name_entry.bind("<FocusOut>", confirm)
                name_entry.bind("<Escape>", lambda e: name_entry.destroy())
        
        elif field_type == "tags":
            # Редактирование тегов
            current_tags_str = tree.item(item)["values"][0] if tree.item(item)["values"] else ""
            current_tags = [t.strip() for t in current_tags_str.strip("[]").split(",") if t.strip()] if current_tags_str else []
            
            tags_entry = ttk.Entry(tree)
            tags_entry.insert(0, ", ".join(current_tags))
            
            bbox = tree.bbox(item, "tags")
            if bbox:
                x, y, width, height = bbox
                tags_entry.place(x=x, y=y, width=width, height=height)
                tags_entry.focus()
                tags_entry.select_range(0, tk.END)
                
                def save_tags(event=None):
                    new_tags_str = tags_entry.get().strip()
                    new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()] if new_tags_str else []
                    
                    # Обновляем структуру
                    part_name = tree.item(item)["text"].split(" [")[0]
                    self._update_part_tags(part_name, new_tags)
                    
                    # Обновляем деревья
                    self.update_body_parts_tree()
                    if self.parts_list_visible:
                        self.update_parts_list_tree()
                    tags_entry.destroy()
                
                tags_entry.bind("<Return>", save_tags)
                tags_entry.bind("<FocusOut>", save_tags)
                tags_entry.bind("<Escape>", lambda e: tags_entry.destroy())
    
    def _update_part_tags(self, part_name, new_tags):
        """Обновляет теги указанной части в структуре."""
        for parent_key, children in self.current_body_structure.items():
            if parent_key is None:
                continue
            for i, child in enumerate(children):
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == part_name:
                    if isinstance(child, dict):
                        child["tags"] = new_tags
                    else:
                        # Заменяем строку на dict с тегами
                        children[i] = {"name": child_name, "tags": new_tags}
                    return
    
    def on_copy_parts(self):
        """Копирует выбранные части тела в буфер обмена."""
        selection = self.body_parts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select part(s) to copy.", parent=self.parent)
            return
        
        # Копируем выбранные части и их дочерние элементы с использованием deepcopy
        self.clipboard_parts = []
        for item in selection:
            part_name = self.body_parts_tree.item(item)["text"].split(" [")[0]
            part_tags = []
            tags_val = self.body_parts_tree.item(item)["values"]
            if tags_val and len(tags_val) > 0 and tags_val[0]:
                tags_str = tags_val[0].strip("[]")
                if tags_str:
                    part_tags = [t.strip() for t in tags_str.split(",")]
            
            # Собираем полную структуру части с детьми из current_body_structure
            part_data = self._extract_part_structure(part_name)
            self.clipboard_parts.append(part_data)
        
        messagebox.showinfo("Copy", f"Copied {len(self.clipboard_parts)} part(s) to clipboard.", parent=self.parent)
    
    def _extract_part_structure(self, part_name):
        """Извлекает полную структуру части с детьми и тегами используя deepcopy."""
        # Находим часть в структуре
        part_data = {"name": part_name, "tags": [], "children": []}
        
        # Ищем часть в родителях чтобы получить теги
        for parent_key, children in self.current_body_structure.items():
            if parent_key is None:
                continue
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == part_name:
                    part_data["tags"] = child.get("tags", []) if isinstance(child, dict) else []
                    break
        
        # Рекурсивно копируем детей с использованием deepcopy для предотвращения проблем с ссылками
        children = self.current_body_structure.get(part_name, [])
        for child in children:
            child_name = child["name"] if isinstance(child, dict) else child
            child_subtree = self._extract_part_structure(child_name)
            part_data["children"].append(child_subtree)
        
        return part_data
    
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
        
        # Создаем глубокую копию данных буфера обмена для предотвращения проблем с ссылками
        parts_to_paste = copy.deepcopy(self.clipboard_parts)
        
        # Вставляем скопированные части
        if parent_name not in self.current_body_structure:
            self.current_body_structure[parent_name] = []
        
        def add_part_with_children(part_data, parent_key):
            """Рекурсивно добавляет часть и её детей с уникальными именами."""
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
            new_name = name
            while new_name in existing_names:
                new_name = f"{base_name}_{counter}"
                counter += 1
            
            # Добавляем часть с новым (уникальным) именем
            self.current_body_structure[parent_key].append({"name": new_name, "tags": tags})
            if new_name not in self.current_body_structure:
                self.current_body_structure[new_name] = []
            
            # Добавляем детей с рекурсией, передавая новое имя родителя
            for child_data in part_data.get("children", []):
                add_part_with_children(child_data, new_name)
        
        for part_data in parts_to_paste:
            add_part_with_children(part_data, parent_name)
        
        # Сохраняем состояние для Undo
        self._save_action_state("paste", {"parts": parts_to_paste, "parent": parent_name})
        
        self.update_body_parts_tree()
        messagebox.showinfo("Paste", "Parts pasted successfully.", parent=self.parent)
    
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
        parent_name = self.body_parts_tree.item(parent_item, "text")
        
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
            
            # Добавляем часть к родителю с уникальным именем
            if parent_name not in self.current_body_structure:
                self.current_body_structure[parent_name] = []
            
            self.current_body_structure[parent_name].append({
                "name": new_name,
                "tags": part_data.get("tags", [])
            })
            
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
            def build_tree_dict(part_name):
                result = {"name": part_name, "children": []}
                children = self.current_body_structure.get(part_name, [])
                for child in children:
                    child_name = child["name"] if isinstance(child, dict) else child
                    result["children"].append(build_tree_dict(child_name))
                return result
            
            # Если есть выделение, сохраняем только поддерево
            if selection:
                item = selection[0]
                root_name = self.body_parts_tree.item(item, "text")
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
        
        def add_tree_recursive(tree_data, parent_key, visited=None):
            """Рекурсивно добавляет части дерева с защитой от дублирования имен"""
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
            
            tags = tree_data.get("tags", [])
            self.current_body_structure[parent_key].append({"name": new_name, "tags": tags})
            
            # Добавляем новое имя в посещенные
            visited.add(new_name)
            
            if "children" in tree_data:
                for child in tree_data["children"]:
                    add_tree_recursive(child, new_name, visited.copy())
        
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
                parent_name = self.body_parts_tree.item(parent_item, "text")
            else:
                # Если нет выделения, добавляем к Body
                parent_name = "Body"
                if "Body" not in self.current_body_structure:
                    self.current_body_structure["Body"] = []
            
            # Добавляем дерево
            tree_data = template_data["tree_data"]
            add_tree_recursive(tree_data, parent_name)
            
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
    
    def new_body(self):
        """Создает новое тело (сбрасывает текущую структуру)"""
        if self.action_history:
            if not messagebox.askyesno("Confirm", "Clear current work and start a new body?"):
                return
        
        # Сбрасываем структуру и дерево
        self.current_body_structure = {None: []}
        self.update_body_parts_tree()
        
        # Очищаем поля формы
        self.new_body_class_name_entry.delete(0, tk.END)
        self.new_body_display_name_entry.delete(0, tk.END)
        self.new_body_gender_var.set("N/A")
        self.new_body_gender_custom_entry.delete(0, tk.END)
        self.new_body_desc_template_entry.delete(0, tk.END)
        self.new_body_height_min_entry.delete(0, tk.END)
        self.new_body_height_min_entry.insert(0, "150")
        self.new_body_height_max_entry.delete(0, tk.END)
        self.new_body_height_max_entry.insert(0, "200")
        self.update_auto_size()
        
        # Очищаем историю действий
        self.action_history.clear()
        self.redo_stack.clear()
    
    def save_body(self):
        """Сохраняет текущее тело (вызывает on_create_body_type_clicked)"""
        self.on_create_body_type_clicked()
    
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
            
            # Очищаем историю действий после создания нового тела
            self.action_history.clear()
            self.redo_stack.clear()
            
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
    
    def _save_action_state(self, action_type, data):
        """Сохраняет состояние действия для возможности Undo."""
        # Сохраняем полную копию текущей структуры
        state_copy = copy.deepcopy(self.current_body_structure)
        self.action_history.append({
            "action": action_type,
            "data": data,
            "state": state_copy
        })
        
        # Ограничиваем размер истории
        if len(self.action_history) > self.max_history_size:
            self.action_history.pop(0)
        
        # Очищаем redo стек при новом действии
        self.redo_stack.clear()
    
    def on_undo(self):
        """Отменяет последнее действие."""
        if not self.action_history:
            messagebox.showinfo("Undo", "Nothing to undo.", parent=self.parent)
            return
        
        # Сохраняем текущее состояние для Redo
        current_state = copy.deepcopy(self.current_body_structure)
        last_action = self.action_history.pop()
        self.redo_stack.append({
            "action": last_action["action"],
            "data": last_action["data"],
            "state": current_state
        })
        
        # Восстанавливаем предыдущее состояние
        self.current_body_structure = copy.deepcopy(last_action["state"])
        self.update_body_parts_tree()
    
    def on_redo(self):
        """Повторяет отмененное действие."""
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nothing to redo.", parent=self.parent)
            return
        
        # Сохраняем текущее состояние для Undo
        current_state = copy.deepcopy(self.current_body_structure)
        redo_action = self.redo_stack.pop()
        self.action_history.append({
            "action": redo_action["action"],
            "data": redo_action["data"],
            "state": current_state
        })
        
        # Восстанавливаем состояние
        self.current_body_structure = copy.deepcopy(redo_action["state"])
        self.update_body_parts_tree()
    
    def _bind_shortcuts(self):
        """Привязывает горячие клавиши к функциям."""
        # Копирование/Вставка
        self.parent.bind("<Control-c>", lambda e: self.on_copy_parts())
        self.parent.bind("<Control-v>", lambda e: self.on_paste_parts())
        
        # Undo/Redo
        self.parent.bind("<Control-z>", lambda e: self.on_undo())
        self.parent.bind("<Control-y>", lambda e: self.on_redo())
        
        # Удаление
        self.parent.bind("<Delete>", lambda e: self.on_delete_part())
        
        # Переименование (F2)
        self.parent.bind("<F2>", lambda e: self.on_rename_part())
    
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
            
            # Обновляем список частей если он открыт
            if self.parts_list_visible:
                self.update_parts_list_tree()
            
            # Очищаем историю действий при загрузке нового тела
            self.action_history.clear()
            self.redo_stack.clear()
            
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
