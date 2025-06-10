"""
Type definitions and constants for MIDI operations.

This module provides centralized type definitions and constants for MIDI operations,
with a focus on pitch bend functionality and performance optimization.
"""

from typing import Union, Tuple, Literal, TypeVar, List, TypeAlias
from dataclasses import dataclass
from enum import Enum, auto

# Type Definitions
NoteValue = int  # 0-127
Tick = int      # MIDI tick count
Velocity = int  # 0-127
Channel = int   # 0-15
BendValue = int # -8192 to 8191 for MIDO compatibility

# Legacy type for structured MIDI events
MidiEvent = Tuple[int, int, int, int]  # (note, start_tick, duration_tick, velocity)

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

# Wobble Effect Constants - Note-synchronized musical movement
DEFAULT_BEND_UP_CENTS = 23.0    # Maximum upward bend
DEFAULT_BEND_DOWN_CENTS = 21.0  # Maximum downward bend (slightly asymmetric)
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

class MidiEventType(Enum):
    """Enumeration of MIDI event types."""
    NOTE_ON = auto()
    NOTE_OFF = auto()
    PITCH_BEND = auto()
    CONTROL_CHANGE = auto()

@dataclass(frozen=True)
class MidiEvent:
    """Immutable representation of a MIDI event."""
    event_type: MidiEventType
    tick: Tick
    value1: int  # note number for notes, controller number for CC, bend value for pitch bend
    value2: int  # velocity for notes, value for CC, unused for pitch bend
    channel: Channel = 0

    def __post_init__(self):
        """Validate event values."""
        if not isinstance(self.tick, int) or self.tick < 0:
            raise ValueError(f"Invalid tick value: {self.tick}")
        if not isinstance(self.channel, int) or not 0 <= self.channel <= 15:
            raise ValueError(f"Invalid channel: {self.channel}")
        
        if self.event_type == MidiEventType.NOTE_ON or self.event_type == MidiEventType.NOTE_OFF:
            if not 0 <= self.value1 <= 127:  # note number
                raise ValueError(f"Invalid note value: {self.value1}")
            if not 0 <= self.value2 <= 127:  # velocity
                raise ValueError(f"Invalid velocity value: {self.value2}")
        elif self.event_type == MidiEventType.PITCH_BEND:
            if not MIDI_PITCH_BEND_MIN <= self.value1 <= MIDI_PITCH_BEND_MAX:
                raise ValueError(f"Invalid pitch bend value: {self.value1}")
        elif self.event_type == MidiEventType.CONTROL_CHANGE:
            if not 0 <= self.value1 <= 127:  # controller number
                raise ValueError(f"Invalid controller number: {self.value1}")
            if not 0 <= self.value2 <= 127:  # controller value
                raise ValueError(f"Invalid controller value: {self.value2}")

    @classmethod
    def note_on(cls, tick: Tick, note: NoteValue, velocity: Velocity, channel: Channel = 0) -> 'MidiEvent':
        """Create a note-on event."""
        return cls(MidiEventType.NOTE_ON, tick, note, velocity, channel)

    @classmethod
    def note_off(cls, tick: Tick, note: NoteValue, velocity: Velocity = 0, channel: Channel = 0) -> 'MidiEvent':
        """Create a note-off event."""
        return cls(MidiEventType.NOTE_OFF, tick, note, velocity, channel)

    @classmethod
    def pitch_bend(cls, tick: Tick, value: BendValue, channel: Channel = 0) -> 'MidiEvent':
        """Create a pitch bend event."""
        return cls(MidiEventType.PITCH_BEND, tick, value, 0, channel)

    @classmethod
    def control_change(cls, tick: Tick, controller: int, value: int, channel: Channel = 0) -> 'MidiEvent':
        """Create a control change event."""
        return cls(MidiEventType.CONTROL_CHANGE, tick, controller, value, channel)

    def to_legacy_tuple(self) -> Tuple:
        """Convert to legacy tuple format for backward compatibility."""
        if self.event_type == MidiEventType.NOTE_ON:
            return ('note_on', self.tick, self.value1, self.value2, self.channel)
        elif self.event_type == MidiEventType.NOTE_OFF:
            return ('note_off', self.tick, self.value1, self.value2, self.channel)
        elif self.event_type == MidiEventType.PITCH_BEND:
            return ('pitch_bend', self.tick, self.value1, 0, self.channel)
        else:
            return ('control_change', self.tick, self.value1, self.value2, self.channel)

    @classmethod
    def from_legacy_tuple(cls, event_tuple: Tuple) -> 'MidiEvent':
        """Create from legacy tuple format."""
        if not isinstance(event_tuple, tuple) or len(event_tuple) < 4:
            raise ValueError(f"Invalid event tuple: {event_tuple}")
            
        event_type, tick, value1, value2, *rest = event_tuple
        channel = rest[0] if rest else 0
        
        if event_type == 'note_on':
            return cls.note_on(tick, value1, value2, channel)
        elif event_type == 'note_off':
            return cls.note_off(tick, value1, value2, channel)
        elif event_type == 'pitch_bend':
            return cls.pitch_bend(tick, value1, channel)
        elif event_type == 'control_change':
            return cls.control_change(tick, value1, value2, channel)
        else:
            raise ValueError(f"Unknown event type: {event_type}")

    def __lt__(self, other: 'MidiEvent') -> bool:
        """Enable sorting of events."""
        if not isinstance(other, MidiEvent):
            return NotImplemented
        # Sort by tick first
        if self.tick != other.tick:
            return self.tick < other.tick
        # For same tick, sort by event type priority
        self_priority = self._get_event_priority()
        other_priority = other._get_event_priority()
        return self_priority < other_priority

    def _get_event_priority(self) -> int:
        """Get priority for event sorting (lower = earlier)."""
        priorities = {
            MidiEventType.PITCH_BEND: 0,
            MidiEventType.CONTROL_CHANGE: 1,
            MidiEventType.NOTE_ON: 2,
            MidiEventType.NOTE_OFF: 3
        }
        return priorities[self.event_type]

# Type alias for backward compatibility
MidiInstruction: TypeAlias = Union[Tuple, MidiEvent] 
