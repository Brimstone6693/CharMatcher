"""
Graph_Overlord Module for Char_maker.
Manages user interests as a directed graph with two types of edges and dual-axis evaluation.
"""

from .models import InterestNode, Edge, GraphModel, Project
from .templates import Template, TemplateManager
from .solver import GraphSolver
from .constants import (
    ATT_LEVELS, INT_LEVELS,
    DEFAULT_ALPHA_PARENT, DEFAULT_ALPHA_CHILD, DEFAULT_ALPHA_ASSOC,
    DEFAULT_K_INT_TO_ATT, DEFAULT_K_ATT_TO_INT, DEFAULT_DAMPING,
    DEFAULT_D_THRESHOLD
)

__all__ = [
    'InterestNode',
    'Edge',
    'GraphModel',
    'Project',
    'Template',
    'TemplateManager',
    'GraphSolver',
    'ATT_LEVELS',
    'INT_LEVELS',
    'DEFAULT_ALPHA_PARENT',
    'DEFAULT_ALPHA_CHILD',
    'DEFAULT_ALPHA_ASSOC',
    'DEFAULT_K_INT_TO_ATT',
    'DEFAULT_K_ATT_TO_INT',
    'DEFAULT_DAMPING',
    'DEFAULT_D_THRESHOLD'
]
