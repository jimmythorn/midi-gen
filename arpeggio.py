from .scale import get_scale
import random
import math

def create_arpeggio(root: int, mode: str, length: int = 16, min_octave: int = 4, max_octave: int = 6, arp_mode: str = 'up', range_octaves: int = 1, evolution_rate: float = 0.1, repetition_factor: int = 5, rhythmic_variation: bool = False, chord_progression: list = None, embellish: bool = False) -> list:
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
    :return: List of MIDI note numbers forming the arpeggio with enhancements.
    """
    scale = get_scale(root, mode)
    arpeggio = []
    full_scale = []
    
    # Build the full scale across octaves
    for octave in range(min_octave, min_octave + range_octaves + 1):
        full_scale.extend([note + (octave * 12) for note in scale])

    # Base Pattern Creation
    if arp_mode == 'up':
        pattern = full_scale
    elif arp_mode == 'down':
        pattern = list(reversed(full_scale))
    elif arp_mode == 'up_down':
        pattern = full_scale + list(reversed(full_scale[1:-1]))  # Up and then down
    elif arp_mode == 'random':
        pattern = [random.choice(full_scale) for _ in range(length)]
    elif arp_mode == 'order':
        pattern = full_scale
        random.shuffle(pattern)

    # Adjust for repetition_factor
    repetition_factor = max(1, min(10, repetition_factor))
    pattern = pattern * (length // len(pattern) + 1)
    if repetition_factor < 10:
        for i in range(len(pattern)):
            if random.random() > (repetition_factor / 10):
                pattern[i] = random.choice(full_scale)

    base_pattern = pattern[:length]

    # Rhythmic Variation
    if rhythmic_variation:
        syncopated = [note if i % 4 != 3 else None for i, note in enumerate(base_pattern)]  # Syncopation on 4th step of each group
        tuplets = []
        for i in range(0, length, 3):  # Every 3 notes, group into triplets
            if i + 2 < length:
                tuplets.extend(base_pattern[i:i+3])
            else:
                tuplets.extend(base_pattern[i:])
                tuplets.extend([None] * (3 - (length - i)))  # Pad with None for rhythm
        base_pattern = syncopated if random.choice([True, False]) else tuplets

    # Harmonic Variation with Chord Progression
    if chord_progression:
        arpeggio = []
        current_chord = 0
        for i, note in enumerate(base_pattern):
            if i % (length // len(chord_progression)) == 0:  # Change chord every segment
                current_chord = (current_chord + 1) % len(chord_progression)
                new_root = chord_progression[current_chord]  # Assume this is a MIDI note number for the new root
                scale = get_scale(new_root, mode)
                full_scale = [n + (octave * 12) for octave in range(min_octave, min_octave + range_octaves + 1) for n in scale]
            # Map current note to the new scale or use original if not found
            arpeggio.append(min(full_scale, key=lambda x: abs(x - note)) if note is not None else None)
    else:
        arpeggio = base_pattern

    # Melodic Embellishments
    if embellish:
        embellished_arpeggio = []
        for note in arpeggio:
            if note is not None:
                if random.random() < 0.3:  # 30% chance for embellishment
                    if random.random() < 0.5:  # Passing tone
                        index = full_scale.index(note)
                        embellished_arpeggio.append(full_scale[(index + 1) % len(full_scale)])
                    else:  # Neighbor note
                        index = full_scale.index(note)
                        embellished_arpeggio.append(full_scale[(index + random.choice([-1, 1])) % len(full_scale)])
                embellished_arpeggio.append(note)
            else:
                embellished_arpeggio.append(None)
        arpeggio = embellished_arpeggio

    # Evolution Mechanism (unchanged from previous)
    if evolution_rate > 0:
        evolved_arpeggio = []
        for i, note in enumerate(arpeggio):
            if note is not None and random.random() < evolution_rate:
                if random.random() < 0.5:
                    index = full_scale.index(note)
                    new_index = (index + random.choice([-1, 1])) % len(full_scale)
                    evolved_arpeggio.append(full_scale[new_index])
                else:
                    evolved_arpeggio.append(random.choice(full_scale))
            else:
                evolved_arpeggio.append(note)
        arpeggio = evolved_arpeggio

    # Remove None values if they exist due to rhythmic variation
    return [note for note in arpeggio if note is not None][:length]
