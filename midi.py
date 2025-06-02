import mido
from typing import Dict, List, Tuple, Optional
# import random # No longer needed
# import math # No longer needed
from .effects_base import MidiEffect, NoteContext

# Removed calculate_note_length function as it's overcomplicated for fixed 16th notes

# Type alias for structured MIDI events
MidiEvent = Tuple[int, int, int, int] # (note, start_tick, duration_tick, velocity)

def create_midi_file(event_list: List, options: Dict, active_effects: List[MidiEffect]) -> str:
    """
    Generates a MIDI file from a list of events.
    The format of event_list depends on options['generation_type'].
    For 'arpeggio', it's List[Optional[int]] representing sequential 16th notes.
    For 'drone', it's List[MidiEvent] representing (note, start_tick, duration_tick, velocity).

    :param event_list: List of MIDI notes/events.
    :param options: Dictionary containing configuration options.
    :param active_effects: A list of instantiated MidiEffect objects (primarily for arpeggios).
    :return: The filename where the MIDI was saved.
    """
    bpm = options.get('bpm', 120)
    filename = options.get('filename', "arpeggio.mid")
    generation_type = options.get('generation_type', 'arpeggio')

    ticks_per_beat = 480 # Standard MIDI ticks per quarter note

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo_event_time = 0 # Tempo event is first
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=tempo_event_time))

    processed_events: List[Tuple[int, int, str]] = [] # (tick, type='note_on'/'note_off', note_number, velocity)

    if generation_type == 'arpeggio':
        # Convert flat list of 16th notes to structured events
        # Arpeggio effects are applied here before converting to note_on/note_off events
        sixteenth_note_duration_ticks = ticks_per_beat // 4
        current_tick = 0
        for raw_note_value in event_list: # event_list is List[Optional[int]] for arpeggios
            if raw_note_value == 0 or raw_note_value is None:  # Rest
                current_tick += sixteenth_note_duration_ticks
            else:
                note_ctx = NoteContext(note=int(raw_note_value), velocity=64) # Default arpeggio velocity
                for effect in active_effects: # Apply arpeggio-specific effects
                    note_ctx = effect.apply(note_ctx)
                
                note = max(0, min(127, int(round(note_ctx['note']))))
                velocity = max(0, min(127, int(round(note_ctx['velocity']))))

                if note == 0: velocity = 0 # Treat note 0 as silence

                processed_events.append((current_tick, 'note_on', note, velocity))
                processed_events.append((current_tick + sixteenth_note_duration_ticks, 'note_off', note, 0))
                current_tick += sixteenth_note_duration_ticks
    elif generation_type == 'drone':
        # event_list is List[MidiEvent] = List[Tuple[note, start_tick, duration_tick, velocity]]
        # Drone effects (if any) should ideally be part of how drone events are generated.
        # Here we just schedule them.
        for note, start_tick, duration_tick, velocity in event_list:
            if duration_tick <= 0: continue # Skip zero/negative duration notes
            note = max(0, min(127, int(round(note))))
            velocity = max(0, min(127, int(round(velocity))))
            if note == 0: velocity = 0

            processed_events.append((start_tick, 'note_on', note, velocity))
            processed_events.append((start_tick + duration_tick, 'note_off', note, 0))
    else:
        raise ValueError(f"Unknown generation_type: {generation_type}")

    # Sort all events by tick, then by type (note_off before note_on at same tick for correctness)
    # Mido handles simultaneous events correctly if note_off appears before note_on for re-articulation.
    # Sorting order: 1. Tick time, 2. Event type ('note_off' < 'note_on')
    processed_events.sort(key=lambda x: (x[0], x[1] == 'note_on'))

    last_tick = 0
    for tick, type, note, velocity in processed_events:
        delta_tick = tick - last_tick
        track.append(mido.Message(type, note=note, velocity=velocity, time=delta_tick))
        last_tick = tick

    mid.save(filename)
    return filename
