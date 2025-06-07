"""
Tape wobble effect that simulates tape machine pitch instability.
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .base import BaseEffect, EffectConfiguration, EffectType

@dataclass
class TapeWobbleConfiguration(EffectConfiguration):
    """Configuration for tape wobble effect."""
    # Frequency of the wobble in Hz
    wobble_frequency: float = 0.5
    # Depth of the wobble in semitones
    wobble_depth: float = 0.15
    # Random variation in wobble frequency (0-1)
    frequency_variation: float = 0.1
    # Random variation in wobble depth (0-1)
    depth_variation: float = 0.1
    # Resolution of pitch bend messages in ticks
    resolution_ticks: int = 10

    def __post_init__(self):
        """Validate configuration parameters."""
        self.effect_type = EffectType.SEQUENCE_PROCESSOR
        if not 0.01 <= self.wobble_frequency <= 10.0:
            raise ValueError("Wobble frequency must be between 0.01 and 10.0 Hz")
        if not 0.0 <= self.wobble_depth <= 2.0:
            raise ValueError("Wobble depth must be between 0.0 and 2.0 semitones")
        if not 0.0 <= self.frequency_variation <= 1.0:
            raise ValueError("Frequency variation must be between 0.0 and 1.0")
        if not 0.0 <= self.depth_variation <= 1.0:
            raise ValueError("Depth variation must be between 0.0 and 1.0")
        if not 1 <= self.resolution_ticks <= 100:
            raise ValueError("Resolution must be between 1 and 100 ticks")

class TapeWobbleEffect(BaseEffect):
    """Effect that simulates tape machine pitch instability."""

    def __init__(self, config: TapeWobbleConfiguration):
        super().__init__(config)
        self.config: TapeWobbleConfiguration = config
        self._last_wobble_value = 0.0

    def _validate_configuration(self) -> None:
        """Ensure config is of correct type."""
        if not isinstance(self.config, TapeWobbleConfiguration):
            raise TypeError("TapeWobbleEffect requires TapeWobbleConfiguration")

    def _process_note_impl(self, ctx: Dict) -> Dict:
        """Note processing not used for tape wobble."""
        return ctx

    def _generate_wobble(self, time_seconds: float) -> float:
        """Generate a wobble value for a given time point."""
        # Add random variations to parameters
        freq_var = 1.0 + (random.random() * 2 - 1) * self.config.frequency_variation
        depth_var = 1.0 + (random.random() * 2 - 1) * self.config.depth_variation
        
        # Calculate base wobble using sine wave
        wobble = math.sin(
            2 * math.pi * self.config.wobble_frequency * freq_var * time_seconds
        )
        
        # Apply depth variation and scale to semitones
        wobble *= self.config.wobble_depth * depth_var
        
        # Smooth transitions between values
        wobble = 0.7 * wobble + 0.3 * self._last_wobble_value
        self._last_wobble_value = wobble
        
        return wobble

    def _process_sequence_impl(self, events: List[Dict], options: Dict) -> List[Dict]:
        """Apply tape wobble effect to the sequence."""
        if not events:
            return events

        processed_events = []
        ticks_per_beat = options.get('ticks_per_beat', 480)
        bpm = options.get('bpm', 120)
        
        # Find sequence duration
        max_tick = max(event['tick'] for event in events)
        
        # Generate pitch bend events
        current_tick = 0
        while current_tick <= max_tick:
            time_seconds = (current_tick / ticks_per_beat) * (60.0 / bpm)
            wobble_value = self._generate_wobble(time_seconds)
            
            # Convert wobble to pitch bend value (-8192 to 8191)
            # 2 semitones = 8192, so scale accordingly
            pitch_bend = int(wobble_value * 8192 / 2.0)
            pitch_bend = max(-8192, min(8191, pitch_bend))
            
            processed_events.append({
                'type': 'pitch_bend',
                'tick': current_tick,
                'channel': 0,  # Use same channel as notes
                'value': pitch_bend
            })
            
            current_tick += self.config.resolution_ticks
        
        # Merge original events with pitch bends, maintaining order
        all_events = processed_events + events
        all_events.sort(key=lambda x: (x['tick'], x.get('type', '') != 'pitch_bend'))
        
        return all_events 
