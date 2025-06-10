"""
Base classes and types for the MIDI effect system.

This module provides the foundation for creating and managing MIDI effects,
including both real-time note processing and post-processing sequence effects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Union, Optional, Tuple, TypedDict
from midi_gen.utils.midi_types import (
    MidiInstruction, Tick, NoteValue, Velocity, Channel, BendValue,
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
