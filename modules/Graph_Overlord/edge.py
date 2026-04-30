"""
Edge - Represents a connection between nodes in the interest graph.

Two types of edges:
- parent: Hierarchical relationship (tree structure)
- association: Associative relationship (arbitrary connections)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EdgeType(Enum):
    """Type of edge connection."""
    PARENT = "parent"
    ASSOCIATION = "association"


# Discrete levels for Attitude-related weights
ATT_WEIGHT_LEVELS = {
    'strong_positive': 0.9,
    'medium_positive': 0.7,
    'weak_positive': 0.4,
    'neutral': 0.0,
    'weak_negative': -0.4,
    'medium_negative': -0.7,
    'strong_negative': -0.9,
}

# Discrete levels for Interest-related weights
INT_WEIGHT_LEVELS = {
    'full': 1.0,
    'strong': 0.8,
    'medium': 0.6,
    'weak': 0.3,
    'minimal': 0.1,
    'none': 0.0,
}


@dataclass
class Edge:
    """Represents an edge between two nodes."""
    
    source_id: str
    target_id: str
    type: EdgeType
    
    # For parent edges (hierarchical)
    w_down_att: float = 0.7  # Parent -> Child attitude weight
    w_down_int: float = 0.6  # Parent -> Child interest weight
    w_up_att: float = 0.5    # Child -> Parent attitude weight
    w_up_int: float = 0.5    # Child -> Parent interest weight
    
    # For association edges (bidirectional influence)
    fw_att: float = 0.7      # Forward attitude weight (source -> target)
    fw_int: float = 0.6      # Forward interest weight (source -> target)
    bw_att: float = 0.7      # Backward attitude weight (target -> source)
    bw_int: float = 0.6      # Backward interest weight (target -> source)
    
    def __post_init__(self):
        """Validate edge configuration."""
        if self.type == EdgeType.PARENT:
            # Parent edges should not have association weights used
            pass
        elif self.type == EdgeType.ASSOCIATION:
            # Association edges use fw/bw weights
            pass
    
    @classmethod
    def create_parent_edge(
        cls,
        source_id: str,
        target_id: str,
        att_level: str = 'medium_positive',
        int_level: str = 'medium'
    ) -> 'Edge':
        """Create a parent edge with discrete weight levels."""
        return cls(
            source_id=source_id,
            target_id=target_id,
            type=EdgeType.PARENT,
            w_down_att=ATT_WEIGHT_LEVELS.get(att_level, 0.7),
            w_down_int=INT_WEIGHT_LEVELS.get(int_level, 0.6),
            w_up_att=ATT_WEIGHT_LEVELS.get(att_level, 0.5),
            w_up_int=INT_WEIGHT_LEVELS.get(int_level, 0.5),
        )
    
    @classmethod
    def create_association_edge(
        cls,
        source_id: str,
        target_id: str,
        att_level: str = 'medium_positive',
        int_level: str = 'medium',
        bidirectional: bool = True
    ) -> 'Edge':
        """Create an association edge with discrete weight levels."""
        att_weight = ATT_WEIGHT_LEVELS.get(att_level, 0.7)
        int_weight = INT_WEIGHT_LEVELS.get(int_level, 0.6)
        
        return cls(
            source_id=source_id,
            target_id=target_id,
            type=EdgeType.ASSOCIATION,
            fw_att=att_weight,
            fw_int=int_weight,
            bw_att=att_weight if bidirectional else 0.0,
            bw_int=int_weight if bidirectional else 0.0,
        )
    
    def get_forward_weights(self) -> tuple[float, float]:
        """Get forward weights (att, int) based on edge type."""
        if self.type == EdgeType.PARENT:
            return (self.w_down_att, self.w_down_int)
        else:
            return (self.fw_att, self.fw_int)
    
    def get_backward_weights(self) -> tuple[float, float]:
        """Get backward weights (att, int) based on edge type."""
        if self.type == EdgeType.PARENT:
            return (self.w_up_att, self.w_up_int)
        else:
            return (self.bw_att, self.bw_int)
    
    def to_dict(self) -> dict:
        """Serialize edge to dictionary."""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type.value,
            'w_down_att': self.w_down_att,
            'w_down_int': self.w_down_int,
            'w_up_att': self.w_up_att,
            'w_up_int': self.w_up_int,
            'fw_att': self.fw_att,
            'fw_int': self.fw_int,
            'bw_att': self.bw_att,
            'bw_int': self.bw_int,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Edge':
        """Deserialize edge from dictionary."""
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            type=EdgeType(data['type']),
            w_down_att=data.get('w_down_att', 0.7),
            w_down_int=data.get('w_down_int', 0.6),
            w_up_att=data.get('w_up_att', 0.5),
            w_up_int=data.get('w_up_int', 0.5),
            fw_att=data.get('fw_att', 0.7),
            fw_int=data.get('fw_int', 0.6),
            bw_att=data.get('bw_att', 0.7),
            bw_int=data.get('bw_int', 0.6),
        )
