"""
Command-line interface configuration handling.
"""

import questionary
from typing import Dict, List, Optional
from midi_gen.core.config import (
    MidiGenConfig,
    CommonConfig,
    ArpeggioConfig,
    DroneConfig,
    TapeWobbleConfig,
    HumanizeConfig,
    GenerationType,
    Mode,
    ArpMode
)

# Constants for CLI defaults
DEFAULT_ROOT_NOTES = ["E4", "A4", "D4", "G4"]
DEFAULT_MODE = Mode.MINOR
DEFAULT_MIN_OCTAVE = 3
DEFAULT_MAX_OCTAVE = 5
DEFAULT_BPM = 120
DEFAULT_BARS = 16

# Arpeggio defaults
DEFAULT_ARP_STEPS = 8
DEFAULT_ARP_MODE = ArpMode.UP_DOWN
DEFAULT_RANGE_OCTAVES = 2
DEFAULT_EVOLUTION_RATE = 0.35
DEFAULT_REPETITION_FACTOR = 9

# Effect defaults
DEFAULT_TAPE_WOBBLE_ENABLED = True
DEFAULT_WOW_RATE_HZ = 0.5
DEFAULT_WOW_DEPTH = 25.0
DEFAULT_FLUTTER_RATE_HZ = 8.0
DEFAULT_FLUTTER_DEPTH = 5.0
DEFAULT_WOBBLE_RANDOMNESS = 0.5

DEFAULT_HUMANIZE_ENABLED = True
DEFAULT_HUMANIZE_RANGE = 10

# Drone defaults
DEFAULT_DRONE_BASE_VELOCITY = 70
DEFAULT_DRONE_VARIATION_INTERVAL_BARS = 1
DEFAULT_DRONE_MIN_NOTES_HELD = 2
DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE = 0.25

def get_cli_config() -> MidiGenConfig:
    """Get configuration from command-line interface."""
    print("Welcome to the MIDI Generator!")
    print("Please answer the following questions to configure your MIDI output.")
    print("Press Enter to accept the default value shown in (parentheses).\n")

    # Get generation type
    generation_type = GenerationType(questionary.select(
        "Select generation type:",
        choices=[
            questionary.Choice("Arpeggio", value="arpeggio"),
            questionary.Choice("Drone/Pad", value="drone")
        ],
        default="arpeggio"
    ).ask())

    # Get common configuration
    root_notes = get_root_notes()
    mode = Mode(questionary.select(
        "Select the musical mode:",
        choices=[mode.value for mode in Mode],
        default=DEFAULT_MODE.value
    ).ask())

    min_octave = int(questionary.text(
        "Minimum octave for notes:",
        default=str(DEFAULT_MIN_OCTAVE)
    ).ask() or DEFAULT_MIN_OCTAVE)

    max_octave = int(questionary.text(
        "Maximum octave for notes:",
        default=str(DEFAULT_MAX_OCTAVE)
    ).ask() or DEFAULT_MAX_OCTAVE)

    bpm = int(questionary.text(
        "BPM (tempo):",
        default=str(DEFAULT_BPM)
    ).ask() or DEFAULT_BPM)

    bars = int(questionary.text(
        "Number of bars:",
        default=str(DEFAULT_BARS)
    ).ask() or DEFAULT_BARS)

    use_chord_tones = not questionary.confirm(
        "Use all scale notes? (Default is No, only chord tones like 1,3,5 will be used)",
        default=False
    ).ask()

    common_config = CommonConfig(
        generation_type=generation_type,
        root_notes=root_notes,
        mode=mode,
        min_octave=min_octave,
        max_octave=max_octave,
        bpm=bpm,
        bars=bars,
        use_chord_tones=use_chord_tones
    )

    # Get generation-specific configuration
    arpeggio_config = None
    drone_config = None

    if generation_type == GenerationType.ARPEGGIO:
        arpeggio_config = get_arpeggio_config()
    else:
        drone_config = get_drone_config()

    # Get effect configuration
    tape_wobble_config = get_tape_wobble_config()
    humanize_config = get_humanize_config()

    return MidiGenConfig(
        common=common_config,
        arpeggio=arpeggio_config,
        drone=drone_config,
        tape_wobble=tape_wobble_config,
        humanize=humanize_config
    )

