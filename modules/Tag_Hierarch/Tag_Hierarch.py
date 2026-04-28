#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер связанных списков — расширенная версия:
  • 7 уровней статуса (-3 … +3)
  • Типы зависимостей: EQ, PM1, LE, GE с цветовой маркировкой
  • Обратные зависимости (depended_by)
  • Ссылки всегда двусторонние
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


DEP_TYPES = {
    "EQ": "Строго равно",
    "PM1": "± 1",
    "LE": "Не больше (≤)",
    "GE": "Не меньше (≥)",
}

DEP_COLORS = {
    "EQ": "#9c27b0",
    "PM1": "#2196f3",
    "LE": "#f44336",
    "GE": "#4caf50",
}

STATUS_COLORS = {
    -3: "#8b0000",
    -2: "#d32f2f",
    -1: "#f57c00",
    0: "#616161",
    1: "#7cb342",
    2: "#388e3c",
    3: "#1b5e20",
}


# ==================== МОДЕЛЬ ДАННЫХ ====================

@dataclass
class Element:
    name: str
    description: str = ""
    element_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    references: Dict[str, Dict[str, str]] = field(default_factory=dict)
    referenced_by: List[str] = field(default_factory=list)
    depends_on: Dict[str, str] = field(default_factory=dict)
    depended_by: Dict[str, str] = field(default_factory=dict)
    status: int = 0
    custom_status: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id, "name": self.name,
            "description": self.description, "parent_id": self.parent_id,
            "children_ids": self.children_ids, "references": self.references,
            "referenced_by": self.referenced_by,
            "depends_on": self.depends_on, "depended_by": self.depended_by,
            "status": self.status, "custom_status": self.custom_status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Element":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            element_id=data["element_id"],
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            references=data.get("references", {}),
            referenced_by=data.get("referenced_by", []),
            depends_on=data.get("depends_on", {}),
            depended_by=data.get("depended_by", {}),
            status=data.get("status", 0),
            custom_status=data.get("custom_status"),
            metadata=data.get("metadata", {}),
        )


