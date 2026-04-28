# file: modules/Tag_Hierarch/core/config.py
"""
Конфигурация Tag Hierarch - типы зависимостей, цвета и константы.
"""

DEP_TYPES = {
    "EQ": "Строго равно",
    "PM1": "± 1",
    "LE": "Не больше (≤)",
    "GE": "Не меньше (≥)",
}

DEP_COLORS = {
    "EQ": "#9c27b0",
    "PM1": "#2196f3",
    "LE": "#f44336",
    "GE": "#4caf50",
}

STATUS_COLORS = {
    -3: "#8b0000",
    -2: "#d32f2f",
    -1: "#f57c00",
    0: "#616161",
    1: "#7cb342",
    2: "#388e3c",
    3: "#1b5e20",
}
