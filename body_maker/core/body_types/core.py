# file: body_type_manager/core.py
"""
Основной класс BodyTypeManager и базовая функциональность.
"""

import os
import json
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import copy
from core.module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR
from data.parts_database import PartsDatabase

from .ui_structure import UIStructureMixin
from .ui_parts_list import PartsListMixin
from .ui_tags_manager import TagsManagerMixin
from .tree_operations import TreeOperationsMixin
from .tree_editing import TreeEditingMixin
from .tree_clipboard import TreeClipboardMixin
from .database_operations import DatabaseOperationsMixin
from .body_management import BodyManagementMixin
from .history import HistoryMixin


class BodyTypeManager(
    HistoryMixin,
    TreeOperationsMixin, 
    TreeEditingMixin,
    TreeClipboardMixin,
    PartsListMixin,
    TagsManagerMixin,
    DatabaseOperationsMixin,
    BodyManagementMixin,
    UIStructureMixin
):
    """
    Класс для управления типами тел в GUI.
    Инкапсулирует всю логику работы с формами, деревьями частей тела и файлами JSON.
    
    Миксины предоставляют следующую функциональность:
    - HistoryMixin: Undo/Redo
    - TreeOperationsMixin: Операции с деревом частей тела
    - PartsListMixin: Список всех частей тела
    - TagsManagerMixin: Менеджер тегов
    - DatabaseOperationsMixin: Сохранение/загрузка из базы данных
    - BodyManagementMixin: Управление типами тел (создание, сохранение, загрузка)
    - UIStructureMixin: Создание UI элементов
    """
    
    # Пороги размеров для standing height (человеческий стандарт)
    STANDING_SIZE_THRESHOLDS = [
        (30, "Tiny"),
        (100, "Small"),
        (180, "Medium"),
        (400, "Large"),
        (700, "Huge"),
        (float('inf'), "Gargantuan")
    ]
    
    # Пороги размеров для withers height (высота в холке)
    WITHERS_SIZE_THRESHOLDS = [
        (20, "Tiny"),
        (60, "Small"),
        (120, "Medium"),
        (250, "Large"),
        (450, "Huge"),
        (float('inf'), "Gargantuan")
    ]
    
    def __init__(self, parent_window):
        """
        Инициализирует менеджер типов тел.
        
        Args:
            parent_window: Родительское окно Tkinter
        """
        self.parent = parent_window
        self.available_components = {}
        self.available_bodies = {}
        
        # Переменные формы
        self.height_type_var = None
        self.auto_size_label = None
        self.current_body_structure = {}
        self.tree_expanded_items = set()
        self.body_parts_tree = None
        self.bodies_listbox = None
        self.body_list_menu = None
        
        # Буфер для копирования/вставки частей
        self.clipboard_parts = None
        
        # История действий для Undo/Redo
        self.action_history = []
        self.redo_stack = []
        self.max_history_size = 50
        
        # База данных частей тела
        self.parts_db = PartsDatabase()
        
        # Состояние видимости панели списка частей
        self.parts_list_visible = False
        self.parts_list_frame = None
        self.parts_list_tree = None
        
        # Менеджер тегов
        self.tags_manager_frame = None
        self.tags_manager_visible = False
        
        # Загружаем доступные модули и тела
        self._reload_available_bodies()
