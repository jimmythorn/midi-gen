from midi_gen.core.scale import get_scale
from midi_gen.utils.notes import note_str_to_midi
import random
import math

def create_arpeggio(
    root_notes: list[str],
    mode: str,
    min_octave: int = 4,
    max_octave: int = 6,
    bpm: int = 120,
    bars: int = 16,
    use_chord_tones: bool = True,
    steps: int = 8,
    arp_mode: str = 'up',
    range_octaves: int = 1,
    evolution_rate: float = 0.1,
    repetition_factor: int = 5,
    repeat_pattern: bool = False,
    rhythmic_variation: bool = False,
    chord_progression: list = None,
    embellish: bool = False
) -> list:
    """
    Creates an arpeggio with various musical enhancements.

    Args:
        root_notes: List of root note names (e.g., ["E4", "A4"])
        mode: String representing the mode of the scale
        min_octave: The lowest octave to use for notes
        max_octave: The highest octave to use for notes
        bpm: Beats per minute
        bars: Number of bars to generate
        use_chord_tones: If True, use only chord tones (1,3,5). If False, use all scale notes
        steps: Number of steps in the arpeggio pattern (4, 8, or 16)
        arp_mode: Arpeggiator mode - 'up', 'down', 'up_down', 'random', or 'order'
        range_octaves: Number of octaves to span with the arpeggio
        evolution_rate: Rate at which the arpeggio evolves (0.0 to 1.0)
        repetition_factor: Controls repetition level (1 to 10)
        repeat_pattern: If True, repeat shorter patterns with 16th notes
        rhythmic_variation: If True, introduces syncopation or tuplets
        chord_progression: List of chord roots for harmonic variation
        embellish: If True, adds passing tones and neighbor notes

    Returns:
        List of MIDI events for the arpeggio
    """
    # Convert root notes to MIDI numbers
    root_midi_numbers = [note_str_to_midi(note) for note in root_notes]
    if not root_midi_numbers:
        raise ValueError("At least one root note must be provided")

    # Calculate steps per bar and total steps
    steps_per_bar = 16  # Each bar has 16 16th notes
    total_steps = bars * steps_per_bar

    # Calculate how many bars each root note gets
    bars_per_root = bars // len(root_midi_numbers)
    remaining_bars = bars % len(root_midi_numbers)

    # This will hold all our events
    all_events = []

    # Generate events for each root note
    for i, root in enumerate(root_midi_numbers):
        # Calculate how many bars this root note gets
        current_bars = bars_per_root + (1 if i < remaining_bars else 0)
        if current_bars <= 0:
            continue

        # Get the base pitch classes for this root
        pitch_classes = get_scale(root, mode, use_chord_tones=use_chord_tones)
        if not pitch_classes:
            pitch_classes = [root % 12]

        # Build the source notes across octaves
        arpeggio_source_notes = []
        for octave in range(min_octave, min_octave + range_octaves + 1):
            arpeggio_source_notes.extend([note + (octave * 12) for note in pitch_classes])

        # Ensure we have at least one note
        if not arpeggio_source_notes:
            arpeggio_source_notes = [root + (min_octave * 12)]

        # Generate the pattern for this root
        pattern = []
        if arp_mode == 'up_down':
            # Handle up_down pattern
            half_steps = steps // 2
            remaining_steps = steps - half_steps

            # Up part
            source_up = list(arpeggio_source_notes)
            for i in range(half_steps):
                pattern.append(source_up[i % len(source_up)])

            # Down part
            source_down = list(reversed(arpeggio_source_notes))
            for i in range(remaining_steps):
                pattern.append(source_down[i % len(source_down)])
        else:
            # Handle other patterns
            if arp_mode == 'up':
                pattern = list(arpeggio_source_notes)
            elif arp_mode == 'down':
                pattern = list(reversed(arpeggio_source_notes))
            elif arp_mode == 'random':
                pattern = [random.choice(arpeggio_source_notes) for _ in range(steps)]
            elif arp_mode == 'order':
                pattern = list(arpeggio_source_notes)
                random.shuffle(pattern)
            else:
                pattern = list(arpeggio_source_notes)

            # Apply repetition factor
            if repetition_factor < 10:
                for i in range(len(pattern)):
                    if random.random() > (repetition_factor / 10):
                        pattern[i] = random.choice(arpeggio_source_notes)

        # Calculate how many steps this root note gets
        steps_for_root = current_bars * steps_per_bar

        # Generate events for this root
        root_events = []
        if repeat_pattern or steps == 16:
            # Use 16th notes, repeat the pattern
            repeats = steps_for_root // len(pattern)
            root_events.extend(pattern * repeats)
            root_events.extend(pattern[:(steps_for_root % len(pattern))])
        else:
            # Use longer notes (8th or quarter)
            steps_per_note = steps_per_bar // steps  # 2 for 8 steps, 4 for 4 steps
            for note in pattern:
                root_events.append(note)
                root_events.extend([None] * (steps_per_note - 1))

            # Repeat for all bars for this root
            root_events = root_events * current_bars

        # Apply evolution if needed
        if evolution_rate > 0:
            for i in range(len(root_events)):
                if root_events[i] is not None and random.random() < evolution_rate:
                    if random.random() < 0.5:
                        # Move to adjacent note in scale
                        current_note = root_events[i]
                        try:
                            idx = arpeggio_source_notes.index(current_note)
                            new_idx = (idx + random.choice([-1, 1])) % len(arpeggio_source_notes)
                            root_events[i] = arpeggio_source_notes[new_idx]
                        except ValueError:
                            root_events[i] = random.choice(arpeggio_source_notes)
                    else:
                        # Random note from scale
                        root_events[i] = random.choice(arpeggio_source_notes)

        all_events.extend(root_events)

    # Ensure we have exactly the right number of events
    if len(all_events) > total_steps:
        all_events = all_events[:total_steps]
    elif len(all_events) < total_steps:
        # Pad with None if we're short
        all_events.extend([None] * (total_steps - len(all_events)))

    return all_events
