"""
Humanization effect for MIDI velocity values.

This module provides velocity humanization to make MIDI notes sound more natural
by adding controlled randomness and musical emphasis to note velocities.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Union, Optional, Tuple, Sequence

from midi_gen.effects.base import (
    MidiEffect,
    EffectConfiguration,
    EffectType,
    NoteContext
)
from midi_gen.utils.midi_types import (
    MidiEvent,
    MidiEventType,
    MidiInstruction,
    Velocity,
    NoteValue,
    Channel,
    Tick
)

# Default values for humanize velocity configuration
DEFAULT_HUMANIZE_RANGE = 10
DEFAULT_BASE_VELOCITY = 85
DEFAULT_DOWNBEAT_EMPHASIS = 4
DEFAULT_PATTERN_STRENGTH = 0.6
DEFAULT_TREND_PROBABILITY = 0.3

@dataclass
class HumanizeVelocityConfiguration(EffectConfiguration):
    """Configuration for velocity humanization effect."""
    base_velocity: int = DEFAULT_BASE_VELOCITY  # Base velocity for notes (0-127)
    humanization_range: int = DEFAULT_HUMANIZE_RANGE  # Maximum velocity adjustment (±range/2)
    downbeat_emphasis: int = DEFAULT_DOWNBEAT_EMPHASIS  # Additional velocity for downbeats
    pattern_strength: float = DEFAULT_PATTERN_STRENGTH  # How strongly to apply musical patterns (0-1)
    trend_probability: float = DEFAULT_TREND_PROBABILITY  # Probability of starting a velocity trend
    
    def __post_init__(self):
        """Set default values and validate configuration."""
        self.effect_type = EffectType.NOTE_PROCESSOR
        self.priority = 100  # Apply early in the chain
        
        # Validate velocity parameters
        if not 0 <= self.base_velocity <= 127:
            raise ValueError("base_velocity must be between 0 and 127")
        if self.humanization_range < 0:
            raise ValueError("humanization_range must be non-negative")
        if self.base_velocity + (self.humanization_range / 2) + self.downbeat_emphasis > 127:
            raise ValueError("base_velocity + (humanization_range/2) + downbeat_emphasis cannot exceed 127")
        if self.base_velocity - (self.humanization_range / 2) < 1:
            raise ValueError("base_velocity - (humanization_range/2) cannot be less than 1")
        if not 0 <= self.pattern_strength <= 1:
            raise ValueError("pattern_strength must be between 0 and 1")
        if not 0 <= self.trend_probability <= 1:
            raise ValueError("trend_probability must be between 0 and 1")

class HumanizeVelocityEffect(MidiEffect):
    """
    Adds natural variation to MIDI note velocities.
    
    This effect makes MIDI sequences sound more human by:
    1. Adding controlled randomness to velocities
    2. Emphasizing important musical positions (downbeats)
    3. Creating gradual velocity trends
    4. Maintaining musical patterns
    """
    
    def __init__(self, config: Optional[HumanizeVelocityConfiguration] = None):
        """Initialize with optional configuration."""
        super().__init__(config or HumanizeVelocityConfiguration())
        self.config = config or HumanizeVelocityConfiguration()
        self._reset_state()
    
    def _reset_state(self) -> None:
        """Reset internal state variables."""
        self.current_trend = 0  # Current velocity trend (-1, 0, or 1)
        self.trend_remaining = 0  # How many more notes to apply trend to
        self.last_velocity = self.config.base_velocity
    
    def _validate_configuration(self) -> None:
        """Configuration is already validated in HumanizeVelocityConfiguration.__post_init__"""
        pass
    
    def _calculate_position_emphasis(self, ctx: NoteContext) -> int:
        """Calculate velocity emphasis based on musical position."""
        emphasis = 0
        
        # Emphasize downbeats
        if ctx['beat_position'] < 0.1:  # Note is close to beat start
            emphasis += self.config.downbeat_emphasis
            
        # Add pattern-based emphasis
        if random.random() < self.config.pattern_strength:
            if ctx['beat_position'] < 0.1:  # Strong beat
                emphasis += 2
            elif abs(ctx['beat_position'] - 0.5) < 0.1:  # Back beat
                emphasis += 1
                
        return emphasis
    
    def _calculate_beat_emphasis(self, ctx: NoteContext) -> int:
        """Calculate emphasis based on beat position and patterns."""
        beat_position = ctx['beat_position']
        emphasis = 0
        
        # Strong emphasis on downbeat (position 0.0)
        if beat_position < 0.1:
            emphasis += 3
        # Medium emphasis on backbeat (position 0.5)
        elif 0.4 < beat_position < 0.6:
            emphasis += 2
        # Slight emphasis on other strong beats
        elif 0.15 < beat_position < 0.35:
            emphasis += 1
            
        return emphasis
    
    def _update_velocity_trend(self) -> int:
        """Update and return the current velocity trend value."""
        if self.trend_remaining <= 0:
            if random.random() < self.config.trend_probability:
                self.current_trend = random.choice([-1, 1])
                self.trend_remaining = random.randint(3, 8)
            else:
                self.current_trend = 0
                self.trend_remaining = 0
        else:
            self.trend_remaining -= 1
            
        return self.current_trend
    
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Process a single note, humanizing its velocity."""
        if not self.config.enabled:
            return ctx
            
        # Start with base velocity
        new_velocity = self.config.base_velocity
        
        # Add controlled randomness
        random_adjustment = random.randint(
            -self.config.humanization_range // 2,
            self.config.humanization_range // 2
        )
        new_velocity += random_adjustment
        
        # Add position-based emphasis
        new_velocity += self._calculate_position_emphasis(ctx)
        
        # Apply velocity trending
        trend_value = self._update_velocity_trend()
        new_velocity += trend_value * 2
        
        # Ensure velocity stays within MIDI bounds
        new_velocity = max(1, min(127, new_velocity))
        
        # Update last velocity for next note
        self.last_velocity = new_velocity
        
        # Create new context with updated velocity
        new_ctx = ctx.copy()
        new_ctx['velocity'] = new_velocity
        return new_ctx
    
    def _process_sequence_impl(self, 
                             events: Sequence[MidiInstruction], 
                             options: Dict) -> List[MidiEvent]:
        """Convert sequence to use new MidiEvent type."""
        result_events: List[MidiEvent] = []
        
        for event in events:
            if isinstance(event, tuple):
                try:
                    midi_event = MidiEvent.from_legacy_tuple(event)
                    result_events.append(midi_event)
                except (ValueError, TypeError):
                    continue
            elif isinstance(event, MidiEvent):
                result_events.append(event)
        
        return sorted(result_events) 
