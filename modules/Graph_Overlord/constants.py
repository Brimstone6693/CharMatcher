"""
Constants for Graph_Overlord module.
Defines discrete levels for edge weights and global algorithm parameters.
"""

# Discrete levels for Att-related weights (w_down_att, fw_att, etc.)
# Maps level name to numeric value [-0.9, 0.9]
ATT_LEVELS = {
    "strong_positive": 0.9,
    "medium_positive": 0.7,
    "weak_positive": 0.4,
    "neutral": 0.0,
    "weak_negative": -0.4,
    "medium_negative": -0.7,
    "strong_negative": -0.9,
}

# Discrete levels for Int-related weights (w_down_int, fw_int, etc.)
# Maps level name to numeric value [0.0, 1.0]
INT_LEVELS = {
    "full_transfer": 1.0,
    "strong": 0.8,
    "medium": 0.6,
    "weak": 0.3,
    "minimal": 0.1,
    "no_transfer": 0.0,
}

# Default levels for new connections
DEFAULT_ATT_LEVEL = "medium_positive"
DEFAULT_INT_LEVEL = "medium"

# Global coefficients for network signal calculation
DEFAULT_ALPHA_PARENT = 0.4
DEFAULT_ALPHA_CHILD = 0.3
DEFAULT_ALPHA_ASSOC = 0.5

# Inter-axis influence coefficients
DEFAULT_K_INT_TO_ATT = 0.1
DEFAULT_K_ATT_TO_INT = 0.3

# Damping factor for iterative calculation
DEFAULT_DAMPING = 0.4

# Threshold for variance penalty in parent Att calculation
DEFAULT_D_THRESHOLD = 25.0  # Variance threshold

# Convergence threshold for iterative calculation
DEFAULT_EPSILON = 0.1

# Activation function temperature parameters
DEFAULT_TAU_ATT = 50.0
DEFAULT_TAU_INT = 50.0
