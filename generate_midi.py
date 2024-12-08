import random
from mido import Message, MidiFile, MidiTrack

def generate_midi_with_options(options):
    """
    Generate a MIDI file with arpeggiation, melodies, timing variance, groove, and rhythmic-based features.
    Adds a subtle pitch wobble to the first note of each bar.
    """
    # Extract options
    notes = options.get('notes', [('C4', 480), ('E4', 480), ('G4', 480), ('C5', 480)])
    style = options.get('style', 'hip_hop')
    bpm = options.get('bpm', 120)
    output_path = options.get('output_path', 'output.mid')
    bars = options.get('bars', 16)  # Ensure 16 bars by default
    timing_variance = options.get('timing_variance', 30)
    swing_strength = options.get('swing_strength', 0.4)  # Strength of groove
    velocity_variance = options.get('velocity_variance', 10)  # Variance in note velocity
    rhythmic_density = options.get('rhythmic_density', 4)  # Control rhythmic density (1/8, 1/16, etc.)
    pitch_wobble_strength = options.get('pitch_wobble_strength', 150)  # Strength of pitch wobble (range 0 to 8191)

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

        # Create rhythmic arpeggiation with specified rhythmic density (e.g., 1/16, 1/8)
        arpeggio = base_notes * rhythmic_density  # Adjust density for note groupings

        # Apply rhythmic variations to arpeggio
        arpeggio_with_rhythm = []
        for note in arpeggio:
            if random.random() < 0.5:
                # Replace note with a random note from the scale
                arpeggio_with_rhythm.append(random.choice(scale))
            else:
                arpeggio_with_rhythm.append(note)
        return arpeggio_with_rhythm

    # Style-specific modifications
    scale = [note_name_to_number(n) for n in ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']]
    if style == 'hip_hop':
        timing_variance = 60
    elif style == 'classical':
        timing_variance = 10
    elif style == 'rock':
        timing_variance = 40

    # Generate the arpeggio sequence with rhythmic focus
    arpeggiated_notes = arpeggiate_with_melody(notes, scale)

    # Add notes to the track
    time_elapsed = 0
    first_note_in_bar = True  # Flag to handle the very first note of each bar

    while time_elapsed < total_ticks:
        for midi_note in arpeggiated_notes:
            if time_elapsed >= total_ticks:
                break

            # Determine note duration with rhythmic structure (1/16 or 1/8 notes)
            if rhythmic_density == 4:
                # 1/16 note rhythm
                duration = ticks_per_beat // 4
            elif rhythmic_density == 2:
                # 1/8 note rhythm
                duration = ticks_per_beat // 2
            else:
                # Default to 1/4 note if rhythmic_density isn't 1/16 or 1/8
                duration = ticks_per_beat

            # Apply timing variance (except for the first note)
            if first_note_in_bar:
                time = 0  # First note starts at the beginning of the track
            else:
                variance = random.randint(-timing_variance, timing_variance)
                time = max(0, duration + variance)  # Ensure no negative time

            # Humanize note velocity (variation within a range)
            velocity = random.randint(50, 127)  # Base velocity range
            velocity += random.randint(-velocity_variance, velocity_variance)  # Apply variance
            velocity = max(1, min(127, velocity))  # Ensure the velocity stays within MIDI range

            # Add pitch wobble to the first note of each bar
            if first_note_in_bar:
                # Apply subtle pitch wobble with a random pitch bend (between -8192 and 8191)
                pitch_bend_value = random.randint(-pitch_wobble_strength, pitch_wobble_strength)
                pitch_bend_value = max(-8192, min(8191, pitch_bend_value))  # Ensure it's within the valid range
                track.append(Message('pitchwheel', time=0, pitch=pitch_bend_value))  # Pitch wheel at the start of the note

            # Add note on/off messages
            track.append(Message('note_on', note=midi_note, velocity=velocity, time=time))
            track.append(Message('note_off', note=midi_note, velocity=velocity, time=duration))

            # Update elapsed time
            time_elapsed += time + duration

            # Update bar flag
            first_note_in_bar = False
            if time_elapsed % ticks_per_bar == 0:
                first_note_in_bar = True  # Reset flag for the first note of the next bar

    # Save the MIDI file
    mid.save(output_path)
    print(f"MIDI file generated and saved to {output_path}")
