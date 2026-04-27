"""
Утилиты для работы с размерами тел.
"""


def calculate_auto_size(height: float, race: str = "human") -> str:
    """
    Автоматическое определение размера тела по высоте.
    
    Args:
        height: Высота в сантиметрах
        race: Раса персонажа (для пороговых значений)
    
    Returns:
        Строковое обозначение размера: 'tiny', 'small', 'medium', 'large', 'huge'
    """
    # Пороги для гуманоидов (standing height)
    if race in ["human", "elf", "dwarf", "orc", "halfling"]:
        if height < 60:
            return "tiny"
        elif height < 120:
            return "small"
        elif height < 180:
            return "medium"
        elif height < 240:
            return "large"
        else:
            return "huge"
    
    # Пороги для четвероногих (withers height)
    elif race in ["horse", "wolf", "dragon"]:
        if height < 30:
            return "tiny"
        elif height < 60:
            return "small"
        elif height < 150:
            return "medium"
        elif height < 200:
            return "large"
        else:
            return "huge"
    
    # По умолчанию используем гуманоидные пороги
    else:
        if height < 60:
            return "tiny"
        elif height < 120:
            return "small"
        elif height < 180:
            return "medium"
        elif height < 240:
            return "large"
        else:
            return "huge"


STANDING_SIZE_THRESHOLDS = {
    "tiny": 60,
    "small": 120,
    "medium": 180,
    "large": 240,
    "huge": float('inf')
}

WITHERS_SIZE_THRESHOLDS = {
    "tiny": 30,
    "small": 60,
    "medium": 150,
    "large": 200,
    "huge": float('inf')
}
