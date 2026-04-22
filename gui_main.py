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
        ttk.Label(form_frame, text="Class Name (e.g., InsectoidBody):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.new_body_class_name_entry = ttk.Entry(form_frame)
        self.new_body_class_name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

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

        # Части тела (через запятую)
        ttk.Label(form_frame, text="Body Parts (comma-separated, e.g., head, torso, wing_left, wing_right):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.new_body_parts_entry = ttk.Entry(form_frame)
        self.new_body_parts_entry.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        # Описание внешности (шаблон)
        ttk.Label(form_frame, text="Appearance Description Template (use {size}, {gender}, {race}):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.new_body_desc_template_entry = ttk.Entry(form_frame, width=60)
        self.new_body_desc_template_entry.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        ttk.Label(form_frame, text="Example: A {size} {gender} {race} with an insectoid body.").grid(row=6, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))

        # Кнопка создания
        create_btn = ttk.Button(form_frame, text="Create Body Type", command=self.on_create_body_type_clicked)
        create_btn.grid(row=7, column=0, columnspan=2, pady=15)

        # Список существующих типов тел
        list_frame = ttk.LabelFrame(frame, text="Existing Body Types")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self.bodies_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bodies_listbox.yview)
        self.bodies_listbox.configure(yscrollcommand=scrollbar.set)

        self.bodies_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Заполняем список
        self.refresh_bodies_list()

        # Кнопка назад
        back_btn = ttk.Button(frame, text="Back to Start", command=self.show_start_screen)
        back_btn.pack(pady=5)

    def refresh_bodies_list(self):
        """Обновляет список отображаемых типов тел в ListBox."""
        self.bodies_listbox.delete(0, tk.END)
        for body_name in sorted(self.available_bodies.keys()):
            self.bodies_listbox.insert(tk.END, body_name)

    def on_create_body_type_clicked(self):
        """Обработчик создания нового типа тела через интерфейс."""
        class_name = self.new_body_class_name_entry.get().strip()
        display_name = self.new_body_display_name_entry.get().strip()
        default_size = self.new_body_size_var.get().strip()
        default_gender = self.new_body_gender_entry.get().strip()
        body_parts_str = self.new_body_parts_entry.get().strip()
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
        if not body_parts_str:
            messagebox.showwarning("Invalid Input", "Body Parts are required (comma-separated).")
            return
        if not desc_template:
            messagebox.showwarning("Invalid Input", "Appearance Description Template is required.")
            return

        # Проверка на дубликат
        if class_name in self.available_bodies:
            messagebox.showwarning("Duplicate", f"A body type with class name '{class_name}' already exists.")
            return

        # Парсинг частей тела
        body_parts = [part.strip() for part in body_parts_str.split(',') if part.strip()]
        if not body_parts:
            messagebox.showwarning("Invalid Input", "Please provide at least one valid body part.")
            return

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
        
        code_lines.append(f"        self.body_parts = {body_parts}")
        code_lines.append("")
        
        # Формируем описание
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
            
            # Очищаем поля формы
            self.new_body_class_name_entry.delete(0, tk.END)
            self.new_body_display_name_entry.delete(0, tk.END)
            self.new_body_gender_entry.delete(0, tk.END)
            self.new_body_parts_entry.delete(0, tk.END)
            self.new_body_desc_template_entry.delete(0, tk.END)
            self.new_body_size_var.set("Medium")

            messagebox.showinfo("Success", f"Successfully created new body type '{class_name}'!\nIt is now available for selection.")
            
        except Exception as e:
            messagebox.showerror("Creation Error", f"Failed to create body type file:\n{e}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()