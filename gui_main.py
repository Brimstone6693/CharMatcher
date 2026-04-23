# file: gui_main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from character import Character
from module_loader import load_available_modules_and_bodies
from body import AbstractBody
from components import BaseComponent

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Character Creator GUI")
        self.geometry("600x400")

        # Загружаем модули при старте приложения
        self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
        print(f"GUI: Loaded {len(self.available_components)} components: {list(self.available_components.keys())}")
        print(f"GUI: Loaded {len(self.available_bodies)} bodies: {list(self.available_bodies.keys())}")

        self.current_character = None # Для хранения текущего персонажа

        self.show_start_screen()

    def show_start_screen(self):
        """Показывает начальный экран с кнопками Load и Create."""
        # Очищаем предыдущее содержимое
        for widget in self.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self)
        frame.pack(expand=True)

        label = ttk.Label(frame, text="Welcome to Character Creator!", font=("Arial", 16))
        label.pack(pady=20)

        load_button = ttk.Button(frame, text="Load Character", command=self.on_load_clicked)
        load_button.pack(pady=5)

        create_button = ttk.Button(frame, text="Create New Character", command=self.on_create_clicked)
        create_button.pack(pady=5)

        manage_bodies_button = ttk.Button(frame, text="Manage Body Types", command=self.show_manage_bodies_screen)
        manage_bodies_button.pack(pady=5)

    def on_load_clicked(self):
        """Обработчик кнопки Load."""
        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Select Character Save File",
            initialdir="saved_characters",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Загружаем персонажа, передавая ему загруженные классы
                self.current_character = Character.from_dict(data, self.available_components, self.available_bodies)
                print(f"GUI: Successfully loaded character {self.current_character.name} from {file_path}")
                # Показываем окно просмотра загруженного персонажа
                self.show_character_view()
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load character:\n{e}")

    def on_create_clicked(self):
        """Обработчик кнопки Create."""
        # Показываем окно создания
        self.show_creation_screen()

    def show_creation_screen(self):
        """Показывает экран создания персонажа."""
        # Очищаем предыдущее содержимое
        for widget in self.winfo_children():
            widget.destroy()

        if not self.available_bodies:
            messagebox.showwarning("No Bodies", "No body types found. Cannot create character.")
            self.show_start_screen() # Возвращаемся назад
            return

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Имя персонажа
        ttk.Label(frame, text="Character Name:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(frame)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))

        # Выбор тела
        ttk.Label(frame, text="Body Type:").pack(anchor=tk.W)
        body_names = list(self.available_bodies.keys())
        self.body_var = tk.StringVar(value=body_names[0] if body_names else "") # Выбираем первый по умолчанию
        self.body_combo = ttk.Combobox(frame, textvariable=self.body_var, values=body_names, state="readonly")
        self.body_combo.pack(fill=tk.X, pady=(0, 10))

        # Выбор компонентов
        ttk.Label(frame, text="Select Components:").pack(anchor=tk.W)
        self.component_vars = {}
        comp_frame = ttk.Frame(frame)
        comp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        canvas = tk.Canvas(comp_frame)
        scrollbar = ttk.Scrollbar(comp_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for comp_name in self.available_components.keys():
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(scrollable_frame, text=comp_name, variable=var)
            chk.pack(anchor=tk.W)
            self.component_vars[comp_name] = var

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        # Кнопка создания
        create_btn = ttk.Button(frame, text="Create Character", command=self.on_create_confirm_clicked)
        create_btn.pack(pady=10)

        # Кнопка назад
        back_btn = ttk.Button(frame, text="Back", command=self.show_start_screen)
        back_btn.pack()

    def on_create_confirm_clicked(self):
        """Обработчик подтверждения создания."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid Input", "Please enter a character name.")
            return

        # Получаем выбранный тип тела
        selected_body_name = self.body_var.get()
        selected_body_class = self.available_bodies.get(selected_body_name)
        if not selected_body_class:
             # Это маловероятно, если Combobox readonly, но на всякий случай
            messagebox.showerror("Creation Error", f"Selected body type '{selected_body_name}' not found.")
            return

        # Создаём тело (с минимальными параметрами для примера)
        # В реальности здесь может быть больше полей для ввода, специфичных для тела
        body_instance = selected_body_class(race=selected_body_name.replace("Body", "").lower(), gender="N/A")

        # Создаём персонажа
        self.current_character = Character(name=name, body=body_instance)

        # Добавляем выбранные компоненты
        for comp_name, var in self.component_vars.items():
            if var.get(): # Если чекбокс отмечен
                comp_class = self.available_components[comp_name]
                comp_instance = comp_class() # Создаём с параметрами по умолчанию
                self.current_character.add_component(comp_instance)

        print(f"GUI: Created character {self.current_character.name}")
        # Показываем созданный персонаж
        self.show_character_view()


    def show_character_view(self):
        """Показывает экран просмотра персонажа."""
        # Очищаем предыдущее содержимое
        for widget in self.winfo_children():
            widget.destroy()

        if not self.current_character:
            messagebox.showerror("View Error", "No character to display.")
            self.show_start_screen()
            return

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Имя
        ttk.Label(frame, text=f"Name: {self.current_character.name}", font=("Arial", 12, "bold")).pack(anchor=tk.W)

        # Тело
        ttk.Label(frame, text="Body:", font=("Arial", 10, "underline")).pack(anchor=tk.W)
        ttk.Label(frame, text=self.current_character.body.describe_appearance()).pack(anchor=tk.W, padx=(20, 0))

        # Компоненты
        ttk.Label(frame, text="Components:", font=("Arial", 10, "underline")).pack(anchor=tk.W, pady=(10, 0))
        comp_details_frame = ttk.Frame(frame)
        comp_details_frame.pack(fill=tk.BOTH, expand=True, padx=(20, 0))

        for comp_type, comp_instance in self.current_character.components.items():
            # Просто выводим имя компонента и его to_dict()
            comp_label = ttk.Label(comp_details_frame, text=f"- {comp_type.__name__}: {comp_instance.to_dict()}")
            comp_label.pack(anchor=tk.W)

        # Кнопка сохранения
        save_btn = ttk.Button(frame, text="Save Character", command=self.on_save_clicked)
        save_btn.pack(pady=10)

        # Кнопка назад к стартовому экрану
        back_btn = ttk.Button(frame, text="Back to Start", command=self.show_start_screen)
        back_btn.pack()


    def on_save_clicked(self):
        """Обработчик кнопки Save."""
        if not self.current_character:
            messagebox.showwarning("Save Warning", "No character is currently loaded to save.")
            return

            # Диалог сохранения
            # --- Новое: используем промежуточную переменную ---
            safe_name_for_file = self.current_character.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            initial_filename = f"{safe_name_for_file}_save.json"
            # ---

            file_path = filedialog.asksaveasfilename(
                title="Save Character As",
                initialdir="saved_characters",
                # --- Передаём подготовленную строку ---
                initialfile=initial_filename,
                # ---
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        if file_path:
            try:
                data = self.current_character.to_dict()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"GUI: Saved character {self.current_character.name} to {file_path}")
                messagebox.showinfo("Save Success", f"Character saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save character:\n{e}")

    def show_manage_bodies_screen(self):
        """Показывает экран управления типами тел (добавление новых)."""
        # Очищаем предыдущее содержимое
        for widget in self.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        ttk.Label(frame, text="Manage Body Types", font=("Arial", 14, "bold")).pack(pady=10)

        # Форма добавления нового типа тела
        form_frame = ttk.LabelFrame(frame, text="Add New Body Type")
        form_frame.pack(fill=tk.X, pady=10, padx=10)

        # Имя класса (например, InsectoidBody)
        ttk.Label(form_frame, text="Class Name (e.g., Insectoid):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.new_body_class_name_entry = ttk.Entry(form_frame)
        self.new_body_class_name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        ttk.Label(form_frame, text="('Body' will be added automatically)").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(5, 0))

        # Отображаемое имя (например, Insectoid)
        ttk.Label(form_frame, text="Display Name (e.g., Insectoid):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.new_body_display_name_entry = ttk.Entry(form_frame)
        self.new_body_display_name_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        # Размер по умолчанию
        ttk.Label(form_frame, text="Default Size:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.new_body_size_var = tk.StringVar(value="Medium")
        size_combo = ttk.Combobox(form_frame, textvariable=self.new_body_size_var, values=["Tiny", "Small", "Medium", "Large", "Huge"], state="readonly")
        size_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        # Пол (опционально)
        ttk.Label(form_frame, text="Default Gender (optional, leave empty for N/A):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.new_body_gender_entry = ttk.Entry(form_frame)
        self.new_body_gender_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        # Части тела (интерактивное дерево)
        ttk.Label(form_frame, text="Body Parts Hierarchy:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Фрейм для дерева и кнопок
        tree_frame = ttk.Frame(form_frame)
        tree_frame.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0), rowspan=3)
        
        # Дерево для отображения иерархии с поддержкой множественного выбора
        columns = ("name",)
        self.body_parts_tree = ttk.Treeview(tree_frame, columns=columns, show="tree", height=8, selectmode="extended")
        self.body_parts_tree.heading("#0", text="Body Parts")
        self.body_parts_tree.column("#0", width=250)
        
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient="vertical", command=self.body_parts_tree.yview)
        self.body_parts_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        self.body_parts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        rename_part_btn.pack(side=tk.LEFT)
        
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
        self.body_list_menu = tk.Menu(self, tearoff=0)
        self.body_list_menu.add_command(label="Load into Editor", command=self.on_load_body_to_editor)
        self.body_list_menu.add_command(label="Rename", command=self.on_rename_body_type)
        self.body_list_menu.add_command(label="Copy", command=self.on_copy_body_type)
        self.body_list_menu.add_command(label="Delete", command=self.on_delete_body_type)

        # Привязка контекстного меню к списку
        self.bodies_listbox.bind("<Button-3>", self.on_body_list_right_click)
        self.bodies_listbox.bind("<Double-Button-1>", lambda e: self.on_load_body_to_editor())

        # Заполняем список
        self.refresh_bodies_list()
        
        # Инициализируем дерево с обязательной корневой частью "Body"
        self.init_body_structure_with_root()

        # Кнопка назад
        back_btn = ttk.Button(frame, text="Back to Start", command=self.show_start_screen)
        back_btn.pack(pady=5)

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
        # Сохраняем текущее состояние раскрытия узлов
        self.tree_expanded_items = set(self.body_parts_tree.item(item, "open") for item in self.body_parts_tree.get_children("") if self.body_parts_tree.item(item, "open"))
        
        # Очищаем дерево
        for item in self.body_parts_tree.get_children():
            self.body_parts_tree.delete(item)
        
        # Рекурсивно добавляем узлы
        def add_children(parent_node_id, parent_key):
            children = self.current_body_structure.get(parent_key, [])
            for child_name in children:
                # Добавляем узел в дерево
                node_id = self.body_parts_tree.insert(parent_node_id, "end", text=child_name, values=(child_name,))
                # Рекурсивно добавляем детей этого узла
                add_children(node_id, child_name)
        
        # Начинаем с корневых элементов (ключ None)
        root_parts = self.current_body_structure.get(None, [])
        for part_name in root_parts:
            node_id = self.body_parts_tree.insert("", "end", text=part_name, values=(part_name,))
            # Раскрываем корневые узлы по умолчанию
            self.body_parts_tree.item(node_id, open=True)
            add_children(node_id, part_name)

    def on_add_root_part(self):
        """Добавляет дочернюю часть к 'Body' (независимо от выбора пользователя)."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Body Part")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            if name in self.current_body_structure:
                messagebox.showwarning("Duplicate", f"Part '{name}' already exists.", parent=dialog)
                return
            
            # Добавляем как дочернюю часть к 'Body'
            if "Body" not in self.current_body_structure:
                self.current_body_structure["Body"] = []
            self.current_body_structure["Body"].append(name)
            self.current_body_structure[name] = []
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=confirm).pack(pady=5)

    def on_add_child_part(self):
        """Добавляет дочернюю часть к выбранным узлам (поддержка множественного выбора)."""
        selected = self.body_parts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select one or more parent parts first.", parent=self)
            return
        
        # Получаем имена всех выбранных родительских узлов
        parent_names = [self.body_parts_tree.item(item)["text"] for item in selected]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Child to {len(parent_names)} part(s)")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Child Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            if name in self.current_body_structure:
                messagebox.showwarning("Duplicate", f"Part '{name}' already exists.", parent=dialog)
                return
            
            # Добавляем как дочернюю часть ко всем выбранным родителям
            for parent_name in parent_names:
                if parent_name not in self.current_body_structure:
                    self.current_body_structure[parent_name] = []
                self.current_body_structure[parent_name].append(name)
            
            self.current_body_structure[name] = []
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=confirm).pack(pady=5)

    def on_delete_part(self):
        """Удаляет выбранную часть и всех её потомков."""
        selected = self.body_parts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a part to delete.", parent=self)
            return
        
        part_name = self.body_parts_tree.item(selected[0])["text"]
        
        if not messagebox.askyesno("Confirm Delete", f"Delete '{part_name}' and all its children?", parent=self):
            return
        
        # Удаляем из списка родителя
        for parent, children in list(self.current_body_structure.items()):
            if part_name in children:
                children.remove(part_name)
        
        # Рекурсивно собираем всех потомков для удаления
        def get_all_descendants(part):
            descendants = []
            children = self.current_body_structure.get(part, [])
            for child in children:
                descendants.append(child)
                descendants.extend(get_all_descendants(child))
            return descendants
        
        all_to_remove = [part_name] + get_all_descendants(part_name)
        
        # Удаляем записи о детях
        for part in all_to_remove:
            if part in self.current_body_structure:
                del self.current_body_structure[part]
        
        self.update_body_parts_tree()

    def on_rename_part(self):
        """Переименовывает выбранную часть."""
        selected = self.body_parts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a part to rename.", parent=self)
            return
        
        old_name = self.body_parts_tree.item(selected[0])["text"]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Rename '{old_name}'")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.insert(0, old_name)
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)
        
        def confirm():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            if new_name == old_name:
                dialog.destroy()
                return
            if new_name in self.current_body_structure:
                messagebox.showwarning("Duplicate", f"Part '{new_name}' already exists.", parent=dialog)
                return
            
            # Обновляем структуру
            # 1. Находим родителя и обновляем список детей
            parent_key = None
            for p, children in self.current_body_structure.items():
                if old_name in children:
                    children[children.index(old_name)] = new_name
                    parent_key = p
                    break
            
            # 2. Обновляем ключ в словаре (если это не None)
            if old_name in self.current_body_structure:
                children_list = self.current_body_structure.pop(old_name)
                self.current_body_structure[new_name] = children_list
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=5)

    def on_create_body_type_clicked(self):
        """Обработчик создания нового типа тела через интерфейс."""
        class_name = self.new_body_class_name_entry.get().strip()
        display_name = self.new_body_display_name_entry.get().strip()
        default_size = self.new_body_size_var.get().strip()
        default_gender = self.new_body_gender_entry.get().strip()
        desc_template = self.new_body_desc_template_entry.get().strip()

        # Валидация
        if not class_name:
            messagebox.showwarning("Invalid Input", "Class Name is required.")
            return
        if not class_name.endswith("Body"):
             messagebox.showwarning("Invalid Input", "Class Name should end with 'Body' (e.g., InsectoidBody).")
             return
        if not display_name:
            display_name = class_name.replace("Body", "")
        
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

        # Генерация кода для нового файла тела
        # Используем простой шаблон, предполагая, что у всех тел есть race, size, gender (опционально)
        has_gender = bool(default_gender)
        
        code_lines = [
            f"# file: bodies/{class_name.lower()}.py",
            "from body import AbstractBody",
            "",
            f"class {class_name}(AbstractBody):",
            "    def __init__(self, race=\"Custom\", size=\"" + default_size + "\"" + (f", gender=\"{default_gender}\"" if has_gender else "") + "):",
            "        super().__init__(race, size)",
        ]
        
        if has_gender:
            code_lines.append("        self.gender = gender")
        
        # Форматируем body_structure для вывода в коде
        structure_str = str(body_structure).replace("'", '"')
        code_lines.append(f"        self.body_structure = {structure_str}")
        code_lines.append("")
        
        # Формируем описание
        # Если шаблон пустой, используем дефолтный
        if not desc_template:
            desc_template = f"A {{size}} {{gender}} {display_name}."
        
        # Заменяем плейсхолдеры в шаблоне на атрибуты объекта
        # Шаблон пользователя: "A {size} {gender} {race} with an insectoid body."
        # В коде будет: return f"A {self.size} {self.gender} {self.race} with an insectoid body."
        desc_code = desc_template.replace("{size}", "{self.size}").replace("{gender}", "{self.gender}").replace("{race}", "{self.race}")
        code_lines.append(f"    def describe_appearance(self):")
        code_lines.append(f"        return f\"{desc_code}\"")
        code_lines.append("")

        new_code = "\n".join(code_lines)

        # Сохранение файла
        filename = f"{class_name.lower()}.py"
        filepath = os.path.join("bodies", filename)
        
        # Создаем директорию bodies если нет (на всякий случай)
        os.makedirs("bodies", exist_ok=True)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
            print(f"GUI: Created new body type file: {filepath}")
            
            # Перезагрузка списка доступных тел
            # Просто заново вызываем загрузчик
            self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
            print(f"GUI: Reloaded modules. Now have {len(self.available_bodies)} bodies.")
            
            # Обновляем список в интерфейсе
            self.refresh_bodies_list()
            
            # Очищаем поля формы и дерево
            self.new_body_class_name_entry.delete(0, tk.END)
            self.new_body_display_name_entry.delete(0, tk.END)
            self.new_body_gender_entry.delete(0, tk.END)
            self.new_body_desc_template_entry.delete(0, tk.END)
            self.new_body_size_var.set("Medium")
            
            # Сбрасываем структуру и дерево
            self.current_body_structure = {None: []}
            self.update_body_parts_tree()

            messagebox.showinfo("Success", f"Successfully created new body type '{class_name}'!\nIt is now available for selection.")
            
        except Exception as e:
            messagebox.showerror("Creation Error", f"Failed to create body type file:\n{e}")

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
        # Получаем путь к файлу тела
        filename = f"{body_name.lower()}.py"
        filepath = os.path.join("bodies", filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File for '{body_name}' not found at {filepath}.")
            return
        
        try:
            # Динамически загружаем модуль
            import importlib.util
            spec = importlib.util.spec_from_file_location(body_name, filepath)
            module = importlib.util.module_from_spec(spec)
            
            # Проверяем, не является ли класс встроенным
            # Если файл содержит определение класса, загружаем его
            with open(filepath, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Выполняем код модуля в безопасном контексте
            exec(source_code, module.__dict__)
            
            # Получаем класс из модуля
            body_class = getattr(module, body_name, None)
            
            if not body_class:
                messagebox.showerror("Error", f"Could not find class '{body_name}' in the module.")
                return
            
            # Создаем экземпляр для получения данных

            if hasattr(body_class, '__init__') and 'gender' in body_class.__init__.__code__.co_varnames:
                instance = body_class(race=body_name.replace("Body", ""), gender="N/A")
            else:
                instance = body_class(race=body_name.replace("Body", ""))
            
            # Заполняем поля формы
            self.new_body_class_name_entry.delete(0, tk.END)
            self.new_body_class_name_entry.insert(0, body_name)
            
            display_name = body_name.replace("Body", "")
            self.new_body_display_name_entry.delete(0, tk.END)
            self.new_body_display_name_entry.insert(0, display_name)
            
            self.new_body_size_var.set(getattr(instance, 'size', 'Medium'))
            
            if hasattr(instance, 'gender'):
                self.new_body_gender_entry.delete(0, tk.END)
                self.new_body_gender_entry.insert(0, getattr(instance, 'gender', ''))
            
            # Загружаем структуру частей тела
            if hasattr(instance, 'body_structure'):
                self.current_body_structure = dict(instance.body_structure)
                self.update_body_parts_tree()
            
            # Пытаемся получить шаблон описания из исходного кода

            import re
            match = re.search(r'return\s+f["\'](.+?)["\']', source_code, re.DOTALL)

            if match:
                desc_template = match.group(1)
                # Восстанавливаем плейсхолдеры
                desc_template = desc_template.replace("{self.size}", "{size}").replace("{self.gender}", "{gender}").replace("{self.race}", "{race}")
                self.new_body_desc_template_entry.delete(0, tk.END)
                self.new_body_desc_template_entry.insert(0, desc_template)
            
            messagebox.showinfo("Loaded", f"Loaded '{body_name}' into editor.\nYou can now modify and save it as a new type.")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load body data:\n{e}")

    def on_rename_body_type(self):
        """Переименовывает выбранный тип тела (создает копию с новым именем и удаляет старый)."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to rename.")
            return
        
        old_name = self.bodies_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Rename '{old_name}'")
        dialog.geometry("400x150")
        dialog.transient(self)
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

            # Загружаем данные старого тела из файла
            filename = f"{old_name.lower()}.py"
            filepath = os.path.join("bodies", filename)
            
            if not os.path.exists(filepath):
                messagebox.showerror("Error", f"File for '{old_name}' not found at {filepath}.")
                return
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                import importlib.util
                spec = importlib.util.spec_from_file_location(old_name, filepath)
                module = importlib.util.module_from_spec(spec)
                exec(source_code, module.__dict__)
                
                body_class = getattr(module, old_name, None)
                if not body_class:
                    messagebox.showerror("Error", f"Could not find class '{old_name}' in the module.")
                    return

                if hasattr(body_class, '__init__') and 'gender' in body_class.__init__.__code__.co_varnames:
                    instance = body_class(race=old_name.replace("Body", ""), gender="N/A")
                else:
                    instance = body_class(race=old_name.replace("Body", ""))
                
                # Генерируем новый код с новым именем
                body_structure = dict(instance.body_structure)
                structure_str = str(body_structure).replace("'", '"')

                # Получаем шаблон описания из исходного кода
                import re
                match = re.search(r'return\\s+f["\'](.+?)["\']', source_code, re.DOTALL)

                desc_code = match.group(1) if match else f"A {{self.size}} {{self.gender}} {new_name.replace('Body', '')}."
                
                has_gender = hasattr(instance, 'gender')
                default_gender = getattr(instance, 'gender', '')
                default_size = getattr(instance, 'size', 'Medium')
                
                code_lines = [
                    f"# file: bodies/{new_name.lower()}.py",
                    "from body import AbstractBody",
                    "",
                    f"class {new_name}(AbstractBody):",
                    "    def __init__(self, race=\"Custom\", size=\"" + default_size + "\"" + (f", gender=\"{default_gender}\"" if has_gender else "") + "):",
                    "        super().__init__(race, size)",
                ]
                
                if has_gender:
                    code_lines.append("        self.gender = gender")
                
                code_lines.append(f"        self.body_structure = {structure_str}")
                code_lines.append("")
                code_lines.append(f"    def describe_appearance(self):")
                code_lines.append(f"        return f\"{desc_code}\"")
                code_lines.append("")
                
                new_code = "\n".join(code_lines)
                
                # Сохраняем новый файл
                filename = f"{new_name.lower()}.py"
                filepath = os.path.join("bodies", filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_code)
                
                # Удаляем старый файл
                old_filename = f"{old_name.lower()}.py"
                old_filepath = os.path.join("bodies", old_filename)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
                
                # Перезагружаем список тел
                self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
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
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Copy '{old_name}'")
        dialog.geometry("400x150")
        dialog.transient(self)
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
            

            # Загружаем данные старого тела из файла
            filename = f"{old_name.lower()}.py"
            filepath = os.path.join("bodies", filename)
            
            if not os.path.exists(filepath):
                messagebox.showerror("Error", f"File for '{old_name}' not found at {filepath}.")
                return
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                import importlib.util
                spec = importlib.util.spec_from_file_location(old_name, filepath)
                module = importlib.util.module_from_spec(spec)
                exec(source_code, module.__dict__)
                
                body_class = getattr(module, old_name, None)
                if not body_class:
                    messagebox.showerror("Error", f"Could not find class '{old_name}' in the module.")
                    return

                if hasattr(body_class, '__init__') and 'gender' in body_class.__init__.__code__.co_varnames:
                    instance = body_class(race=old_name.replace("Body", ""), gender="N/A")
                else:
                    instance = body_class(race=old_name.replace("Body", ""))
                
                # Генерируем новый код
                body_structure = dict(instance.body_structure)
                structure_str = str(body_structure).replace("'", '"')
                

                import re
                match = re.search(r'return\\s+f["\'](.+?)["\']', source_code, re.DOTALL)

                desc_code = match.group(1) if match else f"A {{self.size}} {{self.gender}} {new_name.replace('Body', '')}."
                
                has_gender = hasattr(instance, 'gender')
                default_gender = getattr(instance, 'gender', '')
                default_size = getattr(instance, 'size', 'Medium')
                
                code_lines = [
                    f"# file: bodies/{new_name.lower()}.py",
                    "from body import AbstractBody",
                    "",
                    f"class {new_name}(AbstractBody):",
                    "    def __init__(self, race=\"Custom\", size=\"" + default_size + "\"" + (f", gender=\"{default_gender}\"" if has_gender else "") + "):",
                    "        super().__init__(race, size)",
                ]
                
                if has_gender:
                    code_lines.append("        self.gender = gender")
                
                code_lines.append(f"        self.body_structure = {structure_str}")
                code_lines.append("")
                code_lines.append(f"    def describe_appearance(self):")
                code_lines.append(f"        return f\"{desc_code}\"")
                code_lines.append("")
                
                new_code = "\n".join(code_lines)
                
                # Сохраняем новый файл
                filename = f"{new_name.lower()}.py"
                filepath = os.path.join("bodies", filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_code)
                
                # Перезагружаем список тел
                self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
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
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{body_name}'?\nThis will permanently remove the file."):
            return
        
        try:
            # Удаляем файл
            filename = f"{body_name.lower()}.py"
            filepath = os.path.join("bodies", filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
                # Перезагружаем список тел
                self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
                self.refresh_bodies_list()
                
                messagebox.showinfo("Success", f"Successfully deleted '{body_name}'.")
            else:
                messagebox.showerror("Error", f"File for '{body_name}' not found at {filepath}.")
                
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete body type:\n{e}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()