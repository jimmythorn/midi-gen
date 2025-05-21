import os
from .notes import note_str_to_midi, note_to_name
from .arpeggio import create_arpeggio
from .midi import create_midi_file
from typing import Dict, List
from .effects import ShimmerEffect, HumanizeVelocityEffect
from .effects_base import MidiEffect

def create_arp(options: Dict):
    """
    Main function to generate MIDI arpeggio based on given options.
    """
    root = options.get('root', 0)
    root_notes_str = options.get('root_notes', None)
    
    # Convert string notes to MIDI numbers if root_notes is provided
    if root_notes_str:
        root_notes = [note_str_to_midi(note) for note in root_notes_str]
    else:
        root_notes = [root] * options.get('bars', 16)  # Use root for each bar if not specified

    mode = options.get('mode', 'major')
    arp_steps = options.get('arp_steps', 16)  # Number of steps in arpeggio sequence
    min_octave = options.get('min_octave', 4)
    max_octave = options.get('max_octave', 6)
    bars = options.get('bars', 16)
    arp_mode = options.get('arp_mode', 'up')
    range_octaves = options.get('range_octaves', 1)

    # Instantiate effects based on config
    active_effects: List[MidiEffect] = []
    effects_config = options.get('effects_config', [])
    for effect_conf in effects_config:
        effect_name = effect_conf.get('name')
        effect_params = {k: v for k, v in effect_conf.items() if k != 'name'}
        if effect_name == 'shimmer':
            active_effects.append(ShimmerEffect(**effect_params))
        elif effect_name == 'humanize_velocity':
            active_effects.append(HumanizeVelocityEffect(**effect_params))
        # Add other effects here if needed

    arpeggios = []
    if root_notes:
        bars_per_note = bars // len(root_notes)
        for bar_root in root_notes:
            arpeggio = create_arpeggio(bar_root, mode, arp_steps, min_octave, max_octave, arp_mode, range_octaves)
            
            # Fill each segment with arpeggios to ensure 16 steps per bar
            for _ in range(bars_per_note):
                # Extend the arpeggio to fill 16 steps in each bar
                arpeggios.extend(arpeggio * (16 // arp_steps))
                arpeggios.extend(arpeggio[:16 % arp_steps])  # Add remaining notes from the arpeggio cycle
    else:
        # If no root_notes provided, use the single root for all bars
        arpeggio = create_arpeggio(root, mode, arp_steps, min_octave, max_octave, arp_mode, range_octaves)
        for _ in range(bars):
            # Extend the arpeggio to fill 16 steps in each bar
            arpeggios.extend(arpeggio * (16 // arp_steps))
            arpeggios.extend(arpeggio[:16 % arp_steps])  # Add remaining notes from the arpeggio cycle

    # Ensure we don't exceed the total number of steps for the specified bars
    arpeggios = arpeggios[:bars * 16]  # Each bar should have 16 steps

    # Use only the root notes for filename to keep it shorter
    root_notes_names = '-'.join([note_to_name(note) for note in root_notes])
    
    # Create a base filename with just the root notes of each bar
    base_filename = f"arpeggio_{mode}_{root_notes_names}"
    
    # Define the output folder within the project directory
    output_folder = "generated"
    # Correctly get project_directory: assume this file is in the project's root package
    project_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # If effects.py, notes.py etc are in the same directory as arpeggio_generation.py, then:
    # project_directory = os.path.dirname(os.path.abspath(__file__))
    # This needs to be robust depending on actual project structure if arpeggio_generation is in a sub-package.
    # For now, assuming it is NOT in a sub-package relative to where 'generated' should be.
    # If arpeggio_generation.py is at the root of a package (e.g. my_package/arpeggio_generation.py)
    # and 'generated' should be in 'my_package/generated', then os.path.dirname(os.path.abspath(__file__)) is correct.
    # If 'generated' should be at the workspace root, then more complex path logic or a fixed path might be needed.
    # Given current structure seems to be flat, os.path.dirname(os.path.abspath(__file__)) for output path is likely fine.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_script_dir, output_folder) # Output generated folder next to the script

    # Create 'generated' folder if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Set the filename path to be within the 'generated' folder in the project directory
    file_path = os.path.join(output_path, f"{base_filename}.mid")
    
    options['filename'] = file_path
    # Pass active_effects to create_midi_file
    result_filename = create_midi_file(arpeggios, options, active_effects=active_effects)
    print(f"MIDI file '{result_filename}' created with the following settings:")
    for key, value in options.items():
        print(f"- {key}: {value}")
