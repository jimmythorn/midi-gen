"""
Configuration classes for MIDI generation.

This module provides strongly-typed configuration classes for different aspects
of MIDI generation, including common settings, arpeggiator settings, and effects.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum

# Musical Constants
class Mode(str, Enum):
    MAJOR = 'major'
    MINOR = 'minor'
    DORIAN = 'dorian'
    PHRYGIAN = 'phrygian'
    LYDIAN = 'lydian'
    MIXOLYDIAN = 'mixolydian'
    LOCRIAN = 'locrian'

class ArpMode(str, Enum):
    UP = 'up'
    DOWN = 'down'
    UP_DOWN = 'up_down'
    RANDOM = 'random'
    ORDER = 'order'

class GenerationType(str, Enum):
    ARPEGGIO = 'arpeggio'
    DRONE = 'drone'

@dataclass
class CommonConfig:
    """Common configuration settings shared between different generation types."""
    generation_type: GenerationType
    root_notes: List[str]  # List of note names (e.g., ["E4", "A4"])
    mode: Mode
    min_octave: int = 3
    max_octave: int = 5
    bpm: int = 120
    bars: int = 16
    use_chord_tones: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if not self.root_notes:
            raise ValueError("At least one root note must be specified")
        if self.min_octave > self.max_octave:
            raise ValueError("min_octave cannot be greater than max_octave")
        if not 20 <= self.bpm <= 300:
            raise ValueError("BPM must be between 20 and 300")
        if self.bars < 1:
            raise ValueError("Must generate at least 1 bar")

@dataclass
class ArpeggioConfig:
    """Configuration specific to arpeggio generation."""
    steps: int = 8  # 4, 8, or 16 steps
    mode: ArpMode = ArpMode.UP_DOWN
    range_octaves: int = 2
    evolution_rate: float = 0.35
    repetition_factor: int = 9
    repeat_pattern: bool = False
    
    def __post_init__(self):
        """Validate arpeggio-specific configuration."""
        if self.steps not in [4, 8, 16]:
            raise ValueError("Steps must be 4, 8, or 16")
        if not 0 <= self.evolution_rate <= 1:
            raise ValueError("Evolution rate must be between 0 and 1")
        if not 1 <= self.repetition_factor <= 10:
            raise ValueError("Repetition factor must be between 1 and 10")
        if self.range_octaves < 1:
            raise ValueError("Range must be at least 1 octave")

@dataclass
class DroneConfig:
    """Configuration specific to drone generation."""
    base_velocity: int = 70
    variation_interval_bars: int = 1
    min_notes_held: int = 2
    octave_doubling_chance: float = 0.25
    allow_octave_shifts: bool = True
    enable_walkdowns: bool = True
    walkdown_num_steps: int = 2
    walkdown_step_ticks: int = 240  # Default to eighth notes (480/2)
    
    def __post_init__(self):
        """Validate drone-specific configuration."""
        if not 0 <= self.base_velocity <= 127:
            raise ValueError("Base velocity must be between 0 and 127")
        if self.variation_interval_bars < 1:
            raise ValueError("Variation interval must be at least 1 bar")
        if self.min_notes_held < 1:
            raise ValueError("Must hold at least 1 note")
        if not 0 <= self.octave_doubling_chance <= 1:
            raise ValueError("Octave doubling chance must be between 0 and 1")

@dataclass
class TapeWobbleConfig:
    """Configuration for tape wobble effect."""
    enabled: bool = True
    wow_rate_hz: float = 0.5
    wow_depth: float = 25.0
    flutter_rate_hz: float = 8.0
    flutter_depth: float = 5.0
    randomness: float = 0.5
    depth_units: Literal['cents', 'semitones'] = 'cents'
    
    def __post_init__(self):
        """Validate tape wobble configuration."""
        if self.enabled:
            if not 0.1 <= self.wow_rate_hz <= 1.0:
                raise ValueError("Wow rate must be between 0.1 and 1.0 Hz")
            if not 5 <= self.wow_depth <= 50:
                raise ValueError("Wow depth must be between 5 and 50")
            if not 3 <= self.flutter_rate_hz <= 12:
                raise ValueError("Flutter rate must be between 3 and 12 Hz")
            if not 1 <= self.flutter_depth <= 10:
                raise ValueError("Flutter depth must be between 1 and 10")
            if not 0 <= self.randomness <= 1:
                raise ValueError("Randomness must be between 0 and 1")

@dataclass
class HumanizeConfig:
    """Configuration for humanization effect."""
    enabled: bool = True
    velocity_range: int = 10
    
    def __post_init__(self):
        """Validate humanization configuration."""
        if self.enabled and not 1 <= self.velocity_range <= 64:
            raise ValueError("Velocity range must be between 1 and 64")

@dataclass
class MidiGenConfig:
    """Main configuration class that combines all settings."""
    common: CommonConfig
    arpeggio: Optional[ArpeggioConfig] = None
    drone: Optional[DroneConfig] = None
    tape_wobble: TapeWobbleConfig = field(default_factory=TapeWobbleConfig)
    humanize: HumanizeConfig = field(default_factory=HumanizeConfig)
    
    def __post_init__(self):
        """Validate the complete configuration."""
        if self.common.generation_type == GenerationType.ARPEGGIO and not self.arpeggio:
            raise ValueError("Arpeggio configuration required for arpeggio generation type")
        if self.common.generation_type == GenerationType.DRONE and not self.drone:
            raise ValueError("Drone configuration required for drone generation type")

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'MidiGenConfig':
        """Create a configuration instance from a dictionary."""
        common = CommonConfig(
            generation_type=GenerationType(config_dict.get('generation_type', 'arpeggio')),
            root_notes=config_dict.get('root_notes', ["E4", "A4", "D4", "G4"]),
            mode=Mode(config_dict.get('mode', 'minor')),
            min_octave=config_dict.get('min_octave', 3),
            max_octave=config_dict.get('max_octave', 5),
            bpm=config_dict.get('bpm', 120),
            bars=config_dict.get('bars', 16),
            use_chord_tones=config_dict.get('use_chord_tones', True)
        )
        
        arpeggio = None
        if common.generation_type == GenerationType.ARPEGGIO:
            arpeggio = ArpeggioConfig(
                steps=config_dict.get('arp_steps', 8),
                mode=ArpMode(config_dict.get('arp_mode', 'up_down')),
                range_octaves=config_dict.get('range_octaves', 2),
                evolution_rate=config_dict.get('evolution_rate', 0.35),
                repetition_factor=config_dict.get('repetition_factor', 9),
                repeat_pattern=config_dict.get('repeat_pattern', False)
            )
        
        drone = None
        if common.generation_type == GenerationType.DRONE:
            drone = DroneConfig(
                base_velocity=config_dict.get('drone_base_velocity', 70),
                variation_interval_bars=config_dict.get('drone_variation_interval_bars', 1),
                min_notes_held=config_dict.get('drone_min_notes_held', 2),
                octave_doubling_chance=config_dict.get('drone_octave_doubling_chance', 0.25),
                allow_octave_shifts=config_dict.get('drone_allow_octave_shifts', True),
                enable_walkdowns=config_dict.get('drone_enable_walkdowns', True),
                walkdown_num_steps=config_dict.get('drone_walkdown_num_steps', 2),
                walkdown_step_ticks=config_dict.get('drone_walkdown_step_ticks', 240)
            )
        
        effects_config = config_dict.get('effects_config', [])
        tape_wobble = TapeWobbleConfig()
        humanize = HumanizeConfig()
        
        for effect in effects_config:
            if effect.get('name') == 'tape_wobble':
                tape_wobble = TapeWobbleConfig(
                    enabled=True,
                    wow_rate_hz=effect.get('wow_rate_hz', 0.5),
                    wow_depth=effect.get('wow_depth', 25.0),
                    flutter_rate_hz=effect.get('flutter_rate_hz', 8.0),
                    flutter_depth=effect.get('flutter_depth', 5.0),
                    randomness=effect.get('randomness', 0.5),
                    depth_units=effect.get('depth_units', 'cents')
                )
            elif effect.get('name') == 'humanize_velocity':
                humanize = HumanizeConfig(
                    enabled=True,
                    velocity_range=effect.get('humanization_range', 10)
                )
        
        return cls(
            common=common,
            arpeggio=arpeggio,
            drone=drone,
            tape_wobble=tape_wobble,
            humanize=humanize
        ) 
