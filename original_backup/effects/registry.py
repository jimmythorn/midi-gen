"""
Registry for MIDI effects.

This module provides the central registry for creating and managing MIDI effects.
"""

from typing import Dict, Optional
from .base import MidiEffect

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
            from .processors.tape_wobble import TapeWobbleEffect, TapeWobbleConfiguration
            config = TapeWobbleConfiguration(
                bend_up_cents=effect_conf.get('wow_depth'),
                bend_down_cents=effect_conf.get('wow_depth'),
                randomness=effect_conf.get('randomness'),
                depth_units=effect_conf.get('depth_units', 'cents'),
                pitch_bend_update_rate=effect_conf.get('flutter_rate_hz')
            )
            return TapeWobbleEffect(config)
            
        elif effect_name == 'humanize_velocity':
            from .processors.humanize import HumanizeVelocityEffect, HumanizeVelocityConfiguration
            config = HumanizeVelocityConfiguration(
                humanization_range=effect_conf.get('humanization_range')
            )
            return HumanizeVelocityEffect(config)
            
        return None