def get_root_notes() -> List[str]:
    """Get root notes configuration from CLI."""
    use_multiple_root_notes = questionary.confirm(
        "Use a list of root notes for different bars? (If no, a single root note will be used)",
        default=True
    ).ask()

    if use_multiple_root_notes:
        root_notes_str = questionary.text(
            f"Enter root notes for each bar, separated by spaces (e.g., {' '.join(DEFAULT_ROOT_NOTES)}):",
            default=' '.join(DEFAULT_ROOT_NOTES)
        ).ask()
        return root_notes_str.split() if root_notes_str else DEFAULT_ROOT_NOTES
    else:
        root_note = questionary.text(
            "Enter root note (e.g., C4):",
            default="C4"
        ).ask() or "C4"
        return [root_note]

def get_arpeggio_config() -> ArpeggioConfig:
    """Get arpeggio configuration from CLI."""
    print("\n--- Arpeggio Specific Settings ---")
    print("Choose how many steps in your arpeggio cycle.")
    print("Fewer steps = longer notes. The pattern will fill the entire bar.")

    steps = int(questionary.select(
        "Steps per arpeggio cycle:",
        choices=[
            questionary.Choice("16 steps (16th notes)", value=16),
            questionary.Choice("8 steps (8th notes)", value=8),
            questionary.Choice("4 steps (quarter notes)", value=4)
        ],
        default=DEFAULT_ARP_STEPS
    ).ask())

    repeat_pattern = False
    if steps < 16:
        print("\nYou can either:")
        print(f"- Repeat the {steps}-step pattern using 16th notes")
        print(f"- Use longer notes ({steps} {'8th' if steps == 8 else 'quarter'} notes)")
        repeat_pattern = questionary.confirm(
            "Would you like to repeat the pattern using 16th notes?",
            default=False
        ).ask()

    mode = ArpMode(questionary.select(
        "Arpeggiator mode:",
        choices=[mode.value for mode in ArpMode],
        default=DEFAULT_ARP_MODE.value
    ).ask())

    range_octaves = int(questionary.text(
        "Arpeggio range in octaves (from min_octave):",
        default=str(DEFAULT_RANGE_OCTAVES)
    ).ask() or DEFAULT_RANGE_OCTAVES)

    evolution_rate = float(questionary.text(
        "Arpeggio evolution rate (0.0 to 1.0):",
        default=str(DEFAULT_EVOLUTION_RATE)
    ).ask() or DEFAULT_EVOLUTION_RATE)

    repetition_factor = int(questionary.text(
        "Arpeggio repetition factor (1-10):",
        default=str(DEFAULT_REPETITION_FACTOR)
    ).ask() or DEFAULT_REPETITION_FACTOR)

    return ArpeggioConfig(
        steps=steps,
        mode=mode,
        range_octaves=range_octaves,
        evolution_rate=evolution_rate,
        repetition_factor=repetition_factor,
        repeat_pattern=repeat_pattern
    )

