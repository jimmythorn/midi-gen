"""
Registry for MIDI effects.

This module provides the central registry for creating and managing MIDI effects.
"""

from typing import Dict, Optional, Union
from .base import MidiEffect, EffectConfiguration
from .processors import (
    TapeWobbleEffect,
    TapeWobbleConfiguration,
    HumanizeVelocityEffect,
    HumanizeVelocityConfiguration,
    DEFAULT_WOW_RATE_HZ,
    DEFAULT_WOW_DEPTH,
    DEFAULT_FLUTTER_RATE_HZ,
    DEFAULT_FLUTTER_DEPTH,
    DEFAULT_RANDOMNESS,
    DEFAULT_HUMANIZE_RANGE
)

class EffectRegistry:
    """Registry for MIDI effects."""
    
    @classmethod
    def create_effect(cls, effect_name: str, config: Union[TapeWobbleConfiguration, HumanizeVelocityConfiguration]) -> Optional[MidiEffect]:
        """
        Create an effect from configuration.
        
        Args:
            effect_name: Name of the effect to create
            config: Configuration object for the effect
            
        Returns:
            Configured MidiEffect instance or None if effect type is not recognized
        """
        if effect_name == 'tape_wobble' and isinstance(config, TapeWobbleConfiguration):
            return TapeWobbleEffect(config)
        elif effect_name == 'humanize_velocity' and isinstance(config, HumanizeVelocityConfiguration):
            return HumanizeVelocityEffect(config)
        return None
