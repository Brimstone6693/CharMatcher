# file: body_type_manager/body_management.py
"""
Миксин для управления типами тел (создание, сохранение, загрузка, удаление).
"""

import os
import json
import tkinter as tk
from tkinter import messagebox, ttk
from core.module_loader import BODIES_DATA_DIR, load_available_modules_and_bodies


class BodyManagementMixin:
    """Предоставляет функциональность управления типами тел."""
    
    def _reload_available_bodies(self):
        """Перезагружает список доступных компонентов и тел."""
        self.available_components, self.available_bodies = load_available_modules_and_bodies("modules", "bodies")
    
    def show_start_screen(self):
        """Возвращает к начальному экрану (делегирование родительскому окну)."""
        if hasattr(self.parent, 'show_start_screen'):
            self.parent.show_start_screen()
    
    def init_body_structure_with_root(self):
        """Инициализирует структуру тела с обязательной корневой частью 'Body'."""
        self.current_body_structure = {None: ["Body"], "Body": []}
        self.update_body_parts_tree()
    
    def refresh_bodies_list(self):
        """Обновляет список отображаемых типов тел в ListBox."""
        self.bodies_listbox.delete(0, tk.END)
        # Исключаем "DynamicBody" из списка - это служебный класс для загрузок сохранений
        for body_name in sorted(k for k in self.available_bodies.keys() if k != "DynamicBody"):
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
    
    def new_body(self):
        """Создает новое тело (сбрасывает текущую структуру)"""
        if self.current_body_structure and any(k is not None for k in self.current_body_structure.keys()):
            if not messagebox.askyesno("Confirm", "Discard current body and create new?", parent=self.parent):
                return
        
        # Очищаем форму
        self.new_body_class_name_entry.delete(0, tk.END)
        self.new_body_display_name_entry.delete(0, tk.END)
        self.new_body_height_min_entry.delete(0, tk.END)
        self.new_body_height_max_entry.delete(0, tk.END)
        self.new_body_height_min_entry.insert(0, "150")
        self.new_body_height_max_entry.insert(0, "200")
        self.new_body_gender_var.set("N/A")
        self.new_body_gender_custom_entry.delete(0, tk.END)
        self.new_body_desc_template_entry.delete(0, tk.END)
        self.new_body_desc_template_entry.insert(0, "A {size} {gender} {display_name}.")
        self.height_type_var.set("standing")
        
        # Инициализируем структуру с корнем
        self.init_body_structure_with_root()
        self.update_auto_size()
    
    def save_body(self):
        """Сохраняет текущее тело в файл JSON."""
        class_name = self.new_body_class_name_entry.get().strip()
        display_name = self.new_body_display_name_entry.get().strip()
        
        if not class_name or not display_name:
            messagebox.showwarning("Invalid Input", "Class Name and Display Name are required.", parent=self.parent)
            return
        
        # Добавляем "Body" к имени класса если его нет
        if not class_name.endswith("Body"):
            class_name += "Body"
        
        # Собираем данные
        try:
            min_height = float(self.new_body_height_min_entry.get().strip())
            max_height = float(self.new_body_height_max_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Height values must be numbers.", parent=self.parent)
            return
        
        data = {
            "class_name": class_name,
            "display_name": display_name,
            "height_type": self.height_type_var.get(),
            "min_height_cm": min_height,
            "max_height_cm": max_height,
            "gender": self.get_final_gender(),
            "description_template": self.new_body_desc_template_entry.get().strip(),
            "body_structure": self.current_body_structure
        }
        
        # Сохраняем в файл
        filename = f"{class_name.lower()}.json"
        filepath = os.path.join(BODIES_DATA_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Body type '{class_name}' saved!", parent=self.parent)
            self._reload_available_bodies()
            self.refresh_bodies_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save body type: {str(e)}", parent=self.parent)
    
    def on_create_body_type_clicked(self):
        """Обрабатывает создание нового типа тела из формы."""
        self.save_body()
    
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
            
            min_height = data.get('min_height_cm', 150)
            max_height = data.get('max_height_cm', 200)
            self.new_body_height_min_entry.delete(0, tk.END)
            self.new_body_height_max_entry.delete(0, tk.END)
            self.new_body_height_min_entry.insert(0, str(min_height))
            self.new_body_height_max_entry.insert(0, str(max_height))
            
            # Пол
            gender = data.get('gender', 'N/A')
            predefined_genders = ["Male", "Female", "Herm", "N/A", "Other"]
            if gender in predefined_genders:
                self.new_body_gender_var.set(gender)
                self.new_body_gender_custom_entry.delete(0, tk.END)
            else:
                self.new_body_gender_var.set("Other")
                self.new_body_gender_custom_entry.delete(0, tk.END)
                self.new_body_gender_custom_entry.insert(0, gender)
            
            # Шаблон описания
            desc_template = data.get('description_template', "A {size} {gender} {display_name}.")
            self.new_body_desc_template_entry.delete(0, tk.END)
            self.new_body_desc_template_entry.insert(0, desc_template)
            
            # Структура тела
            self.current_body_structure = data.get("body_structure", {})
            self.update_body_parts_tree()
            self.update_auto_size()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load body type: {str(e)}", parent=self.parent)
    
    def on_rename_body_type(self):
        """Переименовывает выбранный тип тела."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to rename.", parent=self.parent)
            return
        
        old_name = self.bodies_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Rename Body Type")
        dialog.geometry("300x150")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.insert(0, old_name)
        name_entry.pack(pady=5)
        
        def confirm():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Name cannot be empty.", parent=dialog)
                return
            
            if new_name == old_name:
                dialog.destroy()
                return
            
            # Переименовываем файл
            old_filename = f"{old_name.lower()}.json"
            new_filename = f"{new_name.lower()}.json"
            old_filepath = os.path.join(BODIES_DATA_DIR, old_filename)
            new_filepath = os.path.join(BODIES_DATA_DIR, new_filename)
            
            if not os.path.exists(old_filepath):
                messagebox.showerror("Error", f"File for '{old_name}' not found.", parent=dialog)
                return
            
            if os.path.exists(new_filepath):
                messagebox.showerror("Error", f"A body type named '{new_name}' already exists.", parent=dialog)
                return
            
            try:
                os.rename(old_filepath, new_filepath)
                messagebox.showinfo("Success", f"Body type renamed to '{new_name}'!", parent=dialog)
                dialog.destroy()
                self._reload_available_bodies()
                self.refresh_bodies_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename: {str(e)}", parent=dialog)
        
        ttk.Button(dialog, text="Rename", command=confirm).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def on_copy_body_type(self):
        """Копирует выбранный тип тела."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to copy.", parent=self.parent)
            return
        
        source_name = self.bodies_listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Copy Body Type")
        dialog.geometry("300x150")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.insert(0, f"{source_name}_Copy")
        name_entry.pack(pady=5)
        
        def confirm():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Input", "Name cannot be empty.", parent=dialog)
                return
            
            # Копируем файл
            source_filename = f"{source_name.lower()}.json"
            new_filename = f"{new_name.lower()}.json"
            source_filepath = os.path.join(BODIES_DATA_DIR, source_filename)
            new_filepath = os.path.join(BODIES_DATA_DIR, new_filename)
            
            if not os.path.exists(source_filepath):
                messagebox.showerror("Error", f"File for '{source_name}' not found.", parent=dialog)
                return
            
            if os.path.exists(new_filepath):
                messagebox.showerror("Error", f"A body type named '{new_name}' already exists.", parent=dialog)
                return
            
            try:
                import shutil
                shutil.copy2(source_filepath, new_filepath)
                messagebox.showinfo("Success", f"Body type copied to '{new_name}'!", parent=dialog)
                dialog.destroy()
                self._reload_available_bodies()
                self.refresh_bodies_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy: {str(e)}", parent=dialog)
        
        ttk.Button(dialog, text="Copy", command=confirm).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def on_delete_body_type(self):
        """Удаляет выбранный тип тела."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a body type to delete.", parent=self.parent)
            return
        
        body_name = self.bodies_listbox.get(selection[0])
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{body_name}'?", parent=self.parent):
            return
        
        filename = f"{body_name.lower()}.json"
        filepath = os.path.join(BODIES_DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File for '{body_name}' not found.", parent=self.parent)
            return
        
        try:
            os.remove(filepath)
            messagebox.showinfo("Success", f"Body type '{body_name}' deleted!", parent=self.parent)
            self._reload_available_bodies()
            self.refresh_bodies_list()
            
            # Если это было загружено в редактор, очищаем форму
            class_name_in_form = self.new_body_class_name_entry.get().strip()
            if class_name_in_form.endswith("Body"):
                class_name_in_form = class_name_in_form[:-4]
            if class_name_in_form == body_name.replace("Body", ""):
                self.new_body()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {str(e)}", parent=self.parent)
    
    def on_body_list_right_click(self, event):
        """Обрабатывает правый клик по списку тел."""
        item = self.bodies_listbox.nearest(event.y)
        if item >= 0:
            self.bodies_listbox.selection_clear(0, tk.END)
            self.bodies_listbox.selection_set(item)
        
        try:
            self.body_list_menu.post(event.x_root, event.y_root)
        finally:
            self.body_list_menu.grab_release()
