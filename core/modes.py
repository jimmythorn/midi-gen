"""
Mode-related functionality for scale and chord generation.
"""

from typing import List
from .musical_constants import CHORD_TONE_INTERVALS, FULL_SCALE_INTERVALS

def get_chord_tone_intervals(mode: str) -> List[int]:
    """
    Returns the characteristic triad intervals for a given mode.
    For example, 'major' returns [0, 4, 7] for Root, Major Third, Perfect Fifth.

    :param mode: String representing the mode.
    :return: List of integer intervals for the chord tones.
    """
    if mode not in CHORD_TONE_INTERVALS:
        raise ValueError(f"Chord tone intervals for mode '{mode}' not recognized.")
    return CHORD_TONE_INTERVALS[mode]

def get_scale(root: int, mode: str, use_chord_tones: bool = True) -> List[int]:
    """
    Generates musical pitch classes based on the root note, mode, and whether to use chord tones or full scale.

    :param root: MIDI note number for the root of the scale.
    :param mode: String representing the mode (e.g., 'major', 'minor').
    :param use_chord_tones: If True (default), returns only chord tones (typically 1st, 3rd, 5th degrees of the mode).
                          If False, returns all notes of the scale.
    :return: List of MIDI pitch classes (0-11) representing the notes.
    """
    intervals_source = FULL_SCALE_INTERVALS
    if use_chord_tones:
        if mode not in CHORD_TONE_INTERVALS:
            raise ValueError(f"Chord tone intervals for mode '{mode}' not defined, but use_chord_tones is True.")
        intervals_source = CHORD_TONE_INTERVALS
    elif mode not in FULL_SCALE_INTERVALS:
        raise ValueError(f"Full scale intervals for mode '{mode}' not recognized.")

    intervals = intervals_source[mode]
    root_midi_pitch_class = root % 12
    return sorted(list(set([(root_midi_pitch_class + interval) % 12 for interval in intervals])))
