"""
Type definitions and constants for rest pattern processing.
"""

from enum import Enum
from typing import List, Union, Tuple
from dataclasses import dataclass

class RestPatternType(Enum):
    """Types of rest patterns available."""
    FIXED = "fixed"          # Regular interval patterns
    PROBABILITY = "prob"     # Random probability based
    MUSICAL_POS = "pos"      # Based on musical position
    PHRASE = "phrase"        # Phrase-end based

# Type aliases for clarity
RestPattern = List[bool]     # True = rest, False = play
Tick = int                   # MIDI tick position
Step = int                   # Step number in sequence

# Constants for musical timing
TICKS_PER_QUARTER = 480     # Standard MIDI resolution
STEPS_PER_BAR = 16          # Default steps per bar (16th notes)
MIN_PATTERN_LENGTH = 1      # Minimum pattern length
MAX_PATTERN_LENGTH = 32     # Maximum pattern length

# Default values
DEFAULT_REST_ENABLED = False
DEFAULT_PATTERN_TYPE = RestPatternType.FIXED
DEFAULT_MAINTAIN_RHYTHM = True  # Whether to maintain timing when inserting rests 
