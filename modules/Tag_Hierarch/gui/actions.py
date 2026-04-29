# file: modules/Tag_Hierarch/gui/actions.py
"""
Действия пользователя в Tag Hierarch - обработка команд меню и кнопок.
"""

from tkinter import messagebox, simpledialog, filedialog
from typing import Optional
import os


class ActionHandler:
    """Обработчик действий пользователя."""
    
    def __init__(self, app):
        self.app = app
    
    # === Управление списками ===
    
    def add_list(self):
        name = simpledialog.askstring("Новый список", "Введите название списка:", parent=self.app)
        if name and name.strip():
            lst = self.app.manager.create_list(name.strip())
            self.app.current_list_id = lst.list_id
            self.app.refresh_lists()
    
    def delete_list(self):
        if not self.app.current_list_id:
            messagebox.showwarning("Внимание", "Выберите список для удаления")
            return
        lst = self.app.manager.lists[self.app.current_list_id]
        if not messagebox.askyesno("Подтверждение", f"Удалить список '{lst.name}'?\nВсе элементы будут удалены!"):
            return
        self.app.manager.delete_list(self.app.current_list_id)
        self.app.current_list_id = None
        self.app.selected_element_id = None
        self.app.clear_details()
        self.app.refresh_lists()
        self.app.refresh_tree()
    
    def rename_list(self):
        if not self.app.current_list_id:
            return
        old_name = self.app.manager.lists[self.app.current_list_id].name
        new_name = simpledialog.askstring("Переименование", "Новое название:", initialvalue=old_name, parent=self.app)
        if new_name and new_name.strip():
            self.app.manager.lists[self.app.current_list_id].name = new_name.strip()
            self.app.refresh_lists()
    
    # === Управление элементами ===
    
    def add_element(self):
        if not self.app.current_list_id:
            messagebox.showwarning("Внимание", "Сначала создайте или выберите список")
            return
        name = simpledialog.askstring("Новый элемент", "Название элемента:", parent=self.app)
        if name and name.strip():
            desc = simpledialog.askstring("Описание", "Описание (можно оставить пустым):", parent=self.app) or ""
            elem = self.app.manager.add_element(self.app.current_list_id, name.strip(), desc.strip())
            self.app.manager._recalculate_states()
            self.app.refresh_tree()
            if elem and self.app.tree.exists(elem.element_id):
                self.app.tree.selection_set(elem.element_id)
                self.app.tree.see(elem.element_id)
    
    def add_child(self):
        if not self.app.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите родительский элемент в дереве")
            return
        name = simpledialog.askstring("Новый подэлемент", "Название подэлемента:", parent=self.app)
        if name and name.strip():
            desc = simpledialog.askstring("Описание", "Описание (можно оставить пустым):", parent=self.app) or ""
            elem = self.app.manager.add_element(
                self.app.current_list_id, name.strip(), desc.strip(),
                parent_id=self.app.selected_element_id,
            )
            self.app.manager._recalculate_states()
            self.app.refresh_tree()
            self.app.tree.item(self.app.selected_element_id, open=True)
            if elem and self.app.tree.exists(elem.element_id):
                self.app.tree.selection_set(elem.element_id)
                self.app.tree.see(elem.element_id)
    
    def delete_element(self):
        if not self.app.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент для удаления")
            return
        elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
        cascade = messagebox.askyesno(
            "Удаление",
            f"Удалить '{elem.name}'?\n\n"
            "Да — удалить со всеми подэлементами\n"
            "Нет — подэлементы поднимутся на уровень выше",
        )
        self.app.manager.remove_element(self.app.current_list_id, self.app.selected_element_id, cascade=cascade)
        self.app.manager._recalculate_states()
        self.app.selected_element_id = None
        self.app.clear_details()
        self.app.refresh_tree()
    
    # === Сохранение элемента ===
    
    def save_element(self, silent=False):
        if not self.app.selected_element_id or not self.app.current_list_id:
            return
        elem = self.app.manager.lists[self.app.current_list_id].elements[self.app.selected_element_id]
        
        elem.name = self.app.name_var.get().strip()
        elem.description = self.app.desc_text.get("1.0", tk.END).strip()
        
        try:
            val = int(self.app.status_var.get())
            current_auto_status = elem.status
            if val != current_auto_status:
                elem.custom_status = max(-3, min(3, val))
            else:
                elem.custom_status = None
        except ValueError:
            elem.custom_status = None
        
        self.app.manager._recalculate_states()
        self.app.refresh_tree()
        self.app.load_element_details()
        self.app.save_btn.config(bg="#e3f2fd", text="💾 Сохранить изменения")
        if not silent:
            messagebox.showinfo("Готово", "Изменения сохранены")
    
    # === Ссылки и зависимости ===
    
    def create_link(self):
        from modules.Tag_Hierarch.gui.dialogs import SelectElementDialog
        if not self.app.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент-источник")
            return
        dialog = SelectElementDialog(
            self.app, self.app.manager, exclude_id=self.app.selected_element_id,
            title="Создать взаимную ссылку с...",
        )
        if dialog.result:
            try:
                self.app.manager.create_reference(self.app.selected_element_id, dialog.result, "")
                self.app.load_element_details()
                messagebox.showinfo("Готово", "Взаимная ссылка создана")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def add_dependency(self):
        from modules.Tag_Hierarch.gui.dialogs import SelectElementDialog, SelectDepTypeDialog
        if not self.app.selected_element_id:
            messagebox.showwarning("Внимание", "Выберите элемент")
            return
        dialog = SelectElementDialog(
            self.app, self.app.manager, exclude_id=self.app.selected_element_id,
            title="Добавить зависимость от...",
        )
        if not dialog.result:
            return
        type_dialog = SelectDepTypeDialog(self.app)
        if not type_dialog.result:
            return
        
        dep_type = type_dialog.result
        self.app.manager.add_dependency(self.app.selected_element_id, dialog.result, dep_type)
        
        reverse = messagebox.askyesno("Обратная зависимость", "Создать обратную зависимость того же типа?")
        if reverse:
            self.app.manager.add_dependency(dialog.result, self.app.selected_element_id, dep_type)
        
        self.app.manager._recalculate_states()
        self.app.refresh_tree()
        self.app.load_element_details()
        self.app.update_edit_indicator()
    
    # === Файловые операции ===
    
    def save_file(self):
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir=data_dir,
            initialfile="lists_data.json"
        )
        if path:
            self.app.manager.export_to_json(path)
            messagebox.showinfo("Сохранение", f"Данные сохранены в:\n{path}")
    
    def load_file(self):
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            initialdir=data_dir
        )
        if path:
            try:
                self.app.manager.import_from_json(path)
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", str(e))
                return
            self.app.current_list_id = None
            self.app.selected_element_id = None
            self.app.clear_details()
            self.app.refresh_lists()
            self.app.refresh_tree()
            messagebox.showinfo("Загрузка", "Данные загружены")
