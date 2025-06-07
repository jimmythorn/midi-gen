"""
Configuration for rest pattern generation.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class RestPatternConfig:
    """Configuration for rest pattern generation."""
    enabled: bool = False
    steps_between_rests: int = 4  # Insert rest every N steps
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'RestPatternConfig':
        """Create a RestPatternConfig instance from a dictionary."""
        return cls(
            enabled=config_dict.get('enabled', False),
            steps_between_rests=config_dict.get('steps_between_rests', 4)
        ) 
