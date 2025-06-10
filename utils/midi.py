"""
MIDI file creation and event processing.
"""

import mido
from typing import Dict, List, Union, cast, Tuple, Optional, Sequence
# import random # No longer needed
# import math # No longer needed
from midi_gen.effects.base import (
    MidiEffect, NoteContext, EffectChain
)
from midi_gen.effects.registry import EffectRegistry
from midi_gen.utils.midi_types import (
    MidiEvent,
    MidiEventType,
    MidiInstruction,
    NoteValue,
    Velocity,
    Tick,
    BendValue,
    MIDI_PITCH_BEND_CENTER,
    DEFAULT_TICKS_PER_BEAT,
    Channel
)
import os

# Helper functions that were previously imported
def create_note_context(
    note: NoteValue,
    velocity: Velocity,
    tick: Tick,
    options: Dict,
    duration_ticks: Optional[int] = None,
    is_first_note: bool = False,
    is_last_note: bool = False
) -> NoteContext:
    """Create a note context for effect processing."""
    return {
        'note': note,
        'velocity': velocity,
        'channel': options.get('channel', 0),
        'tick': tick,
        'duration_ticks': duration_ticks,
        'time_seconds': tick / (DEFAULT_TICKS_PER_BEAT * options.get('bpm', 120) / 60),
        'bpm': options.get('bpm', 120),
        'beat_position': (tick % DEFAULT_TICKS_PER_BEAT) / DEFAULT_TICKS_PER_BEAT,
        'bar_position': tick // (DEFAULT_TICKS_PER_BEAT * 4),
        'generation_type': options.get('generation_type', 'arpeggio'),
        'is_first_note': is_first_note,
        'is_last_note': is_last_note,
        'processed_by': []
    }

def convert_legacy_to_instructions(events: List) -> List[MidiInstruction]:
    """Convert legacy event format to MidiInstruction format."""
    instructions: List[MidiInstruction] = []
    for event in events:
        if isinstance(event, tuple) and len(event) >= 4:
            note, start_tick, duration_tick, velocity = event[:4]
            channel = event[4] if len(event) > 4 else 0
            
            if duration_tick > 0:
                instructions.extend([
                    ('note_on', start_tick, note, velocity, channel),
                    ('note_off', start_tick + duration_tick, note, 0, channel)
                ])
    return instructions

