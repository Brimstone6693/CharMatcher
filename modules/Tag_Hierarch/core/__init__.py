# file: modules/Tag_Hierarch/core/__init__.py
"""
Tag Hierarch Core - Модуль управления иерархическими списками тегов.
Инкапсулирует всю логику создания, редактирования, удаления и отображения элементов.

Этот модуль полностью независим и способен работать отдельно от core.
"""

# Импортируем модели данных
from modules.Tag_Hierarch.core.models import Element, ItemList, ListManager

# Импортируем конфигурацию
from modules.Tag_Hierarch.core.config import (
    DEP_TYPES,
    DEP_COLORS,
    STATUS_COLORS,
)

__all__ = [
    'Element',
    'ItemList', 
    'ListManager',
    'DEP_TYPES',
    'DEP_COLORS',
    'STATUS_COLORS',
]
