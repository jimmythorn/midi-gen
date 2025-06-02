import random # Added for future, more varied interest
from typing import Dict, List, Tuple
from .scale import get_scale # To get chord tones

# Type alias for structured MIDI events, ensure it matches midi.py if ever moved to a common types file
MidiEvent = Tuple[int, int, int, int] # (note, start_tick, duration_tick, velocity)

# New option for controlling drone interest
DEFAULT_DRONE_VARIATION_INTERVAL_BARS = 1 # How often the drone voicing can change
DEFAULT_DRONE_MIN_NOTES_HELD = 2 # Minimum notes of the chord to hold
DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE = 0.25
DEFAULT_DRONE_ALLOW_OCTAVE_SHIFTS = True
DEFAULT_DRONE_OCTAVE_SHIFT_CHANCE = 0.1 # Chance for a note to shift its octave in an interval

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
    max_octave = options.get('max_octave', 5) # Used for clamping octave shifts/doubles
    base_velocity = options.get('drone_base_velocity', 70)
    
    variation_interval_bars = options.get('drone_variation_interval_bars', DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
    min_notes_held = options.get('drone_min_notes_held', DEFAULT_DRONE_MIN_NOTES_HELD)
    octave_doubling_chance = options.get('drone_octave_doubling_chance', DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)
    allow_octave_shifts = options.get('drone_allow_octave_shifts', DEFAULT_DRONE_ALLOW_OCTAVE_SHIFTS)
    octave_shift_one_note_chance = options.get('drone_octave_shift_one_note_chance', DEFAULT_DRONE_OCTAVE_SHIFT_CHANCE) # Chance for one note in the interval to shift

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
        
        base_chord_notes = sorted(list(set([
            max(0, min(127, pc + (min_octave * 12))) for pc in chord_tone_pitch_classes
        ])))
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

            current_interval_notes = [] # Notes chosen by base voicing pattern
            if num_chord_notes < 3 or num_chord_notes < min_notes_held:
                current_interval_notes = list(base_chord_notes)
            else:
                current_interval_notes.append(base_chord_notes[0]) # Always play root
                pattern_index = variation_pattern_counter % 4
                if pattern_index == 0 or pattern_index == 2: # Play all
                    current_interval_notes.extend(base_chord_notes[1:])
                elif pattern_index == 1: # Play Root + 5th (last note)
                    if num_chord_notes > 1: current_interval_notes.append(base_chord_notes[num_chord_notes-1])
                elif pattern_index == 3: # Play Root + 3rd (second note)
                    if num_chord_notes > 1: current_interval_notes.append(base_chord_notes[1])
            
            current_interval_notes = sorted(list(set(current_interval_notes))) # Ensure unique notes from pattern

            # Ensure min_notes_held
            if len(current_interval_notes) < min_notes_held and num_chord_notes >= min_notes_held:
                needed = min_notes_held - len(current_interval_notes)
                potential_adds = [n for n in base_chord_notes if n not in current_interval_notes]
                current_interval_notes.extend(potential_adds[:needed])
                current_interval_notes = sorted(list(set(current_interval_notes)))

            final_notes_for_interval = list(current_interval_notes) # Start with notes from voicing pattern

            # --- Octave Doubling & Shifting ---
            notes_after_octave_fx = []
            shifted_one_note_this_interval = False

            for note in current_interval_notes: # Iterate over notes from base pattern
                original_note = note
                # 1. Octave Shift (chance for one note in the selection to shift)
                if allow_octave_shifts and not shifted_one_note_this_interval and random.random() < octave_shift_one_note_chance:
                    direction = random.choice([-12, 12])
                    shifted_note = note + direction
                    # Clamp to overall min/max octave boundaries, somewhat loosely
                    if min_octave * 12 <= shifted_note < (max_octave + 1) * 12 and 0 <= shifted_note <= 127:
                        note = shifted_note # The original note is now shifted for this interval
                        shifted_one_note_this_interval = True # Only shift one note per interval
                notes_after_octave_fx.append(note) # Add the (potentially shifted) note

                # 2. Octave Doubling (applies to the potentially shifted note)
                if random.random() < octave_doubling_chance:
                    direction = random.choice([-12, 12])
                    doubled_note = note + direction
                    # Clamp to MIDI range and somewhat to overall octaves
                    if 0 <= doubled_note <= 127 and \
                       (min_octave * 12 <= doubled_note < (max_octave + 2) * 12): # Allow doubling to go one octave beyond max_octave
                        notes_after_octave_fx.append(doubled_note)
            
            final_notes_for_interval = sorted(list(set(notes_after_octave_fx))) # Update and make unique
            
            # Ensure min_notes_held again after octave effects, if it somehow reduced viable notes (e.g. all shifted out of range)
            # This is a safeguard; ideally, clamping logic handles it.
            if len(final_notes_for_interval) < min_notes_held and num_chord_notes >= min_notes_held:
                final_notes_for_interval = list(current_interval_notes) # Revert to pre-octave FX if too few
                needed = min_notes_held - len(final_notes_for_interval)
                potential_adds = [n for n in base_chord_notes if n not in final_notes_for_interval]
                final_notes_for_interval.extend(potential_adds[:needed])
                final_notes_for_interval = sorted(list(set(final_notes_for_interval)))

            print(f"[DRONE DETAIL] Seg {idx}, IVL {variation_pattern_counter}, Tick: {global_current_tick + current_segment_tick_offset}, Notes: {final_notes_for_interval}")

            for note_to_play in final_notes_for_interval:
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
