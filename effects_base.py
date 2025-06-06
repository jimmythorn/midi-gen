"""
Base classes and types for the MIDI effect system.

This module provides the foundation for creating and managing MIDI effects,
including both real-time note processing and post-processing sequence effects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TypedDict, List, Dict, Union, Optional, Tuple, TypeVar, Generic

from .midi_types import (
    NoteValue, Velocity, Tick, MidiInstruction,
    MIDI_PITCH_BEND_CENTER, MIDI_PITCH_BEND_MIN, MIDI_PITCH_BEND_MAX
)

class EffectType(Enum):
    """Defines when in the processing chain an effect should be applied."""
    NOTE_PROCESSOR = auto()  # Applied to individual notes in real-time
    SEQUENCE_PROCESSOR = auto()  # Applied to the full sequence post-generation
    HYBRID = auto()  # Can operate in both modes

class NoteContext(TypedDict):
    """Rich context for MIDI note processing."""
    # Basic MIDI parameters
    note: NoteValue
    velocity: Velocity
    channel: int
    
    # Timing information
    tick: Tick
    duration_ticks: Optional[int]
    time_seconds: float
    
    # Musical context
    bpm: float
    beat_position: float  # Position within the current beat (0.0 to 1.0)
    bar_position: int    # Current bar number
    
    # Generation context
    generation_type: str  # 'arpeggio' or 'drone'
    is_first_note: bool
    is_last_note: bool
    
    # Effect processing
    processed_by: List[str]  # List of effects that have processed this note

@dataclass
class EffectConfiguration:
    """Base configuration for effects."""
    enabled: bool = True
    priority: int = 0  # Lower numbers process first
    effect_type: EffectType = EffectType.SEQUENCE_PROCESSOR

class MidiEffect(ABC):
    """Abstract base class for all MIDI effects."""
    
    def __init__(self, config: EffectConfiguration):
        self.config = config
        self._validate_configuration()
    
    @abstractmethod
    def _validate_configuration(self) -> None:
        """Validate effect-specific configuration parameters."""
        pass
    
    def process_note_context(self, ctx: NoteContext) -> NoteContext:
        """Process a single note in real-time."""
        if self.config.effect_type == EffectType.SEQUENCE_PROCESSOR:
            return ctx
        return self._process_note_impl(ctx)
    
    def process_sequence(self, 
                        events: List[Union[MidiInstruction, Tuple]], 
                        options: Dict) -> List[Union[MidiInstruction, Tuple]]:
        """Process the complete sequence of events."""
        if self.config.effect_type == EffectType.NOTE_PROCESSOR:
            return events
        return self._process_sequence_impl(events, options)
    
    @abstractmethod
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Implementation for note-level processing."""
        pass
    
    @abstractmethod
    def _process_sequence_impl(self, 
                             events: List[Union[MidiInstruction, Tuple]], 
                             options: Dict) -> List[Union[MidiInstruction, Tuple]]:
        """Implementation for sequence-level processing."""
        pass

class EffectChain:
    """Manages a chain of effects and their application order."""
    
    def __init__(self):
        self.effects: List[MidiEffect] = []
    
    def add_effect(self, effect: MidiEffect) -> None:
        """Add an effect to the chain."""
        self.effects.append(effect)
        # Sort by priority
        self.effects.sort(key=lambda x: x.config.priority)
    
    def process_note(self, ctx: NoteContext) -> NoteContext:
        """Process a single note through all applicable effects."""
        current_ctx = ctx.copy()
        for effect in self.effects:
            if effect.config.enabled and effect.config.effect_type in [
                EffectType.NOTE_PROCESSOR, EffectType.HYBRID
            ]:
                current_ctx = effect.process_note_context(current_ctx)
                current_ctx['processed_by'].append(effect.__class__.__name__)
        return current_ctx
    
    def process_sequence(self, 
                        events: List[Union[MidiInstruction, Tuple]], 
                        options: Dict) -> List[Union[MidiInstruction, Tuple]]:
        """Process the complete sequence through all applicable effects."""
        current_events = events
        for effect in self.effects:
            if effect.config.enabled and effect.config.effect_type in [
                EffectType.SEQUENCE_PROCESSOR, EffectType.HYBRID
            ]:
                current_events = effect.process_sequence(current_events, options)
        return current_events

# Utility functions for effect implementation
def create_note_context(
    note: NoteValue,
    velocity: Velocity,
    tick: Tick,
    options: Dict,
    **kwargs
) -> NoteContext:
    """Create a new note context with default values."""
    return NoteContext(
        note=note,
        velocity=velocity,
        channel=kwargs.get('channel', 0),
        tick=tick,
        duration_ticks=kwargs.get('duration_ticks'),
        time_seconds=(tick / options.get('ticks_per_beat', 480)) * 
                    (60.0 / options.get('bpm', 120)),
        bpm=options.get('bpm', 120),
        beat_position=(tick % options.get('ticks_per_beat', 480)) / 
                     options.get('ticks_per_beat', 480),
        bar_position=int(tick / (options.get('ticks_per_beat', 480) * 4)),
        generation_type=options.get('generation_type', 'arpeggio'),
        is_first_note=kwargs.get('is_first_note', False),
        is_last_note=kwargs.get('is_last_note', False),
        processed_by=[]
    )

def convert_legacy_to_instructions(
    events: List[Tuple],
    generation_type: str
) -> List[MidiInstruction]:
    """
    Convert legacy event format to MidiInstructions.
    
    Args:
        events: List of legacy format events
        generation_type: Either 'arpeggio' or 'drone'
        
    Returns:
        List of MidiInstructions in the new format
    """
    instructions: List[MidiInstruction] = []
    
    if generation_type == 'arpeggio':
        # Convert (tick, type, note, velocity) format
        for event in events:
            if len(event) >= 4:  # Ensure we have enough elements
                tick, msg_type, note, velocity = event[:4]
                channel = event[4] if len(event) > 4 else 0
                instructions.append((msg_type, tick, note, velocity, channel))
    
    elif generation_type == 'drone':
        # Convert (note, start_tick, duration_tick, velocity) format
        for event in events:
            if len(event) >= 4:  # Ensure we have enough elements
                note, start_tick, duration_tick, velocity = event
                channel = event[4] if len(event) > 4 else 0
                # Add note_on event
                instructions.append(('note_on', start_tick, note, velocity, channel))
                # Add note_off event
                instructions.append(('note_off', start_tick + duration_tick, note, 0, channel))
    
    # Sort by tick, with note_offs coming after note_ons at the same tick
    return sorted(instructions, key=lambda x: (x[1], x[0] != 'note_off')) 
