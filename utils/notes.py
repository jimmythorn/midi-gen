"""
Utility functions for note name and MIDI number conversions.
"""

from typing import List
from ..core.musical_constants import NOTE_NAMES

def note_str_to_midi(note_str: str) -> int:
    """
    Converts a note string like 'E3' to its MIDI note number.

    :param note_str: String representing a note, e.g., 'E3', 'G#4'.
    :return: Corresponding MIDI note number.
    """
    note = note_str[:-1]  # Remove the octave number
    octave = int(note_str[-1]) + 1  # MIDI starts at -1 for C0, so we add 1
    
    index = NOTE_NAMES.index(note)
    return index + (octave * 12)

def note_to_name(note: int) -> str:
    """
    Converts a MIDI note number to its musical name.

    :param note: MIDI note number.
    :return: String representation of the note (e.g., 'C4').
    """
    octave = note // 12 - 1
    return f"{NOTE_NAMES[note % 12]}{octave}"
