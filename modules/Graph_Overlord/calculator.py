"""
GraphCalculator - Implements the iterative propagation algorithm.

Computes Attitude and Interest values for all nodes based on:
- User-provided evaluations
- Network propagation through edges
- Damping and saturation functions
"""

import math
from typing import Optional
from dataclasses import dataclass

# Handle both package import and direct script execution
try:
    from .graph import InterestGraph
    from .interest_node import InterestNode
    from .edge import Edge, EdgeType
except ImportError:
    from graph import InterestGraph
    from interest_node import InterestNode
    from edge import Edge, EdgeType


@dataclass
class CalculatorConfig:
    """Configuration for the graph calculator."""
    
    # Global coefficients for signal aggregation
    alpha_parent: float = 0.4
    alpha_child: float = 0.3
    alpha_assoc: float = 0.5
    
    # Cross-axis influence coefficients
    k_int_to_att: float = 0.1
    k_att_to_int: float = 0.3
    
    # Damping factor for iterative updates
    damping: float = 0.4
    
    # Convergence threshold
    epsilon: float = 0.1
    
    # Maximum iterations to prevent infinite loops
    max_iterations: int = 100
    
    # Temperature parameters for activation functions
    tau_att: float = 50.0
    tau_int: float = 50.0
    
    # Conflict detection threshold
    conflict_threshold: float = 10.0
    
    # Weak signal threshold
    weak_signal_threshold: float = 0.3
    
    # Variance penalty threshold for parent attitude
    variance_threshold: float = 25.0


