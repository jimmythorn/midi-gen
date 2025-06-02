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
DEFAULT_DRONE_ENABLE_WALKDOWNS = True
DEFAULT_DRONE_WALKDOWN_NUM_STEPS = 2
DEFAULT_DRONE_WALKDOWN_STEP_TICKS = 120 # 16th at 480 TPQN
DEFAULT_MINIMUM_TARGET_SUSTAIN_TICKS_FOR_WALKDOWN = 60 # Min duration for the target note after walkdown

def generate_drone_events(options: Dict, processed_root_notes_midi: List[int]) -> List[MidiEvent]:
    """
    Generates drone events with dynamic voicing, octave doubling/shifts, and melodic walkdowns.
    """
    bpm = options.get('bpm', 120)
    total_bars = options.get('bars', 16)
    mode = options.get('mode', 'major')
    min_octave_param = options.get('min_octave', 3)
    max_octave_param = options.get('max_octave', 5)
    base_velocity = options.get('drone_base_velocity', 70)
    
    variation_interval_bars = options.get('drone_variation_interval_bars', DEFAULT_DRONE_VARIATION_INTERVAL_BARS)
    min_notes_held = options.get('drone_min_notes_held', DEFAULT_DRONE_MIN_NOTES_HELD)
    octave_doubling_chance = options.get('drone_octave_doubling_chance', DEFAULT_DRONE_OCTAVE_DOUBLING_CHANCE)
    allow_octave_shifts = options.get('drone_allow_octave_shifts', DEFAULT_DRONE_ALLOW_OCTAVE_SHIFTS)
    octave_shift_one_note_chance = options.get('drone_octave_shift_one_note_chance', DEFAULT_DRONE_OCTAVE_SHIFT_CHANCE)
    enable_walkdowns = options.get('drone_enable_walkdowns', DEFAULT_DRONE_ENABLE_WALKDOWNS)
    walkdown_num_steps = options.get('drone_walkdown_num_steps', DEFAULT_DRONE_WALKDOWN_NUM_STEPS)
    walkdown_step_ticks = options.get('drone_walkdown_step_ticks', DEFAULT_DRONE_WALKDOWN_STEP_TICKS)
    min_target_sustain_ticks = options.get('min_target_sustain_ticks_for_walkdown', DEFAULT_MINIMUM_TARGET_SUSTAIN_TICKS_FOR_WALKDOWN)

    ticks_per_beat = 480
    ticks_per_bar = ticks_per_beat * 4
    variation_interval_ticks = variation_interval_bars * ticks_per_bar

    final_drone_events: List[MidiEvent] = []
    global_current_tick = 0 # Tracks the absolute start tick for events across segments

    if not processed_root_notes_midi:
        # Fallback for no root notes (unchanged)
        c3_midi = 48 
        drone_chord_notes_pc = get_scale(c3_midi, 'major', use_chord_tones=True) 
        drone_chord_notes_abs = [pc + (min_octave_param * 12) for pc in drone_chord_notes_pc]
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
            max(0, min(127, pc + (min_octave_param * 12))) for pc in chord_tone_pitch_classes
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

            interval_start_abs_tick = global_current_tick + current_segment_tick_offset
            current_interval_base_notes = []
            if num_chord_notes < 3 or num_chord_notes < min_notes_held:
                current_interval_base_notes = list(base_chord_notes)
            else:
                current_interval_base_notes.append(base_chord_notes[0]) # Root
                pattern_idx = variation_pattern_counter % 4
                if pattern_idx == 0 or pattern_idx == 2: current_interval_base_notes.extend(base_chord_notes[1:])
                elif pattern_idx == 1 and num_chord_notes > 1: current_interval_base_notes.append(base_chord_notes[num_chord_notes-1]) # 5th-like
                elif pattern_idx == 3 and num_chord_notes > 1: current_interval_base_notes.append(base_chord_notes[1]) # 3rd-like
            current_interval_base_notes = sorted(list(set(current_interval_base_notes)))
            if len(current_interval_base_notes) < min_notes_held and num_chord_notes >= min_notes_held:
                needed = min_notes_held - len(current_interval_base_notes)
                potential_adds = [n for n in base_chord_notes if n not in current_interval_base_notes]
                current_interval_base_notes.extend(potential_adds[:needed])
                current_interval_base_notes = sorted(list(set(current_interval_base_notes)))

            # 2. Apply octave shift to one note (if enabled) from the base voicing
            notes_for_direct_play_and_doubling_source = list(current_interval_base_notes)
            shifted_one_note_this_interval = False
            if allow_octave_shifts:
                # Create a list of indices to shuffle for randomizing which note gets shifted
                indices_to_try_shift = list(range(len(notes_for_direct_play_and_doubling_source)))
                random.shuffle(indices_to_try_shift)
                for i in indices_to_try_shift:
                    note_to_potentially_shift = notes_for_direct_play_and_doubling_source[i]
                    if random.random() < octave_shift_one_note_chance: # Apply overall chance here too
                        direction = random.choice([-12, 12])
                        shifted_note = note_to_potentially_shift + direction
                        if min_octave_param * 12 <= shifted_note < (max_octave_param + 1) * 12 and 0 <= shifted_note <= 127:
                            notes_for_direct_play_and_doubling_source[i] = shifted_note
                            shifted_one_note_this_interval = True
                            break # Only shift one note per interval
            notes_for_direct_play_and_doubling_source = sorted(list(set(notes_for_direct_play_and_doubling_source)))

            # 3. Add events for these (potentially shifted) main notes
            for main_note in notes_for_direct_play_and_doubling_source:
                final_drone_events.append((main_note, interval_start_abs_tick, interval_actual_duration_ticks, base_velocity))
            
            # 4. Process octave doubling (max one per interval, with walkdowns) for each of these main notes
            has_doubled_a_note_this_interval = False
            shuffled_sources_for_doubling = list(notes_for_direct_play_and_doubling_source) # Create a copy to shuffle
            random.shuffle(shuffled_sources_for_doubling)

            for note_being_doubled_source in shuffled_sources_for_doubling: 
                if not has_doubled_a_note_this_interval and random.random() < octave_doubling_chance:
                    direction = random.choice([-12, 12])
                    doubled_note_target = note_being_doubled_source + direction
                    doubled_note_target = max(0, min(127, doubled_note_target))
                    if not (min_octave_param * 12 <= doubled_note_target < (max_octave_param + 2) * 12):
                        continue 
                    can_walkdown = False
                    total_walkdown_duration = 0
                    if enable_walkdowns and walkdown_num_steps > 0 and walkdown_step_ticks > 0:
                        total_walkdown_duration = walkdown_num_steps * walkdown_step_ticks
                        if interval_actual_duration_ticks >= total_walkdown_duration + min_target_sustain_ticks:
                            can_walkdown = True
                    
                    current_walk_start_offset_in_interval = 0 # For walkdown note placement within interval
                    if can_walkdown:
                        for step_idx in range(walkdown_num_steps):
                            semitone_diff = (walkdown_num_steps - step_idx) 
                            walk_note_pitch = (doubled_note_target - semitone_diff) if doubled_note_target > note_being_doubled_source else (doubled_note_target + semitone_diff)
                            walk_note_pitch = max(0, min(127, walk_note_pitch))
                            final_drone_events.append((
                                walk_note_pitch, 
                                interval_start_abs_tick + current_walk_start_offset_in_interval, 
                                walkdown_step_ticks, 
                                base_velocity - 10 # Slightly softer walk notes
                            ))
                            current_walk_start_offset_in_interval += walkdown_step_ticks
                        
                        final_drone_events.append((
                            doubled_note_target, 
                            interval_start_abs_tick + total_walkdown_duration, 
                            interval_actual_duration_ticks - total_walkdown_duration, 
                            base_velocity
                        ))
                    else: 
                        final_drone_events.append((
                            doubled_note_target, 
                            interval_start_abs_tick, 
                            interval_actual_duration_ticks, 
                            base_velocity
                        ))
                    # Whether walkdown happened or not, if doubling was processed, set the flag and break
                    has_doubled_a_note_this_interval = True 
                    break # Stop after the first successful doubling in this interval

            current_segment_tick_offset += interval_actual_duration_ticks
            variation_pattern_counter += 1
        
        global_current_tick += segment_duration_ticks # Advance global tick by the processed segment duration

    return final_drone_events
