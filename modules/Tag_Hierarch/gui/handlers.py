# file: modules/Tag_Hierarch/gui/handlers.py
"""
Обработчики событий для Tag Hierarch.
"""

import tkinter as tk
from typing import Optional

from modules.Tag_Hierarch.core.config import STATUS_COLORS, DEP_COLORS


class ElementStateHandler:
    """Обработчик состояния элемента (статус, редактирование)."""
    
    def __init__(self, app):
        self.app = app
    
    def on_status_changed(self, event=None):
        """Обработчик изменения статуса в combobox."""
        if not self.app.selected_element_id or not self.app.current_list_id:
            return
        try:
            val = int(self.app.status_var.get())
            elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
            
            if self.app.manual_override_var.get():
                elem.custom_status = max(-3, min(3, val))
            else:
                elem.custom_status = max(-3, min(3, val))
            
            self.app.manager._recalculate_states()
            self.app.refresh_tree()
            self.app.update_edit_indicator()
        except ValueError:
            self.app.status_preview.config(text="(неверное)", fg="#f44336")
        self.app._on_field_changed()
    
    def on_manual_override_changed(self):
        """Обработчик изменения чекбокса 'Ручная настройка'."""
        if not self.app.selected_element_id or not self.app.current_list_id:
            return
        
        elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
        
        if self.app.manual_override_var.get():
            elem.metadata["manual_override"] = True
            try:
                val = int(self.app.status_var.get())
                elem.custom_status = max(-3, min(3, val))
            except ValueError:
                elem.custom_status = 0
            self.app.status_combo.config(state="readonly")
        else:
            elem.metadata["manual_override"] = False
            elem.custom_status = None
            self.app.status_combo.config(state="readonly")
        
        self.app.manager._recalculate_states()
        self.app.refresh_tree()
        self.app.update_edit_indicator()
        self.app._on_field_changed()
    
    def on_field_changed(self, *args):
        """Вызывается при изменении любого поля элемента."""
        if self.app.selected_element_id and self.app.current_list_id:
            elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
            has_custom = elem.custom_status is not None
            has_deps = len(elem.depends_on) > 0
            is_manual_override = elem.metadata.get("manual_override", False)
            
            if is_manual_override:
                self.app.save_btn.config(bg="#ffcdd2", text="💾 Сохранить изменения**")
            elif has_custom and has_deps:
                self.app.save_btn.config(bg="#ffcdd2", text="💾 Сохранить изменения**")
            elif has_custom:
                self.app.save_btn.config(bg="#bbdefb", text="💾 Сохранить изменения*")
            else:
                self.app.save_btn.config(bg="#e3f2fd", text="💾 Сохранить изменения")
    
    def update_edit_indicator(self):
        """Обновляет индикатор редактирования."""
        if not self.app.selected_element_id or not self.app.current_list_id:
            return
        elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
        
        has_custom_status = elem.custom_status is not None
        has_dependencies = len(elem.depends_on) > 0
        is_manual_override = elem.metadata.get("manual_override", False)
        
        self.app.manual_override_var.set(is_manual_override)
        
        if is_manual_override:
            self.app.element_edit_state = "overridden"
            self.app.status_preview.config(
                text=f"(ручной: {elem.custom_status}) **",
                fg=STATUS_COLORS.get(elem.custom_status, "#000")
            )
        elif has_custom_status:
            if has_dependencies:
                self.app.element_edit_state = "overridden"
                self.app.status_preview.config(
                    text=f"(ручной: {elem.custom_status}) **",
                    fg=STATUS_COLORS.get(elem.custom_status, "#000")
                )
            else:
                self.app.element_edit_state = "edited"
                self.app.status_preview.config(
                    text=f"(ручной: {elem.custom_status})*",
                    fg=STATUS_COLORS.get(elem.custom_status, "#000")
                )
        else:
            self.app.element_edit_state = None
            info = self.app.manager.get_element_info(self.app.selected_element_id)
            if info:
                self.app.status_preview.config(
                    text=f"→ Авто: {info['status']}",
                    fg=STATUS_COLORS.get(info['status'], "#000")
                )


