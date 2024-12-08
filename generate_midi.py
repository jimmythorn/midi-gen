import random
from mido import Message, MidiFile, MidiTrack

def generate_midi_with_options(options):
    """
    Generate a MIDI file with customizable options for different musical styles (e.g., Hip Hop, Classical, Rock, Pad).
    
    Parameters:
        options (dict): Configuration options for MIDI generation.
            - style (str): Musical style ('hip_hop', 'classical', 'rock', 'pad').
            - notes (list of tuples): Sequence of notes and durations [(note, duration), ...].
            - swing_ratio (float): Ratio for swing timing (e.g., 0.6 for 60% long, 40% short).
            - timing_variance (int): Max ticks for random timing deviations.
            - glitch_probability (float): Chance a note glitches (0 to 1).
            - glitch_duration_reduction (float): Fraction of duration to reduce for glitches.
            - bpm (int): Beats per minute (e.g., 120).
            - output_path (str): Path to save the generated MIDI file.
            - bars (int): Number of bars to generate (e.g., 4 bars).
            - min_duration (int): Minimum duration for the notes (in ticks).
            - max_duration (int): Maximum duration for the notes (in ticks).
            - sustain_duration (int): Duration for sustained notes (in ticks).
    """
    notes = options.get('notes', [('C4', 480), ('E4', 480), ('G4', 480), ('C5', 480)])
    style = options.get('style', 'hip_hop')
    swing_ratio = options.get('swing_ratio', 0.6)
    timing_variance = options.get('timing_variance', 30)
    glitch_probability = options.get('glitch_probability', 0.3)
    glitch_duration_reduction = options.get('glitch_duration_reduction', 0.5)
    bpm = options.get('bpm', 120)
    output_path = options.get('output_path', 'output.mid')
    bars = options.get('bars', 4)  # Number of bars to generate
    min_duration = options.get('min_duration', 240)  # Minimum note duration in ticks (default 240 = half beat)
    max_duration = options.get('max_duration', 960)  # Maximum note duration in ticks (default 960 = two beats)
    sustain_duration = options.get('sustain_duration', 1920)  # Sustain duration for pad (default 4 beats)

    # Constants
    ticks_per_beat = 480  # Standard resolution for most MIDI files
    beats_per_bar = 4  # 4/4 time signature
    ticks_per_bar = ticks_per_beat * beats_per_bar  # Ticks per bar (4 beats per bar)

    # Calculate the total ticks for the given number of bars
    total_ticks_for_bars = ticks_per_bar * bars

    # Create a new MIDI file and track
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Helper function to convert note names to MIDI numbers
    note_to_midi = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4,
        'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9,
        'A#': 10, 'B': 11
    }

    def note_name_to_number(note):
        pitch = note[:-1]
        octave = int(note[-1])
        return 12 * (octave + 1) + note_to_midi[pitch]

    # Apply stylistic changes
    if style == 'hip_hop':
        notes = [('C4', 480), ('E4', 480), ('G4', 480), ('A3', 480)]  # Typical Hip Hop chord progression
        timing_variance = 60  # More swing and off-beat rhythms
        glitch_probability = 0.5  # Higher glitch chance for a more "lo-fi" feel
        sustain_duration = 960  # Shorter sustain for punchy feel

    elif style == 'classical':
        notes = [('C4', 960), ('E4', 960), ('G4', 960), ('C5', 960)]  # Classical harmonic progressions
        timing_variance = 0  # More structured rhythms
        glitch_probability = 0  # No glitches for classical
        sustain_duration = 1920  # Longer sustained notes for classical legato feel

    elif style == 'rock':
        notes = [('E3', 480), ('G3', 480), ('B3', 480), ('D4', 480)]  # Power chord progression
        timing_variance = 40  # More syncopated rhythm
        glitch_probability = 0.2  # Lower glitch chance for a more consistent rhythm
        sustain_duration = 960  # Moderate sustain for guitar chords

    elif style == 'pad':
        # Pad style: Notes held for the entire duration of 4 bars
        sustain_duration = total_ticks_for_bars  # Full 4 bars for pad style
        # Use basic harmonic progression for a pad
        notes = [('C4', sustain_duration), ('E4', sustain_duration), ('G4', sustain_duration), ('A4', sustain_duration)]

    # Calculate the note durations as a fraction of the total track length
    note_count = len(notes)
    available_time_for_notes = total_ticks_for_bars  # Total time available for notes
    note_duration = available_time_for_notes // note_count  # Divide total time equally among the notes

    # Add notes to the track, ensuring the total length is exactly 4 bars
    time_elapsed = 0
    note_sequence = []

    # Generate the note sequence with randomized notes and varied durations
    while time_elapsed < total_ticks_for_bars:
        # Loop through the notes and add them in order
        for note in notes:
            midi_note = note_name_to_number(note[0])
            duration = note_duration  # Assign calculated duration based on the track length

            # Add note on/off messages for sustained pad style
            track.append(Message('note_on', note=midi_note, velocity=50, time=0))  # Low velocity for pad style
            track.append(Message('note_off', note=midi_note, velocity=50, time=duration))

            # Update the time elapsed
            time_elapsed += duration

            # Store the note duration for later checks
            note_sequence.append((midi_note, duration))

    # Save the MIDI file
    mid.save(output_path)
    print(f"MIDI file generated and saved to {output_path}")
