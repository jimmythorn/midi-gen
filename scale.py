CHORD_TONE_INTERVALS = {
    'major': [0, 4, 7],      # Major triad (1, 3, 5)
    'minor': [0, 3, 7],      # Minor triad (1, b3, 5)
    'dorian': [0, 3, 7],     # Minor triad (based on its 1, b3, 5)
    'phrygian': [0, 3, 7],   # Minor triad (based on its 1, b3, 5)
    'lydian': [0, 4, 7],     # Major triad (based on its 1, 3, 5; #4 is a color tone outside basic triad)
    'mixolydian': [0, 4, 7], # Major triad (based on its 1, 3, 5; b7 is a color tone)
    'locrian': [0, 3, 6]     # Diminished triad (1, b3, b5)
}

FULL_SCALE_INTERVALS = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10]
}

def get_chord_tone_intervals(mode: str) -> list[int]:
    """
    Returns the characteristic triad intervals for a given mode.
    For example, 'major' returns [0, 4, 7] for Root, Major Third, Perfect Fifth.

    :param mode: String representing the mode.
    :return: List of integer intervals for the chord tones.
    """
    if mode not in CHORD_TONE_INTERVALS:
        # Fallback to minor triad if mode specific triad not defined, or raise error
        # For simplicity, we'll raise an error if a mode's triad isn't explicitly defined.
        raise ValueError(f"Chord tone intervals for mode '{mode}' not recognized.")
    return CHORD_TONE_INTERVALS[mode]

def get_scale(root: int, mode: str, use_chord_tones: bool = True) -> list[int]:
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
        # Ensure mode exists in CHORD_TONE_INTERVALS if use_chord_tones is True
        if mode not in CHORD_TONE_INTERVALS:
            raise ValueError(f"Chord tone intervals for mode '{mode}' not defined, but use_chord_tones is True.")
        intervals_source = CHORD_TONE_INTERVALS
    elif mode not in FULL_SCALE_INTERVALS: # Check if mode is valid for full scales if not using chord tones
        raise ValueError(f"Full scale intervals for mode '{mode}' not recognized.")

    intervals = intervals_source[mode]
    
    root_midi_pitch_class = root % 12
    return sorted(list(set([(root_midi_pitch_class + interval) % 12 for interval in intervals])))
