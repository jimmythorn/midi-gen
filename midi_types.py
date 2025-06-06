"""
Type definitions and constants for MIDI operations.

This module provides centralized type definitions and constants for MIDI operations,
with a focus on pitch bend functionality and performance optimization.
"""

from typing import Union, Tuple, Literal, TypeVar, List

# Type Definitions
NoteValue = int  # 0-127
Tick = int      # MIDI tick count
Velocity = int  # 0-127
Channel = int   # 0-15
BendValue = int # -8192 to 8191 for MIDO compatibility

# Core MIDI Instruction Types
MidiInstruction = Union[
    Tuple[Literal['note_on'], Tick, NoteValue, Velocity, Channel],     # (type, tick, note, velocity, channel)
    Tuple[Literal['note_off'], Tick, NoteValue, Velocity, Channel],    # (type, tick, note, velocity, channel)
    Tuple[Literal['pitch_bend'], Tick, BendValue, Channel],            # (type, tick, bend_value, channel)
    Tuple[Literal['control_change'], Tick, int, int, Channel],         # (type, tick, control, value, channel)
]

# MIDI Constants
MIDI_PITCH_BEND_MIN = -8192  # MIDO's minimum pitch bend value
MIDI_PITCH_BEND_MAX = 8191   # MIDO's maximum pitch bend value
MIDI_PITCH_BEND_CENTER = 0   # Center/no bend in MIDO's format
SEMITONES_PER_BEND = 2  # Standard pitch bend range in semitones
DEFAULT_TICKS_PER_BEAT = 480

# Performance Optimization Constants
DEFAULT_PITCH_BEND_UPDATE_RATE = 50  # Hz, for smooth transitions
PITCH_BEND_THRESHOLD = 4  # Very small threshold for smoother curves
MIN_TIME_BETWEEN_BENDS_MS = 20  # Quick updates for smooth movement

# Wobble Effect Constants - Bar-synchronized musical movement
DEFAULT_BEND_UP_CENTS = 25.0    # Maximum upward bend
DEFAULT_BEND_DOWN_CENTS = 23.0  # Maximum downward bend (slightly asymmetric)
DEFAULT_RANDOMNESS = 0.05       # Very subtle variation for organic feel

# Wobble State Management
class WobbleState:
    """Maintains state for the wobble effect to ensure smooth transitions."""
    def __init__(self):
        self.last_bend_value: int = MIDI_PITCH_BEND_CENTER
        self.accumulator: float = 0.0
        self.last_emission_time: float = 0.0

    def should_emit_bend(self, new_value: int, current_time: float) -> bool:
        """
        Determines if a new pitch bend message should be emitted based on:
        1. Minimum time between messages
        2. Significant enough value change
        """
        time_delta = current_time - self.last_emission_time
        value_delta = abs(new_value - self.last_bend_value)
        
        return (time_delta >= MIN_TIME_BETWEEN_BENDS_MS / 1000.0 and 
                value_delta >= PITCH_BEND_THRESHOLD)

    def update(self, new_value: int, current_time: float) -> None:
        """Updates the state with new bend value and time."""
        self.last_bend_value = new_value
        self.last_emission_time = current_time 
