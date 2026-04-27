#!/usr/bin/env python3
# file: body_maker_entry.py
"""
Точка входа для Body Maker - автономного приложения для создания и редактирования тел.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Добавляем корень проекта в path для импортов
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from gui.main_window import MainWindow

def main():
    """Главная точка входа приложения."""
    print("=" * 60)
    print("BODY MAKER - Редактор тел и персонажей")
    print("=" * 60)
    
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
