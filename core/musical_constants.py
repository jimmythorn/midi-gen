"""
Musical constants and basic definitions used throughout the MIDI generator.
"""

# Note names and their corresponding indices
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Chord tone intervals for different modes
CHORD_TONE_INTERVALS = {
    'major': [0, 4, 7],      # Major triad (1, 3, 5)
    'minor': [0, 3, 7],      # Minor triad (1, b3, 5)
    'dorian': [0, 3, 7],     # Minor triad (based on its 1, b3, 5)
    'phrygian': [0, 3, 7],   # Minor triad (based on its 1, b3, 5)
    'lydian': [0, 4, 7],     # Major triad (based on its 1, 3, 5; #4 is a color tone outside basic triad)
    'mixolydian': [0, 4, 7], # Major triad (based on its 1, 3, 5; b7 is a color tone)
    'locrian': [0, 3, 6]     # Diminished triad (1, b3, b5)
}

# Full scale intervals for different modes
FULL_SCALE_INTERVALS = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10]
}
