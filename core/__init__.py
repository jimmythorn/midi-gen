"""
Core functionality for MIDI generation and processing.
"""

from .types import (
    NoteValue,
    Tick,
    Velocity,
    Channel,
    BendValue,
    MidiEvent,
    MIDI_PITCH_BEND_MIN,
    MIDI_PITCH_BEND_MAX,
    MIDI_PITCH_BEND_CENTER,
    SEMITONES_PER_BEND,
    DEFAULT_TICKS_PER_BEAT,
    BEATS_PER_BAR,
    TICKS_PER_BAR
)

from .music import (
    get_scale,
    note_str_to_midi,
    note_to_name,
    SCALE_PATTERNS,
    CHORD_TONE_INDICES
)

from .midi import (
    MidiProcessor,
    create_midi_file
)

__all__ = [
    # Types
    'NoteValue',
    'Tick',
    'Velocity',
    'Channel',
    'BendValue',
    'MidiEvent',
    
    # Constants
    'MIDI_PITCH_BEND_MIN',
    'MIDI_PITCH_BEND_MAX',
    'MIDI_PITCH_BEND_CENTER',
    'SEMITONES_PER_BEND',
    'DEFAULT_TICKS_PER_BEAT',
    'BEATS_PER_BAR',
    'TICKS_PER_BAR',
    
    # Musical operations
    'get_scale',
    'note_str_to_midi',
    'note_to_name',
    'SCALE_PATTERNS',
    'CHORD_TONE_INDICES',
    
    # MIDI processing
    'MidiProcessor',
    'create_midi_file'
]