class GraphCalculator:
    """Calculates node values using iterative propagation."""
    
    def __init__(self, graph: InterestGraph, config: Optional[CalculatorConfig] = None):
        """Initialize calculator with graph and optional configuration."""
        self.graph = graph
        self.config = config or CalculatorConfig()
    
    def calculate(self) -> int:
        """
        Run the iterative calculation until convergence.
        
        Returns:
            Number of iterations performed
        """
        # Initialize all active nodes
        self._initialize()
        
        iterations = 0
        for iteration in range(self.config.max_iterations):
            iterations += 1
            
            # Save current state for change detection
            for node_id in self.graph.get_active_nodes():
                self.graph.nodes[node_id].save_state()
            
            # Update all active, non-locked nodes
            max_change = 0.0
            for node_id in self.graph.get_active_nodes():
                node = self.graph.nodes[node_id]
                
                if node.locked:
                    continue
                
                # Compute network signals
                net_att, net_int, att_weights_sum, int_weights_sum = self._compute_network_signals(node_id)
                
                # Apply cross-axis influence
                net_att += self.config.k_int_to_att * (node.int / 100.0) * 50.0
                net_att_int_contrib = self.config.k_att_to_int * max(node.att, 0) * 0.5
                net_int += net_att_int_contrib
                
                # Compromise with user input
                computed_att = self._compromise_with_user(
                    node, 'att', net_att, att_weights_sum
                )
                computed_int = self._compromise_with_user(
                    node, 'int', net_int, int_weights_sum
                )
                
                # Apply damping
                new_att = node.att + self.config.damping * (computed_att - node.att)
                new_int = node.int + self.config.damping * (computed_int - node.int)
                
                # Apply activation and clamping
                node.att = self._clamp_att(new_att)
                node.int = self._clamp_int(new_int)
                
                # Track maximum change
                change_att, change_int = node.get_change()
                max_change = max(max_change, change_att, change_int)
            
            # Check convergence
            if max_change < self.config.epsilon:
                break
        
        # Calculate uncertainty scores after convergence
        self._calculate_uncertainty()
        
        return iterations
    
    def _initialize(self) -> None:
        """Initialize node values before calculation."""
        for node_id in self.graph.get_active_nodes():
            node = self.graph.nodes[node_id]
            
            # Set inactive nodes to zero (they won't be calculated anyway)
            if not self.graph.is_node_effectively_active(node_id):
                node.att = 0.0
                node.int = 0.0
                continue
            
            # Initialize from user values if present
            if node.user_att is not None:
                node.att = node.user_att
            if node.user_int is not None:
                node.int = node.user_int
            
            # If only one axis provided, compute the other
            if node.user_att is not None and node.user_int is None:
                node.int = max(0, node.user_att) * 0.7
            elif node.user_int is not None and node.user_att is None:
                node.att = node.user_int - 50
    
    def _compute_network_signals(
        self, node_id: str
    ) -> tuple[float, float, float, float]:
        """
        Compute network signals for a node.
        
        Returns:
            Tuple of (net_att, net_int, att_weights_sum, int_weights_sum)
        """
        node = self.graph.nodes[node_id]
        net_att = 0.0
        net_int = 0.0
        att_weights_sum = 0.0
        int_weights_sum = 0.0
        
        # Parent contribution
        parent_id = self.graph.get_parent(node_id)
        if parent_id and self.graph.is_node_effectively_active(parent_id):
            parent = self.graph.nodes[parent_id]
            # Find the edge
            for edge in self.graph.edges:
                if edge.type == EdgeType.PARENT and edge.target_id == node_id:
                    w_att, w_int = edge.get_forward_weights()
                    net_att += parent.att * w_att
                    net_int += parent.int * w_int
                    att_weights_sum += abs(w_att)
                    int_weights_sum += abs(w_int)
                    break
        
        # Children contribution (only if category)
        if node.is_category:
            children_att_values = []
            for child_id in self.graph.get_children(node_id):
                if not self.graph.is_node_effectively_active(child_id):
                    continue
                    
                child = self.graph.nodes[child_id]
                # Find the edge
                for edge in self.graph.edges:
                    if edge.type == EdgeType.PARENT and edge.source_id == node_id:
                        w_att, w_int = edge.get_backward_weights()
                        net_att += child.att * w_att
                        net_int += child.int * w_int
                        att_weights_sum += abs(w_att)
                        int_weights_sum += abs(w_int)
                        children_att_values.append(child.att)
                        break
            
            # Apply conflict penalty for parent attitude
            if len(children_att_values) > 1:
                variance = self._compute_variance(children_att_values)
                if variance > self.config.variance_threshold:
                    penalty = 1.0 - min(variance / 100.0, 0.5)
                    # Re-compute children att contribution with penalty
                    children_att_sum = sum(
                        self.graph.nodes[cid].att * 
                        next((e.w_up_att for e in self.graph.edges 
                              if e.type == EdgeType.PARENT and e.source_id == node_id and e.target_id == cid), 0)
                        for cid in self.graph.get_children(node_id)
                        if self.graph.is_node_effectively_active(cid)
                    )
                    net_att = net_att - children_att_sum + children_att_sum * penalty
        
        # Association contributions
        for connected_id, edge in self.graph.get_associations(node_id):
            if not self.graph.is_node_effectively_active(connected_id):
                continue
            
            connected_node = self.graph.nodes[connected_id]
            
            # Determine which weights to use based on edge direction
            if edge.source_id == node_id:
                # Backward influence (target -> source)
                w_att, w_int = edge.get_backward_weights()
            else:
                # Forward influence (source -> target)
                w_att, w_int = edge.get_forward_weights()
            
            net_att += connected_node.att * w_att
            net_int += connected_node.int * w_int
            att_weights_sum += abs(w_att)
            int_weights_sum += abs(w_int)
        
        # Apply alpha coefficients
        net_att *= self.config.alpha_parent + self.config.alpha_child + self.config.alpha_assoc
        net_int *= self.config.alpha_parent + self.config.alpha_child + self.config.alpha_assoc
        
        return net_att, net_int, att_weights_sum, int_weights_sum
    
    def _compromise_with_user(
        self, node: InterestNode, axis: str, net_value: float, net_weight: float
    ) -> float:
        """Compute compromise between user input and network signal."""
        user_value = node.user_att if axis == 'att' else node.user_int
        user_weight = node.user_weight_att if axis == 'att' else node.user_weight_int
        
        if node.locked and user_value is not None:
            return user_value
        
        if user_value is None:
            return net_value
        
        # Use default network weight if not computed
        if net_weight < 0.001:
            net_weight = 0.5
        
        return (user_weight * user_value + net_weight * net_value) / (user_weight + net_weight)
    
    def _clamp_att(self, value: float) -> float:
        """Clamp attitude value to [-100, 100] with tanh activation."""
        # Apply tanh activation scaled to [-100, 100]
        activated = math.tanh(value / self.config.tau_att) * 100.0
        return max(-100.0, min(100.0, activated))
    
    def _clamp_int(self, value: float) -> float:
        """Clamp interest value to [0, 100] with sigmoid activation."""
        # Apply sigmoid activation scaled to [0, 100]
        if value < -100:  # Prevent overflow
            activated = 0.0
        elif value > 100:
            activated = 100.0
        else:
            activated = 1.0 / (1.0 + math.exp(-value / self.config.tau_int)) * 100.0
        return max(0.0, min(100.0, activated))
    
    def _compute_variance(self, values: list[float]) -> float:
        """Compute variance of a list of values."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)
    
    def _calculate_uncertainty(self) -> None:
        """Calculate uncertainty scores for all active nodes."""
        for node_id in self.graph.get_active_nodes():
            node = self.graph.nodes[node_id]
            
            # Collect incoming signal values for conflict detection
            att_signals = []
            total_weight = 0.0
            
            # From parent
            parent_id = self.graph.get_parent(node_id)
            if parent_id and self.graph.is_node_effectively_active(parent_id):
                for edge in self.graph.edges:
                    if edge.type == EdgeType.PARENT and edge.target_id == node_id:
                        w_att, _ = edge.get_forward_weights()
                        att_signals.append(self.graph.nodes[parent_id].att * w_att)
                        total_weight += abs(w_att)
                        break
            
            # From children
            for child_id in self.graph.get_children(node_id):
                if not self.graph.is_node_effectively_active(child_id):
                    continue
                for edge in self.graph.edges:
                    if edge.type == EdgeType.PARENT and edge.source_id == node_id:
                        w_att, _ = edge.get_backward_weights()
                        att_signals.append(self.graph.nodes[child_id].att * w_att)
                        total_weight += abs(w_att)
                        break
            
            # From associations
            for connected_id, edge in self.graph.get_associations(node_id):
                if not self.graph.is_node_effectively_active(connected_id):
                    continue
                if edge.source_id == node_id:
                    w_att, _ = edge.get_backward_weights()
                else:
                    w_att, _ = edge.get_forward_weights()
                att_signals.append(self.graph.nodes[connected_id].att * w_att)
                total_weight += abs(w_att)
            
            # Calculate conflict score (variance of incoming signals)
            conflict_score = self._compute_variance(att_signals) if len(att_signals) > 1 else 0.0
            
            # Detect weak signal
            weak_signal = total_weight < self.config.weak_signal_threshold
            
            # Mark node
            node.mark_uncertain(conflict_score, weak_signal)
    
    def get_uncertainty(self, node_id: str) -> tuple[float, bool]:
        """
        Get uncertainty information for a specific node.
        
        Returns:
            Tuple of (conflict_score, is_weak_signal)
        """
        node = self.graph.nodes.get(node_id)
        if not node:
            return (0.0, False)
        
        return (node.conflict_score or 0.0, node.weak_signal or False)
