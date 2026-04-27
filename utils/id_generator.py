"""
Генераторы уникальных ID для проекта.
"""
import uuid


def generate_short_id(length: int = 8) -> str:
    """
    Генерация короткого уникального ID.
    
    Args:
        length: Длина возвращаемого ID (по умолчанию 8 символов)
    
    Returns:
        Строка уникального ID указанной длины
    """
    return str(uuid.uuid4())[:length]


def generate_uuid() -> str:
    """
    Генерация полного UUID.
    
    Returns:
        Полный UUID в строковом формате
    """
    return str(uuid.uuid4())
