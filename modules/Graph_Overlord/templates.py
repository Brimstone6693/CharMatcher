"""
TemplateManager - Manages graph templates for quick graph construction.

Templates are predefined graph fragments (subtrees with associations)
that can be imported and linked to existing nodes.
"""

import json
from typing import Optional
from dataclasses import dataclass, field

from .interest_node import InterestNode
from .edge import Edge, EdgeType
from .graph import InterestGraph


@dataclass
class TemplateNode:
    """Represents a node in a template."""
    
    id: str
    name: str
    is_category: bool = False
    user_att: Optional[float] = None
    user_int: Optional[float] = None
    active: bool = True
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'is_category': self.is_category,
            'user_att': self.user_att,
            'user_int': self.user_int,
            'active': self.active,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TemplateNode':
        return cls(
            id=data['id'],
            name=data['name'],
            is_category=data.get('is_category', False),
            user_att=data.get('user_att'),
            user_int=data.get('user_int'),
            active=data.get('active', True),
        )


@dataclass
class TemplateEdge:
    """Represents an edge in a template."""
    
    source_id: str
    target_id: str
    type: str  # 'parent' or 'association'
    att_level: str = 'medium_positive'
    int_level: str = 'medium'
    bidirectional: bool = True
    
    # For external references (placeholders to be replaced during insertion)
    is_external_source: bool = False
    is_external_target: bool = False
    
    def to_dict(self) -> dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type,
            'att_level': self.att_level,
            'int_level': self.int_level,
            'bidirectional': self.bidirectional,
            'is_external_source': self.is_external_source,
            'is_external_target': self.is_external_target,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TemplateEdge':
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            type=data['type'],
            att_level=data.get('att_level', 'medium_positive'),
            int_level=data.get('int_level', 'medium'),
            bidirectional=data.get('bidirectional', True),
            is_external_source=data.get('is_external_source', False),
            is_external_target=data.get('is_external_target', False),
        )


@dataclass
class GraphTemplate:
    """Represents a complete graph template."""
    
    name: str
    description: str
    nodes: list[TemplateNode] = field(default_factory=list)
    edges: list[TemplateEdge] = field(default_factory=list)
    root_node_id: Optional[str] = None  # Node to attach to parent during insertion
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges],
            'root_node_id': self.root_node_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GraphTemplate':
        template = cls(
            name=data['name'],
            description=data.get('description', ''),
            root_node_id=data.get('root_node_id'),
        )
        template.nodes = [TemplateNode.from_dict(n) for n in data.get('nodes', [])]
        template.edges = [TemplateEdge.from_dict(e) for e in data.get('edges', [])]
        return template
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GraphTemplate':
        data = json.loads(json_str)
        return cls.from_dict(data)