class MidiProcessor:
    """Handles MIDI event processing and effect application."""
    
    def __init__(self):
        self.effect_chain = EffectChain()
        
    def add_effect(self, effect: MidiEffect) -> None:
        """Add an effect to the processing chain."""
        self.effect_chain.add_effect(effect)
    
    def process_events(self, 
                      event_list: Sequence[MidiInstruction],
                      options: Dict) -> List[MidiEvent]:
        """
        Process a list of MIDI events through the effect chain.
        Handles both new MidiEvent format and legacy formats.
        """
        # First determine if we're dealing with new format instructions
        if event_list and isinstance(event_list[0], MidiEvent):
            # Already in new format, process directly
            return self.effect_chain.process_sequence(event_list, options)
        else:
            # Convert legacy format to intermediate representation
            processed_events = self._process_legacy_format_events(event_list, options)
            # Process through effect chain
            return self.effect_chain.process_sequence(processed_events, options)
    
    def _process_legacy_format_events(self, 
                                    event_list: List,
                                    options: Dict) -> List[MidiEvent]:
        """Process legacy format events into MidiEvent objects."""
        processed_events: List[MidiEvent] = []
        generation_type = options.get('generation_type', 'arpeggio')
        
        if generation_type == 'arpeggio':
            current_tick = 0
            sixteenth_note_duration_ticks = DEFAULT_TICKS_PER_BEAT // 4
            
            for step_index, raw_note_value in enumerate(event_list):
                if raw_note_value == 0 or raw_note_value is None:
                    current_tick += sixteenth_note_duration_ticks
                    continue
                
                # Create note context for this step
                ctx = create_note_context(
                    note=int(raw_note_value),
                    velocity=64,
                    tick=current_tick,
                    options=options,
                    duration_ticks=sixteenth_note_duration_ticks,
                    is_first_note=(step_index == 0),
                    is_last_note=(step_index == len(event_list) - 1)
                )
                
                # Process through note-level effects
                processed_ctx = self.effect_chain.process_note(ctx)
                
                # Create note events if note is valid
                if processed_ctx['note'] > 0:
                    processed_events.extend([
                        MidiEvent.note_on(
                            current_tick,
                            processed_ctx['note'],
                            processed_ctx['velocity'],
                            processed_ctx['channel']
                        ),
                        MidiEvent.note_off(
                            current_tick + sixteenth_note_duration_ticks,
                            processed_ctx['note'],
                            0,
                            processed_ctx['channel']
                        )
                    ])
                
                current_tick += sixteenth_note_duration_ticks
                
        elif generation_type == 'drone':
            # For drones, we need to track the maximum tick for proper duration calculation
            max_tick = 0
            
            for event in event_list:
                if len(event) < 4:  # Skip invalid events
                    continue
                    
                note, start_tick, duration_tick, velocity = event
                if duration_tick <= 0:
                    continue
                    
                # Update max_tick considering both start and duration
                max_tick = max(max_tick, start_tick + duration_tick)
                    
                # Create note context
                ctx = create_note_context(
                    note=note,
                    velocity=velocity,
                    tick=start_tick,
                    options=options,
                    duration_ticks=duration_tick
                )
                
                # Process through note-level effects
                processed_ctx = self.effect_chain.process_note(ctx)
                
                if processed_ctx['note'] > 0:
                    processed_events.extend([
                        MidiEvent.note_on(
                            start_tick,
                            processed_ctx['note'],
                            processed_ctx['velocity'],
                            processed_ctx['channel']
                        ),
                        MidiEvent.note_off(
                            start_tick + duration_tick,
                            processed_ctx['note'],
                            0,
                            processed_ctx['channel']
                        )
                    ])
            
            # Update options with the correct total duration
            options['total_ticks'] = max_tick
        
        return processed_events

def create_midi_file(
    event_list: Sequence[MidiInstruction],
    options: Dict,
    active_effects: List[MidiEffect]
) -> str:
    """Creates a MIDI file from the processed events."""
    # Initialize processor and add the already created effects
    processor = MidiProcessor()
    for effect in active_effects:
        processor.add_effect(effect)
    
    # Process all events through the effect chain
    processed_events = processor.process_events(event_list, options)
    
    # Sort all events by tick time and event type priority (using MidiEvent's built-in sorting)
    processed_events.sort()
    
    # Create MIDI file
    filename = options.get('filename', "output.mid")
    bpm = options.get('bpm', 120)
    ticks_per_beat = options.get('ticks_per_beat', DEFAULT_TICKS_PER_BEAT)
    
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    
    # Convert all events to MIDI messages
    last_tick = 0
    for event in processed_events:
        delta_time = event.tick - last_tick
        last_tick = event.tick
        
        if event.event_type == MidiEventType.NOTE_ON:
            track.append(mido.Message('note_on', note=event.value1, 
                                    velocity=event.value2, time=delta_time,
                                    channel=event.channel))
        elif event.event_type == MidiEventType.NOTE_OFF:
            track.append(mido.Message('note_off', note=event.value1,
                                    velocity=event.value2, time=delta_time,
                                    channel=event.channel))
        elif event.event_type == MidiEventType.PITCH_BEND:
            # No conversion needed - both use -8192..8191 range
            track.append(mido.Message('pitchwheel', pitch=event.value1,
                                    time=delta_time, channel=event.channel))
        elif event.event_type == MidiEventType.CONTROL_CHANGE:
            track.append(mido.Message('control_change', 
                                    control=event.value1,
                                    value=event.value2,
                                    time=delta_time,
                                    channel=event.channel))
    
    # Save the file - use the filename as is since it's already properly constructed
    mid.save(filename)
    return filename
