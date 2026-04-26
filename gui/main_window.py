# file: gui_main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from core.character import Character
from core.module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR
from core.body_types.body_classes import AbstractBody
from modules import BaseComponent

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
        # Делегируем создание экрана менеджеру типов тел
        if not hasattr(self, 'body_manager'):
            from core.body_types.core import BodyTypeManager
            self.body_manager = BodyTypeManager(self)
        
        self.body_manager.create_manage_bodies_screen()

    def init_body_structure_with_root(self):
        """Инициализирует структуру тела с обязательной корневой частью 'Body'."""
        self.current_body_structure = {None: ["Body"], "Body": []}
        self.update_body_parts_tree()

    def refresh_bodies_list(self):
        """Обновляет список отображаемых типов тел в ListBox."""
        self.bodies_listbox.delete(0, tk.END)
        for body_name in sorted(self.available_bodies.keys()):
            self.bodies_listbox.insert(tk.END, body_name)

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
            # Для standing height (человеческий стандарт - рост от земли до макушки)
            # Tiny: < 30cm, Small: 30-100cm, Medium: 100-180cm, Large: 180-400cm, Huge: 400-700cm, Gargantuan: > 700cm
            if height_type == "standing":
                if avg_height < 30:
                    size_category = "Tiny"
                elif avg_height < 100:
                    size_category = "Small"
                elif avg_height < 180:
                    size_category = "Medium"
                elif avg_height < 400:
                    size_category = "Large"
                elif avg_height < 700:
                    size_category = "Huge"
                else:
                    size_category = "Gargantuan"
            # Для withers height (высота в холке - для четвероногих существ)
            # Холка обычно составляет ~60-70% от полной высоты стоящего существа
            # Поэтому пороги ниже: Tiny: < 20cm, Small: 20-60cm, Medium: 60-120cm, Large: 120-250cm, Huge: 250-450cm, Gargantuan: > 450cm
            else:  # withers
                if avg_height < 20:
                    size_category = "Tiny"
                elif avg_height < 60:
                    size_category = "Small"
                elif avg_height < 120:
                    size_category = "Medium"
                elif avg_height < 250:
                    size_category = "Large"
                elif avg_height < 450:
                    size_category = "Huge"
                else:
                    size_category = "Gargantuan"
            
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

    def update_body_parts_tree(self):
        """Обновляет дерево частей тела на основе current_body_structure с сохранением состояния раскрытия."""
        # Сохраняем текущее состояние раскрытия узлов по их именам
        expanded_items = set()
        for item in self.body_parts_tree.get_children(""):
            if self.body_parts_tree.item(item, "open"):
                item_text = self.body_parts_tree.item(item)["text"].split(" [")[0]  # Убираем теги для пути
                expanded_items.add(item_text)
                # Сохраняем также детей этого узла
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
        """Добавляет корневую часть тела (к ключу None)."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Root Body Part")
        dialog.geometry("350x180")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus()
        
        ttk.Label(dialog, text="Tags (comma-separated, optional):").pack(pady=5)
        tags_entry = ttk.Entry(dialog)
        tags_entry.pack(pady=5)
        
        def confirm():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            
            # Парсим теги
            tags_input = tags_entry.get().strip()
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            # Добавляем как корневую часть (ключ None)
            if None not in self.current_body_structure:
                self.current_body_structure[None] = []
            
            # Проверяем дубликаты
            existing_names = [c["name"] if isinstance(c, dict) else c for c in self.current_body_structure[None]]
            if name in existing_names:
                messagebox.showwarning("Duplicate", f"Part '{name}' already exists.", parent=dialog)
                return
            
            self.current_body_structure[None].append({"name": name, "tags": tags})
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
        
        # Получаем имена всех выбранных родительских узлов (из колонки text, а не values)
        parent_names = [self.body_parts_tree.item(item)["text"] for item in selected]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Child to {len(parent_names)} part(s)")
        dialog.geometry("350x180")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Child Part Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus()
        
        ttk.Label(dialog, text="Tags (comma-separated, optional):").pack(pady=5)
        tags_entry = ttk.Entry(dialog)
        tags_entry.pack(pady=5)
        
        def confirm():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            
            # Парсим теги
            tags_input = tags_entry.get().strip()
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            # Добавляем как дочернюю часть ко всем выбранным родителям
            for parent_name in parent_names:
                if parent_name not in self.current_body_structure:
                    self.current_body_structure[parent_name] = []
                
                # Проверяем дубликаты у каждого родителя
                existing_names = [c["name"] if isinstance(c, dict) else c for c in self.current_body_structure[parent_name]]
                if name not in existing_names:
                    self.current_body_structure[parent_name].append({"name": name, "tags": tags})
            
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
            normalized_children = [c["name"] if isinstance(c, dict) else c for c in children]
            if part_name in normalized_children:
                idx = normalized_children.index(part_name)
                children.pop(idx)
        
        # Рекурсивно собираем всех потомков для удаления
        def get_all_descendants(part):
            descendants = []
            children = self.current_body_structure.get(part, [])
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                descendants.append(child_name)
                descendants.extend(get_all_descendants(child_name))
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
        dialog.geometry("350x180")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.insert(0, old_name)
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)
        
        # Показываем текущие теги
        current_tags = []
        for parent, children in self.current_body_structure.items():
            for child in children:
                child_name = child["name"] if isinstance(child, dict) else child
                if child_name == old_name:
                    current_tags = child.get("tags", []) if isinstance(child, dict) else []
                    break
        
        ttk.Label(dialog, text="Tags (comma-separated):").pack(pady=5)
        tags_entry = ttk.Entry(dialog)
        tags_entry.insert(0, ", ".join(current_tags))
        tags_entry.pack(pady=5)
        
        def confirm():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Part name cannot be empty.", parent=dialog)
                return
            if new_name == old_name and tags_entry.get().strip() == ", ".join(current_tags):
                dialog.destroy()
                return
            
            # Проверяем дубликаты имен
            all_names = self.get_all_part_names_from_structure()
            if new_name != old_name and new_name in all_names:
                messagebox.showwarning("Duplicate", f"Part '{new_name}' already exists.", parent=dialog)
                return
            
            # Парсим новые теги
            tags_input = tags_entry.get().strip()
            new_tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            # Обновляем структуру
            # 1. Находим родителя и обновляем список детей
            for p, children in self.current_body_structure.items():
                for i, child in enumerate(children):
                    child_name = child["name"] if isinstance(child, dict) else child
                    if child_name == old_name:
                        # Обновляем имя и теги
                        if isinstance(child, dict):
                            child["name"] = new_name
                            child["tags"] = new_tags
                        else:
                            children[i] = {"name": new_name, "tags": new_tags}
                        break
            
            # 2. Обновляем ключ в словаре (если это не None)
            if old_name in self.current_body_structure:
                children_list = self.current_body_structure.pop(old_name)
                # Обновляем имена родителей у детей этой части
                self.current_body_structure[new_name] = children_list
            
            self.update_body_parts_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=5)

    def get_all_part_names_from_structure(self):
        """Возвращает все имена частей из текущей структуры."""
        names = []
        for children in self.current_body_structure.values():
            for child in children:
                names.append(child["name"] if isinstance(child, dict) else child)
        return names

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
        # Убираем проверку на окончание "Body" - теперь добавляем автоматически
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
        
        # Создаем словарь данных для JSON
        body_data = {
            "class_name": class_name,
            "race": "Custom",
            "size": default_size,
            "gender": default_gender if default_gender else "N/A",
            "display_name": display_name,
            "description_template": desc_template,
            "body_structure": body_structure
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
            # Просто заново вызываем загрузчик
            self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
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
            
            # Размер теперь определяется через диапазон высот
            # Для обратной совместимости используем дефолтные значения
            size_category = data.get('size', 'Medium')
            # Устанавливаем примерные значения высоты на основе категории размера
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
            # Удаляем файл JSON
            filename = f"{body_name.lower()}.json"
            filepath = os.path.join(BODIES_DATA_DIR, filename)
            
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