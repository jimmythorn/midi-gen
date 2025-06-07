"""
Base class for MIDI sequence generators.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..core.types import MidiEvent

class BaseGenerator(ABC):
    """Abstract base class for MIDI sequence generators."""
    
    def __init__(self, bpm: int = 120):
        """Initialize the base generator.
        
        Args:
            bpm: Beats per minute for the sequence
        """
        self.bpm = bpm
        self._sequence: List[MidiEvent] = []

    @abstractmethod
    def generate(self, **kwargs) -> List[MidiEvent]:
        """Generate a sequence of MIDI events.
        Must be implemented by concrete generator classes.
        
        Args:
            **kwargs: Generator-specific parameters
        
        Returns:
            List of MIDI events
        """
        pass

    @abstractmethod
    def validate_params(self, **kwargs) -> bool:
        """Validate generator-specific parameters.
        Must be implemented by concrete generator classes.
        
        Args:
            **kwargs: Generator-specific parameters
        
        Returns:
            True if parameters are valid, False otherwise
        """
        pass

    def clear(self) -> None:
        """Clear the current sequence."""
        self._sequence = []

    @property
    def sequence(self) -> List[MidiEvent]:
        """Get the current sequence.
        
        Returns:
            List of MIDI events
        """
        return self._sequence.copy()

    def set_bpm(self, bpm: int) -> None:
        """Set the tempo in beats per minute.
        
        Args:
            bpm: Beats per minute
        
        Raises:
            ValueError: If bpm is not positive
        """
        if bpm <= 0:
            raise ValueError("BPM must be positive")
        self.bpm = bpm
