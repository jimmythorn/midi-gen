"""
Humanization effects for adding natural variations to MIDI parameters.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .base import BaseEffect, EffectConfiguration, EffectType, NoteContext

@dataclass
class HumanizeVelocityConfiguration(EffectConfiguration):
    """Configuration for humanizing note velocities."""
    # Base amount of random velocity variation (0-1)
    variation_amount: float = 0.15
    # Increase variation for offbeat notes (0-1)
    offbeat_emphasis: float = 0.2
    # Reduce velocity of consecutive fast notes (0-1)
    fast_note_reduction: float = 0.1
    # Minimum time between notes to be considered "fast" (in seconds)
    fast_note_threshold: float = 0.1
    # Bias towards accenting first note of each beat (0-1)
    beat_emphasis: float = 0.1
    # Bias towards accenting first note of each bar (0-1)
    bar_emphasis: float = 0.2
    # Minimum allowed velocity after all modifications
    min_velocity: int = 30
    # Maximum allowed velocity after all modifications
    max_velocity: int = 127

    def __post_init__(self):
        """Validate configuration parameters."""
        self.effect_type = EffectType.NOTE_PROCESSOR
        if not 0.0 <= self.variation_amount <= 1.0:
            raise ValueError("Variation amount must be between 0.0 and 1.0")
        if not 0.0 <= self.offbeat_emphasis <= 1.0:
            raise ValueError("Offbeat emphasis must be between 0.0 and 1.0")
        if not 0.0 <= self.fast_note_reduction <= 1.0:
            raise ValueError("Fast note reduction must be between 0.0 and 1.0")
        if not 0.0 <= self.fast_note_threshold <= 1.0:
            raise ValueError("Fast note threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.beat_emphasis <= 1.0:
            raise ValueError("Beat emphasis must be between 0.0 and 1.0")
        if not 0.0 <= self.bar_emphasis <= 1.0:
            raise ValueError("Bar emphasis must be between 0.0 and 1.0")
        if not 0 <= self.min_velocity <= 127:
            raise ValueError("Minimum velocity must be between 0 and 127")
        if not 0 <= self.max_velocity <= 127:
            raise ValueError("Maximum velocity must be between 0 and 127")
        if self.min_velocity > self.max_velocity:
            raise ValueError("Minimum velocity cannot be greater than maximum velocity")

class HumanizeVelocityEffect(BaseEffect):
    """Effect that adds natural velocity variations to notes."""

    def __init__(self, config: HumanizeVelocityConfiguration):
        super().__init__(config)
        self.config: HumanizeVelocityConfiguration = config
        self._last_note_time: Optional[float] = None

    def _validate_configuration(self) -> None:
        """Ensure config is of correct type."""
        if not isinstance(self.config, HumanizeVelocityConfiguration):
            raise TypeError("HumanizeVelocityEffect requires HumanizeVelocityConfiguration")

    def _process_sequence_impl(self, events: List[Dict], options: Dict) -> List[Dict]:
        """Sequence processing not used for humanize velocity."""
        return events

    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Apply humanization to note velocity."""
        # Start with base velocity
        velocity = ctx['velocity']
        
        # Add random variation
        variation = (random.random() * 2 - 1) * self.config.variation_amount
        velocity = int(velocity * (1.0 + variation))
        
        # Apply offbeat emphasis
        if 0.2 < ctx['beat_position'] < 0.8:  # Consider middle 60% of beat as offbeat
            offbeat_var = random.random() * self.config.offbeat_emphasis
            velocity = int(velocity * (1.0 + offbeat_var))
        
        # Apply fast note reduction
        if self._last_note_time is not None:
            time_since_last = ctx['time_seconds'] - self._last_note_time
            if time_since_last < self.config.fast_note_threshold:
                reduction = (1.0 - time_since_last / self.config.fast_note_threshold) * self.config.fast_note_reduction
                velocity = int(velocity * (1.0 - reduction))
        self._last_note_time = ctx['time_seconds']
        
        # Apply beat emphasis
        if ctx['beat_position'] < 0.1:  # First 10% of beat
            beat_var = random.random() * self.config.beat_emphasis
            velocity = int(velocity * (1.0 + beat_var))
        
        # Apply bar emphasis
        if ctx['bar_position'] == 0 and ctx['beat_position'] < 0.1:
            bar_var = random.random() * self.config.bar_emphasis
            velocity = int(velocity * (1.0 + bar_var))
        
        # Clamp to allowed range
        velocity = max(self.config.min_velocity, min(self.config.max_velocity, velocity))
        
        # Update context with new velocity
        new_ctx = ctx.copy()
        new_ctx['velocity'] = velocity
        
        return new_ctx 
