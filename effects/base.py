"""
Base classes and utilities for MIDI effects.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, TypedDict, Optional
from ..core.types import MidiEvent, DEFAULT_TICKS_PER_BEAT

class NoteContext(TypedDict):
    """Rich context for MIDI note processing."""
    # Basic MIDI parameters
    note: int
    velocity: int
    channel: int
    
    # Timing information
    time: int  # Tick position
    duration: Optional[int]  # Duration in ticks
    time_seconds: float  # Absolute time in seconds
    
    # Musical context
    bpm: int
    beat_position: float  # Position within beat (0-1)
    bar_position: int  # Current bar number
    
    # Generation context
    generation_type: str  # Type of generator that created this note
    is_first_note: bool  # Whether this is the first note in sequence
    is_last_note: bool  # Whether this is the last note in sequence
    
    # Effect processing
    processed_by: List[str]  # List of effects that have processed this note

def create_note_context(
    note: int,
    velocity: int,
    time: int,
    options: Dict[str, Any],
    **kwargs
) -> NoteContext:
    """Create a new note context with default values.
    
    Args:
        note: MIDI note number
        velocity: Note velocity
        time: Tick position
        options: Generation options including bpm, ticks_per_beat, etc.
        **kwargs: Additional context parameters
    
    Returns:
        Initialized note context
    """
    ticks_per_beat = options.get('ticks_per_beat', DEFAULT_TICKS_PER_BEAT)
    bpm = options.get('bpm', 120)
    
    return NoteContext(
        # Basic MIDI parameters
        note=note,
        velocity=velocity,
        channel=kwargs.get('channel', 0),
        
        # Timing information
        time=time,
        duration=kwargs.get('duration'),
        time_seconds=(time / ticks_per_beat) * (60.0 / bpm),
        
        # Musical context
        bpm=bpm,
        beat_position=(time % ticks_per_beat) / ticks_per_beat,
        bar_position=int(time / (ticks_per_beat * 4)),
        
        # Generation context
        generation_type=options.get('generation_type', 'arpeggio'),
        is_first_note=kwargs.get('is_first_note', False),
        is_last_note=kwargs.get('is_last_note', False),
        
        # Effect processing
        processed_by=[]
    )

class BaseEffect(ABC):
    """Abstract base class for all MIDI effects."""
    
    def __init__(self, **config):
        """Initialize the effect with configuration parameters."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate effect-specific configuration parameters."""
        pass
    
    def process_note(self, ctx: NoteContext) -> NoteContext:
        """Process a single note context.
        
        Args:
            ctx: Note context to process
        
        Returns:
            Processed note context
        """
        if self.__class__.__name__ in ctx['processed_by']:
            return ctx
        
        new_ctx = self._process_note_impl(ctx.copy())
        new_ctx['processed_by'].append(self.__class__.__name__)
        return new_ctx
    
    def process_sequence(self, events: List[MidiEvent], options: Dict) -> List[MidiEvent]:
        """Process a sequence of MIDI events.
        
        Args:
            events: List of MIDI events to process
            options: Processing options
        
        Returns:
            Processed MIDI events
        """
        return self._process_sequence_impl(events, options)
    
    @abstractmethod
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Implementation for note-level processing."""
        return ctx
    
    @abstractmethod
    def _process_sequence_impl(self, events: List[MidiEvent], options: Dict) -> List[MidiEvent]:
        """Implementation for sequence-level processing."""
        return events

class EffectChain:
    """Chain of MIDI effects to be applied in sequence."""
    
    def __init__(self):
        """Initialize an empty effect chain."""
        self.effects: List[BaseEffect] = []
    
    def add_effect(self, effect: BaseEffect) -> None:
        """Add an effect to the chain.
        
        Args:
            effect: Effect to add
        """
        self.effects.append(effect)
    
    def process_note(self, ctx: NoteContext) -> NoteContext:
        """Process a note through all effects in the chain.
        
        Args:
            ctx: Note context to process
        
        Returns:
            Processed note context
        """
        for effect in self.effects:
            ctx = effect.process_note(ctx)
        return ctx
    
    def process_sequence(self, events: List[MidiEvent], options: Dict) -> List[MidiEvent]:
        """Process a sequence through all effects in the chain.
        
        Args:
            events: MIDI events to process
            options: Processing options
        
        Returns:
            Processed MIDI events
        """
        processed_events = events
        for effect in self.effects:
            processed_events = effect.process_sequence(processed_events, options)
        return processed_events
