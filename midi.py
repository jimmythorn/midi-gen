import mido
from typing import Dict, List
import random
import math
from midi_gen.effects_base import MidiEffect, NoteContext

def calculate_note_length(bar_length: int, notes_per_bar: int) -> int:
    """
    Calculates the length of each note based on the number of bars and notes per bar.
    """
    ticks_per_beat = 480  # Assuming standard resolution
    ticks_per_bar = ticks_per_beat * 4 * bar_length  # For 4/4 time signature
    note_length_in_ticks = ticks_per_bar / (notes_per_bar * bar_length)
    return round(note_length_in_ticks)

def create_midi_file(arpeggio: list, options: Dict, active_effects: List[MidiEffect]) -> str:
    """
    Generates a MIDI file from the arpeggio with specified options and applies active effects.

    :param arpeggio: List of MIDI notes to use in the arpeggio.
    :param options: Dictionary containing various configuration options.
    :param active_effects: A list of instantiated MidiEffect objects to apply to notes.
    :return: The filename where the MIDI was saved.
    """
    bpm = options.get('bpm', 120)
    bars = options.get('bars', 16)
    arp_steps = options.get('arp_steps', 16)  
    filename = options.get('filename', "arpeggio.mid")

    ticks_per_beat = 480

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo = mido.bpm2tempo(bpm)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    note_duration = calculate_note_length(bars, arp_steps)

    time_accumulator = 0
    for raw_note_value in arpeggio[:bars * arp_steps]:  # Limit to the desired number of notes
        if raw_note_value == 0 or raw_note_value is None:  # Skip if note is 0 or None (for rest or error handling)
            time_accumulator += note_duration
        else:
            # Initial note context
            note_ctx = NoteContext(note=raw_note_value, velocity=64) # Default velocity, can be configured too

            # Apply all active effects in sequence
            for effect in active_effects:
                note_ctx = effect.apply(note_ctx)
            
            # Extract processed note values
            processed_note = note_ctx['note']
            processed_velocity = note_ctx['velocity']

            # Ensure note and velocity are valid MIDI values after effects
            processed_note = max(0, min(127, processed_note))
            processed_velocity = max(0, min(127, processed_velocity if processed_note > 0 else 0))
            
            track.append(mido.Message('note_on', note=processed_note, velocity=processed_velocity, time=time_accumulator))
            track.append(mido.Message('note_off', note=processed_note, velocity=processed_velocity, time=note_duration))
            time_accumulator = 0 # Reset time for the next message after a note_on

    mid.save(filename)
    return filename
