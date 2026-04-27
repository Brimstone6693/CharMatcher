"""
Утилиты для проекта Character Creator.
"""

from utils.id_generator import generate_short_id, generate_uuid
from utils.size_calculator import (
    calculate_auto_size,
    STANDING_SIZE_THRESHOLDS,
    WITHERS_SIZE_THRESHOLDS
)
from utils.gender_utils import get_final_gender, normalize_gender, is_custom_gender

__all__ = [
    'generate_short_id',
    'generate_uuid',
    'calculate_auto_size',
    'STANDING_SIZE_THRESHOLDS',
    'WITHERS_SIZE_THRESHOLDS',
    'get_final_gender',
    'normalize_gender',
    'is_custom_gender',
]
