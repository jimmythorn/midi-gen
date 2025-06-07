"""
Core musical operations and utilities.
"""

from typing import List, Dict, Optional

# Scale definitions
SCALE_PATTERNS = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10]
}

# Chord tone indices in scale degrees (0-based)
CHORD_TONE_INDICES = [0, 2, 4]  # Root, Third, Fifth

def get_scale(root: int, mode: str, use_chord_tones: bool = False) -> List[int]:
    """Get scale or chord tones for a given root note and mode.
    
    Args:
        root: MIDI note number of the root
        mode: Scale mode ('major', 'minor', etc.)
        use_chord_tones: If True, return only chord tones
    
    Returns:
        List of MIDI note numbers in the scale/chord
    """
    if mode not in SCALE_PATTERNS:
        return []
    
    # Get the pitch class of the root note
    root_pc = root % 12
    
    # Get the scale pattern
    pattern = SCALE_PATTERNS[mode]
    
    # Generate all pitch classes in the scale
    scale_pcs = [(root_pc + interval) % 12 for interval in pattern]
    
    if use_chord_tones:
        # Return only chord tones (root, third, fifth)
        return [scale_pcs[i] for i in CHORD_TONE_INDICES if i < len(scale_pcs)]
    
    return scale_pcs

def note_str_to_midi(note_str: str) -> int:
    """Convert a note string (e.g., 'C4', 'F#5') to MIDI note number."""
    # Note name to semitone mapping
    NOTE_TO_SEMITONE = {
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4,
        'F': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11
    }
    
    # Handle empty or invalid input
    if not note_str:
        return 60  # Middle C as default
    
    # Parse note and octave
    note = ''
    octave = ''
    for char in note_str:
        if char.isdigit() or char == '-':
            octave += char
        else:
            note += char
    
    # Get base semitone for note
    base = NOTE_TO_SEMITONE.get(note, 0)
    
    # Calculate MIDI note number
    try:
        octave_num = int(octave) if octave else 4
        midi_note = base + (octave_num + 1) * 12
        return max(0, min(127, midi_note))
    except ValueError:
        return 60  # Middle C as fallback

def note_to_name(midi_note: int) -> str:
    """Convert a MIDI note number to note name (e.g., 60 -> 'C4')."""
    SEMITONE_TO_NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    if not 0 <= midi_note <= 127:
        return 'C4'  # Default to middle C
    
    note_name = SEMITONE_TO_NOTE[midi_note % 12]
    octave = (midi_note // 12) - 1
    
    return f"{note_name}{octave}" 
