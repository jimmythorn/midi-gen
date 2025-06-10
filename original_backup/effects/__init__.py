"""
MIDI effect system initialization and utilities.

This module provides utility functions for creating and managing MIDI effects.
"""

from typing import Dict, List, Tuple, Optional
from midi_gen.utils.midi_types import MidiInstruction, NoteValue, Velocity, Tick
from .base import NoteContext

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
