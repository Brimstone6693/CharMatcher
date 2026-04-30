"""
InterestNode - Represents a node in the interest graph.

Each node has two independent evaluation axes:
- Attitude (Att): [-100, +100]
- Interest (Int): [0, 100]
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InterestNode:
    """Represents an interest node in the graph."""
    
    id: str
    name: str
    is_category: bool = False
    
    # Computed values
    att: float = 0.0  # Attitude [-100, 100]
    int: float = 0.0  # Interest [0, 100]
    
    # User-provided values
    user_att: Optional[float] = None
    user_int: Optional[float] = None
    user_weight_override: Optional[float] = None
    
    # State flags
    locked: bool = False
    active: bool = True
    
    # Internal state for calculations
    _prev_att: float = field(default=0.0, repr=False)
    _prev_int: float = field(default=0.0, repr=False)
    _uncertainty_score: float = field(default=0.0, repr=False)
    _conflict_score: float = field(default=0.0, repr=False)
    _weak_signal: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        """Initialize node with default values and compute initial state."""
        self._prev_att = self.att
        self._prev_int = self.int
        
        # Store original user values before computing missing axis
        original_user_att = self.user_att
        original_user_int = self.user_int
        
        # If only one axis is provided, compute the other
        self._compute_missing_axis()
        
        # Initialize user weights if not overridden (after computing missing axis)
        if self.user_weight_override is None:
            # Use both user values to compute weight if both are present
            weights = []
            if original_user_att is not None:
                weights.append(abs(original_user_att) / 100.0)
            if original_user_int is not None:
                weights.append(abs(original_user_int) / 100.0)
            if weights:
                self.user_weight_override = sum(weights) / len(weights)
    
    def _compute_missing_axis(self):
        """Compute missing axis value if only one is provided."""
        if self.user_att is not None and self.user_int is None:
            # int = max(0, att) * 0.7
            self.user_int = max(0, self.user_att) * 0.7
        elif self.user_int is not None and self.user_att is None:
            # att = int - 50 (heuristic)
            self.user_att = self.user_int - 50
    
    @property
    def user_weight_att(self) -> float:
        """Get user weight for attitude axis."""
        if self.user_att is not None:
            return abs(self.user_att) / 100.0
        return 0.0
    
    @property
    def user_weight_int(self) -> float:
        """Get user weight for interest axis."""
        if self.user_int is not None:
            return abs(self.user_int) / 100.0
        return 0.0
    
    @property
    def is_locked(self) -> bool:
        """Check if node is locked (won't be recalculated)."""
        return self.locked
    
    @property
    def is_active(self) -> bool:
        """Check if node is active (included in calculations)."""
        return self.active
    
    def get_effective_att(self) -> float:
        """Get effective attitude value considering lock state."""
        if self.locked and self.user_att is not None:
            return self.user_att
        return self.att
    
    def get_effective_int(self) -> float:
        """Get effective interest value considering lock state."""
        if self.locked and self.user_int is not None:
            return self.user_int
        return self.int
    
    def save_state(self):
        """Save current state for change detection."""
        self._prev_att = self.att
        self._prev_int = self.int
    
    def get_change(self) -> tuple[float, float]:
        """Get change since last saved state."""
        return (abs(self.att - self._prev_att), abs(self.int - self._prev_int))
    
    def mark_uncertain(self, conflict_score: float, weak_signal: bool):
        """Mark node as uncertain with given scores."""
        self._conflict_score = conflict_score
        self._weak_signal = weak_signal
        self._uncertainty_score = conflict_score + (1.0 if weak_signal else 0.0)
    
    @property
    def uncertainty_score(self) -> float:
        """Get uncertainty score."""
        return self._uncertainty_score
    
    @property
    def needs_clarification(self) -> bool:
        """Check if node needs clarification (high uncertainty)."""
        return self._conflict_score > 10.0 or self._weak_signal
    
    def to_dict(self) -> dict:
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
    def from_dict(cls, data: dict) -> 'InterestNode':
        """Deserialize node from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            is_category=data.get('is_category', False),
            att=data.get('att', 0.0),
            int=data.get('int', 0.0),
            user_att=data.get('user_att'),
            user_int=data.get('user_int'),
            user_weight_override=data.get('user_weight_override'),
            locked=data.get('locked', False),
            active=data.get('active', True),
        )
