"""
MIDI effect processors package.

This package provides various MIDI effects for processing notes and sequences.
"""

from .humanize import (
    HumanizeVelocityEffect,
    HumanizeVelocityConfiguration,
    DEFAULT_HUMANIZE_RANGE,
    DEFAULT_BASE_VELOCITY,
    DEFAULT_DOWNBEAT_EMPHASIS,
    DEFAULT_PATTERN_STRENGTH,
    DEFAULT_TREND_PROBABILITY
)

from .tape_wobble import (
    TapeWobbleEffect,
    TapeWobbleConfiguration,
    WobbleState,
    DEFAULT_WOW_RATE_HZ,
    DEFAULT_WOW_DEPTH,
    DEFAULT_FLUTTER_RATE_HZ,
    DEFAULT_FLUTTER_DEPTH,
    DEFAULT_RANDOMNESS,
    DEFAULT_BEND_UP_CENTS,
    DEFAULT_BEND_DOWN_CENTS
)

__all__ = [
    # Humanize Velocity Effect
    'HumanizeVelocityEffect',
    'HumanizeVelocityConfiguration',
    'DEFAULT_HUMANIZE_RANGE',
    'DEFAULT_BASE_VELOCITY',
    'DEFAULT_DOWNBEAT_EMPHASIS',
    'DEFAULT_PATTERN_STRENGTH',
    'DEFAULT_TREND_PROBABILITY',
    
    # Tape Wobble Effect
    'TapeWobbleEffect',
    'TapeWobbleConfiguration',
    'WobbleState',
    'DEFAULT_WOW_RATE_HZ',
    'DEFAULT_WOW_DEPTH',
    'DEFAULT_FLUTTER_RATE_HZ',
    'DEFAULT_FLUTTER_DEPTH',
    'DEFAULT_RANDOMNESS',
    'DEFAULT_BEND_UP_CENTS',
    'DEFAULT_BEND_DOWN_CENTS'
]