class SelectionHandler:
    """Обработчик выбора элементов и списков."""
    
    def __init__(self, app):
        self.app = app
    
    def on_list_select(self, event=None):
        sel = self.app.lists_lb.curselection()
        if not sel:
            return
        if self.app.selected_element_id and self.app.current_list_id:
            self.app.save_element(silent=True)
        self.app.current_list_id = list(self.app.manager.lists.keys())[sel[0]]
        self.app.selected_element_id = None
        self.app.clear_details()
        self.app.refresh_tree()
    
    def on_tree_select(self, event=None):
        sel = self.app.tree.selection()
        if not sel:
            return
        if self.app.selected_element_id and self.app.current_list_id:
            self.app.save_element(silent=True)
        self.app.selected_element_id = sel[0]
        self.app.load_element_details()
        self.app.save_btn.config(bg="#e3f2fd", text="💾 Сохранить изменения")


class DetailsLoader:
    """Загрузчик деталей элемента в панель свойств."""
    
    def __init__(self, app):
        self.app = app
    
    def load_element_details(self):
        if not self.app.selected_element_id:
            return
        info = self.app.manager.get_element_info(self.app.selected_element_id)
        if not info:
            return
        
        self.app.name_var.set(info["name"])
        self.app.desc_text.delete("1.0", tk.END)
        self.app.desc_text.insert("1.0", info.get("description", ""))
        
        elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
        is_manual_override = elem.metadata.get("manual_override", False)
        
        self.app.manual_override_var.set(is_manual_override)
        self.app.status_combo.config(state="readonly")
        
        cs = info.get("custom_status")
        
        if is_manual_override:
            self.app.status_var.set(str(cs) if cs is not None else "0")
            self.app.status_preview.config(
                text=f"(ручной: {cs}) **",
                fg=STATUS_COLORS.get(cs, "#000"),
            )
        elif cs is not None:
            self.app.status_var.set(str(cs))
            has_dependencies = len(info.get("resolved_dependencies", [])) > 0
            if has_dependencies:
                self.app.status_preview.config(
                    text=f"(ручной: {cs}) **", 
                    fg=STATUS_COLORS.get(cs, "#000")
                )
            else:
                self.app.status_preview.config(
                    text=f"(ручной: {cs})*", 
                    fg=STATUS_COLORS.get(cs, "#000")
                )
        else:
            self.app.status_var.set(str(info["status"]))
            self.app.status_preview.config(
                text=f"→ Авто: {info['status']}",
                fg=STATUS_COLORS.get(info["status"], "#000"),
            )
        
        self._load_references(info)
        self._load_dependencies(info)
        self._load_reverse_dependencies(info)
    
    def _load_references(self, info):
        self.app.refs_lb.delete(0, tk.END)
        self.app.links_map.clear()
        for i, ref in enumerate(info.get("resolved_references", [])):
            display = f"{ref['name']} ({ref['list_name']})"
            if ref.get("note"):
                display += f" — {ref['note']}"
            self.app.refs_lb.insert(tk.END, display)
            self.app.links_map[i] = ref["element_id"]
    
    def _load_dependencies(self, info):
        self.app.deps_lb.delete(0, tk.END)
        self.app.deps_map.clear()
        for i, dep in enumerate(info.get("resolved_dependencies", [])):
            color = DEP_COLORS.get(dep["type"], "#000")
            display = f"[{dep['type']}] [{dep['status']}] {dep['name']}"
            self.app.deps_lb.insert(tk.END, display)
            self.app.deps_lb.itemconfig(tk.END, fg=color)
            self.app.deps_map[i] = dep["element_id"]
    
    def _load_reverse_dependencies(self, info):
        self.app.rev_deps_lb.delete(0, tk.END)
        self.app.rev_deps_map.clear()
        for i, dep in enumerate(info.get("resolved_depended_by", [])):
            color = DEP_COLORS.get(dep["type"], "#000")
            display = f"[{dep['type']}] [{dep['status']}] {dep['name']} ({dep['list_name']})"
            self.app.rev_deps_lb.insert(tk.END, display)
            self.app.rev_deps_lb.itemconfig(tk.END, fg=color)
            self.app.rev_deps_map[i] = dep["element_id"]
    
    def clear_details(self):
        self.app.name_var.set("")
        self.app.desc_text.delete("1.0", tk.END)
        self.app.status_var.set("0")
        self.app.manual_override_var.set(False)
        self.app.status_combo.config(state="readonly")
        self.app.status_preview.config(text="→ Авто: 0", fg="#616161")
        self.app.refs_lb.delete(0, tk.END)
        self.app.deps_lb.delete(0, tk.END)
        self.app.rev_deps_lb.delete(0, tk.END)
        self.app.links_map.clear()
        self.app.deps_map.clear()
        self.app.rev_deps_map.clear()
        self.app.element_edit_state = None
