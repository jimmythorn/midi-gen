"""
Core type definitions and constants for MIDI operations.
"""

from typing import Dict, List, Union, TypedDict, Literal

# Basic MIDI types
NoteValue = int  # 0-127
Tick = int      # MIDI tick count
Velocity = int  # 0-127
Channel = int   # 0-15
BendValue = int # -8192 to 8191

class MidiEvent(TypedDict, total=False):
    """Type definition for MIDI events."""
    type: Literal['note_on', 'note_off', 'pitch_bend', 'control_change']
    time: Tick
    note: NoteValue
    velocity: Velocity
    channel: Channel
    value: BendValue  # For pitch bend
    control: int      # For control change

# MIDI Constants
MIDI_PITCH_BEND_MIN = -8192
MIDI_PITCH_BEND_MAX = 8191
MIDI_PITCH_BEND_CENTER = 0
SEMITONES_PER_BEND = 2.0  # Standard pitch bend range
DEFAULT_TICKS_PER_BEAT = 480

# Performance Constants
MIN_TIME_BETWEEN_BENDS_MS = 5.0  # Minimum time between pitch bend messages
PITCH_BEND_THRESHOLD = 4  # Minimum value change to emit new bend

# Musical Constants
BEATS_PER_BAR = 4  # Assuming 4/4 time
TICKS_PER_BAR = DEFAULT_TICKS_PER_BEAT * BEATS_PER_BAR 
