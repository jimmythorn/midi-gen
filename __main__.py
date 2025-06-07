"""
MIDI sequence generator command line interface.
"""

import os
import questionary
from typing import Dict, List, Optional

from .generators import (
    ArpeggioGenerator,
    DroneGenerator,
    ChordGenerator
)

from .effects import (
    TapeWobbleEffect,
    HumanizeVelocityEffect
)

from .core.music import note_str_to_midi

# Default values
DEFAULT_ROOT = 0
DEFAULT_ROOT_NOTES = ["E4", "A4", "D4", "G4"]
DEFAULT_MODE = 'minor'
MODE_CHOICES = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'locrian']
DEFAULT_ARP_STEPS = 8

# Define step choices with musical note lengths
ARP_STEP_CHOICES = [
    questionary.Choice("16 steps (16th notes)", value=16),
    questionary.Choice("8 steps (8th notes)", value=8),
    questionary.Choice("4 steps (quarter notes)", value=4)
]

DEFAULT_MIN_OCTAVE = 3
DEFAULT_MAX_OCTAVE = 5
DEFAULT_BPM = 120
DEFAULT_BARS = 16
DEFAULT_FILENAME = 'output.mid'

def ensure_generated_dir():
    """Ensure the generated directory exists."""
    generated_dir = os.path.join(os.path.dirname(__file__), 'generated')
    if not os.path.exists(generated_dir):
        os.makedirs(generated_dir)
    return generated_dir

