# file: core/__init__.py
"""
Ядро системы Character Creator.
Содержит базовые классы для персонажей, тел и компонентов.

Core предоставляет удобный интерфейс для вызова модулей и должен быть независимым.
"""

from core.body_types.body_classes import AbstractBody, DynamicBody
from core.utils import generate_short_id, generate_uuid
from core.character import Character
from core.components import BaseComponent, Stats, Inventory, Personality, GhostlyFeatures
from core.module_loader import load_available_modules_and_bodies

__all__ = [
    'AbstractBody',
    'DynamicBody', 
    'generate_short_id',
    'generate_uuid',
    'Character',
    'BaseComponent',
    'Stats',
    'Inventory',
    'Personality',
    'GhostlyFeatures',
    'load_available_modules_and_bodies',
]
