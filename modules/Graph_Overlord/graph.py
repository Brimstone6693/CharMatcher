"""
InterestGraph - Main graph structure for managing interest nodes and edges.

Provides methods for:
- Adding/removing nodes and edges
- Querying graph structure
- Serialization/deserialization
- Managing active/inactive subtrees
"""

import json
from typing import Optional
from collections import defaultdict

# Handle both package import and direct script execution
try:
    from .interest_node import InterestNode
    from .edge import Edge, EdgeType
except ImportError:
    from interest_node import InterestNode
    from edge import Edge, EdgeType


class InterestGraph:
    """Manages the interest graph structure."""
    
    def __init__(self):
        """Initialize empty graph."""
        self.nodes: dict[str, InterestNode] = {}
        self.edges: list[Edge] = []
        
        # Indexes for fast lookups
        self._parent_edges: dict[str, Edge] = {}  # child_id -> edge (each node has at most one parent)
        self._children_map: dict[str, list[str]] = defaultdict(list)  # parent_id -> [child_ids]
        self._association_edges: dict[str, list[Edge]] = defaultdict(list)  # node_id -> [edges]
    
    def add_node(self, node_id: str, name: str, is_category: bool = False, **kwargs) -> InterestNode:
        """Add a node to the graph. Returns the created node."""
        # Check if node already exists
        if node_id in self.nodes:
            return self.nodes[node_id]
        
        # Create node with provided parameters
        node = InterestNode(
            id=node_id,
            name=name,
            is_category=is_category,
            att=kwargs.get('att', 0.0),
            int=kwargs.get('int', 0.0),
            user_att=kwargs.get('user_att'),
            user_int=kwargs.get('user_int'),
            user_weight_override=kwargs.get('user_weight_override'),
            locked=kwargs.get('locked', False),
            active=kwargs.get('active', True),
        )
        self.nodes[node_id] = node
        return node
    
    def add_node_object(self, node: InterestNode) -> None:
        """Add an existing InterestNode object to the graph."""
        self.nodes[node.id] = node
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges from the graph."""
        if node_id not in self.nodes:
            return
        
        # Remove parent edge
        if node_id in self._parent_edges:
            edge = self._parent_edges.pop(node_id)
            self.edges.remove(edge)
            if edge.source_id in self._children_map:
                self._children_map[edge.source_id].remove(node_id)
        
        # Remove as parent
        if node_id in self._children_map:
            for child_id in self._children_map.pop(node_id):
                if child_id in self._parent_edges:
                    edge = self._parent_edges.pop(child_id)
                    self.edges.remove(edge)
        
        # Remove association edges
        for edge in self._association_edges.pop(node_id, []):
            if edge in self.edges:
                self.edges.remove(edge)
        
        # Remove from other nodes' association lists
        for other_id, edges in self._association_edges.items():
            self._association_edges[other_id] = [e for e in edges if e.target_id != node_id and e.source_id != node_id]
        
        del self.nodes[node_id]
    
    def add_edge(self, edge: Edge) -> bool:
        """Add an edge to the graph. Returns False if constraint violated."""
        if edge.type == EdgeType.PARENT:
            # Check: each node can have at most one parent
            if edge.target_id in self._parent_edges:
                return False
            
            # Validate nodes exist
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                return False
            
            self.edges.append(edge)
            self._parent_edges[edge.target_id] = edge
            self._children_map[edge.source_id].append(edge.target_id)
            
        elif edge.type == EdgeType.ASSOCIATION:
            # Validate nodes exist
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                return False
            
            self.edges.append(edge)
            self._association_edges[edge.source_id].append(edge)
            self._association_edges[edge.target_id].append(edge)
        
        return True
    
    def remove_edge(self, edge: Edge) -> None:
        """Remove an edge from the graph."""
        if edge not in self.edges:
            return
        
        self.edges.remove(edge)
        
        if edge.type == EdgeType.PARENT:
            if edge.target_id in self._parent_edges:
                del self._parent_edges[edge.target_id]
            if edge.source_id in self._children_map:
                self._children_map[edge.source_id].remove(edge.target_id)
        elif edge.type == EdgeType.ASSOCIATION:
            if edge.source_id in self._association_edges:
                self._association_edges[edge.source_id] = [
                    e for e in self._association_edges[edge.source_id] if e != edge
                ]
            if edge.target_id in self._association_edges:
                self._association_edges[edge.target_id] = [
                    e for e in self._association_edges[edge.target_id] if e != edge
                ]
    
    def get_parent(self, node_id: str) -> Optional[str]:
        """Get parent node ID."""
        edge = self._parent_edges.get(node_id)
        return edge.source_id if edge else None
    
    def get_children(self, node_id: str) -> list[str]:
        """Get list of child node IDs."""
        return self._children_map.get(node_id, [])
    
    def get_associations(self, node_id: str) -> list[tuple[str, Edge]]:
        """Get list of (connected_node_id, edge) tuples for associations."""
        result = []
        for edge in self._association_edges.get(node_id, []):
            if edge.source_id == node_id:
                result.append((edge.target_id, edge))
            else:
                result.append((edge.source_id, edge))
        return result
    
    def get_root_nodes(self) -> list[str]:
        """Get all root nodes (nodes without parents)."""
        roots = []
        for node_id in self.nodes:
            if node_id not in self._parent_edges:
                roots.append(node_id)
        return roots
    
    def set_node_active(self, node_id: str, active: bool, recursive: bool = True) -> None:
        """Set node active state. If recursive, also affects subtree."""
        if node_id not in self.nodes:
            return
        
        self.nodes[node_id].active = active
        
        if recursive and not active:
            # Deactivate all children recursively
            for child_id in self.get_children(node_id):
                self.set_node_active(child_id, False, recursive=True)
    
    def is_node_effectively_active(self, node_id: str) -> bool:
        """Check if node is effectively active (node and all ancestors are active)."""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        if not node.active:
            return False
        
        # Check all ancestors
        current_id = node_id
        while True:
            parent_id = self.get_parent(current_id)
            if parent_id is None:
                break
            if not self.nodes[parent_id].active:
                return False
            current_id = parent_id
        
        return True
    
    def get_active_nodes(self) -> list[str]:
        """Get list of effectively active node IDs."""
        return [nid for nid in self.nodes if self.is_node_effectively_active(nid)]
    
    def get_subtree(self, node_id: str) -> list[str]:
        """Get all node IDs in subtree rooted at node_id (inclusive)."""
        if node_id not in self.nodes:
            return []
        
        result = [node_id]
        for child_id in self.get_children(node_id):
            result.extend(self.get_subtree(child_id))
        return result
    
    def to_dict(self) -> dict:
        """Serialize graph to dictionary."""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InterestGraph':
        """Deserialize graph from dictionary."""
        graph = cls()
        
        for node_data in data.get('nodes', []):
            node = InterestNode.from_dict(node_data)
            graph.add_node_object(node)
        
        for edge_data in data.get('edges', []):
            edge = Edge.from_dict(edge_data)
            graph.add_edge(edge)
        
        return graph
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'InterestGraph':
        """Deserialize graph from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, filepath: str) -> None:
        """Save graph to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'InterestGraph':
        """Load graph from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
