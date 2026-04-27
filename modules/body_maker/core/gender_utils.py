# file: modules/body_maker/core/gender_utils.py
"""
Миксин для утилит работы с полом персонажей.
"""


class GenderUtilsMixin:
    """Предоставляет утилиты для работы с полом."""
    
    def get_final_gender(self):
        """Возвращает итоговое значение пола с учётом custom поля."""
        base_gender = self.new_body_gender_var.get()
        custom_gender = self.new_body_gender_custom_entry.get().strip()
        
        if base_gender == "Other" and custom_gender:
            return custom_gender
        return base_gender if base_gender else "N/A"
    
    @staticmethod
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
    
    @staticmethod
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
