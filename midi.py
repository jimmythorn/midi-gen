import mido
from typing import Dict, List
# import random # No longer needed
# import math # No longer needed
from .effects_base import MidiEffect, NoteContext

# Removed calculate_note_length function as it's overcomplicated for fixed 16th notes

def create_midi_file(arpeggio: list, options: Dict, active_effects: List[MidiEffect]) -> str:
    """
    Generates a MIDI file from the arpeggio with specified options and applies active effects.
    The input 'arpeggio' list is assumed to contain events that are 16th notes.

    :param arpeggio: List of MIDI notes, where each element represents a 16th note step.
    :param options: Dictionary containing various configuration options.
    :param active_effects: A list of instantiated MidiEffect objects to apply to notes.
    :return: The filename where the MIDI was saved.
    """
    bpm = options.get('bpm', 120)
    # bars = options.get('bars', 16) # Not directly needed for iteration if arpeggio list is complete
    # arp_steps = options.get('arp_steps', 16) # Not directly needed for iteration
    filename = options.get('filename', "arpeggio.mid")

    ticks_per_beat = 480 # Standard MIDI ticks per quarter note

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo = mido.bpm2tempo(bpm)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    # Duration of each note in the arpeggio list (assuming they are all 16th notes)
    # A 16th note is 1/4 of a beat.
    sixteenth_note_duration_ticks = ticks_per_beat // 4 

    time_since_last_event = 0 # Mido time is delta time from previous event
    
    # Iterate over the entire arpeggio list. 
    # arpeggio_generation.py ensures this list has (total_bars * 16) notes.
    for raw_note_value in arpeggio:
        if raw_note_value == 0 or raw_note_value is None:  # Treat 0 or None as a rest
            time_since_last_event += sixteenth_note_duration_ticks
        else:
            note_ctx = NoteContext(note=int(raw_note_value), velocity=64) # Ensure note is int

            for effect in active_effects:
                note_ctx = effect.apply(note_ctx)
            
            processed_note = note_ctx['note']
            processed_velocity = note_ctx['velocity']

            processed_note = max(0, min(127, int(round(processed_note)))) # Ensure int and clamped
            processed_velocity = max(0, min(127, int(round(processed_velocity)))) # Ensure int and clamped
            
            # If note is 0 after processing, it can be treated as a rest or skipped.
            # For now, writing note 0 with velocity 0 is like a rest too.
            if processed_note == 0 : processed_velocity = 0

            track.append(mido.Message('note_on', note=processed_note, velocity=processed_velocity, time=time_since_last_event))
            track.append(mido.Message('note_off', note=processed_note, velocity=0, time=sixteenth_note_duration_ticks))
            time_since_last_event = 0 # Reset delta time for next event, as it follows immediately after note_off

    mid.save(filename)
    return filename