def get_drone_config() -> DroneConfig:
    """Get drone configuration from CLI."""
    print("\n--- Drone Specific Settings ---")

    base_velocity = int(questionary.text(
        "Base MIDI velocity for drone notes (0-127):",
        default=str(DEFAULT_DRONE_BASE_VELOCITY)
    ).ask() or DEFAULT_DRONE_BASE_VELOCITY)

    variation_interval_bars = int(questionary.text(
        "Drone variation interval in bars (how often voicing changes, e.g., 1-4):",
        default=str(DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
    ).ask() or DEFAULT_DRONE_VARIATION_INTERVAL_BARS)

    min_notes_held = int(questionary.text(
        "Minimum notes to hold in drone chord (e.g., 2):",
        default=str(DEFAULT_DRONE_MIN_NOTES_HELD)
    ).ask() or DEFAULT_DRONE_MIN_NOTES_HELD)

    octave_doubling_chance = float(questionary.text(
        "Chance (0.0-1.0) to double a drone note in another octave:",
        default=str(DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)
    ).ask() or DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)

    allow_octave_shifts = questionary.confirm(
        "Allow notes to shift octave during variation?",
        default=True
    ).ask()

    enable_walkdowns = questionary.confirm(
        "Enable melodic walkdowns to doubled notes?",
        default=True
    ).ask()

    return DroneConfig(
        base_velocity=base_velocity,
        variation_interval_bars=variation_interval_bars,
        min_notes_held=min_notes_held,
        octave_doubling_chance=octave_doubling_chance,
        allow_octave_shifts=allow_octave_shifts,
        enable_walkdowns=enable_walkdowns
    )

def get_tape_wobble_config() -> TapeWobbleConfig:
    """Get tape wobble effect configuration from CLI."""
    print("\n--- Effects Configuration ---")
    enabled = questionary.confirm(
        "Enable Tape Wobble pitch effect?",
        default=DEFAULT_TAPE_WOBBLE_ENABLED
    ).ask()

    if not enabled:
        return TapeWobbleConfig(enabled=False)

    wow_rate_hz = float(questionary.text(
        "Wow Rate (Hz, slow pitch drift, e.g., 0.1-1.0):",
        default=str(DEFAULT_WOW_RATE_HZ)
    ).ask() or DEFAULT_WOW_RATE_HZ)

    wow_depth = float(questionary.text(
        "Wow Depth (e.g., 5-50):",
        default=str(DEFAULT_WOW_DEPTH)
    ).ask() or DEFAULT_WOW_DEPTH)

    flutter_rate_hz = float(questionary.text(
        "Flutter Rate (Hz, faster pitch drift, e.g., 3-12):",
        default=str(DEFAULT_FLUTTER_RATE_HZ)
    ).ask() or DEFAULT_FLUTTER_RATE_HZ)

    flutter_depth = float(questionary.text(
        "Flutter Depth (e.g., 1-10):",
        default=str(DEFAULT_FLUTTER_DEPTH)
    ).ask() or DEFAULT_FLUTTER_DEPTH)

    randomness = float(questionary.text(
        "Wobble Randomness (0.0-1.0):",
        default=str(DEFAULT_WOBBLE_RANDOMNESS)
    ).ask() or DEFAULT_WOBBLE_RANDOMNESS)

    depth_units = questionary.select(
        "Units for Wow/Flutter Depth?",
        choices=["cents", "semitones"],
        default="cents"
    ).ask()

    return TapeWobbleConfig(
        enabled=enabled,
        wow_rate_hz=wow_rate_hz,
        wow_depth=wow_depth,
        flutter_rate_hz=flutter_rate_hz,
        flutter_depth=flutter_depth,
        randomness=randomness,
        depth_units=depth_units
    )

def get_humanize_config() -> HumanizeConfig:
    """Get humanization effect configuration from CLI."""
    enabled = questionary.confirm(
        "Enable Humanize Velocity effect? (adds natural variation to note velocities)",
        default=DEFAULT_HUMANIZE_ENABLED
    ).ask()

    if not enabled:
        return HumanizeConfig(enabled=False)

    velocity_range = int(questionary.text(
        "Humanize: Velocity variation range:",
        default=str(DEFAULT_HUMANIZE_RANGE)
    ).ask() or DEFAULT_HUMANIZE_RANGE)

    return HumanizeConfig(
        enabled=enabled,
        velocity_range=velocity_range
    ) 
