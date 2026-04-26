# file: body_type_manager/ui_structure.py
"""
Миксин для создания UI структуры экрана управления телами.
"""

import tkinter as tk
from tkinter import ttk


class UIStructureMixin:
    """Предоставляет функциональность создания UI структуры."""
    
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
        workspace.grid_columnconfigure(0, weight=1)  # Левая панель (растягивается когда видима)
        workspace.grid_columnconfigure(1, weight=10) # Основное дерево
        workspace.grid_columnconfigure(2, weight=3)  # Правая панель (свойства и список тел)
        workspace.grid_rowconfigure(0, weight=1)     # Все содержимое растягивается
        
        # Центральная часть: Дерево частей тела (занимает column=1, растягивается)
        tree_container = ttk.LabelFrame(workspace, text="Body Parts Structure", padding=5)
        tree_container.grid(row=0, column=1, sticky="nsew")
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
        # Дерево с вертикальным и горизонтальным скроллбарами
        columns = ("tags", "part_id")
        self.body_parts_tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", selectmode="extended")
        self.body_parts_tree.heading("#0", text="Bodypart")
        self.body_parts_tree.column("#0", width=200, minwidth=150)
        self.body_parts_tree.heading("tags", text="Tags")
        self.body_parts_tree.column("tags", width=150, minwidth=100)
        # Скрываем колонку part_id (используется только для внутренней логики)
        self.body_parts_tree.heading("part_id", text="ID")
        self.body_parts_tree.column("part_id", width=0, minwidth=0, stretch=False)
        
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
        
        # Подменю для добавления тегов
        self.add_tag_menu = tk.Menu(self.tree_menu, tearoff=0)
        self.tree_menu.add_cascade(label="Add Tag", menu=self.add_tag_menu)
        
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
        
        # Правая панель: Свойства и список тел (теперь справа от дерева в column=2)
        right_panel = ttk.Frame(workspace)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(1, weight=1)  # Список тел растягивается
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
        self.left_panel_container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_panel_container.grid_remove()  # Скрываем по умолчанию
        # Настраиваем row weights динамически в _update_left_panel_layout
        self.left_panel_container.grid_columnconfigure(0, weight=1)
        
        # Создаем контекстное меню для списка тел
        self.body_list_menu = tk.Menu(self.parent, tearoff=0)
        self.body_list_menu.add_command(label="Load", command=self.on_load_body_to_editor)
        self.body_list_menu.add_command(label="Rename", command=self.on_rename_body_type)
        self.body_list_menu.add_command(label="Copy", command=self.on_copy_body_type)
        self.body_list_menu.add_separator()
        self.body_list_menu.add_command(label="Delete", command=self.on_delete_body_type)
        
        self.bodies_listbox.bind("<Button-3>", self.on_body_list_right_click)
        
        # Загрузка списка тел
        self.refresh_bodies_list()
        
        # Инициализация авто-размера
        self.update_auto_size()
        
        # Инициализируем дерево с обязательной корневой частью "Body"
        self.init_body_structure_with_root()
