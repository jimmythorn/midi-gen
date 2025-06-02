# import sys # Removed sys import
# import os # Removed os import

# Removed sys.path modification block

from .arpeggio_generation import create_arp # Updated to use package name
from typing import Dict, List, Optional
import questionary # Import questionary

# Default values from the previous argparse setup
DEFAULT_ROOT = 0
DEFAULT_ROOT_NOTES = ["E4", "A4", "D4", "G4"]
DEFAULT_MODE = 'minor'
MODE_CHOICES = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'locrian']
DEFAULT_ARP_STEPS = 8
DEFAULT_MIN_OCTAVE = 3
DEFAULT_MAX_OCTAVE = 5
DEFAULT_BPM = 120
DEFAULT_BARS = 16
DEFAULT_FILENAME = 'arpeggio.mid' # Will be dynamically prefixed by generation type
DEFAULT_DRONE_FILENAME = 'drone.mid' # Default for drone generation
DEFAULT_ARP_MODE = 'up_down'
ARP_MODE_CHOICES = ['up', 'down', 'up_down', 'random', 'order']
DEFAULT_RANGE_OCTAVES = 2 # Arpeggio specific
DEFAULT_EVOLUTION_RATE = 0.35 # Arpeggio specific
DEFAULT_REPETITION_FACTOR = 9 # Arpeggio specific

DEFAULT_SHIMMER_ENABLED_BY_WOBBLE = False # Shimmer is off if wobble is 0
DEFAULT_SHIMMER_WOBBLE_RANGE = 0.0
DEFAULT_SHIMMER_SMOOTH_FACTOR = 0.675

DEFAULT_HUMANIZE_ENABLED = True
DEFAULT_HUMANIZE_RANGE = 10

# Drone specific defaults (can be expanded)
DEFAULT_DRONE_BASE_VELOCITY = 70
DEFAULT_DRONE_VARIATION_INTERVAL_BARS = 1 # How often the drone voicing can change
DEFAULT_DRONE_MIN_NOTES_HELD = 2 # Minimum notes of the chord to hold
DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE = 0.25 # Chance to double a note an octave up/down
DEFAULT_DRONE_ALLOW_OCTAVE_SHIFTS = True # Allow notes to shift octave during variation

