"""
Tape wobble effect for MIDI pitch modulation.

This module simulates the pitch instability characteristics of analog tape machines,
including both slow wow and faster flutter modulations.
"""

import random
import math
from dataclasses import dataclass
from typing import Dict, List, Union, Optional, Tuple, cast, Sequence

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
    MIDI_PITCH_BEND_CENTER,
    MIDI_PITCH_BEND_MIN,
    MIDI_PITCH_BEND_MAX,
    DEFAULT_PITCH_BEND_UPDATE_RATE,
    PITCH_BEND_THRESHOLD,
    Tick,
    BendValue
)

# Constants for tape wobble effect
SEMITONES_PER_BEND = 2.0  # Standard pitch bend range
MIN_TIME_BETWEEN_BENDS_MS = 5.0  # Minimum time between pitch bend messages

# Default values for tape wobble configuration
DEFAULT_WOW_RATE_HZ = 0.5
DEFAULT_WOW_DEPTH = 20.0  # cents
DEFAULT_FLUTTER_RATE_HZ = 7.0
DEFAULT_FLUTTER_DEPTH = 5.0  # cents
DEFAULT_RANDOMNESS = 1.0

@dataclass
class TapeWobbleConfiguration(EffectConfiguration):
    """Configuration for tape wobble effect."""
    wow_rate_hz: float = DEFAULT_WOW_RATE_HZ
    wow_depth: float = DEFAULT_WOW_DEPTH
    flutter_rate_hz: float = DEFAULT_FLUTTER_RATE_HZ
    flutter_depth: float = DEFAULT_FLUTTER_DEPTH
    randomness: float = DEFAULT_RANDOMNESS
    depth_units: str = 'cents'
    pitch_bend_update_rate: float = DEFAULT_PITCH_BEND_UPDATE_RATE

    def __post_init__(self):
        """Validate configuration parameters and set effect type."""
        self.effect_type = EffectType.SEQUENCE_PROCESSOR
        self.priority = 200  # Run after note-level effects
        
        # Validate parameters
        if self.wow_rate_hz <= 0:
            raise ValueError("wow_rate_hz must be positive")
        if self.wow_depth < 0:
            raise ValueError("wow_depth must be non-negative")
        if self.flutter_rate_hz <= 0:
            raise ValueError("flutter_rate_hz must be positive")
        if self.flutter_depth < 0:
            raise ValueError("flutter_depth must be non-negative")
        if not 0 <= self.randomness <= 1:
            raise ValueError("randomness must be between 0 and 1")
        if self.depth_units not in ['cents', 'semitones']:
            raise ValueError("depth_units must be 'cents' or 'semitones'")
        if self.pitch_bend_update_rate <= 0:
            raise ValueError("pitch_bend_update_rate must be positive")

@dataclass
class WobbleState:
    """State container for tape wobble effect."""
    wow_phase: float = 0.0
    flutter_phase: float = 0.0
    last_bend_value: int = 0
    last_bend_time: float = 0.0
    
    def reset(self):
        """Reset state to initial values with random phase offsets."""
        self.wow_phase = random.random() * 2 * math.pi
        self.flutter_phase = random.random() * 2 * math.pi
        self.last_bend_value = 0
        self.last_bend_time = 0.0

