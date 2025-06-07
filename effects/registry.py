"""
Registry for managing MIDI effect creation and configuration.
"""

from typing import Dict, List, Type, Union

from .base import BaseEffect, EffectConfiguration
from .humanize import HumanizeVelocityEffect, HumanizeVelocityConfiguration
from .tape_wobble import TapeWobbleEffect, TapeWobbleConfiguration

class EffectRegistry:
    """Registry for managing MIDI effect creation and configuration."""
    
    def __init__(self):
        """Initialize the registry with available effects."""
        self._effects: Dict[str, Type[BaseEffect]] = {
            'humanize_velocity': HumanizeVelocityEffect,
            'tape_wobble': TapeWobbleEffect
        }
        
        self._configurations: Dict[str, Type[EffectConfiguration]] = {
            'humanize_velocity': HumanizeVelocityConfiguration,
            'tape_wobble': TapeWobbleConfiguration
        }
    
    def get_available_effects(self) -> List[str]:
        """Get list of available effect names."""
        return list(self._effects.keys())
    
    def create_effect(
        self,
        effect_name: str,
        config_params: Dict = None
    ) -> BaseEffect:
        """Create an effect instance with the given configuration.
        
        Args:
            effect_name: Name of the effect to create
            config_params: Optional dictionary of configuration parameters
        
        Returns:
            Configured effect instance
        
        Raises:
            ValueError: If effect_name is not recognized
            TypeError: If config_params contains invalid parameters
        """
        if effect_name not in self._effects:
            raise ValueError(f"Unknown effect: {effect_name}")
        
        # Get the configuration class for this effect
        config_class = self._configurations[effect_name]
        
        # Create configuration with default values
        if config_params is None:
            config_params = {}
        
        try:
            config = config_class(**config_params)
        except TypeError as e:
            raise TypeError(f"Invalid configuration parameters for {effect_name}: {str(e)}")
        
        # Create and return the effect instance
        effect_class = self._effects[effect_name]
        return effect_class(config)
    
    def create_effect_chain(
        self,
        effect_configs: List[Dict[str, Union[str, Dict]]]
    ) -> List[BaseEffect]:
        """Create multiple effects from a list of configurations.
        
        Args:
            effect_configs: List of dictionaries containing:
                - 'name': Name of the effect
                - 'config': Optional dictionary of configuration parameters
        
        Returns:
            List of configured effect instances in specified order
        """
        effects = []
        for effect_config in effect_configs:
            name = effect_config['name']
            config = effect_config.get('config', {})
            effects.append(self.create_effect(name, config))
        return effects
