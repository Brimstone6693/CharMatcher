# file: modules/Tag_Hierarch/core/status_calculator.py
"""
Модуль расчёта статусов элементов на основе зависимостей.
"""

from typing import Dict, List, Any, Optional
from modules.Tag_Hierarch.core.config import BASE_WEIGHTS


def calculate_constraint_strength(statuses: List[int]) -> float:
    """Вычисляет силу ограничения как среднее арифметическое абсолютных значений базовых весов."""
    if not statuses:
        return 0.0
    total = sum(abs(BASE_WEIGHTS.get(s, 0)) for s in statuses)
    return total / len(statuses)


class StatusCalculator:
    """Класс для расчёта статусов элементов на основе зависимостей."""
    
    @staticmethod
    def recalculate_states(manager) -> None:
        """
        Пересчитывает статусы всех элементов с использованием системы весов.
        
        Алгоритм:
        1. Топологическая сортировка для учёта зависимостей
        2. Для каждого элемента:
           - Если полный ручной режим -> используем custom_status напрямую
           - Если есть custom_status (но не ручной режим) -> используем его
           - Иначе вычисляем статус через агрегацию ограничений
        """
        visited, temp_mark, order = set(), set(), []

        def visit(eid):
            if eid in temp_mark:
                return
            if eid in visited:
                return
            temp_mark.add(eid)
            lid = manager._global_elements.get(eid)
            if lid and eid in manager.lists[lid].elements:
                for dep_id in manager.lists[lid].elements[eid].depends_on.keys():
                    visit(dep_id)
            temp_mark.remove(eid)
            visited.add(eid)
            order.append(eid)

        all_elements = [eid for lst in manager.lists.values() for eid in lst.elements.keys()]
        for eid in all_elements:
            if eid not in visited:
                visit(eid)

        for eid in order:
            lid = manager._global_elements.get(eid)
            if not lid:
                continue
            elem = manager.lists[lid].elements[eid]
            
            # Полный ручной режим - игнорируем зависимости
            if elem.metadata.get("manual_override", False):
                if elem.custom_status is not None:
                    elem.status = max(-3, min(3, elem.custom_status))
                continue
            
            # Если установлен ручной статус (но не полный ручной режим)
            if elem.custom_status is not None:
                elem.status = max(-3, min(3, elem.custom_status))
                continue

            # Собираем ограничения от зависимостей
            constraints = []
            
            # Ограничение от родителя
            if elem.parent_id:
                parent_lid = manager._global_elements.get(elem.parent_id)
                if parent_lid and elem.parent_id in manager.lists[parent_lid].elements:
                    parent_status = manager.lists[parent_lid].elements[elem.parent_id].status
                    constraints.append({
                        "range": (-3, parent_status),
                        "force": abs(BASE_WEIGHTS[parent_status])
                    })

            # Ограничения от зависимостей
            for dep_id, dep_type in elem.depends_on.items():
                dep_lid = manager._global_elements.get(dep_id)
                if not dep_lid or dep_id not in manager.lists[dep_lid].elements:
                    continue
                s = manager.lists[dep_lid].elements[dep_id].status
                
                StatusCalculator._add_dependency_constraint(constraints, dep_type, s)

            # Если нет ограничений, статус 0
            if not constraints:
                elem.status = 0
                continue

            # Расчёт Score для каждого статуса
            scores = {}
            for status in range(-3, 4):
                score = 0.0
                for constraint in constraints:
                    low, high = constraint["range"]
                    if low <= status <= high:
                        score += constraint["force"]
                scores[status] = score

            # Выбор статуса с максимальным Score
            max_score = max(scores.values())
            candidates = [s for s, sc in scores.items() if sc == max_score]

            if len(candidates) == 1:
                elem.status = candidates[0]
            else:
                # Tie-breaking: предпочтение статусу с большим |BASE_WEIGHTS|
                candidates.sort(key=lambda s: (-abs(BASE_WEIGHTS[s]), -s))
                elem.status = candidates[0]

            # Если суммарная сила всех ограничений равна нулю
            total_force = sum(c["force"] for c in constraints)
            if total_force == 0:
                elem.status = 0
    
    @staticmethod
    def _add_dependency_constraint(constraints: List[Dict], dep_type: str, s: int) -> None:
        """Добавляет ограничение на основе типа зависимости."""
        if dep_type == "EQ":
            # Диапазон: {s}, Сила: |BASE_WEIGHTS[s]|
            constraints.append({
                "range": (s, s),
                "force": abs(BASE_WEIGHTS[s])
            })
        elif dep_type == "PM1":
            # Диапазон: [s-1, s+1], Сила: 4 если s=±3, иначе |BASE_WEIGHTS[s]|
            low = max(-3, s - 1)
            high = min(3, s + 1)
            force = 4 if abs(s) == 3 else abs(BASE_WEIGHTS[s])
            constraints.append({
                "range": (low, high),
                "force": force
            })
        elif dep_type == "LE":
            # Диапазон: [-3, s], Сила: среднее |BASE_WEIGHTS| от -3 до s
            weights_in_range = [abs(BASE_WEIGHTS[i]) for i in range(-3, s + 1)]
            force = sum(weights_in_range) / len(weights_in_range) if weights_in_range else 0
            constraints.append({
                "range": (-3, s),
                "force": force
            })
        elif dep_type == "GE":
            # Диапазон: [s, 3], Сила: среднее |BASE_WEIGHTS| от s до 3
            weights_in_range = [abs(BASE_WEIGHTS[i]) for i in range(s, 4)]
            force = sum(weights_in_range) / len(weights_in_range) if weights_in_range else 0
            constraints.append({
                "range": (s, 3),
                "force": force
            })
        elif dep_type == "WLE":
            # Слабое LE: диапазон [-3, s+1] (сдвиг +1), сила уменьшена вдвое
            adjusted_s = min(3, s + 1)
            weights_in_range = [abs(BASE_WEIGHTS[i]) for i in range(-3, adjusted_s + 1)]
            force = (sum(weights_in_range) / len(weights_in_range) if weights_in_range else 0) * 0.5
            constraints.append({
                "range": (-3, adjusted_s),
                "force": force
            })
        elif dep_type == "WGE":
            # Слабое GE: диапазон [s-1, 3] (сдвиг -1), сила уменьшена вдвое
            adjusted_s = max(-3, s - 1)
            weights_in_range = [abs(BASE_WEIGHTS[i]) for i in range(adjusted_s, 4)]
            force = (sum(weights_in_range) / len(weights_in_range) if weights_in_range else 0) * 0.5
            constraints.append({
                "range": (adjusted_s, 3),
                "force": force
            })