def generate_wobble_data(options: dict) -> List[tuple[float, BendValue]]:
    """
    Generates a simulated "tape wobble" modulation signal over time.
    
    Returns:
        List of tuples (time_sec, bend_value) where:
        - time_sec: The time in seconds when this bend value should be applied
        - bend_value: The MIDI pitch bend value (-8192 to 8191)
    """
    duration = options.get('duration_sec', 5.0)
    wow_rate = options.get('wow_rate_hz', DEFAULT_WOW_RATE_HZ)
    wow_depth = options.get('wow_depth', DEFAULT_WOW_DEPTH)
    flutter_rate = options.get('flutter_rate_hz', DEFAULT_FLUTTER_RATE_HZ)
    flutter_depth = options.get('flutter_depth', DEFAULT_FLUTTER_DEPTH)
    randomness = options.get('randomness', DEFAULT_RANDOMNESS)
    depth_units = options.get('depth_units', 'cents')
    
    # Lower sample rate for more DAW-friendly output
    sample_rate_hz = 20  # Fixed rate for more stable output
    
    if duration <= 0:
        return []

    num_samples = int(duration * sample_rate_hz)
    wobble_data: List[tuple[float, BendValue]] = []
    last_emitted_value = 0
    last_emission_time = 0.0

    # Initialize phase offsets with reduced randomness
    clamped_randomness = max(0.0, min(0.5, randomness))  # Limit max randomness
    wow_phase = random.random() * 2 * math.pi * clamped_randomness
    flutter_phase = random.random() * 2 * math.pi * clamped_randomness
    
    # Always emit initial center value
    wobble_data.append((0.0, MIDI_PITCH_BEND_CENTER))

    for i in range(num_samples):
        t = i / sample_rate_hz
        
        # Calculate components with full depth
        wow = wow_depth * math.sin(2 * math.pi * wow_rate * t + wow_phase)
        flutter = flutter_depth * math.sin(2 * math.pi * flutter_rate * t + flutter_phase)
        total_mod = wow + flutter

        # Convert to pitch bend value
        if depth_units == 'cents':
            semitones = total_mod / 100.0
        else:
            semitones = total_mod

        # Scale to MIDI pitch bend range (-8192 to 8191)
        # SEMITONES_PER_BEND is typically 2, so we scale our semitones to that range
        bend_value = int(round((semitones / SEMITONES_PER_BEND) * 8191))  # Use 8191 to stay within range
        bend_value = max(MIDI_PITCH_BEND_MIN, min(MIDI_PITCH_BEND_MAX, bend_value))

        # More conservative emission threshold
        time_since_last = t - last_emission_time
        value_change = abs(bend_value - last_emitted_value)
        
        if (time_since_last >= MIN_TIME_BETWEEN_BENDS_MS / 1000.0 and 
            value_change >= PITCH_BEND_THRESHOLD):
            wobble_data.append((t, bend_value))
            last_emitted_value = bend_value
            last_emission_time = t

    # Always end with center value
    wobble_data.append((duration, MIDI_PITCH_BEND_CENTER))
    return wobble_data

class TapeWobbleEffect(MidiEffect):
    """
    Simulates tape machine pitch instability through wow and flutter effects.
    This is a sequence-level processor that generates MIDI pitch bend messages.
    """
    
    def __init__(self, config: Optional[TapeWobbleConfiguration] = None):
        """Initialize with optional configuration."""
        super().__init__(config or TapeWobbleConfiguration())
        self.config = cast(TapeWobbleConfiguration, self.config)
        self.wobble_state = WobbleState()
    
    def _validate_configuration(self) -> None:
        """Configuration is already validated in TapeWobbleConfiguration.__post_init__"""
        pass
    
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Note-level processing is a no-op for this effect."""
        return ctx
    
    def _process_sequence_impl(self, 
                             events: Sequence[MidiInstruction], 
                             options: Dict) -> List[MidiEvent]:
        """Process the complete sequence, adding pitch bend messages for the wobble effect."""
        if not events:
            return []

        # Convert all events to MidiEvent type and normalize ticks
        normalized_events: List[MidiEvent] = []
        max_tick = 0
        
        for event in events:
            if isinstance(event, tuple):
                try:
                    midi_event = MidiEvent.from_legacy_tuple(event)
                    normalized_events.append(midi_event)
                    max_tick = max(max_tick, midi_event.tick)
                except (ValueError, TypeError):
                    continue
            elif isinstance(event, MidiEvent):
                normalized_events.append(event)
                max_tick = max(max_tick, event.tick)
        
        bpm = options.get('bpm', 120)
        ticks_per_beat = options.get('ticks_per_beat', 480)
        
        # Generate wobble events with full depth
        duration_sec = (max_tick / ticks_per_beat) * (60.0 / bpm)
        wobble_options = {
            'duration_sec': duration_sec,
            'wow_rate_hz': self.config.wow_rate_hz,
            'wow_depth': self.config.wow_depth,
            'flutter_rate_hz': self.config.flutter_rate_hz,
            'flutter_depth': self.config.flutter_depth,
            'randomness': self.config.randomness,
            'depth_units': self.config.depth_units
        }
        
        wobble_data = generate_wobble_data(wobble_options)
        
        # Convert time-based wobble events to tick-based MIDI events
        result_events: List[MidiEvent] = []
        
        # First, add the initial pitch bend center
        result_events.append(MidiEvent.pitch_bend(0, MIDI_PITCH_BEND_CENTER))
        
        # Add all normalized original events
        result_events.extend(normalized_events)
        
        # Add wobble events with proper timing
        for time_sec, bend_value in wobble_data:
            tick = int(round((time_sec * bpm * ticks_per_beat) / 60.0))
            # Only add if we have a significant change
            if abs(bend_value - MIDI_PITCH_BEND_CENTER) > PITCH_BEND_THRESHOLD:
                result_events.append(MidiEvent.pitch_bend(tick, bend_value))
        
        # Add final pitch bend center at the end
        result_events.append(MidiEvent.pitch_bend(max_tick, MIDI_PITCH_BEND_CENTER))
            
        # Sort events using MidiEvent's built-in sorting
        return sorted(result_events)
