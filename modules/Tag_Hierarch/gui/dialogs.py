# file: modules/Tag_Hierarch/gui/dialogs.py
"""
Диалоги Tag Hierarch - SelectElementDialog, SelectDepTypeDialog.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional


class SelectElementDialog(tk.Toplevel):
    """Диалог выбора элемента."""
    
    def __init__(self, parent, manager, exclude_id=None, title="Выбор элемента"):
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
    """Диалог выбора типа зависимости."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Тип зависимости")
        self.geometry("320x220")
        self.transient(parent)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Импортируем здесь для избежания циклических импортов
        from modules.Tag_Hierarch.core.config import DEP_TYPES, DEP_COLORS

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
