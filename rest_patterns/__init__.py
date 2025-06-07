"""
Rest pattern generation module for MIDI sequences.
"""

from .types import (
    RestPatternType,
    RestPattern,
    Tick,
    Step,
    TICKS_PER_QUARTER,
    STEPS_PER_BAR,
    MIN_PATTERN_LENGTH,
    MAX_PATTERN_LENGTH,
    DEFAULT_REST_ENABLED,
    DEFAULT_PATTERN_TYPE,
    DEFAULT_MAINTAIN_RHYTHM
)

from .rest_config import (
    BaseRestConfig,
    FixedPatternConfig,
    ProbabilityConfig,
    MusicalPosConfig,
    PhraseConfig,
    RestPatternConfig
)

__all__ = [
    # Types and constants
    'RestPatternType',
    'RestPattern',
    'Tick',
    'Step',
    'TICKS_PER_QUARTER',
    'STEPS_PER_BAR',
    'MIN_PATTERN_LENGTH',
    'MAX_PATTERN_LENGTH',
    'DEFAULT_REST_ENABLED',
    'DEFAULT_PATTERN_TYPE',
    'DEFAULT_MAINTAIN_RHYTHM',
    
    # Configuration classes
    'BaseRestConfig',
    'FixedPatternConfig',
    'ProbabilityConfig',
    'MusicalPosConfig',
    'PhraseConfig',
    'RestPatternConfig'
] 
