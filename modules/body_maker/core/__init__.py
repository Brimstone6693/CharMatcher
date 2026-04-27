# file: modules/body_maker/core/__init__.py
"""
Модуль для управления типами тел (Body Maker Core).
Инкапсулирует всю логику создания, редактирования, удаления и отображения типов тел.
"""

# Импортируем классы тел отдельно - они не зависят от tkinter
from .body_classes import AbstractBody, DynamicBody, generate_short_id

# Импортируем миксины
from .tree_operations import TreeOperationsMixin
from .tree_editing import TreeEditingMixin
from .tree_clipboard import TreeClipboardMixin
from .body_management import BodyManagementMixin
from .database_operations import DatabaseOperationsMixin
from .history import HistoryMixin
from .ui_parts_list import PartsListMixin
from .ui_tags_manager import TagsManagerMixin
from .ui_structure import UIStructureMixin
from .size_calculator import SizeCalculatorMixin
from .gender_utils import GenderUtilsMixin

# BodyTypeManager импортируем с задержкой или через getattr для избежания circular imports
# и проблем с tkinter при импорте только классов тел
__all__ = [
    'AbstractBody', 
    'DynamicBody', 
    'generate_short_id', 
    'BodyTypeManager',
    'TreeOperationsMixin',
    'TreeEditingMixin',
    'TreeClipboardMixin',
    'BodyManagementMixin',
    'DatabaseOperationsMixin',
    'HistoryMixin',
    'PartsListMixin',
    'TagsManagerMixin',
    'UIStructureMixin',
    'SizeCalculatorMixin',
    'GenderUtilsMixin',
]

def __getattr__(name):
    if name == 'BodyTypeManager':
        from .core import BodyTypeManager
        return BodyTypeManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
