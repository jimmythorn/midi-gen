"""
Base classes and protocols for MIDI effects.
"""

from typing import TypedDict, Protocol, Union, List, Dict
from .midi_types import NoteValue, Velocity, MidiInstruction

class NoteContext(TypedDict):
    """Context for a single MIDI note, including its properties."""
    note: NoteValue
    velocity: Velocity
    # Future properties like duration, time_since_last_note, bpm, etc., can be added here.

class MidiEffect(Protocol):
    """Protocol defining the interface for MIDI effects."""
    def __init__(self, **kwargs) -> None:
        """Initialize the effect with its specific parameters."""
        ...

    def apply(self, event_list: List, options: Dict) -> Union[List[MidiInstruction], List]:
        """
        Apply the effect to a list of MIDI events.
        
        Args:
            event_list: List of MIDI events (format depends on generation_type)
            options: Dictionary of effect options and parameters
            
        Returns:
            Either a list of MidiInstructions (new format) or the original format
            based on the options and compatibility settings.
        """
        ... 
