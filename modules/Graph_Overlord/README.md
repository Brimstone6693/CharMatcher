# Graph Overlord

Система хранения и вычисления пользовательских предпочтений в виде ориентированного графа.

## Описание

Graph Overlord хранит увлечения пользователя в виде ориентированного графа с двумя типами связей и на основе явно заданных оценок для части узлов вычисляет предпочтения (отношение и интерес) для всех остальных узлов.

### Ключевые особенности

- **Две независимые оси оценки:**
  - Отношение (Att): [-100, +100]
  - Интерес (Int): [0, 100]

- **Иерархическое дерево** с одним родителем на узел
- **Ассоциативные связи** между произвольными узлами
- **Итеративное распространение оценок** с демпфированием и насыщением
- **Подсветка узлов с высокой неопределённостью**
- **Возможность отключения узлов** (вместе с поддеревьями)
- **Шаблоны связей** на основе дискретных уровней силы
- **Система шаблонов графов** для быстрого построения

## Установка

```bash
# Просто скопируйте папку modules/Graph_Overlord в ваш проект
```

## Быстрый старт

```python
from modules.Graph_Overlord import (
    InterestNode,
    Edge,
    EdgeType,
    InterestGraph,
    TemplateManager,
    GraphCalculator,
)

# Создание графа
graph = InterestGraph()

# Добавление корневого узла
root = InterestNode(id="interests", name="Мои интересы", is_category=True)
graph.add_node(root)

# Использование шаблонов
manager = TemplateManager()
manager.create_builtin_templates()  # Спорт, игры, творчество

# Вставка шаблона "Спорт"
sports_template = manager.get_template("sports")
manager.insert_template(sports_template, graph, parent_node_id="interests")

# Пользователь оценивает некоторые узлы
chess_node = next(n for n in graph.nodes.values() if "chess" in n.id)
chess_node.user_att = 90.0
chess_node.user_int = 85.0

# Запуск пересчёта
calculator = GraphCalculator(graph)
iterations = calculator.calculate()

print(f"Пересчёт выполнен за {iterations} итераций")

# Просмотр результатов
for node in graph.nodes.values():
    if node.int > 50 and node.att > 0:
        print(f"{node.name}: Att={node.att:.1f}, Int={node.int:.1f}")
```

## Основные компоненты

### InterestNode

Узел графа интересов.

```python
node = InterestNode(
    id="unique_id",           # Уникальный идентификатор
    name="Название",          # Человекочитаемое название
    is_category=True,         # Является ли категорией
    user_att=80.0,           # Оценка отношения пользователем
    user_int=70.0,           # Оценка интереса пользователем
    locked=False,            # Заблокирован ли узел
    active=True,             # Активен ли узел
)
```

### Edge

Связь между узлами.

```python
# Иерархическая связь (родитель → ребёнок)
edge = Edge.create_parent_edge(
    source_id="parent",
    target_id="child",
    att_level='medium_positive',  # Сила влияния на отношение
    int_level='medium',           # Сила влияния на интерес
)

# Ассоциативная связь
edge = Edge.create_association_edge(
    source_id="node1",
    target_id="node2",
    att_level='strong_positive',
    int_level='strong',
    bidirectional=True,
)
```

#### Уровни силы связей

**Для Attitude:**
- `strong_positive`: +0.9
- `medium_positive`: +0.7 (по умолчанию)
- `weak_positive`: +0.4
- `neutral`: 0.0
- `weak_negative`: -0.4
- `medium_negative`: -0.7
- `strong_negative`: -0.9

**Для Interest:**
- `full`: 1.0
- `strong`: 0.8
- `medium`: 0.6 (по умолчанию)
- `weak`: 0.3
- `minimal`: 0.1
- `none`: 0.0

### InterestGraph

Основная структура графа.

```python
graph = InterestGraph()

# Добавление узлов и рёбер
graph.add_node(node)
graph.add_edge(edge)

# Управление активностью
graph.set_node_active("node_id", False, recursive=True)

# Проверка активности
if graph.is_node_effectively_active("node_id"):
    ...

# Сериализация
json_str = graph.to_json()
graph.save_to_file("graph.json")

# Десериализация
graph = InterestGraph.from_json(json_str)
graph = InterestGraph.load_from_file("graph.json")
```

### GraphCalculator

Алгоритм распространения оценок.

```python
calculator = GraphCalculator(
    graph,
    config=CalculatorConfig(
        alpha_parent=0.4,      # Коэффициент влияния родителя
        alpha_child=0.3,       # Коэффициент влияния детей
        alpha_assoc=0.5,       # Коэффициент ассоциативных связей
        damping=0.4,           # Фактор демпфирования
        epsilon=0.1,           # Порог сходимости
        max_iterations=100,    # Максимум итераций
    )
)

iterations = calculator.calculate()
```

### TemplateManager

Управление шаблонами графов.

```python
manager = TemplateManager()
manager.create_builtin_templates()  # Создать встроенные шаблоны

# Получить шаблон
sports = manager.get_template("sports")

# Вставить шаблон в граф
inserted_ids = manager.insert_template(
    sports,
    graph,
    parent_node_id="root_node_id"
)

# Сохранить/загрузить шаблон
manager.save_template_to_file("sports", "sports_template.json")
manager.load_template_from_file("custom_template.json")
```

## Встроенные шаблоны

- **sports** - Спорт и физические активности
  - Командные виды (футбол, баскетбол)
  - Индивидуальные виды (теннис, плавание, бег)

- **intellectual_games** - Интеллектуальные игры
  - Настольные игры (шахматы, го, головоломки)
  - Стратегические игры

- **creative_arts** - Творчество и искусство
  - Визуальное искусство (рисование, живопись, фотография)
  - Музыка (инструменты, композиция)
  - Письмо (проза, поэзия)

## Алгоритм распространения

1. **Инициализация**: Узлы с пользовательскими оценками инициализируются этими значениями
2. **Итеративный цикл**:
   - Вычисление сетевых сигналов от родителей, детей и ассоциаций
   - Применение межосевого влияния (Int → Att, Att → Int)
   - Компромисс между пользовательским вводом и сетевыми сигналами
   - Демпфирование изменений
   - Применение функций активации (tanh для Att, sigmoid для Int)
3. **Расчёт неопределённости**: Выявление узлов с противоречивыми сигналами

## API Reference

Полная документация по классам и методам доступна в исходном коде через docstrings.

## Тестирование

```bash
python modules/Graph_Overlord/test_graph_overlord.py
```

## Лицензия

MIT
