"""
Tests for the configuration system.
"""
import pytest
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

def test_common_config_validation():
    """Test validation of common configuration."""
    # Valid configuration
    config = CommonConfig(
        generation_type=GenerationType.ARPEGGIO,
        root_notes=["E4", "A4"],
        mode=Mode.MINOR
    )
    assert config.generation_type == GenerationType.ARPEGGIO
    assert config.root_notes == ["E4", "A4"]
    assert config.mode == Mode.MINOR
    
    # Invalid configurations
    with pytest.raises(ValueError):
        CommonConfig(
            generation_type=GenerationType.ARPEGGIO,
            root_notes=[],  # Empty root notes
            mode=Mode.MINOR
        )
    
    with pytest.raises(ValueError):
        CommonConfig(
            generation_type=GenerationType.ARPEGGIO,
            root_notes=["E4"],
            mode=Mode.MINOR,
            min_octave=5,
            max_octave=3  # min > max
        )

def test_arpeggio_config_validation():
    """Test validation of arpeggio configuration."""
    # Valid configuration
    config = ArpeggioConfig(
        steps=8,
        mode=ArpMode.UP_DOWN,
        range_octaves=2,
        evolution_rate=0.5,
        repetition_factor=5
    )
    assert config.steps == 8
    assert config.mode == ArpMode.UP_DOWN
    
    # Invalid configurations
    with pytest.raises(ValueError):
        ArpeggioConfig(steps=7)  # Invalid step count
    
    with pytest.raises(ValueError):
        ArpeggioConfig(evolution_rate=1.5)  # Rate > 1
    
    with pytest.raises(ValueError):
        ArpeggioConfig(repetition_factor=11)  # Factor > 10

def test_drone_config_validation():
    """Test validation of drone configuration."""
    # Valid configuration
    config = DroneConfig(
        base_velocity=100,
        variation_interval_bars=2,
        min_notes_held=3,
        octave_doubling_chance=0.5
    )
    assert config.base_velocity == 100
    assert config.variation_interval_bars == 2
    
    # Invalid configurations
    with pytest.raises(ValueError):
        DroneConfig(base_velocity=128)  # Velocity > 127
    
    with pytest.raises(ValueError):
        DroneConfig(min_notes_held=0)  # Must hold at least 1 note

def test_effect_config_validation():
    """Test validation of effect configurations."""
    # Valid tape wobble configuration
    tape_config = TapeWobbleConfig(
        enabled=True,
        wow_rate_hz=0.5,
        wow_depth=25.0,
        flutter_rate_hz=8.0,
        flutter_depth=5.0
    )
    assert tape_config.enabled
    assert tape_config.wow_rate_hz == 0.5
    
    # Invalid tape wobble configurations
    with pytest.raises(ValueError):
        TapeWobbleConfig(
            enabled=True,
            wow_rate_hz=0.05  # Too low
        )
    
    with pytest.raises(ValueError):
        TapeWobbleConfig(
            enabled=True,
            wow_depth=60.0  # Too high
        )
    
    # Valid humanize configuration
    humanize_config = HumanizeConfig(
        enabled=True,
        velocity_range=10
    )
    assert humanize_config.enabled
    assert humanize_config.velocity_range == 10
    
    # Invalid humanize configuration
    with pytest.raises(ValueError):
        HumanizeConfig(
            enabled=True,
            velocity_range=65  # Too high
        )

def test_config_from_dict():
    """Test creating configuration from dictionary."""
    config_dict = {
        'generation_type': 'arpeggio',
        'root_notes': ['E4', 'A4'],
        'mode': 'minor',
        'min_octave': 3,
        'max_octave': 5,
        'bpm': 120,
        'bars': 16,
        'use_chord_tones': True,
        'arp_steps': 8,
        'arp_mode': 'up_down',
        'range_octaves': 2,
        'evolution_rate': 0.35,
        'repetition_factor': 9,
        'repeat_pattern': False,
        'effects_config': [
            {
                'name': 'tape_wobble',
                'wow_rate_hz': 0.5,
                'wow_depth': 25.0,
                'flutter_rate_hz': 8.0,
                'flutter_depth': 5.0,
                'randomness': 0.5,
                'depth_units': 'cents'
            },
            {
                'name': 'humanize_velocity',
                'humanization_range': 10
            }
        ]
    }
    
    config = MidiGenConfig.from_dict(config_dict)
    assert config.common.generation_type == GenerationType.ARPEGGIO
    assert config.common.root_notes == ['E4', 'A4']
    assert config.arpeggio is not None
    assert config.arpeggio.steps == 8
    assert config.tape_wobble.wow_rate_hz == 0.5
    assert config.humanize.velocity_range == 10

def test_complete_config_validation():
    """Test validation of complete configuration."""
    # Valid arpeggio configuration
    common = CommonConfig(
        generation_type=GenerationType.ARPEGGIO,
        root_notes=["E4"],
        mode=Mode.MINOR
    )
    arpeggio = ArpeggioConfig()
    config = MidiGenConfig(common=common, arpeggio=arpeggio)
    assert config.common.generation_type == GenerationType.ARPEGGIO
    assert config.arpeggio is not None
    
    # Missing arpeggio config
    with pytest.raises(ValueError):
        MidiGenConfig(
            common=CommonConfig(
                generation_type=GenerationType.ARPEGGIO,
                root_notes=["E4"],
                mode=Mode.MINOR
            )
        )
    
    # Missing drone config
    with pytest.raises(ValueError):
        MidiGenConfig(
            common=CommonConfig(
                generation_type=GenerationType.DRONE,
                root_notes=["E4"],
                mode=Mode.MINOR
            )
        ) 
