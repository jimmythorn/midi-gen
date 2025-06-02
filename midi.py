import mido
from typing import Dict, List, Union, cast, Tuple, Optional
# import random # No longer needed
# import math # No longer needed
from .effects_base import MidiEffect, NoteContext
from .midi_types import (
    MidiInstruction, NoteValue, Velocity, Tick, BendValue,
    MIDI_PITCH_BEND_CENTER, DEFAULT_TICKS_PER_BEAT
)

# Removed calculate_note_length function as it's overcomplicated for fixed 16th notes

# Type alias for structured MIDI events
MidiEvent = Tuple[int, int, int, int] # (note, start_tick, duration_tick, velocity)

def create_midi_file(
    event_list: Union[List[MidiInstruction], List],
    options: Dict,
    active_effects: List[MidiEffect]
) -> str:
    """
    Generates a MIDI file from a list of events.
    Supports both new MidiInstruction format and legacy formats:
    - New: List[MidiInstruction] with explicit note_on, note_off, pitch_bend, and control_change events
    - Legacy Arpeggio: List[Optional[int]] representing sequential 16th notes
    - Legacy Drone: List[Tuple[int, int, int, int]] representing (note, start_tick, duration_tick, velocity)

    Args:
        event_list: List of MIDI events in either new or legacy format
        options: Dictionary containing configuration options
        active_effects: List of instantiated MidiEffect objects

    Returns:
        The filename where the MIDI was saved
    """
    bpm = options.get('bpm', 120)
    filename = options.get('filename', "arpeggio.mid")
    generation_type = options.get('generation_type', 'arpeggio')
    ticks_per_beat = options.get('ticks_per_beat', DEFAULT_TICKS_PER_BEAT)

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))

    # Check if we're dealing with new format instructions
    if event_list and isinstance(event_list[0], tuple) and isinstance(event_list[0][0], str):
        processed_events = _process_new_format_events(cast(List[MidiInstruction], event_list))
    else:
        processed_events = _process_legacy_format_events(event_list, options, active_effects)

    # Sort all events by tick, then by type (note_off before note_on at same tick)
    processed_events.sort(key=lambda x: (x[0], x[1] == 'note_on'))

    last_tick = 0
    for event in processed_events:
        tick = event[0]
        msg_type = event[1]
        delta_tick = tick - last_tick

        if msg_type == 'pitch_bend':
            # event format: (tick, 'pitch_bend', value, channel)
            track.append(mido.Message('pitchwheel', 
                                    pitch=event[2],  # Already in 0-16383 range
                                    channel=event[3],
                                    time=delta_tick))
        elif msg_type == 'control_change':
            # event format: (tick, 'control_change', control, value, channel)
            channel = event[4] if len(event) > 4 else 0
            track.append(mido.Message('control_change',
                                    control=event[2],
                                    value=event[3],
                                    channel=channel,
                                    time=delta_tick))
        else:  # note_on or note_off
            # event format: (tick, 'note_on/off', note, velocity, channel)
            channel = event[4] if len(event) > 4 else 0
            track.append(mido.Message(msg_type,
                                    note=event[2],
                                    velocity=event[3],
                                    channel=channel,
                                    time=delta_tick))
        last_tick = tick

    mid.save(filename)
    return filename

def _process_new_format_events(event_list: List[MidiInstruction]) -> List[tuple]:
    """Process events in the new MidiInstruction format."""
    processed_events = []
    for event in event_list:
        if len(event) < 3:  # Skip malformed events
            continue
            
        event_type = event[0]
        tick = int(event[1])  # Ensure tick is an integer
        
        if event_type == 'pitch_bend':
            # Include channel if provided
            channel = event[3] if len(event) > 3 else 0
            processed_events.append((tick, event_type, event[2], channel))
        elif event_type == 'control_change':
            # Include channel if provided
            channel = event[4] if len(event) > 4 else 0
            processed_events.append((tick, event_type, event[2], event[3], channel))
        else:  # note_on or note_off
            # Include channel if provided
            channel = event[4] if len(event) > 4 else 0
            processed_events.append((tick, event_type, event[2], event[3], channel))
            
    return processed_events

def _process_legacy_format_events(
    event_list: List,
    options: Dict,
    active_effects: List[MidiEffect]
) -> List[tuple]:
    """Process events in the legacy format based on generation type."""
    generation_type = options.get('generation_type', 'arpeggio')
    processed_events = []
    
    if generation_type == 'arpeggio':
        # Convert flat list of 16th notes to note events
        sixteenth_note_duration_ticks = DEFAULT_TICKS_PER_BEAT // 4
        current_tick = 0
        
        for raw_note_value in event_list:
            if raw_note_value == 0 or raw_note_value is None:
                current_tick += sixteenth_note_duration_ticks
            else:
                note_ctx = NoteContext(note=int(raw_note_value), velocity=64)
                for effect in active_effects:
                    note_ctx = effect.apply(note_ctx)
                
                note = max(0, min(127, int(round(note_ctx['note']))))
                velocity = max(0, min(127, int(round(note_ctx['velocity']))))
                
                if note > 0:
                    processed_events.append((current_tick, 'note_on', note, velocity))
                    processed_events.append((
                        current_tick + sixteenth_note_duration_ticks,
                        'note_off',
                        note,
                        0
                    ))
                current_tick += sixteenth_note_duration_ticks
                
    elif generation_type == 'drone':
        # Process List[Tuple[note, start_tick, duration_tick, velocity]]
        for note, start_tick, duration_tick, velocity in event_list:
            if duration_tick <= 0:
                continue
            note = max(0, min(127, int(round(note))))
            velocity = max(0, min(127, int(round(velocity))))
            if note > 0:
                processed_events.append((start_tick, 'note_on', note, velocity))
                processed_events.append((start_tick + duration_tick, 'note_off', note, 0))
    
    return processed_events
