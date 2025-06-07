"""
MIDI effects for modifying and enhancing MIDI sequences.
"""

from .base import (
    BaseEffect,
    EffectChain,
    NoteContext,
    create_note_context
)

from .effects import (
    TapeWobbleEffect,
    HumanizeVelocityEffect
)

__all__ = [
    # Base classes
    'BaseEffect',
    'EffectChain',
    'NoteContext',
    
    # Utilities
    'create_note_context',
    
    # Effects
    'TapeWobbleEffect',
    'HumanizeVelocityEffect',
]
