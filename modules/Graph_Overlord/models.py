"""
Data models for Graph_Overlord module.
Defines InterestNode, Edge, GraphModel, and Project classes.
"""

import uuid
import math
from typing import Optional, Dict, List, Set, Any, Tuple
from dataclasses import dataclass, field
from .constants import (
    ATT_LEVELS, INT_LEVELS, DEFAULT_ATT_LEVEL, DEFAULT_INT_LEVEL,
    DEFAULT_ALPHA_PARENT, DEFAULT_ALPHA_CHILD, DEFAULT_ALPHA_ASSOC,
    DEFAULT_K_INT_TO_ATT, DEFAULT_K_ATT_TO_INT, DEFAULT_DAMPING,
    DEFAULT_D_THRESHOLD, DEFAULT_EPSILON, DEFAULT_TAU_ATT, DEFAULT_TAU_INT
)


@dataclass
class InterestNode:
    """
    Represents a node in the interest graph.
    
    Attributes:
        id: Unique identifier (string or number)
        name: Human-readable name
        is_category: True if node can have children
        att: Final attitude [-100, 100]
        int: Final interest [0, 100]
        user_att: User-provided attitude (or None)
        user_int: User-provided interest (or None)
        user_weight_override: Manual weight override (0..1 or special), or None
        locked: If True, node is not recalculated
        active: If False, node and subtree are excluded from calculations
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    is_category: bool = True
    att: float = 0.0
    int: float = 0.0
    user_att: Optional[float] = None
    user_int: Optional[float] = None
    user_weight_override: Optional[float] = None
    locked: bool = False
    active: bool = True
    
    # Runtime state (not serialized directly)
    _conflict_score: float = 0.0
    _weak_signal: bool = False
    _net_w_att: float = 0.0
    _net_w_int: float = 0.0
    
    def __post_init__(self):
        """Initialize derived values and validate ranges."""
        self._normalize_values()
        if self.user_att is not None or self.user_int is not None:
            self._initialize_missing_axis()
    
    def _normalize_values(self):
        """Ensure att and int are within valid ranges."""
        self.att = max(-100.0, min(100.0, self.att))
        self.int = max(0.0, min(100.0, self.int))
        if self.user_att is not None:
            self.user_att = max(-100.0, min(100.0, self.user_att))
        if self.user_int is not None:
            self.user_int = max(0.0, min(100.0, self.user_int))
    
    def _initialize_missing_axis(self):
        """
        If only one axis is provided by user, compute initial value for the other.
        int = max(0, att) * 0.7
        att = int - 50 (heuristic)
        """
        if self.user_att is not None and self.user_int is None:
            # Compute initial int from att
            self.int = max(0, self.user_att) * 0.7
        elif self.user_int is not None and self.user_att is None:
            # Compute initial att from int
            self.att = self.user_int - 50
    
    def get_user_weight_att(self) -> float:
        """
        Get user weight for Att axis.
        Returns infinity if locked, computed weight otherwise.
        """
        if self.locked:
            return float('inf')
        if self.user_weight_override is not None:
            return self.user_weight_override
        if self.user_att is not None:
            return abs(self.user_att) / 100.0
        return 0.0
    
    def get_user_weight_int(self) -> float:
        """
        Get user weight for Int axis.
        Returns infinity if locked, computed weight otherwise.
        """
        if self.locked:
            return float('inf')
        if self.user_weight_override is not None:
            return self.user_weight_override
        if self.user_int is not None:
            return self.user_int / 100.0
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'is_category': self.is_category,
            'att': self.att,
            'int': self.int,
            'user_att': self.user_att,
            'user_int': self.user_int,
            'user_weight_override': self.user_weight_override,
            'locked': self.locked,
            'active': self.active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterestNode':
        """Deserialize node from dictionary."""
        return cls(**data)


@dataclass
class Edge:
    """
    Represents a connection between two nodes.
    
    Attributes:
        source_id: ID of source node
        target_id: ID of target node
        type: 'parent' (hierarchy) or 'association'
        
        For parent type:
            w_down_att, w_down_int: Parent -> Child influence
            w_up_att, w_up_int: Child -> Parent influence
        
        For association type:
            fw_att, fw_int: Source -> Target influence
            bw_att, bw_int: Target -> Source influence
    """
    source_id: str
    target_id: str
    type: str  # 'parent' or 'association'
    
    # Parent edge weights
    w_down_att: float = 0.7
    w_down_int: float = 0.6
    w_up_att: float = 0.5
    w_up_int: float = 0.5
    
    # Association edge weights
    fw_att: float = 0.7
    fw_int: float = 0.6
    bw_att: float = 0.7
    bw_int: float = 0.6
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate edge type and normalize weights."""
        if self.type not in ('parent', 'association'):
            raise ValueError(f"Invalid edge type: {self.type}. Must be 'parent' or 'association'.")
    
    def set_att_level(self, level_name: str, weight_type: str):
        """
        Set Att weight using discrete level.
        weight_type: 'w_down', 'w_up', 'fw', 'bw'
        """
        if level_name not in ATT_LEVELS:
            raise ValueError(f"Invalid Att level: {level_name}")
        value = ATT_LEVELS[level_name]
        attr_name = f"{weight_type}_att"
        setattr(self, attr_name, value)
    
    def set_int_level(self, level_name: str, weight_type: str):
        """
        Set Int weight using discrete level.
        weight_type: 'w_down', 'w_up', 'fw', 'bw'
        """
        if level_name not in INT_LEVELS:
            raise ValueError(f"Invalid Int level: {level_name}")
        value = INT_LEVELS[level_name]
        attr_name = f"{weight_type}_int"
        setattr(self, attr_name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize edge to dictionary."""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type,
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Deserialize edge from dictionary."""
        return cls(**data)


class GraphModel:
    """
    Manages the graph structure including nodes, edges, and trees.
    Provides methods for graph manipulation and querying.
    """
    
    def __init__(self):
        self.nodes: Dict[str, InterestNode] = {}
        self.edges: Dict[str, Edge] = {}
        self.trees: Dict[str, str] = {}  # tree_name -> root_node_id
        
        # Adjacency lists for efficient traversal
        self._children: Dict[str, List[str]] = {}  # parent_id -> [child_ids]
        self._parents: Dict[str, Optional[str]] = {}  # child_id -> parent_id
        self._associations_out: Dict[str, List[str]] = {}  # source_id -> [target_ids]
        self._associations_in: Dict[str, List[str]] = {}  # target_id -> [source_ids]
    
    def add_node(self, node: InterestNode, parent_id: Optional[str] = None, tree_name: Optional[str] = None) -> str:
        """
        Add a node to the graph.
        If parent_id is provided, creates a parent edge.
        If tree_name is provided and node is root, registers it as tree root.
        """
        self.nodes[node.id] = node
        self._children[node.id] = []
        self._parents[node.id] = None
        self._associations_out[node.id] = []
        self._associations_in[node.id] = []
        
        if parent_id is not None:
            if parent_id not in self.nodes:
                raise ValueError(f"Parent node {parent_id} does not exist")
            self.add_edge(parent_id, node.id, 'parent')
        
        if tree_name is not None and parent_id is None:
            self.trees[tree_name] = node.id
        
        return node.id
    
    def remove_node(self, node_id: str):
        """
        Remove a node and all its connections.
        Also removes all descendants recursively.
        """
        if node_id not in self.nodes:
            return
        
        # Get all descendants first
        descendants = self.get_subtree(node_id)
        
        # Remove all edges connected to these nodes
        edges_to_remove = [
            eid for eid, edge in self.edges.items()
            if edge.source_id in descendants or edge.target_id in descendants
        ]
        for eid in edges_to_remove:
            del self.edges[eid]
        
        # Remove nodes
        for nid in descendants:
            del self.nodes[nid]
            del self._children[nid]
            del self._parents[nid]
            del self._associations_out[nid]
            del self._associations_in[nid]
        
        # Remove from trees
        trees_to_update = [tname for tname, root_id in self.trees.items() if root_id in descendants]
        for tname in trees_to_update:
            del self.trees[tname]
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str,
                 att_level: str = DEFAULT_ATT_LEVEL, 
                 int_level: str = DEFAULT_INT_LEVEL) -> str:
        """
        Add an edge between two nodes.
        For parent edges, ensures target has no existing parent.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Source or target node does not exist")
        
        if edge_type == 'parent':
            # Check if target already has a parent
            if self._parents.get(target_id) is not None:
                raise ValueError(f"Node {target_id} already has a parent")
            
            edge = Edge(source_id=source_id, target_id=target_id, type='parent')
            edge.set_att_level(att_level, 'w_down')
            edge.set_int_level(int_level, 'w_down')
            edge.set_att_level(att_level, 'w_up')
            edge.set_int_level(int_level, 'w_up')
            
            self._parents[target_id] = source_id
            self._children[source_id].append(target_id)
            
        elif edge_type == 'association':
            edge = Edge(source_id=source_id, target_id=target_id, type='association')
            edge.set_att_level(att_level, 'fw')
            edge.set_int_level(int_level, 'fw')
            edge.set_att_level(att_level, 'bw')
            edge.set_int_level(int_level, 'bw')
            
            self._associations_out[source_id].append(target_id)
            self._associations_in[target_id].append(source_id)
        else:
            raise ValueError(f"Invalid edge type: {edge_type}")
        
        self.edges[edge.id] = edge
        return edge.id
    
    def remove_edge(self, edge_id: str):
        """Remove an edge by ID."""
        if edge_id not in self.edges:
            return
        
        edge = self.edges[edge_id]
        
        if edge.type == 'parent':
            if edge.target_id in self._parents:
                self._parents[edge.target_id] = None
            if edge.source_id in self._children:
                if edge.target_id in self._children[edge.source_id]:
                    self._children[edge.source_id].remove(edge.target_id)
        elif edge.type == 'association':
            if edge.source_id in self._associations_out:
                if edge.target_id in self._associations_out[edge.source_id]:
                    self._associations_out[edge.source_id].remove(edge.target_id)
            if edge.target_id in self._associations_in:
                if edge.source_id in self._associations_in[edge.target_id]:
                    self._associations_in[edge.target_id].remove(edge.source_id)
        
        del self.edges[edge_id]
    
    def get_parent(self, node_id: str) -> Optional[str]:
        """Get parent node ID."""
        return self._parents.get(node_id)
    
    def get_children(self, node_id: str) -> List[str]:
        """Get list of child node IDs."""
        return self._children.get(node_id, [])
    
    def get_associations_out(self, node_id: str) -> List[str]:
        """Get list of nodes this node has outgoing associations to."""
        return self._associations_out.get(node_id, [])
    
    def get_associations_in(self, node_id: str) -> List[str]:
        """Get list of nodes that have associations pointing to this node."""
        return self._associations_in.get(node_id, [])
    
    def get_subtree(self, node_id: str) -> Set[str]:
        """Get all node IDs in the subtree rooted at node_id (inclusive)."""
        result = {node_id}
        for child_id in self.get_children(node_id):
            result.update(self.get_subtree(child_id))
        return result
    
    def is_active_effective(self, node_id: str) -> bool:
        """
        Check if node is effectively active.
        A node is inactive if its own active=False or any ancestor is inactive.
        """
        current_id = node_id
        visited = set()
        while current_id is not None:
            if current_id in visited:
                break  # Cycle detection (shouldn't happen in tree)
            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node is None:
                return False
            if not node.active:
                return False
            current_id = self._parents.get(current_id)
        return True
    
    def get_all_active_nodes(self) -> List[str]:
        """Get list of all effectively active node IDs."""
        return [nid for nid in self.nodes if self.is_active_effective(nid)]
    
    def get_root_nodes(self) -> List[str]:
        """Get all root nodes (nodes without parents)."""
        return [nid for nid, parent in self._parents.items() if parent is None]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire graph model."""
        return {
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'edges': {eid: edge.to_dict() for eid, edge in self.edges.items()},
            'trees': self.trees,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphModel':
        """Deserialize graph model from dictionary."""
        model = cls()
        
        # Load nodes first
        for nid, node_data in data.get('nodes', {}).items():
            node = InterestNode.from_dict(node_data)
            model.nodes[nid] = node
            model._children[nid] = []
            model._parents[nid] = None
            model._associations_out[nid] = []
            model._associations_in[nid] = []
        
        # Load edges
        for eid, edge_data in data.get('edges', {}).items():
            edge = Edge.from_dict(edge_data)
            model.edges[eid] = edge
            
            if edge.type == 'parent':
                model._parents[edge.target_id] = edge.source_id
                model._children[edge.source_id].append(edge.target_id)
            elif edge.type == 'association':
                model._associations_out[edge.source_id].append(edge.target_id)
                model._associations_in[edge.target_id].append(edge.source_id)
        
        # Load trees
        model.trees = data.get('trees', {})
        
        return model


class Project:
    """
    Top-level container for the entire project.
    Contains one or more GraphModel instances (trees) and metadata.
    """
    
    def __init__(self, name: str = "Untitled Project"):
        self.name = name
        self.graph = GraphModel()
        self.favorites: Set[str] = set()  # Set of favorite node IDs
        self.settings: Dict[str, Any] = {}
    
    def add_favorite(self, node_id: str):
        """Add node to favorites."""
        if node_id in self.graph.nodes:
            self.favorites.add(node_id)
    
    def remove_favorite(self, node_id: str):
        """Remove node from favorites."""
        self.favorites.discard(node_id)
    
    def is_favorite(self, node_id: str) -> bool:
        """Check if node is in favorites."""
        return node_id in self.favorites
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize project to dictionary."""
        return {
            'name': self.name,
            'graph': self.graph.to_dict(),
            'favorites': list(self.favorites),
            'settings': self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Deserialize project from dictionary."""
        project = cls(name=data.get('name', 'Untitled Project'))
        project.graph = GraphModel.from_dict(data.get('graph', {}))
        project.favorites = set(data.get('favorites', []))
        project.settings = data.get('settings', {})
        return project
