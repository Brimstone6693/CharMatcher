"""
Базовые классы для системы тел.
Этот модуль предоставляет интерфейс к классам тел, сохраняя независимость core от modules.
"""

# Классы теперь находятся непосредственно в core/body_types/body_classes.py
from core.body_types.body_classes import AbstractBody, DynamicBody

__all__ = [
    'AbstractBody',
    'DynamicBody',
]
