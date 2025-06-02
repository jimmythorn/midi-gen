from typing import Dict, List, Tuple
from .scale import get_scale # To get chord tones

# Type alias for structured MIDI events, ensure it matches midi.py if ever moved to a common types file
MidiEvent = Tuple[int, int, int, int] # (note, start_tick, duration_tick, velocity)

def generate_drone_events(options: Dict, processed_root_notes_midi: List[int]) -> List[MidiEvent]:
    """
    Generates a list of structured MIDI events for a drone/pad.
    For this initial version, for each root note segment, it will play the basic triad
    (root, 3rd, 5th) of the mode, starting at the segment's beginning and holding for its full duration.

    :param options: Dictionary containing configuration options (bpm, bars, mode, min_octave, etc.).
    :param processed_root_notes_midi: List of MIDI numbers for root notes of segments.
    :return: A list of MidiEvent tuples.
    """
    bpm = options.get('bpm', 120)
    total_bars = options.get('bars', 16)
    mode = options.get('mode', 'major')
    min_octave = options.get('min_octave', 3) # Drone might be better lower
    # max_octave = options.get('max_octave', 5) # Less critical for simple triads
    base_velocity = options.get('drone_base_velocity', 70) # New option, or default

    ticks_per_beat = 480
    ticks_per_bar = ticks_per_beat * 4

    final_drone_events: List[MidiEvent] = []
    current_tick = 0

    if not processed_root_notes_midi:
        # Fallback: if no root notes, play a single C3 drone for the total duration
        # This case should ideally be handled before calling this function.
        c3_midi = 48 # MIDI C3
        drone_chord_notes = get_scale(c3_midi, 'major', use_chord_tones=True) # Get Cmaj chord tones [0,4,7] relative to C
        drone_chord_notes_abs = [ (c3_midi%12 + interval) + (min_octave * 12) for interval in drone_chord_notes]
        # Ensure notes are within reasonable MIDI range if min_octave is very low/high
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

        segment_duration_ticks = segment_duration_bars * ticks_per_bar

        # Get the 3 chord tones for the current root and mode
        # These are pitch classes (0-11) relative to the root's pitch class
        chord_tone_pitch_classes = get_scale(root_midi_note, mode, use_chord_tones=True)
        
        # Convert to absolute MIDI notes in the specified min_octave
        # We want the notes of the chord based on root_midi_note, not just its pitch class, then adjusted by min_octave
        # Example: root_midi_note = E4 (64). mode = minor. chord_tone_pitch_classes relative to E = [0,3,7] (E,G,B)
        # We want E[min_octave], G[min_octave effectively], B[min_octave effectively]
        # A simple way: form the chord starting at root_midi_note, then transpose to min_octave if needed, or build around min_octave.
        # Let's try to build the chord such that the root of the chord is root_midi_note itself, 
        # then ensure its octave is at least min_octave. Or, build around a base octave.
        
        # Build chord notes based on the actual root_midi_note in its original octave first.
        # Then, if the lowest note is below min_octave, transpose the whole chord up.
        # This is a simple approach; more sophisticated voicing would be better for Phase 2.
        
        # Get absolute chord notes (R, 3, 5) based on the actual root_midi_note
        # The get_scale function returns pitch classes relative to the root's pitch class.
        # We need to apply them to the actual root_midi_note.
        # E.g. root E4 (64), mode minor -> intervals [0,3,7] relative to E itself.
        # So notes are E, G, B in the octave of E4 or around it.
        
        # Let's take root_midi_note as the bass of our chord for this simple version.
        # The chord tones from get_scale are pitch classes [pc1, pc2, pc3]
        # We want actual notes: [root_midi_note, root_midi_note + (pc2-pc1), root_midi_note + (pc3-pc1)]
        # (Careful with modulo arithmetic from get_scale if root_midi_note is high in octave)

        # Simpler: get_scale gives pitch classes [0-11]. Add to root's pitch class, then set octave.
        # This means all notes of the chord will be in the same octave min_octave.
        # Example: E minor, root_midi_note=64 (E4). chord_tone_pitch_classes will be [E,G,B] as (4,7,11) if C=0.
        # If min_octave=3, notes = E3, G3, B3.
        actual_chord_notes = []
        root_pitch_class = root_midi_note % 12
        for interval_from_c in chord_tone_pitch_classes: # these are absolute MIDI pitch classes if root for get_scale was 0
                                                        # if root for get_scale was root_midi_note, these are [0,3,7] or [0,4,7] type intervals
                                                        # get_scale returns: [(root_midi_pitch_class + interval) % 12 ...]
                                                        # So chord_tone_pitch_classes are already absolute 0-11 pitch classes
            # Add octave to these pitch classes
            note = interval_from_c + (min_octave * 12)
            # Heuristic: if this makes the note too far from original root_midi_note's octave, adjust.
            # e.g. root E4 (64), min_octave 2. Chord note B. (11 + 2*12 = 35, B2).
            # This seems okay for now, placing the chord tones in the min_octave.
            # A better voicing might place the root_midi_note itself and build chord around it.
            
            # For simplicity in v1: Take the root_midi_note. Build the triad above it using intervals.
            # Intervals from get_scale when use_chord_tones=True are effectively [0, 3/4, 7] (or 6 for locrian)
            # if get_scale returned intervals relative to its *input* root, not pitch classes.
            # Let's re-check get_scale: it returns `(root_midi_pitch_class + interval) % 12`. So they are PC.
            # To get the actual chord: root_midi_note itself, then find the 3rd and 5th above it.

        # Corrected chord generation for v1:
        # Take the root_midi_note as the lowest note of the chord for now.
        # Determine the quality (major/minor/dim) from the mode.
        # This is implicitly handled by get_scale if we take its output pitch classes and build the chord around min_octave.
        
        current_segment_chord_notes = []
        # The pitch classes from get_scale are absolute (0-11). Add octave.
        for pc in chord_tone_pitch_classes:
            note_in_min_octave = pc + (min_octave * 12)
            # Optional: try to voice them closer to the original root_midi_note's octave if very different
            # For now, just use min_octave as the base for all chord tones.
            current_segment_chord_notes.append(max(0,min(127, note_in_min_octave)))
        
        # Ensure we have distinct notes, especially if min_octave is very high/low clamping them.
        current_segment_chord_notes = sorted(list(set(current_segment_chord_notes)))
        if not current_segment_chord_notes:
            current_segment_chord_notes = [max(0,min(127, root_midi_note))] # Fallback to root

        print(f"[DRONE DEBUG] Root: {root_midi_note}, Mode: {mode}, Chord Tones (PCs): {chord_tone_pitch_classes}, Voiced Notes: {current_segment_chord_notes}")

        for note_to_play in current_segment_chord_notes:
            # Add event: (note, start_tick, duration_tick, velocity)
            final_drone_events.append((note_to_play, current_tick, segment_duration_ticks, base_velocity))

        current_tick += segment_duration_ticks

    return final_drone_events 
