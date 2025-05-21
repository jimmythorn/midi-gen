def get_scale(root: int, mode: str) -> list:
    """
    Generates a musical scale based on the root note and mode.

    :param root: MIDI note number for the root of the scale.
    :param mode: String representing the mode (e.g., 'major', 'minor').
    :return: List of MIDI numbers representing the scale.
    """
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
        'locrian': [0, 1, 3, 5, 6, 8, 10]
    }
    if mode not in scales:
        raise ValueError("Mode not recognized")
    
    root_midi = root % 12
    return [(root_midi + interval) % 12 for interval in scales[mode]]
