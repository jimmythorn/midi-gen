import random
from mido import Message, MidiFile, MidiTrack

def generate_midi_with_options(options):
    """
    Generate a MIDI file with arpeggiation, melodies, timing variance, swing, and velocity humanization.
    Ensures the first note always starts on the 1 beat without timing variance.
    """
    # Extract options
    notes = options.get('notes', [('C4', 480), ('E4', 480), ('G4', 480), ('C5', 480)])
    style = options.get('style', 'hip_hop')
    bpm = options.get('bpm', 120)
    output_path = options.get('output_path', 'output.mid')
    bars = options.get('bars', 16)  # Ensure 16 bars by default
    min_duration = options.get('min_duration', 240)
    max_duration = options.get('max_duration', 480)
    sustain_duration = options.get('sustain_duration', 1920)
    timing_variance = options.get('timing_variance', 30)
    note_spacing = options.get('note_spacing', 120)  # Default to 1/16 note spacing (120 ticks)
    swing_strength = options.get('swing_strength', 0.4)  # Strength of groove
    velocity_variance = options.get('velocity_variance', 10)  # Variance in note velocity (default: 10)

    # Constants
    ticks_per_beat = 480  # Standard resolution for most MIDI files
    beats_per_bar = 4  # 4/4 time signature
    ticks_per_bar = ticks_per_beat * beats_per_bar
    total_ticks = ticks_per_bar * bars

    # Create a new MIDI file and track
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Note-to-MIDI conversion
    note_to_midi = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4,
        'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9,
        'A#': 10, 'B': 11
    }

    def note_name_to_number(note):
        pitch = note[:-1]
        octave = int(note[-1])
        return 12 * (octave + 1) + note_to_midi[pitch]

    # Generate arpeggios with melody variations
    def arpeggiate_with_melody(notes, scale):
        # Convert notes to MIDI numbers
        base_notes = [note_name_to_number(note[0]) for note in notes]
        base_notes.sort()  # Ensure ascending order

        # Create ascending and descending pattern (1/16 note arpeggiation)
        arpeggio = base_notes * 4  # This will create more density in the arpeggiation (4 repetitions)

        # Apply melodic variations to arpeggio
        arpeggio_with_melody = []
        for note in arpeggio:
            if random.random() < 0.5:
                # Replace note with a random note from the scale
                arpeggio_with_melody.append(random.choice(scale))
            else:
                arpeggio_with_melody.append(note)
        return arpeggio_with_melody

    # Style-specific modifications
    scale = [note_name_to_number(n) for n in ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']]
    if style == 'hip_hop':
        timing_variance = 60
    elif style == 'classical':
        timing_variance = 10
    elif style == 'rock':
        timing_variance = 40

    # Generate the arpeggio sequence with melodic variations
    arpeggiated_notes = arpeggiate_with_melody(notes, scale)

    # Add notes to the track
    time_elapsed = 0
    first_note = True  # Flag to handle the very first note

    while time_elapsed < total_ticks:
        for midi_note in arpeggiated_notes:
            if time_elapsed >= total_ticks:
                break

            # Determine note duration with variable spacing (1/16 notes)
            duration = random.randint(min_duration, max_duration)

            # Apply timing variance (except for the first note)
            if first_note:
                time = 0  # First note starts at the beginning of the track
            else:
                variance = random.randint(-timing_variance, timing_variance)
                time = max(0, duration + variance)  # Ensure no negative time

            # Humanize note velocity (variation within a range)
            velocity = random.randint(50, 127)  # Base velocity range
            velocity += random.randint(-velocity_variance, velocity_variance)  # Apply variance
            velocity = max(1, min(127, velocity))  # Ensure the velocity stays within MIDI range

            # Add note on/off messages
            track.append(Message('note_on', note=midi_note, velocity=velocity, time=time))
            track.append(Message('note_off', note=midi_note, velocity=velocity, time=duration))

            # Update elapsed time
            time_elapsed += time + duration
            first_note = False  # Ensure only the first note is not humanized

    # Save the MIDI file
    mid.save(output_path)
    print(f"MIDI file generated and saved to {output_path}")
