from .arpeggio_generation import create_arp
from typing import Dict, List
import questionary # Import questionary

# Default values from the previous argparse setup
DEFAULT_ROOT = 0
DEFAULT_ROOT_NOTES = ["E4", "D#3", "E3", "B4"]
DEFAULT_MODE = 'minor'
MODE_CHOICES = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'locrian']
DEFAULT_ARP_STEPS = 8
DEFAULT_MIN_OCTAVE = 3
DEFAULT_MAX_OCTAVE = 5
DEFAULT_BPM = 120
DEFAULT_BARS = 16
DEFAULT_FILENAME = 'arpeggio.mid'
DEFAULT_ARP_MODE = 'up_down'
ARP_MODE_CHOICES = ['up', 'down', 'up_down', 'random', 'order']
DEFAULT_RANGE_OCTAVES = 2
DEFAULT_EVOLUTION_RATE = 0.35
DEFAULT_REPETITION_FACTOR = 9

DEFAULT_SHIMMER_ENABLED_BY_WOBBLE = False # Shimmer is off if wobble is 0
DEFAULT_SHIMMER_WOBBLE_RANGE = 0.0
DEFAULT_SHIMMER_SMOOTH_FACTOR = 0.675

DEFAULT_HUMANIZE_ENABLED = True
DEFAULT_HUMANIZE_RANGE = 10

if __name__ == "__main__":
    print("Welcome to the MIDI Arpeggio Generator!")
    print("Please answer the following questions to configure your arpeggio.")
    print("Press Enter to accept the default value shown in (parentheses).\n")

    # Ask for root note handling
    use_multiple_root_notes = questionary.confirm(
        "Use a list of root notes for different bars? (If no, a single root note will be used)", 
        default=True
    ).ask()

    root_notes_list: List[str] = []
    root_note_int: int = DEFAULT_ROOT

    if use_multiple_root_notes:
        root_notes_str = questionary.text(
            f"Enter root notes for each bar, separated by spaces (e.g., {' '.join(DEFAULT_ROOT_NOTES)}):",
            default=' '.join(DEFAULT_ROOT_NOTES)
        ).ask()
        if root_notes_str:
            root_notes_list = root_notes_str.split()
    else:
        root_note_int = int(questionary.text(
            f"Enter the MIDI root note number (0-127, C=0):",
            default=str(DEFAULT_ROOT)
        ).ask() or DEFAULT_ROOT)

    mode = questionary.select(
        "Select the musical mode:",
        choices=MODE_CHOICES,
        default=DEFAULT_MODE
    ).ask()

    arp_steps = int(questionary.text("Number of steps per arpeggio/bar:", default=str(DEFAULT_ARP_STEPS)).ask() or DEFAULT_ARP_STEPS)
    min_octave = int(questionary.text("Minimum octave:", default=str(DEFAULT_MIN_OCTAVE)).ask() or DEFAULT_MIN_OCTAVE)
    max_octave = int(questionary.text("Maximum octave:", default=str(DEFAULT_MAX_OCTAVE)).ask() or DEFAULT_MAX_OCTAVE)
    bpm = int(questionary.text("BPM (tempo):", default=str(DEFAULT_BPM)).ask() or DEFAULT_BPM)
    bars = int(questionary.text("Number of bars:", default=str(DEFAULT_BARS)).ask() or DEFAULT_BARS)
    filename = questionary.text("Base filename for output MIDI:", default=DEFAULT_FILENAME).ask() or DEFAULT_FILENAME
    arp_mode = questionary.select("Arpeggiator mode:", choices=ARP_MODE_CHOICES, default=DEFAULT_ARP_MODE).ask()
    range_octaves = int(questionary.text("Range in octaves for arpeggio:", default=str(DEFAULT_RANGE_OCTAVES)).ask() or DEFAULT_RANGE_OCTAVES)
    evolution_rate = float(questionary.text("Evolution rate (0.0 to 1.0):", default=str(DEFAULT_EVOLUTION_RATE)).ask() or DEFAULT_EVOLUTION_RATE)
    repetition_factor = int(questionary.text("Repetition factor (1-10, 10=max repetition):", default=str(DEFAULT_REPETITION_FACTOR)).ask() or DEFAULT_REPETITION_FACTOR)

    # Effects Configuration
    effects_config: List[Dict] = []

    # Shimmer Effect
    enable_shimmer = questionary.confirm("Enable Shimmer effect?", default=(DEFAULT_SHIMMER_WOBBLE_RANGE > 0)).ask()
    if enable_shimmer:
        shimmer_wobble_range = float(questionary.text(
            "Shimmer: Wobble range (semitones):", 
            default=str(DEFAULT_SHIMMER_WOBBLE_RANGE)
        ).ask() or DEFAULT_SHIMMER_WOBBLE_RANGE)
        shimmer_smooth_factor = float(questionary.text(
            "Shimmer: Smooth factor (0.0-1.0):", 
            default=str(DEFAULT_SHIMMER_SMOOTH_FACTOR)
        ).ask() or DEFAULT_SHIMMER_SMOOTH_FACTOR)
        if shimmer_wobble_range > 0: # Only add shimmer if it actually does something
            effects_config.append({
                'name': 'shimmer',
                'wobble_range': shimmer_wobble_range,
                'smooth_factor': shimmer_smooth_factor
            })

    # Humanize Velocity Effect
    enable_humanize = questionary.confirm("Enable Humanize Velocity effect?", default=DEFAULT_HUMANIZE_ENABLED).ask()
    if enable_humanize:
        humanize_range = int(questionary.text(
            "Humanize: Velocity variation range:", 
            default=str(DEFAULT_HUMANIZE_RANGE)
        ).ask() or DEFAULT_HUMANIZE_RANGE)
        effects_config.append({
            'name': 'humanize_velocity',
            'humanization_range': humanize_range
        })

    options: Dict = {
        'root': root_note_int, # Will be overridden by root_notes_list if provided
        'root_notes': root_notes_list if use_multiple_root_notes and root_notes_list else None,
        'mode': mode,
        'arp_steps': arp_steps,
        'min_octave': min_octave,
        'max_octave': max_octave,
        'bpm': bpm,
        'bars': bars,
        'filename': filename,
        'effects_config': effects_config,
        'arp_mode': arp_mode,
        'range_octaves': range_octaves,
        'evolution_rate': evolution_rate,
        'repetition_factor': repetition_factor,
    }
    
    # If single root note was chosen, and root_notes list is empty/None, ensure options['root'] is used
    if not use_multiple_root_notes or not root_notes_list:
        options['root_notes'] = None # Explicitly set to None if not used or empty
        options['root'] = root_note_int # Ensure single root is set
    else:
         options['root'] = 0 # Default if multiple root notes are primary


    print("\nGenerating MIDI with the following options:")
    for key, value in options.items():
        print(f"- {key}: {value}")
    print("\n")
    
    create_arp(options)