class TemplateManager:
    """Manages graph templates."""
    
    def __init__(self):
        """Initialize template manager."""
        self.templates: dict[str, GraphTemplate] = {}
    
    def register_template(self, template: GraphTemplate) -> None:
        """Register a template."""
        self.templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[GraphTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self) -> list[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def load_template_from_file(self, filepath: str) -> Optional[GraphTemplate]:
        """Load a template from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = GraphTemplate.from_json(f.read())
            self.register_template(template)
            return template
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def save_template_to_file(self, template_name: str, filepath: str) -> bool:
        """Save a template to JSON file."""
        template = self.get_template(template_name)
        if not template:
            return False
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template.to_json())
        return True
    
    def insert_template(
        self,
        template: GraphTemplate,
        graph: InterestGraph,
        parent_node_id: Optional[str] = None,
        external_mappings: Optional[dict[str, str]] = None
    ) -> list[str]:
        """
        Insert a template into a graph.
        
        Args:
            template: The template to insert
            graph: The target graph
            parent_node_id: Optional parent node to attach the template root to
            external_mappings: Mapping of external placeholder IDs to real node IDs
        
        Returns:
            List of inserted node IDs
        """
        external_mappings = external_mappings or {}
        inserted_nodes = []
        
        # Create nodes with new IDs to avoid conflicts
        id_mapping = {}
        for tnode in template.nodes:
            new_id = f"{template.name}_{tnode.id}"
            id_mapping[tnode.id] = new_id
            
            node = InterestNode(
                id=new_id,
                name=tnode.name,
                is_category=tnode.is_category,
                user_att=tnode.user_att,
                user_int=tnode.user_int,
                active=tnode.active,
            )
            graph.add_node_object(node)
            inserted_nodes.append(new_id)
        
        # Create edges
        for tedge in template.edges:
            source_id = tedge.source_id
            target_id = tedge.target_id
            
            # Handle external references
            if tedge.is_external_source:
                source_id = external_mappings.get(source_id, parent_node_id)
                if not source_id:
                    continue  # Skip if no mapping found
            else:
                source_id = id_mapping.get(source_id)
            
            if tedge.is_external_target:
                target_id = external_mappings.get(target_id, parent_node_id)
                if not target_id:
                    continue  # Skip if no mapping found
            else:
                target_id = id_mapping.get(target_id)
            
            if not source_id or not target_id:
                continue
            
            # Create edge based on type
            if tedge.type == 'parent':
                edge = Edge.create_parent_edge(
                    source_id=source_id,
                    target_id=target_id,
                    att_level=tedge.att_level,
                    int_level=tedge.int_level,
                )
            else:
                edge = Edge.create_association_edge(
                    source_id=source_id,
                    target_id=target_id,
                    att_level=tedge.att_level,
                    int_level=tedge.int_level,
                    bidirectional=tedge.bidirectional,
                )
            
            graph.add_edge(edge)
        
        # Connect template root to parent if specified
        if parent_node_id and template.root_node_id:
            root_new_id = id_mapping.get(template.root_node_id)
            if root_new_id:
                parent_edge = Edge.create_parent_edge(
                    source_id=parent_node_id,
                    target_id=root_new_id,
                )
                graph.add_edge(parent_edge)
        
        return inserted_nodes
    
    def create_builtin_templates(self) -> None:
        """Create built-in templates for common interest categories."""
        
        # Sports template
        sports = GraphTemplate(
            name="sports",
            description="Sports and physical activities",
            root_node_id="root",
        )
        sports.nodes = [
            TemplateNode(id="root", name="Sports", is_category=True),
            TemplateNode(id="team", name="Team Sports", is_category=True),
            TemplateNode(id="individual", name="Individual Sports", is_category=True),
            TemplateNode(id="football", name="Football"),
            TemplateNode(id="basketball", name="Basketball"),
            TemplateNode(id="tennis", name="Tennis"),
            TemplateNode(id="swimming", name="Swimming"),
            TemplateNode(id="running", name="Running"),
        ]
        sports.edges = [
            TemplateEdge(source_id="root", target_id="team", type="parent"),
            TemplateEdge(source_id="root", target_id="individual", type="parent"),
            TemplateEdge(source_id="team", target_id="football", type="parent"),
            TemplateEdge(source_id="team", target_id="basketball", type="parent"),
            TemplateEdge(source_id="individual", target_id="tennis", type="parent"),
            TemplateEdge(source_id="individual", target_id="swimming", type="parent"),
            TemplateEdge(source_id="individual", target_id="running", type="parent"),
            TemplateEdge(source_id="football", target_id="basketball", type="association"),
            TemplateEdge(source_id="tennis", target_id="running", type="association", att_level="weak_positive"),
        ]
        self.register_template(sports)
        
        # Intellectual games template
        games = GraphTemplate(
            name="intellectual_games",
            description="Intellectual games and puzzles",
            root_node_id="root",
        )
        games.nodes = [
            TemplateNode(id="root", name="Intellectual Games", is_category=True),
            TemplateNode(id="board", name="Board Games", is_category=True),
            TemplateNode(id="digital", name="Digital Games", is_category=True),
            TemplateNode(id="chess", name="Chess"),
            TemplateNode(id="go", name="Go"),
            TemplateNode(id="puzzles", name="Puzzles"),
            TemplateNode(id="strategy", name="Strategy Games"),
        ]
        games.edges = [
            TemplateEdge(source_id="root", target_id="board", type="parent"),
            TemplateEdge(source_id="root", target_id="digital", type="parent"),
            TemplateEdge(source_id="board", target_id="chess", type="parent"),
            TemplateEdge(source_id="board", target_id="go", type="parent"),
            TemplateEdge(source_id="board", target_id="puzzles", type="parent"),
            TemplateEdge(source_id="digital", target_id="strategy", type="parent"),
            TemplateEdge(source_id="chess", target_id="go", type="association", att_level="strong_positive"),
            TemplateEdge(source_id="chess", target_id="strategy", type="association"),
        ]
        self.register_template(games)
        
        # Creative arts template
        arts = GraphTemplate(
            name="creative_arts",
            description="Creative and artistic activities",
            root_node_id="root",
        )
        arts.nodes = [
            TemplateNode(id="root", name="Creative Arts", is_category=True),
            TemplateNode(id="visual", name="Visual Arts", is_category=True),
            TemplateNode(id="music", name="Music", is_category=True),
            TemplateNode(id="writing", name="Writing", is_category=True),
            TemplateNode(id="drawing", name="Drawing"),
            TemplateNode(id="painting", name="Painting"),
            TemplateNode(id="photography", name="Photography"),
            TemplateNode(id="instrument", name="Playing Instrument"),
            TemplateNode(id="composition", name="Music Composition"),
            TemplateNode(id="fiction", name="Fiction Writing"),
            TemplateNode(id="poetry", name="Poetry"),
        ]
        arts.edges = [
            TemplateEdge(source_id="root", target_id="visual", type="parent"),
            TemplateEdge(source_id="root", target_id="music", type="parent"),
            TemplateEdge(source_id="root", target_id="writing", type="parent"),
            TemplateEdge(source_id="visual", target_id="drawing", type="parent"),
            TemplateEdge(source_id="visual", target_id="painting", type="parent"),
            TemplateEdge(source_id="visual", target_id="photography", type="parent"),
            TemplateEdge(source_id="music", target_id="instrument", type="parent"),
            TemplateEdge(source_id="music", target_id="composition", type="parent"),
            TemplateEdge(source_id="writing", target_id="fiction", type="parent"),
            TemplateEdge(source_id="writing", target_id="poetry", type="parent"),
            TemplateEdge(source_id="drawing", target_id="painting", type="association", att_level="strong_positive"),
            TemplateEdge(source_id="instrument", target_id="composition", type="association"),
        ]
        self.register_template(arts)
