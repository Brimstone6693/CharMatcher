"""
Утилиты для работы с полом персонажей.
"""


def get_final_gender(gender_combobox: str, custom_gender_entry: str) -> str:
    """
    Получение финального значения пола с учётом custom поля.
    
    Args:
        gender_combobox: Значение из комбобокса (может быть "custom")
        custom_gender_entry: Значение из поля custom (может быть пустым)
    
    Returns:
        Финальное значение пола
    """
    if gender_combobox == "custom" and custom_gender_entry.strip():
        return custom_gender_entry.strip()
    return gender_combobox


def normalize_gender(gender: str) -> str:
    """
    Нормализация значения пола к стандартному формату.
    
    Args:
        gender: Исходное значение пола
    
    Returns:
        Нормализованное значение (lowercase, trimmed)
    """
    if not gender:
        return ""
    return gender.strip().lower()


def is_custom_gender(gender: str, predefined_genders: list = None) -> bool:
    """
    Проверка, является ли пол кастомным (не из предопределённого списка).
    
    Args:
        gender: Значение пола для проверки
        predefined_genders: Список предопределённых значений
    
    Returns:
        True если пол кастомный, False иначе
    """
    if predefined_genders is None:
        predefined_genders = ["male", "female", "other", "none"]
    
    return gender.lower() not in [g.lower() for g in predefined_genders]
