# file: modules/Tag_Hierarch/__init__.py
"""
Tag Hierarch - Модуль управления иерархическими списками тегов.
Самодостаточный модуль, не зависящий от основного приложения.

Взаимодействие с core ограничено:
1. Core может запустить ListManagerApp через GUI
2. Tag Hierarch сохраняет файлы в своей зоне доступа (data/)
"""

# Экспортируем модели данных (не требуют tkinter)
from modules.Tag_Hierarch.core.models import Element, ItemList, ListManager

# Конфигурация
from modules.Tag_Hierarch.core.config import DEP_TYPES, DEP_COLORS, STATUS_COLORS

# GUI импортируется лениво
__all__ = ['Element', 'ItemList', 'ListManager', 'DEP_TYPES', 'DEP_COLORS', 'STATUS_COLORS', 'ListManagerApp']


def __getattr__(name):
    if name == 'ListManagerApp':
        from modules.Tag_Hierarch.gui.main_app import ListManagerApp
        return ListManagerApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")