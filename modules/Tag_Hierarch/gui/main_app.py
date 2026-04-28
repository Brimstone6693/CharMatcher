# file: modules/Tag_Hierarch/gui/main_app.py
"""
Главное окно приложения Tag Hierarch - ListManagerApp.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Dict, List, Optional

from modules.Tag_Hierarch.core.models import ListManager, ItemList
from modules.Tag_Hierarch.core.config import STATUS_COLORS, DEP_COLORS
from modules.Tag_Hierarch.gui.dialogs import SelectElementDialog, SelectDepTypeDialog


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
        self.links_map: Dict[int, str] = {}
        self.deps_map: Dict[int, str] = {}
        self.rev_deps_map: Dict[int, str] = {}

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

        # --- Левая панель: Списки ---
        left_frame = tk.LabelFrame(main_paned, text="Списки", width=200)
        main_paned.add(left_frame, minsize=180)

        list_btn_frame = tk.Frame(left_frame)
        list_btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(list_btn_frame, text="Создать", command=self.add_list).pack(side="left", padx=(0, 2))
        tk.Button(list_btn_frame, text="Удалить", command=self.delete_list).pack(side="left", padx=(0, 2))
        tk.Button(list_btn_frame, text="Переим.", command=self.rename_list).pack(side="left")

        self.lists_lb = tk.Listbox(left_frame, exportselection=False)
        self.lists_lb.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Центральная панель: Дерево ---
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

        self.tree = ttk.Treeview(
            tree_container,
            columns=("name", "status"),
            show="tree headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
        )
        self.tree.pack(fill="both", expand=True)
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        self.tree.heading("#0", text="")
        self.tree.heading("name", text="Название")
        self.tree.heading("status", text="Уровень")
        self.tree.column("#0", width=30, stretch=False)
        self.tree.column("name", width=300)
        self.tree.column("status", width=60, anchor="center")

        for val, color in STATUS_COLORS.items():
            weight = "bold" if val != 0 else "normal"
            self.tree.tag_configure(f"st{val}", foreground=color, font=("Segoe UI", 9, weight))

        # --- Правая панель: Свойства ---
        right_frame = tk.LabelFrame(main_paned, text="Свойства элемента", width=420)
        main_paned.add(right_frame, minsize=400)

        # Основное
        basic_frame = tk.LabelFrame(right_frame, text="Основное")
        basic_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(basic_frame, text="Название:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.name_var = tk.StringVar()
        tk.Entry(basic_frame, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(basic_frame, text="Описание:").grid(row=1, column=0, sticky="nw", padx=5, pady=3)
        self.desc_text = tk.Text(basic_frame, height=3, wrap="word")
        self.desc_text.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        basic_frame.columnconfigure(1, weight=1)

        # Статус (-3..+3)
        status_frame = tk.LabelFrame(right_frame, text="Статус (-3 … +3)")
        status_frame.pack(fill="x", padx=5, pady=5)

        self.status_auto_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="0")

        auto_cb = tk.Checkbutton(
            status_frame, text="Авто (наследуется от зависимостей)",
            variable=self.status_auto_var,
            command=self._on_auto_changed,
        )
        auto_cb.pack(anchor="w", padx=5, pady=(5, 0))

        manual_frame = tk.Frame(status_frame)
        manual_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(manual_frame, text="Ручной:").pack(side="left")
        self.status_combo = ttk.Combobox(
            manual_frame,
            textvariable=self.status_var,
            values=[str(i) for i in range(-3, 4)],
            state="disabled",
            width=5,
        )
        self.status_combo.pack(side="left", padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", self._on_status_changed)

        self.status_preview = tk.Label(manual_frame, text="→ Авто: 0", font=("Segoe UI", 9, "italic"))
        self.status_preview.pack(side="left", padx=5)

        # Ссылки
        refs_frame = tk.LabelFrame(right_frame, text="Ссылки на элементы (взаимные)")
        refs_frame.pack(fill="both", expand=True, padx=5, pady=5)

        refs_btn_frame = tk.Frame(refs_frame)
        refs_btn_frame.pack(fill="x", padx=2, pady=2)
        tk.Button(refs_btn_frame, text="Добавить", command=self.add_reference).pack(side="left", padx=(0, 2))
        tk.Button(refs_btn_frame, text="Удалить", command=self.remove_reference).pack(side="left")

        refs_scroll = tk.Scrollbar(refs_frame)
        refs_scroll.pack(side="right", fill="y")
        self.refs_lb = tk.Listbox(refs_frame, yscrollcommand=refs_scroll.set)
        self.refs_lb.pack(fill="both", expand=True, padx=2, pady=2)
        refs_scroll.config(command=self.refs_lb.yview)

        # Зависимости (прямые)
        deps_frame = tk.LabelFrame(right_frame, text="Зависимости (элемент зависит от)")
        deps_frame.pack(fill="both", expand=True, padx=5, pady=5)

        deps_btn_frame = tk.Frame(deps_frame)
        deps_btn_frame.pack(fill="x", padx=2, pady=2)
        tk.Button(deps_btn_frame, text="Добавить", command=self.add_dependency).pack(side="left", padx=(0, 2))
        tk.Button(deps_btn_frame, text="Удалить", command=self.remove_dependency).pack(side="left")

        deps_scroll = tk.Scrollbar(deps_frame)
        deps_scroll.pack(side="right", fill="y")
        self.deps_lb = tk.Listbox(deps_frame, yscrollcommand=deps_scroll.set)
        self.deps_lb.pack(fill="both", expand=True, padx=2, pady=2)
        deps_scroll.config(command=self.deps_lb.yview)

        # Обратные зависимости
        rev_deps_frame = tk.LabelFrame(right_frame, text="Обратные зависимости (зависят от этого)")
        rev_deps_frame.pack(fill="both", expand=True, padx=5, pady=5)

        rev_deps_scroll = tk.Scrollbar(rev_deps_frame)
        rev_deps_scroll.pack(side="right", fill="y")
        self.rev_deps_lb = tk.Listbox(rev_deps_frame, yscrollcommand=rev_deps_scroll.set)
        self.rev_deps_lb.pack(fill="both", expand=True, padx=2, pady=2)
        rev_deps_scroll.config(command=self.rev_deps_lb.yview)

        # Сохранить
        self.save_btn = tk.Button(
            right_frame, text="💾 Сохранить изменения",
            command=self.save_element, bg="#e3f2fd",
        )
        self.save_btn.pack(fill="x", padx=5, pady=10)

    def _on_status_changed(self, event=None):
        """Обработчик изменения статуса в combobox (ручной режим)."""
        if not self.selected_element_id or not self.current_list_id:
            return
        try:
            val = int(self.status_var.get())
            # Немедленно обновляем статус в модели для предпросмотра
            elem = self.manager.lists[self.current_list_id].elements[self.selected_element_id]
            elem.custom_status = max(-3, min(3, val))
            self.manager._recalculate_states()
            self.refresh_tree()
            color = STATUS_COLORS.get(val, "#000")
            self.status_preview.config(text=f"(ручной: {val})", fg=color)
            # Визуально подсветим кнопку сохранения, чтобы показать, что есть несохранённые изменения
            self.save_btn.config(bg="#bbdefb", text="💾 Сохранить изменения*")
        except ValueError:
            self.status_preview.config(text="(ручной)", fg="#000")

    def _on_auto_changed(self):
        if not self.selected_element_id or not self.current_list_id:
            return
        # Подсветим кнопку сохранения, так как режим изменился
        self.save_btn.config(bg="#bbdefb", text="💾 Сохранить изменения*")
        if self.status_auto_var.get():
            self.status_combo.config(state="disabled")
            # Показать текущий рассчитанный статус
            info = self.manager.get_element_info(self.selected_element_id)
            if info:
                self.status_var.set(str(info['status']))
                self.status_preview.config(
                    text=f"→ Авто: {info['status']}",
                    fg=STATUS_COLORS.get(info["status"], "#000"),
                )
        else:
            self.status_combo.config(state="readonly")
            # При переключении в ручной режим инициализировать status_var текущим статусом
            info = self.manager.get_element_info(self.selected_element_id)
            if info:
                cs = info.get('custom_status')
                if cs is not None:
                    # Элемент уже имел кастомный статус - восстанавливаем его
                    self.status_var.set(str(cs))
                    self.status_preview.config(text=f"(ручной: {cs})", fg=STATUS_COLORS.get(cs, "#000"))
                else:
                    # Кастомного статуса не было - используем текущий авто-статус как начальное значение
                    self.status_var.set(str(info['status']))
                    # Сразу записываем это значение как custom_status, чтобы оно сохранилось при нажатии кнопки
                    elem = self.manager.lists[self.current_list_id].elements[self.selected_element_id]
                    elem.custom_status = info['status']
                    self.status_preview.config(text=f"(ручной: {info['status']})", fg=STATUS_COLORS.get(info['status'], "#000"))

    def bind_events(self):
        self.lists_lb.bind("<<ListboxSelect>>", self.on_list_select)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

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
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.current_list_id or self.current_list_id not in self.manager.lists:
            return
        lst = self.manager.lists[self.current_list_id]
        self._insert_tree_children(lst, None, "")
        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.see(selected_id)

    def _insert_tree_children(self, lst: ItemList, parent_id: Optional[str], tree_parent: str):
        element_ids = lst.root_elements if parent_id is None else lst.elements[parent_id].children_ids
        for eid in element_ids:
            if eid not in lst.elements:
                continue
            elem = lst.elements[eid]
            tag = f"st{elem.status}"
            item = self.tree.insert(
                tree_parent, "end", iid=eid,
                text="", values=(elem.name, elem.status), tags=(tag,),
            )
            self._insert_tree_children(lst, eid, item)

    def clear_details(self):
        self.name_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.status_auto_var.set(True)
        self.status_var.set("0")
        self.status_combo.config(state="disabled")
        self.status_preview.config(text="→ Авто: 0", fg="#616161")
        self.refs_lb.delete(0, tk.END)
        self.deps_lb.delete(0, tk.END)
        self.rev_deps_lb.delete(0, tk.END)
        self.links_map.clear()
        self.deps_map.clear()
        self.rev_deps_map.clear()

    def load_element_details(self):
        if not self.selected_element_id:
            return
        info = self.manager.get_element_info(self.selected_element_id)
        if not info:
            return

        self.name_var.set(info["name"])
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", info.get("description", ""))

        cs = info.get("custom_status")
        if cs is None:
            self.status_auto_var.set(True)
            self.status_var.set(str(info["status"]))
            self.status_combo.config(state="disabled")
            self.status_preview.config(
                text=f"→ Авто: {info['status']}",
                fg=STATUS_COLORS.get(info["status"], "#000"),
            )
        else:
            self.status_auto_var.set(False)
            self.status_var.set(str(cs))
            self.status_combo.config(state="readonly")
            # Обновление превью с фактическим значением статуса
            self.status_preview.config(text=f"(ручной: {cs})", fg=STATUS_COLORS.get(cs, "#000"))

        # Ссылки
        self.refs_lb.delete(0, tk.END)
        self.links_map.clear()
        for i, ref in enumerate(info.get("resolved_references", [])):
            display = f"{ref['name']} ({ref['list_name']})"
            if ref.get("note"):
                display += f" — {ref['note']}"
            self.refs_lb.insert(tk.END, display)
            self.links_map[i] = ref["element_id"]

        # Зависимости (прямые)
        self.deps_lb.delete(0, tk.END)
        self.deps_map.clear()
        for i, dep in enumerate(info.get("resolved_dependencies", [])):
            color = DEP_COLORS.get(dep["type"], "#000")
            display = f"[{dep['type']}] [{dep['status']}] {dep['name']}"
            self.deps_lb.insert(tk.END, display)
            self.deps_lb.itemconfig(tk.END, fg=color)
            self.deps_map[i] = dep["element_id"]

        # Обратные зависимости
        self.rev_deps_lb.delete(0, tk.END)
        self.rev_deps_map.clear()
        for i, dep in enumerate(info.get("resolved_depended_by", [])):
            color = DEP_COLORS.get(dep["type"], "#000")
            display = f"[{dep['type']}] [{dep['status']}] {dep['name']} ({dep['list_name']})"
            self.rev_deps_lb.insert(tk.END, display)
            self.rev_deps_lb.itemconfig(tk.END, fg=color)
            self.rev_deps_map[i] = dep["element_id"]

    def on_list_select(self, event=None):
        sel = self.lists_lb.curselection()
        if not sel:
            return
        self.current_list_id = list(self.manager.lists.keys())[sel[0]]
        self.selected_element_id = None
        self.clear_details()
        self.refresh_tree()

    def on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_element_id = sel[0]
        self.load_element_details()

    def add_list(self):
        name = simpledialog.askstring("Новый список", "Введите название списка:", parent=self)
        if name and name.strip():
            lst = self.manager.create_list(name.strip())
            self.current_list_id = lst.list_id
            self.refresh_lists()

    def delete_list(self):
        if not self.current_list_id:
            messagebox.showwarning("Внимание", "Выберите список для удаления")
            return
        lst = self.manager.lists[self.current_list_id]
        if not messagebox.askyesno("Подтверждение", f"Удалить список '{lst.name}'?\nВсе элементы будут удалены!"):
            return
        self.manager.delete_list(self.current_list_id)
        self.current_list_id = None
        self.selected_element_id = None
        self.clear_details()
        self.refresh_lists()
        self.refresh_tree()

    def rename_list(self):
        if not self.current_list_id:
            return
        old_name = self.manager.lists[self.current_list_id].name
        new_name = simpledialog.askstring("Переименование", "Новое название:", initialvalue=old_name, parent=self)
        if new_name and new_name.strip():
            self.manager.lists[self.current_list_id].name = new_name.strip()
            self.refresh_lists()

    def add_element(self):
        if not self.current_list_id:
            messagebox.showwarning("Внимание", "Сначала создайте или выберите список")
            return
        name = simpledialog.askstring("Новый элемент", "Название элемента:", parent=self)
        if name and name.strip():
            desc = simpledialog.askstring("Описание", "Описание (можно оставить пустым):", parent=self) or ""
            elem = self.manager.add_element(self.current_list_id, name.strip(), desc.strip())
            self.manager._recalculate_states()
            self.refresh_tree()
            if elem and self.tree.exists(elem.element_id):
                self.tree.selection_set(elem.element_id)
                self.tree.see(elem.element_id)

    def add_child(self):
        if not self.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите родительский элемент в дереве")
            return
        name = simpledialog.askstring("Новый подэлемент", "Название подэлемента:", parent=self)
        if name and name.strip():
            desc = simpledialog.askstring("Описание", "Описание (можно оставить пустым):", parent=self) or ""
            elem = self.manager.add_element(
                self.current_list_id, name.strip(), desc.strip(),
                parent_id=self.selected_element_id,
            )
            self.manager._recalculate_states()
            self.refresh_tree()
            self.tree.item(self.selected_element_id, open=True)
            if elem and self.tree.exists(elem.element_id):
                self.tree.selection_set(elem.element_id)
                self.tree.see(elem.element_id)

    def delete_element(self):
        if not self.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент для удаления")
            return
        elem = self.manager.lists[self.current_list_id].elements[self.selected_element_id]
        cascade = messagebox.askyesno(
            "Удаление",
            f"Удалить '{elem.name}'?\n\n"
            "Да — удалить со всеми подэлементами\n"
            "Нет — подэлементы поднимутся на уровень выше",
        )
        self.manager.remove_element(self.current_list_id, self.selected_element_id, cascade=cascade)
        self.manager._recalculate_states()
        self.selected_element_id = None
        self.clear_details()
        self.refresh_tree()

    def save_element(self):
        if not self.selected_element_id or not self.current_list_id:
            return
        elem = self.manager.lists[self.current_list_id].elements[self.selected_element_id]

        elem.name = self.name_var.get().strip()
        elem.description = self.desc_text.get("1.0", tk.END).strip()

        # Обработка статуса: если "Авто" включено - custom_status = None, иначе сохраняем выбранное значение
        if self.status_auto_var.get():
            elem.custom_status = None
        else:
            # В ручном режиме сохраняем значение из combobox как custom_status
            try:
                val = int(self.status_var.get())
                elem.custom_status = max(-3, min(3, val))
            except ValueError:
                elem.custom_status = None

        self.manager._recalculate_states()
        self.refresh_tree()
        self.load_element_details()
        # Сбросим индикатор несохранённых изменений
        self.save_btn.config(bg="#e3f2fd", text="💾 Сохранить изменения")
        messagebox.showinfo("Готово", "Изменения сохранены")

    def create_link(self):
        if not self.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент-источник")
            return
        dialog = SelectElementDialog(
            self, self.manager, exclude_id=self.selected_element_id,
            title="Создать взаимную ссылку с...",
        )
        if dialog.result:
            try:
                self.manager.create_reference(self.selected_element_id, dialog.result, "")
                self.load_element_details()
                messagebox.showinfo("Готово", "Взаимная ссылка создана")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def add_reference(self):
        self.create_link()

    def remove_reference(self):
        sel = self.refs_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx not in self.links_map:
            return
        target_id = self.links_map[idx]
        self.manager.remove_reference(self.selected_element_id, target_id)
        self.load_element_details()

    def add_dependency(self):
        if not self.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент")
            return
        dialog = SelectElementDialog(
            self, self.manager, exclude_id=self.selected_element_id,
            title="Добавить зависимость от...",
        )
        if not dialog.result:
            return
        type_dialog = SelectDepTypeDialog(self)
        if not type_dialog.result:
            return

        dep_type = type_dialog.result
        self.manager.add_dependency(self.selected_element_id, dialog.result, dep_type)

        reverse = messagebox.askyesno("Обратная зависимость", "Создать обратную зависимость того же типа?")
        if reverse:
            self.manager.add_dependency(dialog.result, self.selected_element_id, dep_type)

        self.manager._recalculate_states()
        self.refresh_tree()
        self.load_element_details()

    def remove_dependency(self):
        sel = self.deps_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx not in self.deps_map:
            return
        dep_id = self.deps_map[idx]
        self.manager.remove_dependency(self.selected_element_id, dep_id)
        self.manager.remove_dependency(dep_id, self.selected_element_id)
        self.manager._recalculate_states()
        self.refresh_tree()
        self.load_element_details()

    def save_file(self):
        import os
        # Используем относительный путь к папке data внутри модуля Tag_Hierarch
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir=data_dir,
            initialfile="lists_data.json"
        )
        if path:
            self.manager.export_to_json(path)
            messagebox.showinfo("Сохранение", f"Данные сохранены в:\n{path}")

    def load_file(self):
        import os
        # Используем относительный путь к папке data внутри модуля Tag_Hierarch
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            initialdir=data_dir
        )
        if path:
            try:
                self.manager.import_from_json(path)
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", str(e))
                return
            self.current_list_id = None
            self.selected_element_id = None
            self.clear_details()
            self.refresh_lists()
            self.refresh_tree()
            messagebox.showinfo("Загрузка", "Данные загружены")