def main():
    """Main entry point for the MIDI generator."""
    print("Welcome to the MIDI Generator!")
    print("Please answer the following questions to configure your MIDI output.")
    print("Press Enter to accept the default value shown in (parentheses).\n")

    # Ask for generation type
    generation_type = questionary.select(
        "Select generation type:",
        choices=[
            questionary.Choice("Arpeggio", value="arpeggio"),
            questionary.Choice("Drone/Pad", value="drone"),
            questionary.Choice("Chord Progression", value="chord")
        ],
        default="arpeggio"
    ).ask()

    # Common parameters
    use_multiple_root_notes = questionary.confirm(
        "Use a list of root notes for different bars?",
        default=True
    ).ask()

    root_notes = []
    if use_multiple_root_notes:
        root_notes_str = questionary.text(
            f"Enter root notes for each bar, separated by spaces (e.g., {' '.join(DEFAULT_ROOT_NOTES)}):",
            default=' '.join(DEFAULT_ROOT_NOTES)
        ).ask()
        root_notes = [note_str_to_midi(note) for note in root_notes_str.split()]
    else:
        root_note = note_str_to_midi(
            questionary.text(
                "Enter root note (e.g., C4, F#3):",
                default="C4"
            ).ask()
        )
        root_notes = [root_note]

    mode = questionary.select(
        "Select the musical mode:",
        choices=MODE_CHOICES,
        default=DEFAULT_MODE
    ).ask()

    min_octave = int(questionary.text(
        "Minimum octave for notes:",
        default=str(DEFAULT_MIN_OCTAVE)
    ).ask())

    max_octave = int(questionary.text(
        "Maximum octave for notes:",
        default=str(DEFAULT_MAX_OCTAVE)
    ).ask())

    bpm = int(questionary.text(
        "BPM (tempo):",
        default=str(DEFAULT_BPM)
    ).ask())

    bars = int(questionary.text(
        "Number of bars:",
        default=str(DEFAULT_BARS)
    ).ask())

    # Effects configuration
    effects = []
    
    if questionary.confirm(
        "Add tape wobble effect?",
        default=True
    ).ask():
        effects.append(TapeWobbleEffect(
            rate_hz=float(questionary.text(
                "Wobble frequency (Hz):",
                default="5.0"
            ).ask()),
            depth=float(questionary.text(
                "Wobble depth (semitones):",
                default="0.3"
            ).ask()),
            phase_variation=float(questionary.text(
                "Phase variation (0-1):",
                default="0.2"
            ).ask())
        ))

    if questionary.confirm(
        "Add humanization effect?",
        default=True
    ).ask():
        effects.append(HumanizeVelocityEffect(
            intensity=float(questionary.text(
                "Humanization intensity (0-1):",
                default="0.3"
            ).ask()),
            beat_emphasis=float(questionary.text(
                "Beat emphasis (0-1):",
                default="0.6"
            ).ask()),
            trend_inertia=float(questionary.text(
                "Trend inertia (0-1):",
                default="0.4"
            ).ask())
        ))

    # Create generator based on type
    if generation_type == "arpeggio":
        generator = ArpeggioGenerator(bpm=bpm)
        # Ask for arpeggio-specific parameters
        print("\nArpeggio Pattern Settings:")
        print("Choose how many steps in your arpeggio cycle.")
        print("Fewer steps = longer notes. The pattern will fill the entire bar.")
        length = questionary.select(
            "Steps per arpeggio cycle:",
            choices=ARP_STEP_CHOICES,
            default=DEFAULT_ARP_STEPS
        ).ask()

        # Ask about pattern repetition if using 8 or 4 steps
        repeat_pattern = False
        if length < 16:
            print("\nYou can either:")
            print(f"- Repeat the {length}-step pattern using 16th notes")
            print(f"- Use longer notes ({length} {'8th' if length == 8 else 'quarter'} notes)")
            repeat_pattern = questionary.confirm(
                "Would you like to repeat the pattern using 16th notes?",
                default=False
            ).ask()
            if repeat_pattern:
                length = length * (16 // length)  # Convert to 16th notes

        print("\nPattern Evolution Settings:")
        evolution_rate = float(questionary.text(
            "Evolution rate (0.0-1.0, higher = more variation):",
            default="0.1"
        ).ask())

        repetition_factor = int(questionary.text(
            "Repetition factor (1-10, higher = more note repetition):",
            default="5"
        ).ask())
        
        events = generator.generate(
            root=root_notes,
            mode=mode,
            bars=bars,
            min_octave=min_octave,
            max_octave=max_octave,
            length=length,
            evolution_rate=evolution_rate,
            repetition_factor=repetition_factor,
            arp_mode=questionary.select(
                "Arpeggio pattern:",
                choices=['up', 'down', 'up_down', 'random'],
                default='up_down'
            ).ask()
        )
    elif generation_type == "drone":
        generator = DroneGenerator(bpm=bpm)
        events = generator.generate(
            root=root_notes[0],
            mode=mode,
            bars=bars,
            min_octave=min_octave,
            max_octave=max_octave
        )
    else:  # chord progression
        generator = ChordGenerator(bpm=bpm)
        events = generator.generate(
            root=root_notes[0],
            mode=mode,
            bars=bars,
            min_octave=min_octave,
            max_octave=max_octave,
            voicing_complexity=float(questionary.text(
                "Voicing complexity (0-1):",
                default="0.5"
            ).ask()),
            rhythmic_variation=float(questionary.text(
                "Rhythmic variation (0-1):",
                default="0.3"
            ).ask())
        )

    # Process through effects
    for effect in effects:
        events = effect.process_sequence(events, {
            'bpm': bpm,
            'ticks_per_beat': 480,  # Standard MIDI resolution
            'generation_type': generation_type
        })

    # Create output filename in generated directory
    generated_dir = ensure_generated_dir()
    filename = os.path.join(generated_dir, f"{generation_type}_{mode}_{bpm}bpm.mid")
    
    # Save MIDI file
    from .core.midi import create_midi_file
    output_path = create_midi_file(
        events=events,
        options={
            'filename': filename,
            'bpm': bpm,
            'ticks_per_beat': 480
        }
    )
    
    print(f"\nMIDI file created: {output_path}")

if __name__ == "__main__":
    main()
