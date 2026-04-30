"""
Graph Overlord - Interest Graph System

A system for storing user interests as a directed graph with two types of connections
and computing preferences (Attitude and Interest) for all nodes based on user-provided
evaluations for some nodes.
"""

from .interest_node import InterestNode
from .edge import Edge, EdgeType
from .graph import InterestGraph
from .templates import TemplateManager
from .calculator import GraphCalculator

__all__ = [
    'InterestNode',
    'Edge',
    'EdgeType',
    'InterestGraph',
    'TemplateManager',
    'GraphCalculator',
]

__version__ = '1.0.0'
