# GUI Mixins package для Body Maker
"""
GUI миксины для интеграции Body Maker с главным окном приложения.
Эти миксины зависят от tkinter и основного приложения.
"""

from modules.body_maker.gui.start_screen_mixin import StartScreenMixin
from modules.body_maker.gui.creation_screen_mixin import CreationScreenMixin
from modules.body_maker.gui.character_view_mixin import CharacterViewMixin
from modules.body_maker.gui.body_editor_mixin import BodyEditorMixin

__all__ = [
    'StartScreenMixin',
    'CreationScreenMixin',
    'CharacterViewMixin',
    'BodyEditorMixin',
]
