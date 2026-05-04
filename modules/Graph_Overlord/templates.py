"""
Template system for Graph_Overlord module.
Allows saving and reusing graph fragments (subtrees with associations).
"""

import uuid
import json
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from .models import InterestNode, Edge, GraphModel


@dataclass
class TemplateNode:
    """
    Represents a node within a template.
    Uses placeholder IDs that are resolved during instantiation.
    """
    id: str  # Placeholder ID within template
    name: str
    is_category: bool
    att: float = 0.0
    int: float = 0.0
    user_att: Optional[float] = None
    user_int: Optional[float] = None
    user_weight_override: Optional[float] = None
    locked: bool = False
    active: bool = True
    is_placeholder: bool = False  # True if this node should be linked to existing node
    
    def to_dict(self) -> Dict[str, Any]:
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
            'is_placeholder': self.is_placeholder,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateNode':
        return cls(**data)


@dataclass
class TemplateEdge:
    """
    Represents an edge within a template.
    """
    source_id: str  # Placeholder ID
    target_id: str  # Placeholder ID
    type: str
    w_down_att: float = 0.7
    w_down_int: float = 0.6
    w_up_att: float = 0.5
    w_up_int: float = 0.5
    fw_att: float = 0.7
    fw_int: float = 0.6
    bw_att: float = 0.7
    bw_int: float = 0.6
    is_external_link: bool = False  # True if connects to external node
    
    def to_dict(self) -> Dict[str, Any]:
        return {
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
            'is_external_link': self.is_external_link,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateEdge':
        return cls(**data)


@dataclass
class Template:
    """
    A reusable graph fragment containing nodes and edges.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Template"
    description: str = ""
    nodes: Dict[str, TemplateNode] = field(default_factory=dict)
    edges: Dict[str, TemplateEdge] = field(default_factory=dict)
    root_id: Optional[str] = None  # Placeholder ID of root node
    external_placeholders: List[str] = field(default_factory=list)  # IDs of placeholder nodes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'edges': {eid: edge.to_dict() for eid, edge in self.edges.items()},
            'root_id': self.root_id,
            'external_placeholders': self.external_placeholders,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        template = cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Untitled Template'),
            description=data.get('description', ''),
            root_id=data.get('root_id'),
            external_placeholders=data.get('external_placeholders', []),
        )
        for nid, node_data in data.get('nodes', {}).items():
            template.nodes[nid] = TemplateNode.from_dict(node_data)
        for eid, edge_data in data.get('edges', {}).items():
            template.edges[eid] = TemplateEdge.from_dict(edge_data)
        return template
    
    @classmethod
    def from_graph_model(cls, graph: GraphModel, root_node_id: str, 
                         name: str = "Template", 
                         include_external: bool = False) -> 'Template':
        """
        Create a template from a subtree of a GraphModel.
        
        Args:
            graph: Source graph model
            root_node_id: ID of the root node to include
            name: Template name
            include_external: If True, include association links to nodes outside subtree as placeholders
        """
        template = cls(name=name)
        template.root_id = root_node_id
        
        # Get all nodes in subtree
        subtree_ids = graph.get_subtree(root_node_id)
        
        # Add nodes
        for nid in subtree_ids:
            node = graph.nodes[nid]
            template_node = TemplateNode(
                id=nid,  # Keep original ID as placeholder
                name=node.name,
                is_category=node.is_category,
                att=node.att,
                int=node.int,
                user_att=node.user_att,
                user_int=node.user_int,
                user_weight_override=node.user_weight_override,
                locked=node.locked,
                active=node.active,
            )
            template.nodes[nid] = template_node
        
        # Add edges within subtree
        for edge in graph.edges.values():
            if edge.source_id in subtree_ids and edge.target_id in subtree_ids:
                template_edge = TemplateEdge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    type=edge.type,
                    w_down_att=edge.w_down_att,
                    w_down_int=edge.w_down_int,
                    w_up_att=edge.w_up_att,
                    w_up_int=edge.w_up_int,
                    fw_att=edge.fw_att,
                    fw_int=edge.fw_int,
                    bw_att=edge.bw_att,
                    bw_int=edge.bw_int,
                )
                template.edges[edge.id] = template_edge
        
        # Handle external associations if requested
        if include_external:
            external_links = set()
            for nid in subtree_ids:
                for assoc_target in graph.get_associations_out(nid):
                    if assoc_target not in subtree_ids:
                        external_links.add((nid, assoc_target, 'out'))
                for assoc_source in graph.get_associations_in(nid):
                    if assoc_source not in subtree_ids:
                        external_links.add((assoc_source, nid, 'in'))
            
            for source_id, target_id, direction in external_links:
                # Find the edge
                edge_found = None
                for edge in graph.edges.values():
                    if edge.source_id == source_id and edge.target_id == target_id and edge.type == 'association':
                        edge_found = edge
                        break
                
                if edge_found:
                    # Create placeholder for external node if not exists
                    external_id = f"ext_{target_id}" if direction == 'out' else f"ext_{source_id}"
                    placeholder_id = target_id if direction == 'out' else source_id
                    
                    if external_id not in template.nodes:
                        template.nodes[external_id] = TemplateNode(
                            id=external_id,
                            name="External Node",
                            is_category=False,
                            is_placeholder=True,
                        )
                        template.external_placeholders.append(external_id)
                    
                    template_edge = TemplateEdge(
                        source_id=source_id if direction == 'out' else external_id,
                        target_id=target_id if direction == 'out' else source_id,
                        type='association',
                        fw_att=edge_found.fw_att,
                        fw_int=edge_found.fw_int,
                        bw_att=edge_found.bw_att,
                        bw_int=edge_found.bw_int,
                        is_external_link=True,
                    )
                    template.edges[f"ext_edge_{uuid.uuid4().hex[:8]}"] = template_edge
        
        return template


class TemplateManager:
    """
    Manages a collection of templates.
    Provides methods for saving, loading, and applying templates.
    """
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
    
    def add_template(self, template: Template):
        """Add a template to the collection."""
        self.templates[template.id] = template
    
    def remove_template(self, template_id: str):
        """Remove a template by ID."""
        if template_id in self.templates:
            del self.templates[template_id]
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def apply_template(self, template: Template, 
                       target_graph: GraphModel,
                       parent_node_id: Optional[str],
                       external_mappings: Dict[str, str] = None) -> Dict[str, str]:
        """
        Apply a template to a graph.
        
        Args:
            template: Template to apply
            target_graph: Target graph model
            parent_node_id: ID of parent node to attach template root (None for root)
            external_mappings: Mapping of placeholder IDs to existing node IDs
        
        Returns:
            Dictionary mapping template node IDs to new node IDs in graph
        """
        if external_mappings is None:
            external_mappings = {}
        
        id_mapping: Dict[str, str] = {}  # template_id -> new_graph_id
        
        # Generate new IDs for all template nodes
        for tid, tnode in template.nodes.items():
            if tnode.is_placeholder and tid in external_mappings:
                # Use existing node
                id_mapping[tid] = external_mappings[tid]
            else:
                # Create new node
                new_node = InterestNode(
                    name=tnode.name,
                    is_category=tnode.is_category,
                    att=tnode.att,
                    int=tnode.int,
                    user_att=tnode.user_att,
                    user_int=tnode.user_int,
                    user_weight_override=tnode.user_weight_override,
                    locked=tnode.locked,
                    active=tnode.active,
                )
                new_id = target_graph.add_node(new_node, parent_id=None)
                id_mapping[tid] = new_id
        
        # Attach root to parent if specified
        if parent_node_id is not None and template.root_id is not None:
            root_new_id = id_mapping.get(template.root_id)
            if root_new_id:
                # Create parent edge
                target_graph.add_edge(parent_node_id, root_new_id, 'parent')
        
        # Create edges
        for edge in template.edges.values():
            source_new_id = id_mapping.get(edge.source_id)
            target_new_id = id_mapping.get(edge.target_id)
            
            if source_new_id and target_new_id:
                # Check if both nodes exist in graph
                if source_new_id in target_graph.nodes and target_new_id in target_graph.nodes:
                    try:
                        new_edge_id = target_graph.add_edge(
                            source_new_id, target_new_id, edge.type,
                            att_level='medium_positive',  # Will override weights manually
                            int_level='medium'
                        )
                        # Manually set weights
                        new_edge = target_graph.edges[new_edge_id]
                        new_edge.w_down_att = edge.w_down_att
                        new_edge.w_down_int = edge.w_down_int
                        new_edge.w_up_att = edge.w_up_att
                        new_edge.w_up_int = edge.w_up_int
                        new_edge.fw_att = edge.fw_att
                        new_edge.fw_int = edge.fw_int
                        new_edge.bw_att = edge.bw_att
                        new_edge.bw_int = edge.bw_int
                    except ValueError:
                        # Edge creation failed (e.g., target already has parent)
                        pass
        
        return id_mapping
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all templates."""
        return {tid: tmpl.to_dict() for tid, tmpl in self.templates.items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateManager':
        """Deserialize templates from dictionary."""
        manager = cls()
        for tid, tmpl_data in data.items():
            manager.templates[tid] = Template.from_dict(tmpl_data)
        return manager
    
    def save_to_file(self, filepath: str):
        """Save templates to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'TemplateManager':
        """Load templates from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
