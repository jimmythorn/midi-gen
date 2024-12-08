from generate_midi import generate_midi_with_options

# Define variables for customization
bars = 16  # Number of bars to generate
bpm = 120  # Beats per minute (tempo)
notes = [('E4', 480), ('A4', 480), ('D4', 480), ('B4', 480)]  # Notes for the progression

# Define the output path as a variable
output_path = './generated/generated_midi.mid'  # You can change this path as needed

# Example usage with customizable variables for bars, bpm, and notes
options = {
    'notes': notes,  # A list of notes and their durations (in ticks)
    'style': 'hip_hop',  # Style of music (e.g., 'hip_hop', 'classical', 'rock')
    'bpm': bpm,  # Beats per minute (tempo of the piece)
    'output_path': output_path,  # Path to save the generated MIDI file
    'bars': bars,  # Number of bars in the piece (default: 16 bars)
    'min_duration': 120,  # Minimum duration for each note (in ticks, default: 240)
    'max_duration': 240,  # Maximum duration for each note (in ticks, default: 480)
    'sustain_duration': 1920,  # Duration for sustained notes (optional, default: 1920)
    'timing_variance': 10,
    'rhythmic_density': 4,  # 1/16 note arpeggiation
    'swing_strength': 0.4,
    'velocity_variance': 10,
    'pitch_wobble_strength': 150  # Subtle pitch wobble strength
}

# Run the script
generate_midi_with_options(options)
