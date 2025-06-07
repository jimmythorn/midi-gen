"""
Configuration classes for rest pattern generation.
"""

from dataclasses import dataclass
from typing import Optional, List
from .types import RestPatternType, MIN_PATTERN_LENGTH, MAX_PATTERN_LENGTH

@dataclass
class BaseRestConfig:
    """Base configuration for all rest patterns."""
    enabled: bool = False
    maintain_rhythm: bool = True  # If True, maintain original timing when inserting rests

@dataclass
class FixedPatternConfig(BaseRestConfig):
    """Configuration for fixed-interval rest patterns."""
    steps_between_rests: int = 4  # Insert rest every N steps
    pattern_shift: bool = False    # Whether pattern position shifts over time
    
    def __post_init__(self):
        """Validate configuration."""
        if not MIN_PATTERN_LENGTH <= self.steps_between_rests <= MAX_PATTERN_LENGTH:
            raise ValueError(f"steps_between_rests must be between {MIN_PATTERN_LENGTH} and {MAX_PATTERN_LENGTH}")

@dataclass
class ProbabilityConfig(BaseRestConfig):
    """Configuration for probability-based rest patterns."""
    rest_chance: float = 0.15     # Probability of rest per step (0-1)
    beat_weight: float = 1.5      # How much to favor strong beats for rests
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.rest_chance <= 1:
            raise ValueError("rest_chance must be between 0 and 1")
        if self.beat_weight < 0:
            raise ValueError("beat_weight must be non-negative")

@dataclass
class MusicalPosConfig(BaseRestConfig):
    """Configuration for musical-position-based rest patterns."""
    rest_positions: List[int] = None  # List of step positions to rest (0-15 in 16-step bar)
    accent_weak_beats: bool = False   # Whether to also add rests on weak beats
    
    def __post_init__(self):
        """Validate configuration."""
        if self.rest_positions is None:
            self.rest_positions = []
        for pos in self.rest_positions:
            if not 0 <= pos < STEPS_PER_BAR:
                raise ValueError(f"Rest positions must be between 0 and {STEPS_PER_BAR-1}")

@dataclass
class PhraseConfig(BaseRestConfig):
    """Configuration for phrase-end rest patterns."""
    phrase_length: int = 16       # Length of each phrase in steps
    rest_length: int = 1          # Length of rest at phrase end in steps
    variable_length: bool = False  # Whether phrase length can vary
    
    def __post_init__(self):
        """Validate configuration."""
        if not MIN_PATTERN_LENGTH <= self.phrase_length <= MAX_PATTERN_LENGTH:
            raise ValueError(f"phrase_length must be between {MIN_PATTERN_LENGTH} and {MAX_PATTERN_LENGTH}")
        if self.rest_length < 1:
            raise ValueError("rest_length must be positive")
        if self.rest_length >= self.phrase_length:
            raise ValueError("rest_length must be less than phrase_length") 

@dataclass
class RestPatternConfig:
    """Main configuration class for rest pattern generation."""
    pattern_type: RestPatternType = RestPatternType.FIXED
    fixed_config: FixedPatternConfig = None
    probability_config: ProbabilityConfig = None
    musical_pos_config: MusicalPosConfig = None
    phrase_config: PhraseConfig = None
    
    def __post_init__(self):
        """Initialize and validate configuration."""
        # Initialize configs with defaults if not provided
        if self.fixed_config is None:
            self.fixed_config = FixedPatternConfig()
        if self.probability_config is None:
            self.probability_config = ProbabilityConfig()
        if self.musical_pos_config is None:
            self.musical_pos_config = MusicalPosConfig()
        if self.phrase_config is None:
            self.phrase_config = PhraseConfig()
            
        # Ensure only one config is enabled
        enabled_configs = []
        if self.fixed_config.enabled:
            enabled_configs.append("fixed")
        if self.probability_config.enabled:
            enabled_configs.append("probability")
        if self.musical_pos_config.enabled:
            enabled_configs.append("musical_pos")
        if self.phrase_config.enabled:
            enabled_configs.append("phrase")
            
        if len(enabled_configs) > 1:
            raise ValueError(f"Only one rest pattern config can be enabled. Found: {enabled_configs}")
            
    def get_active_config(self) -> Optional[BaseRestConfig]:
        """Get the currently active configuration based on pattern_type."""
        config_map = {
            RestPatternType.FIXED: self.fixed_config,
            RestPatternType.PROBABILITY: self.probability_config,
            RestPatternType.MUSICAL_POS: self.musical_pos_config,
            RestPatternType.PHRASE: self.phrase_config
        }
        return config_map.get(self.pattern_type)
        
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'RestPatternConfig':
        """Create a RestPatternConfig from a dictionary."""
        pattern_type = RestPatternType[config_dict.get('pattern_type', 'FIXED')]
        
        # Create specific config based on pattern type
        config_classes = {
            RestPatternType.FIXED: FixedPatternConfig,
            RestPatternType.PROBABILITY: ProbabilityConfig,
            RestPatternType.MUSICAL_POS: MusicalPosConfig,
            RestPatternType.PHRASE: PhraseConfig
        }
        
        specific_config = config_dict.get(f"{pattern_type.lower()}_config", {})
        active_config = config_classes[pattern_type](**specific_config)
        active_config.enabled = True
        
        # Create main config with only the active specific config
        kwargs = {
            'pattern_type': pattern_type,
            f"{pattern_type.lower()}_config": active_config
        }
        
        return cls(**kwargs) 
