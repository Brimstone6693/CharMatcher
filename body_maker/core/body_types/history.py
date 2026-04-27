# file: body_type_manager/history.py
"""
Миксин для управления историей действий (Undo/Redo).
"""

import copy
from tkinter import messagebox
from typing import List, Dict, Any


class HistoryMixin:
    """Предоставляет функциональность Undo/Redo для BodyTypeManager."""
    
    # Атрибуты, которые должны быть инициализированы в использующем классе
    action_history: List[Dict[str, Any]]
    redo_stack: List[Dict[str, Any]]
    max_history_size: int
    current_body_structure: Dict
    parent: Any
    
    def _save_action_state(self, action_type, data):
        """
        Сохраняет состояние действия для возможности отмены.
        
        Args:
            action_type: Тип действия (add_child, delete, paste, etc.)
            data: Данные действия
        """
        state_copy = copy.deepcopy(self.current_body_structure)
        self.action_history.append({
            "action": action_type,
            "data": data,
            "state": state_copy
        })
        
        # Ограничиваем размер истории
        if len(self.action_history) > self.max_history_size:
            self.action_history.pop(0)
        
        # Очищаем redo стек при новом действии
        self.redo_stack.clear()
    
    def on_undo(self):
        """Отменяет последнее действие."""
        if not self.action_history:
            messagebox.showinfo("Undo", "Nothing to undo.", parent=self.parent)
            return
        
        # Сохраняем текущее состояние для Redo
        current_state = copy.deepcopy(self.current_body_structure)
        last_action = self.action_history.pop()
        self.redo_stack.append({
            "action": last_action["action"],
            "data": last_action["data"],
            "state": current_state
        })
        
        # Восстанавливаем предыдущее состояние
        self.current_body_structure = copy.deepcopy(last_action["state"])
        self.update_body_parts_tree()
    
    def on_redo(self):
        """Повторяет отмененное действие."""
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nothing to redo.", parent=self.parent)
            return
        
        # Сохраняем текущее состояние для Undo
        current_state = copy.deepcopy(self.current_body_structure)
        redo_action = self.redo_stack.pop()
        self.action_history.append({
            "action": redo_action["action"],
            "data": redo_action["data"],
            "state": current_state
        })
        
        # Восстанавливаем состояние
        self.current_body_structure = copy.deepcopy(redo_action["state"])
        self.update_body_parts_tree()
    
    def _bind_shortcuts(self):
        """Привязывает горячие клавиши к функциям."""
        # Копирование/Вставка
        self.parent.bind("<Control-c>", lambda e: self.on_copy_parts())
        self.parent.bind("<Control-v>", lambda e: self.on_paste_parts())
        
        # Undo/Redo
        self.parent.bind("<Control-z>", lambda e: self.on_undo())
        self.parent.bind("<Control-y>", lambda e: self.on_redo())
        
        # Удаление
        self.parent.bind("<Delete>", lambda e: self.on_delete_part())
        
        # Переименование (F2)
        self.parent.bind("<F2>", lambda e: self.on_rename_part())
