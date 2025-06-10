"""
Tests for MIDI generation functionality.
"""
import os
import pytest
from midi_gen.core.generation import create_arp
from midi_gen.utils.midi_types import MidiEvent, MidiEventType
from midi_gen.effects.processors.tape_wobble import TapeWobbleEffect, TapeWobbleConfiguration

def test_tape_wobble_pitch_bend_range():
    """Test that tape wobble effect generates valid pitch bend values."""
    config = TapeWobbleConfiguration(
        wow_rate_hz=0.5,
        wow_depth=25.0,
        flutter_rate_hz=8.0,
        flutter_depth=5.0,
        randomness=0.5,
        depth_units='cents'
    )
    effect = TapeWobbleEffect(config)
    
    # Create a simple test sequence
    test_events = [
        MidiEvent.note_on(0, 60, 100),  # C4 note on at tick 0
        MidiEvent.note_off(480, 60, 0)   # C4 note off at tick 480
    ]
    
    # Process events
    options = {'bpm': 120, 'ticks_per_beat': 480}
    processed_events = effect._process_sequence_impl(test_events, options)
    
    # Check pitch bend values are within valid range
    for event in processed_events:
        if event.event_type == MidiEventType.PITCH_BEND:
            assert -8192 <= event.value1 <= 8191, f"Pitch bend value {event.value1} outside valid range"

def test_midi_file_creation(tmp_path):
    """Test MIDI file creation with basic options."""
    # Create a temporary directory for test output
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    
    # Basic test options
    options = {
        'generation_type': 'arpeggio',
        'root_notes': ['C4'],
        'mode': 'major',
        'bars': 4,
        'min_octave': 4,
        'max_octave': 5,
        'bpm': 120,
        'arp_steps': 8,
        'arp_mode': 'up',
        'range_octaves': 1,
        'evolution_rate': 0.1,
        'repetition_factor': 5,
        'use_chord_tones': True,
        'filename': str(output_dir / "test_arpeggio.mid"),
        'effects_config': [
            {
                'name': 'tape_wobble',
                'wow_rate_hz': 0.5,
                'wow_depth': 25.0,
                'flutter_rate_hz': 8.0,
                'flutter_depth': 5.0,
                'randomness': 0.5,
                'depth_units': 'cents'
            }
        ]
    }
    
    # Generate MIDI file
    result_filename = create_arp(options)
    
    # Check file was created
    assert os.path.exists(result_filename), f"MIDI file {result_filename} was not created"
    
    # Basic file size check (should be non-zero)
    assert os.path.getsize(result_filename) > 0, "MIDI file is empty"

def test_arpeggio_pattern_generation():
    """Test arpeggio pattern generation with different modes and options."""
    options = {
        'generation_type': 'arpeggio',
        'root_notes': ['C4'],
        'mode': 'major',
        'bars': 1,
        'min_octave': 4,
        'max_octave': 5,
        'bpm': 120,
        'arp_steps': 8,
        'arp_mode': 'up',
        'range_octaves': 1,
        'evolution_rate': 0.0,  # No evolution for predictable testing
        'repetition_factor': 1,
        'use_chord_tones': True
    }
    
    # Test with different modes
    for mode in ['major', 'minor', 'dorian']:
        options['mode'] = mode
        options['filename'] = f"test_{mode}_arpeggio.mid"
        
        # Generate MIDI file
        result_filename = create_arp(options)
        
        # Basic validation that file was created
        assert os.path.exists(result_filename), f"MIDI file for {mode} mode was not created" 