class ItemList:
    def __init__(self, list_id: str, name: str, description: str = ""):
        self.list_id = list_id
        self.name = name
        self.description = description
        self.elements: Dict[str, Element] = {}
        self.root_elements: List[str] = []

    def add_element(self, element: Element, parent_id: Optional[str] = None) -> Element:
        if parent_id and parent_id in self.elements:
            element.parent_id = parent_id
            self.elements[parent_id].children_ids.append(element.element_id)
        else:
            self.root_elements.append(element.element_id)
        self.elements[element.element_id] = element
        return element

    def remove_element(self, element_id: str, cascade: bool = False) -> List[str]:
        if element_id not in self.elements:
            return []
        removed = [element_id]
        element = self.elements[element_id]
        if element.parent_id and element.parent_id in self.elements:
            self.elements[element.parent_id].children_ids.remove(element_id)
        elif element_id in self.root_elements:
            self.root_elements.remove(element_id)
        if cascade:
            for child_id in element.children_ids[:]:
                removed.extend(self.remove_element(child_id, cascade=True))
        else:
            for child_id in element.children_ids:
                self.elements[child_id].parent_id = element.parent_id
                if element.parent_id:
                    self.elements[element.parent_id].children_ids.append(child_id)
                else:
                    self.root_elements.append(child_id)
        del self.elements[element_id]
        return removed

    def get_tree(self, element_id: Optional[str] = None, depth: int = 0) -> List[tuple]:
        result = []
        ids_to_process = [element_id] if element_id else self.root_elements
        for eid in ids_to_process:
            if eid in self.elements:
                elem = self.elements[eid]
                result.append((elem, depth))
                for child_id in elem.children_ids:
                    result.extend(self._get_subtree(child_id, depth + 1))
        return result

    def _get_subtree(self, element_id: str, depth: int) -> List[tuple]:
        result = []
        if element_id in self.elements:
            elem = self.elements[element_id]
            result.append((elem, depth))
            for child_id in elem.children_ids:
                result.extend(self._get_subtree(child_id, depth + 1))
        return result

    def to_dict(self) -> dict:
        return {
            "list_id": self.list_id, "name": self.name,
            "description": self.description,
            "elements": {eid: elem.to_dict() for eid, elem in self.elements.items()},
            "root_elements": self.root_elements,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ItemList":
        item_list = cls(data["list_id"], data["name"], data.get("description", ""))
        item_list.root_elements = data.get("root_elements", [])
        for eid, elem_data in data.get("elements", {}).items():
            item_list.elements[eid] = Element.from_dict(elem_data)
        return item_list


class ListManager:
    def __init__(self):
        self.lists: Dict[str, ItemList] = {}
        self._global_elements: Dict[str, str] = {}

    def create_list(self, name: str, description: str = "", list_id: Optional[str] = None) -> ItemList:
        lid = list_id or str(uuid.uuid4())
        item_list = ItemList(lid, name, description)
        self.lists[lid] = item_list
        return item_list

    def delete_list(self, list_id: str) -> bool:
        if list_id not in self.lists:
            return False
        for eid in list(self.lists[list_id].elements.keys()):
            self._remove_element_references(eid)
            if eid in self._global_elements:
                del self._global_elements[eid]
        del self.lists[list_id]
        return True

    def add_element(self, list_id: str, name: str, description: str = "",
                    parent_id: Optional[str] = None, element_id: Optional[str] = None) -> Optional[Element]:
        if list_id not in self.lists:
            return None
        element = Element(name=name, description=description, element_id=element_id or str(uuid.uuid4()))
        self.lists[list_id].add_element(element, parent_id)
        self._global_elements[element.element_id] = list_id
        return element

    def remove_element(self, list_id: str, element_id: str, cascade: bool = False) -> List[str]:
        if list_id not in self.lists:
            return []
        lst = self.lists[list_id]
        to_remove = [element_id]
        if cascade:
            self._collect_children(lst, element_id, to_remove)
        for eid in to_remove:
            self._remove_element_references(eid)
        removed = lst.remove_element(element_id, cascade)
        for eid in removed:
            if eid in self._global_elements:
                del self._global_elements[eid]
        return removed

    def _collect_children(self, lst: ItemList, element_id: str, result: List[str]):
        if element_id not in lst.elements:
            return
        for child_id in lst.elements[element_id].children_ids:
            result.append(child_id)
            self._collect_children(lst, child_id, result)

    def create_reference(self, from_element_id: str, to_element_id: str, note: str = ""):
        from_list_id = self._global_elements.get(from_element_id)
        to_list_id = self._global_elements.get(to_element_id)
        if not from_list_id or not to_list_id:
            raise ValueError("Один или оба элемента не найдены")
        from_elem = self.lists[from_list_id].elements[from_element_id]
        from_elem.references[to_element_id] = {"list_id": to_list_id, "note": note}
        to_elem = self.lists[to_list_id].elements[to_element_id]
        if from_element_id not in to_elem.referenced_by:
            to_elem.referenced_by.append(from_element_id)
        to_elem.references[from_element_id] = {"list_id": from_list_id, "note": note}
        if to_element_id not in from_elem.referenced_by:
            from_elem.referenced_by.append(to_element_id)

    def remove_reference(self, from_element_id: str, to_element_id: str):
        from_list_id = self._global_elements.get(from_element_id)
        to_list_id = self._global_elements.get(to_element_id)
        if from_list_id and from_element_id in self.lists[from_list_id].elements:
            elem = self.lists[from_list_id].elements[from_element_id]
            if to_element_id in elem.references:
                del elem.references[to_element_id]
        if to_list_id and to_element_id in self.lists[to_list_id].elements:
            elem = self.lists[to_list_id].elements[to_element_id]
            if from_element_id in elem.referenced_by:
                elem.referenced_by.remove(from_element_id)
        if to_list_id and to_element_id in self.lists[to_list_id].elements:
            elem = self.lists[to_list_id].elements[to_element_id]
            if from_element_id in elem.references:
                del elem.references[from_element_id]
        if from_list_id and from_element_id in self.lists[from_list_id].elements:
            elem = self.lists[from_list_id].elements[from_element_id]
            if to_element_id in elem.referenced_by:
                elem.referenced_by.remove(to_element_id)

    def add_dependency(self, element_id: str, depends_on_id: str, dep_type: str = "LE"):
        list_id = self._global_elements.get(element_id)
        dep_list_id = self._global_elements.get(depends_on_id)
        if list_id and element_id in self.lists[list_id].elements:
            self.lists[list_id].elements[element_id].depends_on[depends_on_id] = dep_type
        if dep_list_id and depends_on_id in self.lists[dep_list_id].elements:
            self.lists[dep_list_id].elements[depends_on_id].depended_by[element_id] = dep_type

    def remove_dependency(self, element_id: str, depends_on_id: str):
        list_id = self._global_elements.get(element_id)
        dep_list_id = self._global_elements.get(depends_on_id)
        if list_id and element_id in self.lists[list_id].elements:
            elem = self.lists[list_id].elements[element_id]
            if depends_on_id in elem.depends_on:
                del elem.depends_on[depends_on_id]
        if dep_list_id and depends_on_id in self.lists[dep_list_id].elements:
            dep_elem = self.lists[dep_list_id].elements[depends_on_id]
            if element_id in dep_elem.depended_by:
                del dep_elem.depended_by[element_id]

    def set_element_custom_status(self, element_id: str, status: Optional[int] = None):
        list_id = self._global_elements.get(element_id)
        if not list_id:
            return
        self.lists[list_id].elements[element_id].custom_status = status
        self._recalculate_states()

    def _recalculate_states(self):
        visited, temp_mark, order = set(), set(), []

        def visit(eid):
            if eid in temp_mark:
                return
            if eid in visited:
                return
            temp_mark.add(eid)
            lid = self._global_elements.get(eid)
            if lid and eid in self.lists[lid].elements:
                for dep_id in self.lists[lid].elements[eid].depends_on.keys():
                    visit(dep_id)
            temp_mark.remove(eid)
            visited.add(eid)
            order.append(eid)

        all_elements = [eid for lst in self.lists.values() for eid in lst.elements.keys()]
        for eid in all_elements:
            if eid not in visited:
                visit(eid)

        for eid in order:
            lid = self._global_elements.get(eid)
            if not lid:
                continue
            elem = self.lists[lid].elements[eid]
            if elem.custom_status is not None:
                elem.status = max(-3, min(3, elem.custom_status))
                continue

            low, high = -3, 3
            if elem.parent_id:
                parent_lid = self._global_elements.get(elem.parent_id)
                if parent_lid and elem.parent_id in self.lists[parent_lid].elements:
                    high = min(high, self.lists[parent_lid].elements[elem.parent_id].status)

            for dep_id, dep_type in elem.depends_on.items():
                dep_lid = self._global_elements.get(dep_id)
                if not dep_lid or dep_id not in self.lists[dep_lid].elements:
                    continue
                s = self.lists[dep_lid].elements[dep_id].status
                if dep_type == "EQ":
                    low = max(low, s)
                    high = min(high, s)
                elif dep_type == "PM1":
                    low = max(low, s - 1)
                    high = min(high, s + 1)
                elif dep_type == "LE":
                    high = min(high, s)
                elif dep_type == "GE":
                    low = max(low, s)

            if low > high:
                elem.status = -3
            else:
                if low <= 0 <= high:
                    elem.status = 0
                elif high < 0:
                    elem.status = high
                else:
                    elem.status = low

    def get_element_info(self, element_id: str) -> Optional[dict]:
        lid = self._global_elements.get(element_id)
        if not lid or element_id not in self.lists[lid].elements:
            return None
        elem = self.lists[lid].elements[element_id]
        info = elem.to_dict()
        info["list_id"] = lid
        info["list_name"] = self.lists[lid].name

        info["resolved_references"] = []
        for ref_id, ref_data in elem.references.items():
            ref_lid = self._global_elements.get(ref_id)
            if ref_lid and ref_id in self.lists[ref_lid].elements:
                ref_elem = self.lists[ref_lid].elements[ref_id]
                info["resolved_references"].append({
                    "element_id": ref_id, "name": ref_elem.name,
                    "list_name": self.lists[ref_lid].name,
                    "note": ref_data.get("note", ""),
                })

        info["resolved_dependencies"] = []
        for dep_id, dep_type in elem.depends_on.items():
            dep_lid = self._global_elements.get(dep_id)
            if dep_lid and dep_id in self.lists[dep_lid].elements:
                dep_elem = self.lists[dep_lid].elements[dep_id]
                info["resolved_dependencies"].append({
                    "element_id": dep_id, "name": dep_elem.name,
                    "status": dep_elem.status, "type": dep_type,
                })

        info["resolved_depended_by"] = []
        for dep_by_id, dep_type in elem.depended_by.items():
            dep_by_lid = self._global_elements.get(dep_by_id)
            if dep_by_lid and dep_by_id in self.lists[dep_by_lid].elements:
                dep_by_elem = self.lists[dep_by_lid].elements[dep_by_id]
                info["resolved_depended_by"].append({
                    "element_id": dep_by_id, "name": dep_by_elem.name,
                    "status": dep_by_elem.status, "type": dep_type,
                    "list_name": self.lists[dep_by_lid].name,
                })

        info["children"] = []
        for child_id in elem.children_ids:
            if child_id in self.lists[lid].elements:
                child = self.lists[lid].elements[child_id]
                info["children"].append({
                    "element_id": child_id, "name": child.name,
                    "status": child.status,
                })
        return info

    def export_to_json(self, filepath: str):
        data = {
            "lists": {lid: lst.to_dict() for lid, lst in self.lists.items()},
            "global_elements": self._global_elements,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_json(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.lists = {}
        self._global_elements = data.get("global_elements", {})
        for lid, lst_data in data.get("lists", {}).items():
            self.lists[lid] = ItemList.from_dict(lst_data)

    def _remove_element_references(self, element_id: str):
        lid = self._global_elements.get(element_id)
        if not lid or element_id not in self.lists[lid].elements:
            return
        elem = self.lists[lid].elements[element_id]
        for ref_id in list(elem.references.keys()):
            self.remove_reference(element_id, ref_id)
        for ref_by_id in elem.referenced_by[:]:
            self.remove_reference(ref_by_id, element_id)
        for dep_id in list(elem.depends_on.keys()):
            self.remove_dependency(element_id, dep_id)
        for dep_by_id in list(elem.depended_by.keys()):
            self.remove_dependency(dep_by_id, element_id)

    def get_all_elements_flat(self) -> List[dict]:
        result = []
        for lst in self.lists.values():
            for elem in lst.elements.values():
                result.append({
                    "element_id": elem.element_id, "name": elem.name,
                    "list_id": lst.list_id, "list_name": lst.name,
                })
        return result


# ==================== ДИАЛОГИ ====================

class SelectElementDialog(tk.Toplevel):
    def __init__(self, parent, manager: ListManager, exclude_id=None, title="Выбор элемента"):
        super().__init__(parent)
        self.manager = manager
        self.exclude_id = exclude_id
        self.result = None
        self.title(title)
        self.geometry("500x400")
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        tk.Label(self, text="Фильтр:").pack(padx=10, pady=(10, 0), anchor="w")
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self.on_filter_change)
        tk.Entry(self, textvariable=self.filter_var).pack(padx=10, pady=(0, 5), fill="x")

        frame = tk.Frame(self)
        frame.pack(padx=10, pady=5, fill="both", expand=True)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.items = []
        self.refresh_list()

        btn_frame = tk.Frame(self)
        btn_frame.pack(padx=10, pady=10, fill="x")
        tk.Button(btn_frame, text="Выбрать", command=self.on_select).pack(side="left", padx=(0, 5))
        tk.Button(btn_frame, text="Отмена", command=self.on_cancel).pack(side="left")

        self.listbox.bind("<Double-Button-1>", lambda e: self.on_select())
        self.center_on_parent()
        self.grab_set()
        self.wait_window(self)

    def center_on_parent(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        self.items = []
        filter_text = self.filter_var.get().lower()
        for item in self.manager.get_all_elements_flat():
            if item["element_id"] == self.exclude_id:
                continue
            display = f"[{item['list_name']}] {item['name']}"
            if filter_text and filter_text not in display.lower():
                continue
            self.items.append(item)
            self.listbox.insert(tk.END, display)

    def on_filter_change(self, *args):
        self.refresh_list()

    def on_select(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите элемент", parent=self)
            return
        self.result = self.items[sel[0]]["element_id"]
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class SelectDepTypeDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Тип зависимости")
        self.geometry("320x220")
        self.transient(parent)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        tk.Label(self, text="Выберите тип зависимости:", font=("Segoe UI", 10, "bold")).pack(pady=10)

        for code, label in DEP_TYPES.items():
            color = DEP_COLORS[code]
            btn = tk.Button(
                self, text=f"{code}: {label}",
                fg=color, font=("Segoe UI", 9, "bold"),
                command=lambda c=code: self.select(c),
            )
            btn.pack(fill="x", padx=20, pady=3)

        tk.Button(self, text="Отмена", command=self.on_cancel).pack(pady=10)
        self.center_on_parent()
        self.grab_set()
        self.wait_window(self)

    def center_on_parent(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def select(self, code):
        self.result = code
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ==================== ГЛАВНОЕ ОКНО ====================

class ListManagerApp(tk.Tk):
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

        # Статус (-3..+3) — ИСПРАВЛЕННЫЙ БЛОК
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
        tk.Button(
            right_frame, text="💾 Сохранить изменения",
            command=self.save_element, bg="#e3f2fd",
        ).pack(fill="x", padx=5, pady=10)

    def _on_auto_changed(self):
        if self.status_auto_var.get():
            self.status_combo.config(state="disabled")
            # Показать текущий рассчитанный статус
            if self.selected_element_id:
                info = self.manager.get_element_info(self.selected_element_id)
                if info:
                    self.status_preview.config(
                        text=f"→ Авто: {info['status']}",
                        fg=STATUS_COLORS.get(info["status"], "#000"),
                    )
        else:
            self.status_combo.config(state="readonly")
            # При переключении в ручной режим показать текущее значение из status_var с правильным цветом
            try:
                val = int(self.status_var.get())
                color = STATUS_COLORS.get(val, "#000")
            except ValueError:
                color = "#000"
            self.status_preview.config(text="(ручной)", fg=color)

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
            self.status_preview.config(text="(ручной)", fg=STATUS_COLORS.get(cs, "#000"))

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

        if self.status_auto_var.get():
            elem.custom_status = None
        else:
            try:
                val = int(self.status_var.get())
                elem.custom_status = max(-3, min(3, val))
            except ValueError:
                elem.custom_status = 0

        self.manager._recalculate_states()
        self.refresh_tree()
        self.load_element_details()
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
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir="data",
            initialfile="lists_data.json"
        )
        if path:
            self.manager.export_to_json(path)
            messagebox.showinfo("Сохранение", f"Данные сохранены в:\n{path}")

    def load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            initialdir="data"
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


if __name__ == "__main__":
    app = ListManagerApp()
    app.mainloop()