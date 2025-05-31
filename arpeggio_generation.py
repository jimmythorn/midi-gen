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
    root_notes_str_param = options.get('root_notes', None) # Renamed for clarity
    
    print(f"[DEBUG] root_notes_str_param from options: {root_notes_str_param}") # DEBUG PRINT

    if root_notes_str_param: # This is a list of strings like ['E4', 'A4', ...]
        root_notes = [note_str_to_midi(note) for note in root_notes_str_param]
    else:
        root_notes = [root] * options.get('bars', 16)
    
    print(f"[DEBUG] Processed root_notes (MIDI numbers): {root_notes}") # DEBUG PRINT
    print(f"[DEBUG] Length of processed root_notes: {len(root_notes) if root_notes else 0}") # DEBUG PRINT

    mode = options.get('mode', 'major')
    arp_steps = options.get('arp_steps', 16)  # Number of steps in arpeggio sequence
    min_octave = options.get('min_octave', 4)
    max_octave = options.get('max_octave', 6)
    bars = options.get('bars', 16)
    arp_mode = options.get('arp_mode', 'up')
    range_octaves = options.get('range_octaves', 1)
    # Get the use_chord_tones option, defaulting to True (use chord tones)
    use_chord_tones = options.get('use_chord_tones', True)
    evolution_rate = options.get('evolution_rate', 0.1) # Assuming evolution_rate is in options
    repetition_factor = options.get('repetition_factor', 5) # Assuming repetition_factor is in options

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
        # Ensure len(root_notes) is not zero to avoid DivisionByZeroError
        bars_per_root_note_segment = bars // len(root_notes) if len(root_notes) > 0 else bars
        print(f"[DEBUG] Total bars: {bars}, Total root notes: {len(root_notes)}, Calculated bars_per_root_note_segment: {bars_per_root_note_segment}") # DEBUG PRINT

        for bar_idx, bar_root in enumerate(root_notes):
            print(f"[DEBUG] Processing bar_idx: {bar_idx}, bar_root (MIDI): {bar_root}") # DEBUG PRINT
            
            num_bars_for_this_segment = bars_per_root_note_segment
            # Adjust for the last segment to ensure total bars are met
            if bar_idx == len(root_notes) - 1:
                num_bars_for_this_segment = bars - (bars_per_root_note_segment * bar_idx)
                # Ensure it's not negative if bars_per_root_note_segment * bar_idx > bars (e.g. if bars_per_root_note_segment was 0 due to too many root notes for few bars)
                if num_bars_for_this_segment < 0: num_bars_for_this_segment = 0 
            
            print(f"[DEBUG] bar_idx: {bar_idx} - num_bars_for_this_segment: {num_bars_for_this_segment}") # DEBUG PRINT

            if num_bars_for_this_segment == 0: # Skip if no bars allocated to this root note
                print(f"[DEBUG] bar_idx: {bar_idx} - Skipped as num_bars_for_this_segment is 0.")
                continue

            arpeggio_pattern = create_arpeggio(
                bar_root, mode, arp_steps, min_octave, max_octave, 
                arp_mode, range_octaves, use_chord_tones=use_chord_tones,
                evolution_rate=evolution_rate, repetition_factor=repetition_factor
            )
            
            # Repeat or extend this pattern for the number of bars assigned to this root note
            for _ in range(num_bars_for_this_segment):
                if arp_steps > 0 and arpeggio_pattern: # Ensure arp_steps and pattern are valid
                    # Extend the arpeggios list to fill 16 steps (or arp_steps if different) in each bar for this segment
                    # This logic assumes create_arpeggio returns a pattern for ONE cycle (e.g. length of arp_steps)
                    # and it needs to be tiled to fill the bar (typically 16 sixteenth notes).
                    # If create_arpeggio already produces a full bar, this tiling is different.
                    # Current create_arpeggio `length` parameter seems to be `arp_steps`.
                    # Let's assume a bar has 16 steps for now, and arp_steps is the cycle length.
                    # This tiling logic might need adjustment based on how create_arpeggio `length` is used.
                    # For now, sticking to original tiling logic for 16 steps per bar:
                    full_bar_steps = 16 # Standard 16th notes per bar
                    if not arpeggio_pattern: # Safety if pattern is empty
                        continue
                    num_repeats = full_bar_steps // len(arpeggio_pattern)
                    remainder_steps = full_bar_steps % len(arpeggio_pattern)
                    
                    for _ in range(num_repeats):
                        arpeggios.extend(arpeggio_pattern)
                    arpeggios.extend(arpeggio_pattern[:remainder_steps])
                elif arpeggio_pattern: # arp_steps is 0 or invalid, but pattern exists
                    arpeggios.extend(arpeggio_pattern) # Add whatever was generated
                # If arpeggio_pattern is empty, nothing to add for this bar segment
            print(f"[DEBUG] bar_idx: {bar_idx} - Length of arpeggios list after processing this root note: {len(arpeggios)}") # DEBUG PRINT

    else: # Single root note for all bars
        arpeggio_pattern = create_arpeggio(
            root, mode, arp_steps, min_octave, max_octave, 
            arp_mode, range_octaves, use_chord_tones=use_chord_tones,
            evolution_rate=evolution_rate, repetition_factor=repetition_factor
        )
        for _ in range(bars):
            if arp_steps > 0 and arpeggio_pattern:
                full_bar_steps = 16
                if not arpeggio_pattern:
                    continue
                num_repeats = full_bar_steps // len(arpeggio_pattern)
                remainder_steps = full_bar_steps % len(arpeggio_pattern)
                for _ in range(num_repeats):
                    arpeggios.extend(arpeggio_pattern)
                arpeggios.extend(arpeggio_pattern[:remainder_steps])
            elif arpeggio_pattern:
                 arpeggios.extend(arpeggio_pattern)

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
