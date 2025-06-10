"""
Main entry point for MIDI generation.
"""

from midi_gen.core.cli import get_cli_config
from midi_gen.core.config import GenerationType
from midi_gen.generators.arpeggio import create_arpeggio
from midi_gen.generators.drone import generate_drone_events
from midi_gen.utils.midi import create_midi_file, MidiProcessor
from midi_gen.effects.base import MidiEffect, NoteContext
from midi_gen.effects.registry import EffectRegistry
from midi_gen.effects import create_note_context, convert_legacy_to_instructions
from midi_gen.effects.processors import (
    TapeWobbleConfiguration,
    HumanizeVelocityConfiguration
)
import os
from midi_gen.utils.notes import note_str_to_midi

def main():
    """Main entry point."""
    # Get configuration from CLI
    config = get_cli_config()

    # Create effects based on configuration
    effects: list[MidiEffect] = []
    
    if config.tape_wobble.enabled:
        effects.append(EffectRegistry.create_effect(
            "tape_wobble",
            TapeWobbleConfiguration(
                wow_rate_hz=config.tape_wobble.wow_rate_hz,
                wow_depth=config.tape_wobble.wow_depth,
                flutter_rate_hz=config.tape_wobble.flutter_rate_hz,
                flutter_depth=config.tape_wobble.flutter_depth,
                randomness=config.tape_wobble.randomness,
                depth_units=config.tape_wobble.depth_units
            )
        ))
    
    if config.humanize.enabled:
        effects.append(EffectRegistry.create_effect(
            "humanize_velocity",
            HumanizeVelocityConfiguration(
                humanization_range=config.humanize.velocity_range
            )
        ))

    # Generate MIDI events based on generation type
    if config.common.generation_type == GenerationType.ARPEGGIO:
        if not config.arpeggio:
            raise ValueError("Arpeggio configuration required for arpeggio generation")
        
        # Create arpeggio events
        midi_events = create_arpeggio(
            root_notes=config.common.root_notes,
            mode=config.common.mode.value,
            min_octave=config.common.min_octave,
            max_octave=config.common.max_octave,
            bpm=config.common.bpm,
            bars=config.common.bars,
            use_chord_tones=config.common.use_chord_tones,
            steps=config.arpeggio.steps,
            arp_mode=config.arpeggio.mode.value,
            range_octaves=config.arpeggio.range_octaves,
            evolution_rate=config.arpeggio.evolution_rate,
            repetition_factor=config.arpeggio.repetition_factor,
            repeat_pattern=config.arpeggio.repeat_pattern
        )
        
        # Create descriptive filename
        root_notes_str = '_'.join(config.common.root_notes)
        filename = f"arpeggio_{root_notes_str}_{config.common.mode.value}"
        filename += f"_oct{config.common.min_octave}-{config.common.max_octave}"
        filename += f"_steps{config.arpeggio.steps}"
        if config.arpeggio.repeat_pattern:
            filename += "_16th"
        filename += ".mid"
    else:
        if not config.drone:
            raise ValueError("Drone configuration required for drone generation")
        
        # Create drone events
        options = {
            'bpm': config.common.bpm,
            'bars': config.common.bars,
            'mode': config.common.mode.value,
            'min_octave': config.common.min_octave,
            'max_octave': config.common.max_octave,
            'use_chord_tones': config.common.use_chord_tones,
            'drone_base_velocity': config.drone.base_velocity,
            'drone_variation_interval_bars': config.drone.variation_interval_bars,
            'drone_min_notes_held': config.drone.min_notes_held,
            'drone_octave_doubling_chance': config.drone.octave_doubling_chance,
            'drone_allow_octave_shifts': config.drone.allow_octave_shifts,
            'drone_enable_walkdowns': config.drone.enable_walkdowns,
            'drone_walkdown_num_steps': config.drone.walkdown_num_steps,
            'drone_walkdown_step_ticks': config.drone.walkdown_step_ticks
        }
        
        # Convert root notes from strings to MIDI numbers
        processed_root_notes_midi = [note_str_to_midi(note) for note in config.common.root_notes]
        
        # Generate drone events
        midi_events = generate_drone_events(options, processed_root_notes_midi)
        
        # Create descriptive filename
        root_notes_str = '_'.join(config.common.root_notes)
        filename = f"drone_{root_notes_str}_{config.common.mode.value}"
        filename += f"_oct{config.common.min_octave}-{config.common.max_octave}"
        filename += ".mid"

    # Create output directory in the project root
    output_dir = os.path.join(os.path.dirname(__file__), "generated")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Use absolute path for the output file
    filename = os.path.join(output_dir, filename)

    # Create MIDI file
    print(f"\nAttempting to create MIDI file...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Target filename: {filename}")
    print(f"Number of MIDI events: {len(midi_events)}")
    
    # Set up options for MIDI file creation
    options = {
        'generation_type': config.common.generation_type.value,
        'bpm': config.common.bpm,
        'ticks_per_beat': 480,  # Standard MIDI ticks per beat
        'filename': filename
    }
    
    # Create MIDI file with effects
    result = create_midi_file(midi_events, options, effects or [])
    print(f"MIDI file created at: {result}")
    print(f"File exists: {os.path.exists(result)}")

if __name__ == "__main__":
    main()
