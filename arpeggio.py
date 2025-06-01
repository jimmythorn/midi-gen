from .scale import get_scale
import random
import math

def create_arpeggio(root: int, mode: str, length: int = 16, min_octave: int = 4, max_octave: int = 6, arp_mode: str = 'up', range_octaves: int = 1, evolution_rate: float = 0.1, repetition_factor: int = 5, rhythmic_variation: bool = False, chord_progression: list = None, embellish: bool = False, use_chord_tones: bool = True) -> list:
    """
    Creates an arpeggio with various musical enhancements.

    :param root: MIDI note number for the root of the scale.
    :param mode: String representing the mode of the scale.
    :param length: Number of notes in the arpeggio.
    :param min_octave: The lowest octave to use for notes.
    :param max_octave: The highest octave to use for notes.
    :param arp_mode: Arpeggiator mode - 'up', 'down', 'up_down', 'random', or 'order'.
    :param range_octaves: Number of octaves to span with the arpeggio.
    :param evolution_rate: Rate at which the arpeggio evolves (0.0 to 1.0, where 0 is no evolution).
    :param repetition_factor: Controls the level of repetition in the arpeggio (1 to 10, 10 being most repetitive).
    :param rhythmic_variation: If True, introduces syncopation or tuplets.
    :param chord_progression: List of chord roots for harmonic variation.
    :param embellish: If True, adds passing tones and neighbor notes.
    :param use_chord_tones: If True (default), arpeggiates using only chord tones (1,3,5 of the mode). 
                            If False, uses all notes of the scale.
    :return: List of MIDI note numbers forming the arpeggio with enhancements.
    """
    # Get the base pitch classes (either chord tones or full scale)
    pitch_classes = get_scale(root, mode, use_chord_tones=use_chord_tones)
    
    # Ensure pitch_classes is not empty before proceeding, especially if a mode might result in no chord tones (e.g. if definition was missing)
    if not pitch_classes:
        # Fallback to a simple root note arpeggio across octaves if scale/chord tones are empty
        # This prevents errors if a mode/chord tone definition is somehow missing or results in an empty list.
        # A more robust solution might be to raise an error or log a warning.
        pitch_classes = [root % 12] 

    arpeggio_source_notes = []
    
    # Build the source notes across octaves
    for octave in range(min_octave, min_octave + range_octaves + 1):
        arpeggio_source_notes.extend([note + (octave * 12) for note in pitch_classes])
    
    # Ensure arpeggio_source_notes is not empty if pitch_classes was valid but octaves didn't yield notes
    if not arpeggio_source_notes:
        # This might happen if min_octave is too high for the root + pitch classes
        # Fallback to just the root note at the min_octave if all else fails
        arpeggio_source_notes = [root % 12 + min_octave * 12]
        # Or, perhaps more safely, if the initial range is problematic:
        # arpeggio_source_notes = [pc + min_octave * 12 for pc in pitch_classes]
        # For now, ensuring at least one note is available.
        if not arpeggio_source_notes: # Still empty after trying with min_octave
             arpeggio_source_notes = [(root % 12) + 4 * 12] # Default to C4 if all else fails

    base_pattern = []

    if arp_mode == 'up_down':
        # New 'up_down' logic: constructs a pattern of exactly 'length' notes.
        # It does not use the subsequent repetition_factor block.
        if not arpeggio_source_notes: # Safeguard
             arpeggio_source_notes = [(root % 12) + min_octave * 12]

        half_length = length // 2
        remaining_length = length - half_length

        source_up = list(arpeggio_source_notes)
        for i in range(half_length):
            if source_up: # Check if source_up is not empty
                base_pattern.append(source_up[i % len(source_up)])
            elif arpeggio_source_notes: # Fallback to original source if source_up became empty (should not happen)
                base_pattern.append(arpeggio_source_notes[i % len(arpeggio_source_notes)])
            else: # Absolute fallback
                base_pattern.append((root % 12) + min_octave * 12)
        
        source_down = list(reversed(arpeggio_source_notes))
        for i in range(remaining_length):
            if source_down: # Check if source_down is not empty
                base_pattern.append(source_down[i % len(source_down)])
            elif arpeggio_source_notes: # Fallback
                base_pattern.append(list(reversed(arpeggio_source_notes))[i % len(list(reversed(arpeggio_source_notes)))])
            else: # Absolute fallback
                base_pattern.append((root % 12) + min_octave * 12)
        # base_pattern is now of 'length' and ready.
    else:
        # Original logic for 'up', 'down', 'random', 'order' that uses an intermediate 'pattern'
        # which is then processed by repetition_factor.
        intermediate_pattern = []
        if arp_mode == 'up':
            intermediate_pattern = list(arpeggio_source_notes)
        elif arp_mode == 'down':
            intermediate_pattern = list(reversed(arpeggio_source_notes))
        elif arp_mode == 'random':
            if arpeggio_source_notes: # Check for empty list
                 intermediate_pattern = [random.choice(arpeggio_source_notes) for _ in range(len(arpeggio_source_notes))] # Create a pattern of same length as source for now
            else:
                 intermediate_pattern = [(root % 12 + min_octave * 12)]
        elif arp_mode == 'order': 
            intermediate_pattern = list(arpeggio_source_notes) 
            random.shuffle(intermediate_pattern)
        else: # Default or unrecognized arp_mode (should not happen if CLI is validated)
            intermediate_pattern = list(arpeggio_source_notes) # Default to 'up' behavior for pattern source

        if not intermediate_pattern: # Handle cases where pattern might be empty
            intermediate_pattern = [(root % 12 + min_octave * 12)] # Fallback to root note if empty

        # Adjust for repetition_factor using the intermediate_pattern
        repetition_factor = max(1, min(10, repetition_factor))
        if len(intermediate_pattern) > 0:
            # Expand based on length of intermediate_pattern relative to desired final 'length'
            expanded_pattern = intermediate_pattern * (length // len(intermediate_pattern) + 1)
            if repetition_factor < 10:
                for i in range(len(expanded_pattern)):
                    if random.random() > (repetition_factor / 10):
                        if arpeggio_source_notes: 
                            expanded_pattern[i] = random.choice(arpeggio_source_notes)
            base_pattern = expanded_pattern[:length]
        else:
            base_pattern = [] # Should be caught by earlier check, but as safeguard

    # Ensure base_pattern is exactly `length` notes, especially if fallbacks occurred or length was 0.
    if len(base_pattern) != length:
        # If too short (e.g. length was 0 or pattern construction failed), fill with root note or truncate.
        # This primarily guards against length=0 or issues if arpeggio_source_notes was initially empty.
        if not arpeggio_source_notes and length > 0 : arpeggio_source_notes = [(root % 12 + min_octave * 12)]
        
        if length == 0: base_pattern = []
        elif len(base_pattern) < length and arpeggio_source_notes:
            # Tile the first note of arpeggio_source_notes to fill remaining space
            filler_note = arpeggio_source_notes[0]
            base_pattern.extend([filler_note] * (length - len(base_pattern)))
        elif len(base_pattern) > length:
            base_pattern = base_pattern[:length]
        elif not base_pattern and length > 0 and arpeggio_source_notes: # Completely empty, fill from source
             source_fill = list(arpeggio_source_notes)
             for i in range(length):
                 base_pattern.append(source_fill[i % len(source_fill)])

    # Rhythmic Variation (ensure base_pattern is not empty)
    if rhythmic_variation and base_pattern:
        syncopated = [note if i % 4 != 3 else None for i, note in enumerate(base_pattern)]
        tuplets = []
        for i in range(0, length, 3):
            if i + 2 < length:
                tuplets.extend(base_pattern[i:i+3])
            else:
                tuplets.extend(base_pattern[i:])
                if len(base_pattern[i:]) < 3 and length > len(base_pattern[i:]):
                     tuplets.extend([None] * (3 - len(base_pattern[i:]))) 
        base_pattern = syncopated if random.choice([True, False]) else tuplets

    current_arpeggio = []
    # Harmonic Variation with Chord Progression
    if chord_progression and base_pattern:
        prog_arpeggio = []
        current_chord_index = 0
        # Determine notes per chord segment
        notes_per_segment = length // len(chord_progression) if len(chord_progression) > 0 else length
        
        for i, note_in_pattern in enumerate(base_pattern):
            if notes_per_segment > 0 and i % notes_per_segment == 0 and i // notes_per_segment < len(chord_progression):
                current_chord_index = i // notes_per_segment
            
            new_root = chord_progression[current_chord_index]
            # Get pitch classes for the new chord root and current mode (and use_chord_tones setting)
            current_chord_pitch_classes = get_scale(new_root, mode, use_chord_tones=use_chord_tones)
            
            # Build full range of notes for this chord
            current_chord_full_range = []
            for octave in range(min_octave, min_octave + range_octaves + 1):
                current_chord_full_range.extend([pc + (octave * 12) for pc in current_chord_pitch_classes])
            
            if not current_chord_full_range: # Fallback if no notes generated
                prog_arpeggio.append(note_in_pattern) # Keep original pattern note
                continue

            if note_in_pattern is not None:
                # Map current pattern note to the closest note in the new chord's full range
                prog_arpeggio.append(min(current_chord_full_range, key=lambda x: abs(x - note_in_pattern)))
            else:
                prog_arpeggio.append(None) # Preserve rests from rhythmic variation
        current_arpeggio = prog_arpeggio
    else:
        current_arpeggio = list(base_pattern) # Ensure it's a mutable list

    # Melodic Embellishments (ensure current_arpeggio and arpeggio_source_notes are not empty)
    if embellish and current_arpeggio and arpeggio_source_notes:
        embellished_arpeggio = []
        for note in current_arpeggio:
            if note is not None:
                if random.random() < 0.3:  # 30% chance for embellishment
                    # Ensure arpeggio_source_notes has notes to pick from for embellishment
                    # And that the current note is actually in arpeggio_source_notes to find its index
                    try:
                        index = arpeggio_source_notes.index(note % 12 + (note // 12) * 12) # Normalize note to find in source
                        if random.random() < 0.5:  # Passing tone
                            embellished_arpeggio.append(arpeggio_source_notes[(index + 1) % len(arpeggio_source_notes)])
                        else:  # Neighbor note
                            embellished_arpeggio.append(arpeggio_source_notes[(index + random.choice([-1, 1])) % len(arpeggio_source_notes)])
                    except ValueError: # Note not in arpeggio_source_notes, skip embellishment for this note
                        pass      
                embellished_arpeggio.append(note)
            else:
                embellished_arpeggio.append(None)
        current_arpeggio = embellished_arpeggio

    # Evolution Mechanism (ensure current_arpeggio and arpeggio_source_notes are not empty)
    if evolution_rate > 0 and current_arpeggio and arpeggio_source_notes:
        evolved_arpeggio = []
        for i, note in enumerate(current_arpeggio):
            if note is not None and random.random() < evolution_rate:
                if random.random() < 0.5:
                    try:
                        index = arpeggio_source_notes.index(note % 12 + (note // 12) * 12) # Normalize note
                        new_index = (index + random.choice([-1, 1])) % len(arpeggio_source_notes)
                        evolved_arpeggio.append(arpeggio_source_notes[new_index])
                    except ValueError:
                        evolved_arpeggio.append(random.choice(arpeggio_source_notes)) # Fallback if note not in source
                else:
                    evolved_arpeggio.append(random.choice(arpeggio_source_notes))
            else:
                evolved_arpeggio.append(note)
        current_arpeggio = evolved_arpeggio

    # Remove None values and ensure correct length
    final_arpeggio = [note for note in current_arpeggio if note is not None]
    return final_arpeggio[:length] if length > 0 else final_arpeggio
