#!/usr/bin/env python3
# file: modules/body_maker/run.py
"""
Точка входа для независимого запуска Body Maker.
Этот скрипт позволяет запустить Body Maker отдельно от основного приложения.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Добавляем корень проекта в путь для импортов
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from modules.body_maker.core.core import BodyTypeManager


class BodyMakerApp(tk.Tk):
    """Основное приложение Body Maker."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Body Maker - Редактор типов тел")
        self.geometry("1024x768")
        
        # Создаем главное окно и передаем его в BodyTypeManager
        self.body_manager = BodyTypeManager(self)
        
        # Инициализируем UI главного окна (создаем виджеты listbox и другие)
        self._setup_ui()
        
        # После создания всех виджетов создаем экран управления телами
        self.body_manager.create_manage_bodies_screen()
    
    def _setup_ui(self):
        """Настраивает основной интерфейс приложения."""
        # Основной фрейм
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="Body Maker - Создание и редактирование типов тел",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Кнопка для создания/редактирования тела
        create_btn = ttk.Button(
            main_frame,
            text="Создать новый тип тела",
            command=self._on_create_body_clicked
        )
        create_btn.pack(pady=10)
        
        # Кнопка для загрузки существующего тела
        load_btn = ttk.Button(
            main_frame,
            text="Загрузить существующий тип тела",
            command=self._on_load_body_clicked
        )
        load_btn.pack(pady=10)
        
        # Список доступных тел
        ttk.Label(main_frame, text="Доступные типы тел:").pack(anchor=tk.W, pady=(20, 5))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox с прокруткой
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.bodies_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.bodies_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.bodies_listbox.yview)
        
        # Заполняем список доступными телами
        self._refresh_bodies_list()
        
        # Контекстное меню для listbox
        self.body_list_menu = tk.Menu(self, tearoff=0)
        self.body_list_menu.add_command(label="Редактировать", command=self._on_edit_body_clicked)
        self.body_list_menu.add_command(label="Удалить", command=self._on_delete_body_clicked)
        self.body_list_menu.add_separator()
        self.body_list_menu.add_command(label="Экспорт в JSON", command=self._on_export_body_clicked)
        
        self.bodies_listbox.bind("<Double-Button-1>", lambda e: self._on_edit_body_clicked())
        self.bodies_listbox.bind("<Button-3>", self._show_body_context_menu)
        
        # Нижняя панель с кнопками
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        refresh_btn = ttk.Button(
            bottom_frame,
            text="Обновить список",
            command=self._refresh_bodies_list
        )
        refresh_btn.pack(side=tk.LEFT)
        
        exit_btn = ttk.Button(
            bottom_frame,
            text="Выход",
            command=self.quit
        )
        exit_btn.pack(side=tk.RIGHT)
    
    def _refresh_bodies_list(self):
        """Обновляет список доступных типов тел."""
        self.bodies_listbox.delete(0, tk.END)
        
        # Получаем список тел из BodyTypeManager
        if hasattr(self.body_manager, 'available_bodies'):
            for body_name in sorted(self.body_manager.available_bodies.keys()):
                self.bodies_listbox.insert(tk.END, body_name)
    
    def _on_create_body_clicked(self):
        """Обработчик кнопки создания нового типа тела."""
        # Сбрасываем форму для нового тела
        self.body_manager.new_body()
    
    def _on_load_body_clicked(self):
        """Обработчик кнопки загрузки существующего типа тела."""
        # Проверяем, существует ли виджет listbox
        if not hasattr(self, 'bodies_listbox') or self.bodies_listbox is None:
            return
            
        try:
            selection = self.bodies_listbox.curselection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите тип тела из списка.")
                return
            
            body_name = self.bodies_listbox.get(selection[0])
            self.body_manager.on_load_body_to_editor()
        except tk.TclError:
            # Виджет был уничтожен, игнорируем ошибку
            return
    
    def _on_edit_body_clicked(self):
        """Обработчик редактирования типа тела."""
        self._on_load_body_clicked()
    
    def _on_delete_body_clicked(self):
        """Обработчик удаления типа тела."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите тип тела из списка.")
            return
        
        body_name = self.bodies_listbox.get(selection[0])
        
        if messagebox.askyesno("Подтверждение", f"Удалить тип тела '{body_name}'?"):
            self.body_manager.on_delete_body_type()
            self._refresh_bodies_list()
    
    def _on_export_body_clicked(self):
        """Обработчик экспорта типа тела в JSON."""
        selection = self.bodies_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите тип тела из списка.")
            return
        
        body_name = self.bodies_listbox.get(selection[0])
        # Экспорт уже реализован через сохранение - просто информируем пользователя
        messagebox.showinfo("Информация", f"Тип тела '{body_name}' уже сохранен в JSON формате в папке data/json_files/")
    
    def _show_body_context_menu(self, event):
        """Показывает контекстное меню для списка тел."""
        self.bodies_listbox.selection_clear(0, tk.END)
        self.bodies_listbox.selection_set(self.bodies_listbox.nearest(event.y))
        self.body_list_menu.post(event.x_root, event.y_root)


def main():
    """Точка входа приложения."""
    print("Запуск Body Maker...")
    
    app = BodyMakerApp()
    app.mainloop()
    
    print("Body Maker завершен.")


if __name__ == "__main__":
    main()
