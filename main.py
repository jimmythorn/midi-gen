from generate_midi import generate_midi_with_options

# Define variables for customization
bars = 16  # Number of bars to generate
bpm = 120  # Beats per minute (tempo)
notes = [('C4', 480), ('E4', 480), ('G4', 480), ('A4', 480)]  # Notes for the progression

# Define the output path as a variable
output_path = './generated/generated_midi_pad_style.mid'  # You can change this path as needed

# Example usage with customizable variables for bars, bpm, and notes
options = {
    'style': 'rock',  # Set the style to 'pad'
    'notes': notes,  # Use the notes defined above
    'swing_ratio': 0.55,
    'timing_variance': 40,
    'glitch_probability': 0.86,
    'glitch_duration_reduction': 0.6,
    'bpm': bpm,  # Use the bpm defined above
    'output_path': output_path,  # Use the output path variable here
    'bars': bars,  # Use the bars defined above
    'min_duration': 240,  # Minimum note duration (half beat)
    'max_duration': 960,  # Maximum note duration (two beats)
    'sustain_duration': 1920  # Sustain duration for pad style
}

# Run the script
generate_midi_with_options(options)
