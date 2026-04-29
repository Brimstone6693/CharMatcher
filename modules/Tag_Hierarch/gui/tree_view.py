# file: modules/Tag_Hierarch/gui/tree_view.py
"""
Компоненты дерева элементов для Tag Hierarch.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from modules.Tag_Hierarch.core.models import ItemList
from modules.Tag_Hierarch.core.config import STATUS_COLORS


class ElementTreeView(ttk.Treeview):
    """Дерево элементов списка с цветовой индикацией статусов."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._configure_columns()
        self._configure_tags()
    
    def _configure_columns(self):
        """Настройка колонок дерева."""
        self.heading("#0", text="")
        self.heading("name", text="Название")
        self.heading("status", text="Уровень")
        self.column("#0", width=30, stretch=False)
        self.column("name", width=300)
        self.column("status", width=60, anchor="center")
    
    def _configure_tags(self):
        """Настройка тегов для цветов статусов."""
        for val, color in STATUS_COLORS.items():
            weight = "bold" if val != 0 else "normal"
            self.tag_configure(f"st{val}", foreground=color, font=("Segoe UI", 9, weight))
    
    def refresh_tree(self, lst: ItemList, selected_id: Optional[str] = None):
        """Обновляет дерево элементами из списка."""
        for item in self.get_children():
            self.delete(item)
        
        self._insert_tree_children(lst, None, "")
        
        if selected_id and self.exists(selected_id):
            self.selection_set(selected_id)
            self.see(selected_id)
    
    def _insert_tree_children(self, lst: ItemList, parent_id: Optional[str], tree_parent: str):
        """Рекурсивно вставляет дочерние элементы."""
        element_ids = lst.root_elements if parent_id is None else lst.elements[parent_id].children_ids
        for eid in element_ids:
            if eid not in lst.elements:
                continue
            elem = lst.elements[eid]
            tag = f"st{elem.status}"
            item = self.insert(
                tree_parent, "end", iid=eid,
                text="", values=(elem.name, elem.status), tags=(tag,),
            )
            self._insert_tree_children(lst, eid, item)
