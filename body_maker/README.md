# Body Maker - Автономное приложение для создания и редактирования тел

## 📖 Описание
Body Maker - это независимое приложение для создания, редактирования и управления типами тел персонажей, а также для создания самих персонажей.

## 🚀 Быстрый старт

### Запуск приложения
```bash
cd body_maker
python body_maker_entry.py
```

Или напрямую:
```bash
python body_maker_entry.py
```

## 📁 Структура проекта

```
body_maker/
├── body_maker_entry.py      # Точка входа приложения
├── __init__.py
│
├── core/                    # Ядро системы
│   ├── __init__.py
│   ├── body_classes.py      # Классы AbstractBody, DynamicBody
│   ├── body_management.py   # CRUD операции с телами
│   ├── character.py         # Класс Character
│   ├── components.py        # Базовые компоненты
│   ├── core.py              # BodyTypeManager (главный класс)
│   ├── database_operations.py # Операции с БД частей
│   ├── history.py           # Undo/Redo
│   ├── module_loader.py     # Загрузка модулей
│   ├── tree_clipboard.py    # Буфер обмена для дерева
│   ├── tree_editing.py      # Редактирование дерева
│   ├── tree_operations.py   # Операции с деревом частей
│   ├── ui_parts_list.py     # UI списка частей
│   ├── ui_structure.py      # UI структура экрана
│   └── ui_tags_manager.py   # Менеджер тегов
│
├── gui/                     # Графический интерфейс
│   ├── __init__.py
│   ├── main_window.py       # Главное окно
│   └── mixins/              # Миксины для MainWindow
│       ├── body_editor_mixin.py
│       ├── character_view_mixin.py
│       ├── creation_screen_mixin.py
│       └── start_screen_mixin.py
│
├── data/                    # Работа с данными
│   ├── __init__.py
│   └── parts_database.py    # База данных частей тела
│
├── utils/                   # Утилиты
│   ├── __init__.py
│   ├── gender_utils.py      # Утилиты пола
│   ├── id_generator.py      # Генератор ID
│   ├── module_generator.py  # Генератор модулей
│   └── size_calculator.py   # Калькулятор размеров
│
├── modules/                 # Пользовательские компоненты
│   ├── __init__.py
│   ├── example_component.py
│   └── traits_system_component.py
│
├── bodies_data/             # JSON файлы типов тел
│   ├── ghostbody.json
│   ├── humanoidbody.json
│   └── quadrupedalbody.json
│
└── body_parts_db.json       # База данных частей тела
```

## 🔧 Требования

- Python 3.8+
- Tkinter (обычно входит в стандартную установку Python)

## 📝 Использование

### Создание нового типа тела
1. Запустите приложение
2. Нажмите "Manage Body Types"
3. Нажмите "New Body Type"
4. Заполните параметры (название, раса, размер, пол)
5. Добавьте части тела через дерево

### Редактирование частей тела
- **Добавить часть**: Правый клик на дереве → "Add Child Part" или "Add Root Part"
- **Переименовать**: Двойной клик на части или кнопка "Rename"
- **Удалить**: Кнопка "Delete" или правый клик → "Delete"
- **Теги**: Правый клик → "Add Tag" для добавления тегов

### Сохранение типа тела
Нажмите "Save Body Type" чтобы сохранить тип тела в JSON файл в папке `bodies_data/`

### Создание персонажа
1. На главном экране нажмите "Create Character"
2. Введите имя персонажа
3. Выберите тип тела из списка
4. Добавьте компоненты (Stats, Inventory и т.д.)
5. Нажмите "Create Character"

### Сохранение персонажа
В режиме просмотра персонажа нажмите "Save Character" для сохранения в JSON файл

## 🛠️ Расширение функциональности

### Добавление нового компонента
Создайте файл в папке `modules/`:

```python
from core.components import BaseComponent

class MyCustomComponent(BaseComponent):
    def __init__(self, custom_param=None):
        self.custom_param = custom_param
    
    def to_dict(self):
        return {"custom_param": self.custom_param}
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
```

Компонент автоматически загрузится при следующем запуске.

### Добавление нового типа тела через код
Используйте `utils/module_generator.py`:

```bash
python utils/module_generator.py --type body --name mybody
```

## 📄 Лицензия
[Укажите вашу лицензию]

## 👥 Авторы
[Укажите авторов]
