# file: modules/Tag_Hierarch/gui/main_app.py
"""
Главное окно приложения Tag Hierarch - ListManagerApp.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from modules.Tag_Hierarch.core.models import ListManager
from modules.Tag_Hierarch.core.config import STATUS_COLORS
from modules.Tag_Hierarch.gui.dialogs import SelectElementDialog, SelectDepTypeDialog
from modules.Tag_Hierarch.gui.tree_view import ElementTreeView
from modules.Tag_Hierarch.gui.panels import ScrollablePropertiesPanel, ReferencesPanel
from modules.Tag_Hierarch.gui.actions import ActionHandler
from modules.Tag_Hierarch.gui.handlers import (
    ElementStateHandler, SelectionHandler, DetailsLoader
)


class ListManagerApp(tk.Tk):
    """Главное окно приложения управления списками."""
    
    def __init__(self):
        super().__init__()
        self.title("Менеджер связанных списков — 7-уровневая система")
        self.geometry("1400x850")
        self.minsize(1100, 650)

        self.manager = ListManager()
        self.current_list_id: Optional[str] = None
        self.selected_element_id: Optional[str] = None
        self.element_edit_state: Optional[str] = None
        
        # Флаги для предотвращения рекурсивных вызовов событий
        self._updating_fields = False
        self._updating_status = False
        self._updating_selection = False

        # Инициализация обработчиков
        self.action_handler = ActionHandler(self)
        self.state_handler = ElementStateHandler(self)
        self.selection_handler = SelectionHandler(self)
        self.details_loader = DetailsLoader(self)

        self.create_menu()
        self.create_ui()
        self.bind_events()
        self.load_demo_data()

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Загрузить", command=self.load_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menubar)
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-o>", lambda e: self.load_file())

    def create_ui(self):
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Левая панель: Списки
        left_frame = tk.LabelFrame(main_paned, text="Списки", width=200)
        main_paned.add(left_frame, minsize=180)

        list_btn_frame = tk.Frame(left_frame)
        list_btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(list_btn_frame, text="Создать", command=self.add_list).pack(side="left", padx=(0, 2))
        tk.Button(list_btn_frame, text="Удалить", command=self.delete_list).pack(side="left", padx=(0, 2))
        tk.Button(list_btn_frame, text="Переим.", command=self.rename_list).pack(side="left")

        self.lists_lb = tk.Listbox(left_frame, exportselection=False)
        self.lists_lb.pack(fill="both", expand=True, padx=5, pady=5)

        # Центральная панель: Дерево
        center_frame = tk.LabelFrame(main_paned, text="Элементы")
        main_paned.add(center_frame, minsize=420)

        tree_btn_frame = tk.Frame(center_frame)
        tree_btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(tree_btn_frame, text="Добавить", command=self.add_element).pack(side="left", padx=(0, 2))
        tk.Button(tree_btn_frame, text="Подэлемент", command=self.add_child).pack(side="left", padx=(0, 2))
        tk.Button(tree_btn_frame, text="Удалить", command=self.delete_element).pack(side="left", padx=(0, 2))
        tk.Button(tree_btn_frame, text="Связать", command=self.create_link).pack(side="left")

        tree_container = tk.Frame(center_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        tree_scroll_y = tk.Scrollbar(tree_container, orient="vertical")
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x = tk.Scrollbar(tree_container, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ElementTreeView(
            tree_container,
            columns=("name", "status"),
            show="tree headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
        )
        self.tree.pack(fill="both", expand=True)
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Правая панель: Свойства
        self.properties_panel = ScrollablePropertiesPanel(main_paned, width=380)
        main_paned.add(self.properties_panel, minsize=400)
        right_frame = self.properties_panel.content_frame

        # Основное
        basic_frame = tk.LabelFrame(right_frame, text="Основное")
        basic_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(basic_frame, text="Название:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(basic_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        self.name_var.trace_add("write", self._on_field_changed)

        tk.Label(basic_frame, text="Описание:").grid(row=1, column=0, sticky="nw", padx=5, pady=3)
        self.desc_text = tk.Text(basic_frame, height=3, wrap="word")
        self.desc_text.grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        self.desc_text.bind("<KeyRelease>", self._on_field_changed)
        basic_frame.columnconfigure(1, weight=1)

        # Статус
        status_frame = tk.LabelFrame(right_frame, text="Статус (-3 … +3)")
        status_frame.pack(fill="x", padx=5, pady=5)

        self.status_var = tk.StringVar(value="0")
        self.manual_override_var = tk.BooleanVar(value=False)

        val_frame = tk.Frame(status_frame)
        val_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(val_frame, text="Значение:").pack(side="left")
        self.status_combo = ttk.Combobox(
            val_frame, textvariable=self.status_var,
            values=[str(i) for i in range(-3, 4)],
            state="readonly", width=5,
        )
        self.status_combo.pack(side="left", padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", self._on_status_changed)

        self.status_preview = tk.Label(val_frame, text="→ Авто: 0", font=("Segoe UI", 9, "italic"))
        self.status_preview.pack(side="left", padx=10)

        self.manual_override_cb = tk.Checkbutton(
            status_frame, text="🔓 Ручная настройка (игнорировать зависимости)",
            variable=self.manual_override_var, command=self._on_manual_override_changed, anchor="w",
        )
        self.manual_override_cb.pack(fill="x", padx=5, pady=2)

        self.save_btn = tk.Button(
            status_frame, text="💾 Сохранить изменения",
            command=self.save_element, bg="#e3f2fd",
        )
        self.save_btn.pack(fill="x", padx=5, pady=10)

        # Ссылки
        self.refs_panel = ReferencesPanel(right_frame, title="Ссылки на элементы (взаимные)")
        self.refs_panel.pack(fill="both", expand=True, padx=5, pady=5)
        self.refs_panel.add_command = self.add_reference
        self.refs_panel.remove_command = self.remove_reference

        # Зависимости
        self.deps_panel = ReferencesPanel(right_frame, title="Зависимости (элемент зависит от)")
        self.deps_panel.pack(fill="both", expand=True, padx=5, pady=5)
        self.deps_panel.add_command = self.add_dependency
        self.deps_panel.remove_command = self.remove_dependency

        # Обратные зависимости
        self.rev_deps_panel = ReferencesPanel(right_frame, title="Обратные зависимости (зависят от этого)")
        self.rev_deps_panel.pack(fill="both", expand=True, padx=5, pady=5)

    def bind_events(self):
        self.lists_lb.bind("<<ListboxSelect>>", self._on_list_select)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # === Делегирование обработчикам ===
    
    def _on_list_select(self, event=None):
        self.selection_handler.on_list_select(event)
    
    def _on_tree_select(self, event=None):
        self.selection_handler.on_tree_select(event)
    
    def _on_status_changed(self, event=None):
        self.state_handler.on_status_changed(event)
    
    def _on_manual_override_changed(self):
        self.state_handler.on_manual_override_changed()
    
    def _on_field_changed(self, *args):
        self.state_handler.on_field_changed(*args)
    
    def update_edit_indicator(self):
        self.state_handler.update_edit_indicator()
    
    def load_element_details(self):
        self.details_loader.load_element_details()
    
    def clear_details(self):
        self.details_loader.clear_details()

    # === Делегирование действий ===
    
    def add_list(self):
        self.action_handler.add_list()
    
    def delete_list(self):
        self.action_handler.delete_list()
    
    def rename_list(self):
        self.action_handler.rename_list()
    
    def add_element(self):
        self.action_handler.add_element()
    
    def add_child(self):
        self.action_handler.add_child()
    
    def delete_element(self):
        self.action_handler.delete_element()
    
    def save_element(self, silent=False):
        self.action_handler.save_element(silent)
    
    def create_link(self):
        self.action_handler.create_link()
    
    def add_reference(self):
        self.action_handler.create_link()
    
    def remove_reference(self):
        target_id = self.refs_panel.get_selected_id()
        if not target_id or not self.selected_element_id:
            return
        self.manager.remove_reference(self.selected_element_id, target_id)
        # Обновляем детали без триггеринга событий
        self._updating_fields = True
        try:
            self.load_element_details()
        finally:
            self._updating_fields = False
    
    def add_dependency(self):
        self.action_handler.add_dependency()
    
    def remove_dependency(self):
        dep_id = self.deps_panel.get_selected_id()
        if not dep_id or not self.selected_element_id:
            return
        self.manager.remove_dependency(self.selected_element_id, dep_id)
        self.manager.remove_dependency(dep_id, self.selected_element_id)
        self.manager._recalculate_states()
        self.refresh_tree()
        # Обновляем детали без триггеринга событий
        self._updating_fields = True
        try:
            self.load_element_details()
            self.update_edit_indicator()
        finally:
            self._updating_fields = False
    
    def save_file(self):
        self.action_handler.save_file()
    
    def load_file(self):
        self.action_handler.load_file()

    # === Вспомогательные методы ===
    
    def refresh_lists(self):
        self.lists_lb.delete(0, tk.END)
        for idx, (lid, lst) in enumerate(self.manager.lists.items()):
            self.lists_lb.insert(tk.END, lst.name)
            if lid == self.current_list_id:
                self.lists_lb.selection_set(idx)
                self.lists_lb.see(idx)
        if self.current_list_id:
            self.refresh_tree()

    def refresh_tree(self):
        selected = self.tree.selection()
        selected_id = selected[0] if selected else None
        if not self.current_list_id or self.current_list_id not in self.manager.lists:
            return
        lst = self.manager.lists[self.current_list_id]
        self.tree.refresh_tree(lst, selected_id)

    def load_demo_data(self):
        l1 = self.manager.create_list("Список 1")
        l2 = self.manager.create_list("Список 2")
        l3 = self.manager.create_list("Список 3")

        e1 = self.manager.add_element(l1.list_id, "Элемент 1", "Содержится в списке 2")
        e2 = self.manager.add_element(l1.list_id, "Элемент 2", "Обычный элемент")
        e3 = self.manager.add_element(l1.list_id, "Элемент 3", "Содержится в списке 3")
        e4 = self.manager.add_element(l1.list_id, "Элемент 4", "Обычный элемент")

        e5 = self.manager.add_element(l2.list_id, "Элемент 5", "Обычный элемент")
        e6 = self.manager.add_element(l2.list_id, "Элемент 1 (L2)", "Указание на список 1", parent_id=e5.element_id)
        e7 = self.manager.add_element(l2.list_id, "Элемент 6", "Содержится в списке 3")
        e8 = self.manager.add_element(l2.list_id, "Элемент 7", "Обычный элемент")

        e9 = self.manager.add_element(l3.list_id, "Элемент 8", "Обычный элемент")
        e10 = self.manager.add_element(l3.list_id, "Элемент 6 (L3)", "Указание на список 2")
        e11 = self.manager.add_element(l3.list_id, "Элемент 9", "Обычный элемент")
        e12 = self.manager.add_element(l3.list_id, "Элемент 3 (L3)", "Указание на список 1")

        self.manager.create_reference(e1.element_id, e6.element_id, "Элемент 1 ↔ список 2")
        self.manager.create_reference(e3.element_id, e12.element_id, "Элемент 3 ↔ список 3")
        self.manager.create_reference(e7.element_id, e10.element_id, "Элемент 6 ↔ список 3")

        self.manager.add_dependency(e2.element_id, e1.element_id, "LE")
        self.manager.add_dependency(e8.element_id, e7.element_id, "EQ")

        self.manager._recalculate_states()
        self.refresh_lists()


if __name__ == "__main__":
    app = ListManagerApp()
    app.mainloop()