if __name__ == "__main__":
    print("Welcome to the MIDI Generator!")
    print("Please answer the following questions to configure your MIDI output.")
    print("Press Enter to accept the default value shown in (parentheses).\n")

    # Ask for generation type FIRST
    generation_type = questionary.select(
        "Select generation type:",
        choices=[
            questionary.Choice("Arpeggio", value="arpeggio"),
            questionary.Choice("Drone/Pad", value="drone")
        ],
        default="arpeggio"
    ).ask()

    # --- Common Questions --- 
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

    min_octave = int(questionary.text("Minimum octave for notes:", default=str(DEFAULT_MIN_OCTAVE)).ask() or DEFAULT_MIN_OCTAVE)
    max_octave = int(questionary.text("Maximum octave for notes:", default=str(DEFAULT_MAX_OCTAVE)).ask() or DEFAULT_MAX_OCTAVE)
    bpm = int(questionary.text("BPM (tempo):", default=str(DEFAULT_BPM)).ask() or DEFAULT_BPM)
    bars = int(questionary.text("Number of bars:", default=str(DEFAULT_BARS)).ask() or DEFAULT_BARS)
    
    # Set default filename based on generation type
    current_default_filename = DEFAULT_DRONE_FILENAME if generation_type == 'drone' else DEFAULT_FILENAME
    base_filename = questionary.text(
        "Base filename for output MIDI (type prefix will be added):", 
        default=current_default_filename
    ).ask() or current_default_filename

    # Ask whether to use full scale or only chord tones (relevant for both, but primarily for arpeggios now)
    # For drones, use_chord_tones is implicitly True for the basic triad.
    # We can refine this later if drones need to access full scales for "interest notes".
    use_full_scale = questionary.confirm(
        "Use all scale notes? (Default is No, only chord tones like 1,3,5 will be used for arpeggios/base of drones)", 
        default=False  
    ).ask()
    use_chord_tones = not use_full_scale

    # --- Arpeggio Specific Questions ---
    arp_steps: Optional[int] = None
    arp_mode: Optional[str] = None
    range_octaves: Optional[int] = None # Arp specific
    evolution_rate: Optional[float] = None # Arp specific
    repetition_factor: Optional[int] = None # Arp specific

    if generation_type == 'arpeggio':
        print("\n--- Arpeggio Specific Settings ---")
        arp_steps = int(questionary.text("Number of steps per arpeggio cycle:", default=str(DEFAULT_ARP_STEPS)).ask() or DEFAULT_ARP_STEPS)
        arp_mode = questionary.select("Arpeggiator mode:", choices=ARP_MODE_CHOICES, default=DEFAULT_ARP_MODE).ask()
        range_octaves = int(questionary.text("Arpeggio range in octaves (from min_octave):", default=str(DEFAULT_RANGE_OCTAVES)).ask() or DEFAULT_RANGE_OCTAVES)
        evolution_rate = float(questionary.text("Arpeggio evolution rate (0.0 to 1.0):", default=str(DEFAULT_EVOLUTION_RATE)).ask() or DEFAULT_EVOLUTION_RATE)
        repetition_factor = int(questionary.text("Arpeggio repetition factor (1-10):", default=str(DEFAULT_REPETITION_FACTOR)).ask() or DEFAULT_REPETITION_FACTOR)
    
    # --- Drone Specific Questions (Placeholder for future) ---
    drone_base_velocity: Optional[int] = None
    drone_variation_interval_bars: Optional[int] = None
    drone_min_notes_held: Optional[int] = None
    drone_octave_doubling_chance: Optional[float] = None
    drone_allow_octave_shifts: Optional[bool] = None

    if generation_type == 'drone':
        print("\n--- Drone Specific Settings ---")
        drone_base_velocity = int(questionary.text("Base MIDI velocity for drone notes (0-127):", default=str(DEFAULT_DRONE_BASE_VELOCITY)).ask() or DEFAULT_DRONE_BASE_VELOCITY)
        drone_variation_interval_bars = int(questionary.text(
            f"Drone variation interval in bars (how often voicing changes, e.g., 1-4):", 
            default=str(DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
        ).ask() or DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
        drone_min_notes_held = int(questionary.text(
            f"Minimum notes to hold in drone chord (e.g., 2):", 
            default=str(DEFAULT_DRONE_MIN_NOTES_HELD)
        ).ask() or DEFAULT_DRONE_MIN_NOTES_HELD)
        drone_octave_doubling_chance = float(questionary.text(
            f"Chance (0.0-1.0) to double a drone note in another octave:",
            default=str(DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)
        ).ask() or DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)
        drone_allow_octave_shifts = questionary.confirm(
            f"Allow drone notes to occasionally shift their primary octave?",
            default=DEFAULT_DRONE_ALLOW_OCTAVE_SHIFTS
        ).ask()
        # Add more drone-specific questions here in the future

    # --- Effects Configuration (Currently more tied to arpeggios but could be generalized) ---
    # For now, let's ask for effects regardless, but they are only applied in arpeggio generation.
    # This can be refined if drones get their own effect processing.
    print("\n--- Effects Configuration ---")
    effects_config: List[Dict] = []
    enable_shimmer = questionary.confirm("Enable Shimmer effect?", default=(DEFAULT_SHIMMER_WOBBLE_RANGE > 0)).ask()
    if enable_shimmer:
        shimmer_wobble_range = float(questionary.text("Shimmer: Wobble range (semitones):", default=str(DEFAULT_SHIMMER_WOBBLE_RANGE)).ask() or DEFAULT_SHIMMER_WOBBLE_RANGE)
        shimmer_smooth_factor = float(questionary.text("Shimmer: Smooth factor (0.0-1.0):", default=str(DEFAULT_SHIMMER_SMOOTH_FACTOR)).ask() or DEFAULT_SHIMMER_SMOOTH_FACTOR)
        if shimmer_wobble_range > 0: 
            effects_config.append({
                'name': 'shimmer',
                'wobble_range': shimmer_wobble_range,
                'smooth_factor': shimmer_smooth_factor
            })

    enable_humanize = questionary.confirm("Enable Humanize Velocity effect?", default=DEFAULT_HUMANIZE_ENABLED).ask()
    if enable_humanize:
        humanize_range = int(questionary.text("Humanize: Velocity variation range:", default=str(DEFAULT_HUMANIZE_RANGE)).ask() or DEFAULT_HUMANIZE_RANGE)
        effects_config.append({
            'name': 'humanize_velocity',
            'humanization_range': humanize_range
        })

    options: Dict = {
        'generation_type': generation_type,
        'root': root_note_int, 
        'root_notes': root_notes_list if use_multiple_root_notes and root_notes_list else None,
        'mode': mode,
        'min_octave': min_octave,
        'max_octave': max_octave,
        'bpm': bpm,
        'bars': bars,
        'filename': base_filename, # Filename prefixing will be handled in arpeggio_generation.py
        'use_chord_tones': use_chord_tones,
        'effects_config': effects_config, # Pass effects, arpeggio_generation will decide to use them

        # Arpeggio-specific - will be None if not arpeggio type
        'arp_steps': arp_steps,
        'arp_mode': arp_mode,
        'range_octaves': range_octaves,
        'evolution_rate': evolution_rate,
        'repetition_factor': repetition_factor,

        # Drone-specific - will be None if not drone type
        'drone_base_velocity': drone_base_velocity,
        'drone_variation_interval_bars': drone_variation_interval_bars,
        'drone_min_notes_held': drone_min_notes_held,
        'drone_octave_doubling_chance': drone_octave_doubling_chance,
        'drone_allow_octave_shifts': drone_allow_octave_shifts
    }
    
    if not use_multiple_root_notes or not root_notes_list:
        options['root_notes'] = None 
        options['root'] = root_note_int 
    else:
         options['root'] = 0 # Default if multiple root notes are primary for arpeggio logic, less relevant for drone with explicit roots

    print("\nGenerating MIDI with the following options:")
    for key, value in options.items():
        print(f"- {key}: {value}")
    print("\n")
    
    create_arp(options)
