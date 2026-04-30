# file: modules/Tag_Hierarch/gui/panels.py
"""
Панели интерфейса для Tag Hierarch.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List


class ScrollablePropertiesPanel(tk.Frame):
    """Прокручиваемая панель свойств элемента."""
    
    def __init__(self, parent, width: int = 380):
        super().__init__(parent)
        self.width = width
        
        self._create_canvas()
        self._create_content_frame()
        self._bind_mousewheel()
    
    def _create_canvas(self):
        """Создаёт canvas с прокруткой."""
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
    
    def _create_content_frame(self):
        """Создаёт прокручиваемый фрейм внутри canvas."""
        self.content_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.content_frame.config(width=self.width)
    
    def _on_frame_configure(self, event):
        """Обновляет область прокрутки при изменении размера фрейма."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Подстраивает ширину фрейма под canvas."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _bind_mousewheel(self):
        """Привязывает прокрутку колёсиком мыши."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def clear(self):
        """Очищает содержимое панели."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()


class ListPanel(tk.Frame):
    """Панель управления списками."""
    
    def __init__(self, parent, on_select_callback=None):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        self._create_buttons()
        self._create_listbox()
    
    def _create_buttons(self):
        """Создаёт кнопки управления списками."""
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(btn_frame, text="Создать", command=self._on_create).pack(side="left", padx=(0, 2))
        tk.Button(btn_frame, text="Удалить", command=self._on_delete).pack(side="left", padx=(0, 2))
        tk.Button(btn_frame, text="Переим.", command=self._on_rename).pack(side="left")
    
    def _create_listbox(self):
        """Создаёт список списков."""
        self.listbox = tk.Listbox(self, exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
    
    def _on_create(self):
        if hasattr(self, 'create_command'):
            self.create_command()
    
    def _on_delete(self):
        if hasattr(self, 'delete_command'):
            self.delete_command()
    
    def _on_rename(self):
        if hasattr(self, 'rename_command'):
            self.rename_command()
    
    def _on_select(self, event=None):
        if self.on_select_callback:
            self.on_select_callback()
    
    def refresh(self, lists_dict: dict, current_id: Optional[str]):
        """Обновляет список списков."""
        self.listbox.delete(0, tk.END)
        for idx, (lid, lst) in enumerate(lists_dict.items()):
            self.listbox.insert(tk.END, lst.name)
            if lid == current_id:
                self.listbox.selection_set(idx)
                self.listbox.see(idx)


class ElementActionsPanel(tk.Frame):
    """Панель действий с элементами."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._create_buttons()
    
    def _create_buttons(self):
        """Создаёт кнопки действий."""
        tk.Button(self, text="Добавить", command=self._on_add).pack(side="left", padx=(0, 2))
        tk.Button(self, text="Подэлемент", command=self._on_add_child).pack(side="left", padx=(0, 2))
        tk.Button(self, text="Удалить", command=self._on_delete).pack(side="left", padx=(0, 2))
        tk.Button(self, text="Связать", command=self._on_link).pack(side="left")
    
    def _on_add(self):
        if hasattr(self, 'add_command'):
            self.add_command()
    
    def _on_add_child(self):
        if hasattr(self, 'add_child_command'):
            self.add_child_command()
    
    def _on_delete(self):
        if hasattr(self, 'delete_command'):
            self.delete_command()
    
    def _on_link(self):
        if hasattr(self, 'link_command'):
            self.link_command()


class ReferencesPanel(tk.Frame):
    """Панель отображения ссылок на элементы."""
    
    def __init__(self, parent, title: str = "Ссылки"):
        super().__init__(parent)
        self.title = title
        self.links_map: Dict[int, str] = {}
        
        self._create_label()
        self._create_buttons()
        self._create_listbox()
    
    def _create_label(self):
        """Создаёт заголовок панели."""
        tk.Label(self, text=self.title, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=2, pady=2)
    
    def _create_buttons(self):
        """Создаёт кнопки управления."""
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=2, pady=2)
        tk.Button(btn_frame, text="Добавить", command=self._on_add).pack(side="left", padx=(0, 2))
        tk.Button(btn_frame, text="Удалить", command=self._on_remove).pack(side="left")
    
    def _create_listbox(self):
        """Создаёт список ссылок."""
        scroll = tk.Scrollbar(self)
        scroll.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(self, yscrollcommand=scroll.set)
        self.listbox.pack(fill="both", expand=True, padx=2, pady=2)
        scroll.config(command=self.listbox.yview)
        # Привязка события выбора элемента в списке
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
    
    def _on_select(self, event=None):
        """Обработчик выбора элемента в списке (для подсветки)."""
        # Пустой обработчик для предотвращения ошибок при отсутствии внешней команды
        pass
    
    def _on_add(self):
        if hasattr(self, 'add_command'):
            self.add_command()
    
    def _on_remove(self):
        if hasattr(self, 'remove_command'):
            self.remove_command()
    
    def clear(self):
        """Очищает список и маппинг."""
        self.listbox.delete(0, tk.END)
        self.links_map.clear()
    
    def add_item(self, display_text: str, element_id: str, **kwargs):
        """Добавляет элемент в список."""
        self.listbox.insert(tk.END, display_text)
        idx = self.listbox.size() - 1
        self.links_map[idx] = element_id
        if kwargs.get('fg'):
            self.listbox.itemconfig(tk.END, fg=kwargs['fg'])
    
    def get_selected_id(self) -> Optional[str]:
        """Возвращает ID выбранного элемента."""
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        return self.links_map.get(idx)
