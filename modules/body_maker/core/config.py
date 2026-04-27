# file: modules/body_maker/core/config.py
"""Конфигурация и пути для модуля Body Maker."""
import os

# Получаем директорию модуля Body Maker
BODY_MAKER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_ROOT = os.path.dirname(BODY_MAKER_ROOT)  # Корень modules/
PROJECT_ROOT = os.path.dirname(MODULES_ROOT)     # Корень проекта

# Пути внутри Body Maker
BODIES_DATA_DIR = os.path.join(BODY_MAKER_ROOT, "data", "json_files")
PARTS_DB_FILE = os.path.join(BODY_MAKER_ROOT, "data", "parts_db.json")
TAGS_DB_FILE = os.path.join(BODY_MAKER_ROOT, "data", "tags_db.json")

__all__ = [
    'BODY_MAKER_ROOT',
    'MODULES_ROOT', 
    'PROJECT_ROOT',
    'BODIES_DATA_DIR',
    'PARTS_DB_FILE',
    'TAGS_DB_FILE',
]
