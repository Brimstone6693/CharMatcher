# file: core/__init__.py
"""
Ядро системы Character Creator.
Содержит базовые классы для персонажей, тел и компонентов.
"""

from .body_types.body_classes import AbstractBody, DynamicBody, generate_short_id
from .character import Character
from .components import BaseComponent, Stats, Inventory, Personality, GhostlyFeatures
from .module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR

__all__ = [
    'AbstractBody',
    'DynamicBody', 
    'generate_short_id',
    'Character',
    'BaseComponent',
    'Stats',
    'Inventory',
    'Personality',
    'GhostlyFeatures',
    'load_available_modules_and_bodies',
    'BODIES_DATA_DIR'
]
