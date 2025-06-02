import random # Added for future, more varied interest
from typing import Dict, List, Tuple
from .scale import get_scale # To get chord tones

# Type alias for structured MIDI events, ensure it matches midi.py if ever moved to a common types file
MidiEvent = Tuple[int, int, int, int] # (note, start_tick, duration_tick, velocity)

# New option for controlling drone interest
DEFAULT_DRONE_VARIATION_INTERVAL_BARS = 1 # How often the drone voicing can change
DEFAULT_DRONE_MIN_NOTES_HELD = 2 # Minimum notes of the chord to hold

def generate_drone_events(options: Dict, processed_root_notes_midi: List[int]) -> List[MidiEvent]:
    """
    Generates a list of structured MIDI events for a drone/pad.
    Introduces variation by changing which notes of the chord are played
    over sub-intervals within each root note's segment, ensuring a minimum
    number of notes are always sounding.
    """
    bpm = options.get('bpm', 120)
    total_bars = options.get('bars', 16)
    mode = options.get('mode', 'major')
    min_octave = options.get('min_octave', 3)
    base_velocity = options.get('drone_base_velocity', 70)
    
    variation_interval_bars = options.get('drone_variation_interval_bars', DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
    min_notes_held = options.get('drone_min_notes_held', DEFAULT_DRONE_MIN_NOTES_HELD)

    ticks_per_beat = 480
    ticks_per_bar = ticks_per_beat * 4
    variation_interval_ticks = variation_interval_bars * ticks_per_bar

    final_drone_events: List[MidiEvent] = []
    global_current_tick = 0 # Tracks the absolute start tick for events across segments

    if not processed_root_notes_midi:
        # Fallback for no root notes (unchanged)
        c3_midi = 48 
        drone_chord_notes_pc = get_scale(c3_midi, 'major', use_chord_tones=True) 
        drone_chord_notes_abs = [pc + (min_octave * 12) for pc in drone_chord_notes_pc]
        drone_chord_notes_abs = [max(0, min(127, note)) for note in drone_chord_notes_abs]
        total_duration_ticks = total_bars * ticks_per_bar
        for note in drone_chord_notes_abs:
            final_drone_events.append((note, 0, total_duration_ticks, base_velocity))
        return final_drone_events

    num_root_notes = len(processed_root_notes_midi)
    bars_per_segment = total_bars // num_root_notes if num_root_notes > 0 else total_bars

    for idx, root_midi_note in enumerate(processed_root_notes_midi):
        segment_duration_bars = bars_per_segment
        if idx == num_root_notes - 1: # Last segment gets remaining bars
            segment_duration_bars = total_bars - (bars_per_segment * idx)
        
        if segment_duration_bars <= 0:
            continue

        segment_start_tick = global_current_tick
        segment_duration_ticks = segment_duration_bars * ticks_per_bar

        chord_tone_pitch_classes = get_scale(root_midi_note, mode, use_chord_tones=True)
        
        base_chord_notes = []
        for pc in chord_tone_pitch_classes:
            note_in_min_octave = pc + (min_octave * 12)
            base_chord_notes.append(max(0,min(127, note_in_min_octave)))
        
        base_chord_notes = sorted(list(set(base_chord_notes)))
        if not base_chord_notes: # Fallback
            base_chord_notes = [max(0,min(127, root_midi_note))] 
        
        num_chord_notes = len(base_chord_notes)
        if num_chord_notes == 0: continue # Should not happen if fallback works

        print(f"[DRONE DEBUG] Root: {root_midi_note}, Mode: {mode}, Base Chord: {base_chord_notes}, Segment Bars: {segment_duration_bars}")

        # Iterate through variation intervals within this segment
        current_segment_tick_offset = 0
        variation_pattern_counter = 0 # Simple counter for alternating pattern

        while current_segment_tick_offset < segment_duration_ticks:
            interval_actual_duration_ticks = min(variation_interval_ticks, segment_duration_ticks - current_segment_tick_offset)
            if interval_actual_duration_ticks <= 0: break

            notes_to_play_in_interval = []
            
            # --- Simple Dynamic Voicing Pattern ---
            # Ensure at least min_notes_held (e.g., 2) are playing.
            # For a 3-note chord (R, 3, 5), let's try to keep R and 5, and alternate 3.
            # If fewer than 3 notes in base_chord_notes, play all of them.
            
            if num_chord_notes < 3: # Typically 1 or 2 notes, play all
                notes_to_play_in_interval = list(base_chord_notes)
            else: # Assume 3 notes (e.g., R, 3rd, 5th) for this basic pattern
                # A more robust solution would handle arbitrary chord sizes.
                # Pattern: 0: R,3,5; 1: R,5; 2: R,3,5; 3: R,3 ... (or something similar)
                
                # Let's try: always play root (index 0).
                # Alternate between playing (3rd and 5th) and (just 3rd or just 5th)
                # to ensure at least two notes.
                
                # Current simple pattern:
                # Slot 0: All notes
                # Slot 1: Root and 5th (if 3 notes) or Root and 2nd (if 2 notes available)
                # Slot 2: All notes
                # Slot 3: Root and 3rd (if 3 notes)
                # This needs num_chord_notes to be at least 1, 2, or 3.
                
                # Ensure base_chord_notes are ordered (e.g. R, 3, 5)
                # For simplicity, assume base_chord_notes[0] is root-like, 
                # base_chord_notes[1] is 3rd-like, base_chord_notes[2] is 5th-like.
                
                notes_to_play_in_interval.append(base_chord_notes[0]) # Always play root

                if variation_pattern_counter % 4 == 0: # Play all
                    notes_to_play_in_interval.extend(base_chord_notes[1:])
                elif variation_pattern_counter % 4 == 1: # Play Root + 5th (or last note if not 5th)
                    if num_chord_notes > 1:
                        notes_to_play_in_interval.append(base_chord_notes[num_chord_notes-1]) 
                elif variation_pattern_counter % 4 == 2: # Play all
                     notes_to_play_in_interval.extend(base_chord_notes[1:])
                elif variation_pattern_counter % 4 == 3: # Play Root + 3rd (or second note)
                    if num_chord_notes > 1:
                         notes_to_play_in_interval.append(base_chord_notes[1])
                
                # Ensure minimum notes are held if the pattern results in too few
                # This logic can be complex. A simpler way for now:
                # If after pattern, notes_to_play < min_notes_held, add more from base_chord_notes.
                # For now, this pattern should give 2 or 3 notes if num_chord_notes >= 2.

                # Make sure notes are unique if logic above somehow duplicates
                notes_to_play_in_interval = sorted(list(set(notes_to_play_in_interval)))

                # If somehow the pattern yields less than min_notes_held, force add more.
                # This is a fallback. A better pattern should guarantee it.
                if len(notes_to_play_in_interval) < min_notes_held and num_chord_notes >= min_notes_held:
                    # Add notes from base_chord_notes until min_notes_held is met
                    needed = min_notes_held - len(notes_to_play_in_interval)
                    potential_adds = [n for n in base_chord_notes if n not in notes_to_play_in_interval]
                    notes_to_play_in_interval.extend(potential_adds[:needed])


            print(f"[DRONE DETAIL] Seg {idx}, Interval {variation_pattern_counter}, Tick: {global_current_tick + current_segment_tick_offset}, Notes: {notes_to_play_in_interval}")

            for note_to_play in notes_to_play_in_interval:
                final_drone_events.append((
                    note_to_play, 
                    global_current_tick + current_segment_tick_offset, 
                    interval_actual_duration_ticks, 
                    base_velocity
                ))
            
            current_segment_tick_offset += interval_actual_duration_ticks
            variation_pattern_counter += 1
        
        global_current_tick += segment_duration_ticks # Advance global tick by the processed segment duration

    return final_drone_events
