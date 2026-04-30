# file: modules/Tag_Hierarch/core/config.py
"""
Конфигурация Tag Hierarch - типы зависимостей, цвета и константы.
"""

DEP_TYPES = {
    "EQ": "Строго равно",
    "PM1": "± 1",
    "LE": "Не больше (≤)",
    "GE": "Не меньше (≥)",
    "WLE": "Слабое ≤ (сдвиг +1)",
    "WGE": "Слабое ≥ (сдвиг -1)",
}

DEP_COLORS = {
    "EQ": "#9c27b0",
    "PM1": "#2196f3",
    "LE": "#f44336",
    "GE": "#4caf50",
    "WLE": "#ff9800",
    "WGE": "#00bcd4",
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

# Базовые веса статусов для расчёта силы ограничений
BASE_WEIGHTS = {
    -3: -5,
    -2: -3,
    -1: -1,
    0: 0,
    1: 1,
    2: 3,
    3: 5,
    None: 0,
}


def get_status_weight(status) -> int:
    """Возвращает базовый вес статуса (может быть отрицательным)."""
    return BASE_WEIGHTS.get(status, 0)


def calculate_constraint_strength(statuses: list) -> float:
    """Вычисляет силу ограничения как среднее арифметическое абсолютных значений базовых весов."""
    if not statuses:
        return 0.0
    total = sum(abs(BASE_WEIGHTS.get(s, 0)) for s in statuses)
    return total / len(statuses)
