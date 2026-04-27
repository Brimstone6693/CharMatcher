# file: modules/body_maker/__init__.py
"""
Body Maker - Модуль создания и редактирования тел персонажей.
Самодостаточный модуль, не зависящий от основного приложения.

Взаимодействие с core ограничено:
1. Core может запустить BodyTypeManager через GUI
2. Body Maker сохраняет файлы в своей зоне доступа (data/saved_bodies)
"""

# Экспортируем только классы тел (не требуют tkinter)
from modules.body_maker.core.body_classes import AbstractBody, DynamicBody

# BodyTypeManager требует tkinter и импортируется лениво
__all__ = ['AbstractBody', 'DynamicBody', 'BodyTypeManager']

def __getattr__(name):
    if name == 'BodyTypeManager':
        from modules.body_maker.core.core import BodyTypeManager
        return BodyTypeManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
