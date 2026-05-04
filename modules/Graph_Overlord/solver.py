"""
Graph Overlord Solver Module.
Реализация алгоритма распространения оценок (Att/Int) по графу интересов.
"""

import math
from typing import Dict, List, Tuple, Optional
from .models import Project, InterestNode, Edge


class GraphSolver:
    """
    Класс для выполнения итеративных расчетов на графе интересов.
    """

    # Глобальные коэффициенты влияния (настраиваемые)
    ALPHA_PARENT = 0.4
    ALPHA_CHILD = 0.3
    ALPHA_ASSOC = 0.5

    # Коэффициенты межосевого влияния
    K_INT_TO_ATT = 0.1
    K_ATT_TO_INT = 0.3

    # Параметры демпфирования и активации
    DAMPING = 0.4
    TAU_ATT = 50.0  # Параметр масштаба для tanh
    TAU_INT = 25.0  # Параметр масштаба для sigmoid

    # Пороги
    EPSILON = 0.1  # Критерий сходимости
    D_THRESHOLD = 400.0  # Порог дисперсии для штрафа (примерно отклонение ~20 в квадрате)
    WEAK_SIGNAL_THRESHOLD = 0.2  # Порог слабого сигнала

    def __init__(self, project: Project):
        self.project = project
        self.graph = project.graph

    def solve(self) -> int:
        """
        Запускает процесс распространения оценок.
        Возвращает количество итераций, потребовавшихся для сходимости.
        """
        # 1. Инициализация
        self._initialize_nodes()

        iterations = 0
        max_iterations = 100  # Защита от бесконечного цикла

        while iterations < max_iterations:
            max_change = 0.0
            
            new_values: Dict[str, Tuple[float, float]] = {}

            active_nodes = [n for n in self.graph.nodes.values() if self._is_effectively_active(n)]

            for node in active_nodes:
                if node.locked:
                    new_values[node.id] = (node.att, node.int)
                    continue

                # Расчет сетевых сигналов
                net_att, net_int = self._calculate_network_signals(node)

                # Межосевое влияние
                net_att += self.K_INT_TO_ATT * (node.int / 100.0) * 50.0
                net_int += self.K_ATT_TO_INT * max(node.att, 0) * 0.5

                # Компромисс с пользовательским вводом
                final_att = self._compromise(node.att, node.user_att, node.get_user_weight_att(), net_att)
                final_int = self._compromise(node.int, node.user_int, node.get_user_weight_int(), net_int)

                # Демпфирование
                damped_att = node.att + self.DAMPING * (final_att - node.att)
                damped_int = node.int + self.DAMPING * (final_int - node.int)

                # Активация и ограничение
                activated_att = math.tanh(damped_att / self.TAU_ATT) * 100.0
                activated_att = max(-100.0, min(100.0, activated_att))

                sig_val = 1.0 / (1.0 + math.exp(-damped_int / self.TAU_INT))
                activated_int = sig_val * 100.0
                activated_int = max(0.0, min(100.0, activated_int))

                new_values[node.id] = (activated_att, activated_int)

                delta_att = abs(activated_att - node.att)
                delta_int = abs(activated_int - node.int)
                max_change = max(max_change, delta_att, delta_int)

            # Применение новых значений
            for node_id, (att, int_val) in new_values.items():
                node = self.graph.nodes[node_id]
                node.att = att
                node.int = int_val

            iterations += 1

            if max_change < self.EPSILON:
                break

        # Пост-обработка: расчет неопределенности
        self._calculate_uncertainty()

        return iterations

    def _is_effectively_active(self, node: InterestNode) -> bool:
        """Проверяет, активен ли узел эффективно (сам и все предки)."""
        if not node.active:
            return False
        
        current_id = node.id
        visited = set()
        while True:
            if current_id in visited:
                break
            visited.add(current_id)
            
            parent_id = self.graph.get_parent(current_id)
            if not parent_id:
                break
            
            parent_node = self.graph.nodes.get(parent_id)
            if not parent_node or not parent_node.active:
                return False
            
            current_id = parent_id
            
        return True

    def _initialize_nodes(self):
        """Шаг 5.1 ТЗ: Инициализация перед циклом."""
        for node in self.graph.nodes.values():
            if not self._is_effectively_active(node):
                node.att = 0.0
                node.int = 0.0
                continue

            # Эвристика заполнения отсутствующей оси
            if node.user_att is not None and node.user_int is None:
                val = node.user_att if node.locked else node.att
                node.int = max(0, val) * 0.7
            
            elif node.user_int is not None and node.user_att is None:
                val = node.user_int if node.locked else node.int
                node.att = val - 50.0

            if node.locked:
                if node.user_att is not None:
                    node.att = node.user_att
                if node.user_int is not None:
                    node.int = node.user_int

    def _get_edge_between(self, source_id: str, target_id: str) -> Optional[Edge]:
        """Находит ребро между двумя узлами."""
        for edge in self.graph.edges.values():
            if edge.source_id == source_id and edge.target_id == target_id:
                return edge
        return None

    def _calculate_network_signals(self, node: InterestNode) -> Tuple[float, float]:
        """Вычисляет суммарный сигнал от соседей."""
        
        comp_parent_att = 0.0
        comp_parent_int = 0.0
        comp_child_att = 0.0
        comp_child_int = 0.0
        comp_assoc_att = 0.0
        comp_assoc_int = 0.0

        # 1. Родитель
        parent_id = self.graph.get_parent(node.id)
        if parent_id:
            parent = self.graph.nodes.get(parent_id)
            edge = self._get_edge_between(parent_id, node.id)
            if parent and edge and self._is_effectively_active(parent):
                comp_parent_att = parent.att * edge.w_down_att
                comp_parent_int = parent.int * edge.w_down_int

        # 2. Дети
        child_ids = self.graph.get_children(node.id)
        child_atts = []
        for child_id in child_ids:
            child = self.graph.nodes.get(child_id)
            edge = self._get_edge_between(node.id, child_id)
            if child and edge and self._is_effectively_active(child):
                comp_child_att += child.att * edge.w_up_att
                comp_child_int += child.int * edge.w_up_int
                child_atts.append(child.att)
        
        # Штраф за дисперсию Att детей
        if len(child_atts) > 1:
            mean_att = sum(child_atts) / len(child_atts)
            variance = sum((x - mean_att) ** 2 for x in child_atts) / len(child_atts)
            if variance > self.D_THRESHOLD:
                penalty = 1.0 - min(variance / 100.0, 0.5)
                comp_child_att *= penalty

        # 3. Ассоциации
        # Исходящие
        out_assoc_ids = self.graph.get_associations_out(node.id)
        for target_id in out_assoc_ids:
            neighbor = self.graph.nodes.get(target_id)
            edge = self._get_edge_between(node.id, target_id)
            if neighbor and edge and self._is_effectively_active(neighbor):
                comp_assoc_att += neighbor.att * edge.fw_att
                comp_assoc_int += neighbor.int * edge.fw_int

        # Входящие
        in_assoc_ids = self.graph.get_associations_in(node.id)
        for source_id in in_assoc_ids:
            neighbor = self.graph.nodes.get(source_id)
            edge = self._get_edge_between(source_id, node.id)
            if neighbor and edge and self._is_effectively_active(neighbor):
                comp_assoc_att += neighbor.att * edge.bw_att
                comp_assoc_int += neighbor.int * edge.bw_int

        # Взвешенное суммирование
        net_att = (self.ALPHA_PARENT * comp_parent_att + 
                   self.ALPHA_CHILD * comp_child_att + 
                   self.ALPHA_ASSOC * comp_assoc_att)
        
        net_int = (self.ALPHA_PARENT * comp_parent_int + 
                   self.ALPHA_CHILD * comp_child_int + 
                   self.ALPHA_ASSOC * comp_assoc_int)

        return net_att, net_int

    def _compromise(self, current_val: float, user_val: Optional[float], 
                    user_weight: float, net_val: float) -> float:
        """Формула компромисса между пользовательским вводом и сетью."""
        if user_val is None:
            return net_val
        
        net_w = 0.5  # Константа силы сети
        
        if user_weight > 1000:  # Бесконечный вес (заблокирован)
            return user_val

        if (user_weight + net_w) == 0:
            return net_val

        return (user_weight * user_val + net_w * net_val) / (user_weight + net_w)

    def _calculate_uncertainty(self):
        """Вычисление показателей неопределенности после стабилизации."""
        for node in self.graph.nodes.values():
            if not self._is_effectively_active(node):
                continue
            
            incoming_atts = []
            total_weight = 0.0
            
            # От родителя
            parent_id = self.graph.get_parent(node.id)
            if parent_id:
                p = self.graph.nodes.get(parent_id)
                edge = self._get_edge_between(parent_id, node.id)
                if p and edge and p.active:
                    incoming_atts.append(p.att * edge.w_down_att)
                    total_weight += abs(edge.w_down_att)
            
            # От детей
            for child_id in self.graph.get_children(node.id):
                c = self.graph.nodes.get(child_id)
                edge = self._get_edge_between(node.id, child_id)
                if c and edge and c.active:
                    incoming_atts.append(c.att * edge.w_up_att)
                    total_weight += abs(edge.w_up_att)
                
            # От ассоциаций (исходящие)
            for target_id in self.graph.get_associations_out(node.id):
                neighbor = self.graph.nodes.get(target_id)
                edge = self._get_edge_between(node.id, target_id)
                if neighbor and edge and neighbor.active:
                    incoming_atts.append(neighbor.att * edge.fw_att)
                    total_weight += abs(edge.fw_att)
            
            # От ассоциаций (входящие)
            for source_id in self.graph.get_associations_in(node.id):
                neighbor = self.graph.nodes.get(source_id)
                edge = self._get_edge_between(source_id, node.id)
                if neighbor and edge and neighbor.active:
                    incoming_atts.append(neighbor.att * edge.bw_att)
                    total_weight += abs(edge.bw_att)
            
            conflict_score = 0.0
            if len(incoming_atts) > 1:
                mean = sum(incoming_atts) / len(incoming_atts)
                conflict_score = sum((x - mean) ** 2 for x in incoming_atts) / len(incoming_atts)
            
            weak_signal = total_weight < self.WEAK_SIGNAL_THRESHOLD
            
            # Сохраняем в атрибуты узла
            node._conflict_score = conflict_score
            node._weak_signal = weak_signal
            node._needs_review = conflict_score > self.D_THRESHOLD or weak_signal
