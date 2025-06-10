"""
Registry for MIDI effects.

This module provides the central registry for creating and managing MIDI effects.
"""

from typing import Dict, Optional
from .base import MidiEffect
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
    def create_effect(cls, effect_conf: Dict) -> Optional[MidiEffect]:
        """
        Create an effect from configuration.
        
        Args:
            effect_conf: Dictionary containing effect configuration
            
        Returns:
            Configured MidiEffect instance or None if effect type is not recognized
        """
        effect_name = effect_conf.get('name', '')
        
        # Import effects only when needed to avoid circular imports
        if effect_name == 'tape_wobble':
            config = TapeWobbleConfiguration(
                wow_rate_hz=effect_conf.get('wow_rate_hz', DEFAULT_WOW_RATE_HZ),
                wow_depth=effect_conf.get('wow_depth', DEFAULT_WOW_DEPTH),
                flutter_rate_hz=effect_conf.get('flutter_rate_hz', DEFAULT_FLUTTER_RATE_HZ),
                flutter_depth=effect_conf.get('flutter_depth', DEFAULT_FLUTTER_DEPTH),
                randomness=effect_conf.get('randomness', DEFAULT_RANDOMNESS),
                depth_units=effect_conf.get('depth_units', 'cents')
            )
            return TapeWobbleEffect(config)
            
        elif effect_name == 'humanize_velocity':
            config = HumanizeVelocityConfiguration(
                humanization_range=effect_conf.get('humanization_range', DEFAULT_HUMANIZE_RANGE)
            )
            return HumanizeVelocityEffect(config)
            
        return None
