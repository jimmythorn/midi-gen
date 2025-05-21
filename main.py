from .arpeggio_generation import create_arp
from typing import Dict

if __name__ == "__main__":
    options: Dict = {
        # 'root': MIDI note number for the root note of the scale if 'root_notes' is not provided (0-127, default 0 for C)
        'root': 0,
        
        # 'root_notes': List of note strings for root notes of each bar, defaults to using 'root' for all bars
        'root_notes': ["E4", "D#3", "E3", "B4"],  # e.g., ['E3', 'G4', 'B3'] for different root notes per bar
        
        # 'mode': Musical mode for the scale (
            # 'major' - Happy, bright;
            # 'minor' - Sad, introspective;
            # 'dorian' - Jazz, bluesy;
            # 'phrygian' - Spanish, exotic;
            # 'lydian' - Dreamy, ethereal;
            # 'mixolydian' - Folk, rock;
            # 'locrian' - Dark, dissonant
        # )
        'mode': 'minor',
        
        # 'arp_steps': Number of steps in arpeggio sequence and notes per bar (default 16)
        'arp_steps': 8,
        
        # 'min_octave': Minimum octave for note generation (default 3)
        'min_octave': 3,
        
        # 'max_octave': Maximum octave for note generation (default 5)
        'max_octave': 5,
        
        # 'bpm': Beats per minute for tempo (positive integer, default 120)
        'bpm': 120,
        
        # 'bars': Number of bars for the arpeggio (positive integer, default 16)
        'bars': 16,
        
        # 'filename': Base name for the output file (string, will be modified with notes and path)
        'filename': 'arpeggio.mid',
        
        # 'effects_config': List of dictionaries specifying effects and their parameters
        # Example: [{'name': 'shimmer', 'wobble_range': 2, 'smooth_factor': 0.1},
        #           {'name': 'humanize_velocity', 'humanization_range': 20}]
        # To disable effects, provide an empty list: []
        'effects_config': [
            {'name': 'shimmer', 'wobble_range': 0, 'smooth_factor': 0.675}, # Set wobble_range to 0 to disable shimmer
            {'name': 'humanize_velocity', 'humanization_range': 10}
        ],
        
        # 'arp_mode': Arpeggiator mode ('up', 'down', 'up_down', 'random', 'order', default 'up')
        'arp_mode': 'up_down',
        
        # 'range_octaves': Number of octaves to span with the arpeggio (default 1)
        'range_octaves': 2,
        
        # 'evolution_rate': Rate at which the arpeggio evolves (0.0 to 1.0, where 0 is no evolution)
        'evolution_rate': 0.35,
        
        # 'repetition_factor': Controls the level of repetition in the arpeggio (1 to 10, 10 being most repetitive)
        'repetition_factor': 9,
    }
    
    create_arp(options)
