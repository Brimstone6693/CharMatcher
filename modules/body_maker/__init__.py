"""
Body Maker - Модуль создания и редактирования тел персонажей.
Самодостаточный модуль, не зависящий от основного приложения.
"""

from modules.body_maker.core.core import BodyTypeManager
from modules.body_maker.core.body_classes import AbstractBody, DynamicBody

__all__ = ['BodyTypeManager', 'AbstractBody', 'DynamicBody']
