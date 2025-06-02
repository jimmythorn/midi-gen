import random
import math
from typing import List, Optional, Dict, Union, cast
from .effects_base import MidiEffect, NoteContext
from .midi_types import (
    MidiInstruction, WobbleState, Tick, NoteValue, Velocity,
    MIDI_PITCH_BEND_CENTER, MIDI_PITCH_BEND_MIN, MIDI_PITCH_BEND_MAX,
    DEFAULT_PITCH_BEND_UPDATE_RATE, PITCH_BEND_THRESHOLD,
    DEFAULT_WOW_RATE_HZ, DEFAULT_WOW_DEPTH,
    DEFAULT_FLUTTER_RATE_HZ, DEFAULT_FLUTTER_DEPTH,
    DEFAULT_RANDOMNESS
)

# Legacy type for backward compatibility
MidiEvent = tuple[int, int, int, int]  # (note, start_tick, duration_tick, velocity)

# --- Tape Wobble Generation Function ---
def tape_wobble(options: dict) -> List[tuple[float, int]]:
    """
    Generates a simulated "tape wobble" modulation signal over time.
    
    Returns:
        List of tuples (time_sec, bend_value) where:
        - time_sec: The time in seconds when this bend value should be applied
        - bend_value: The MIDI pitch bend value (-8192 to 8191)
    """
    print("\n=== Tape Wobble Generation Debug ===")
    duration = options.get('duration_sec', 5.0)
    wow_rate = options.get('wow_rate_hz', DEFAULT_WOW_RATE_HZ)
    wow_depth = options.get('wow_depth', DEFAULT_WOW_DEPTH)
    flutter_rate = options.get('flutter_rate_hz', DEFAULT_FLUTTER_RATE_HZ)
    flutter_depth = options.get('flutter_depth', DEFAULT_FLUTTER_DEPTH)
    randomness = options.get('randomness', DEFAULT_RANDOMNESS)
    depth_units = options.get('depth_units', 'cents')
    
    print(f"Parameters:")
    print(f"  Duration: {duration:.2f} sec")
    print(f"  Wow Rate: {wow_rate:.2f} Hz, Depth: {wow_depth:.2f}")
    print(f"  Flutter Rate: {flutter_rate:.2f} Hz, Depth: {flutter_depth:.2f}")
    print(f"  Randomness: {randomness:.2f}")
    print(f"  Depth Units: {depth_units}")
    
    # Calculate optimal sample rate
    nyquist_factor = 4.0
    min_sample_rate = max(
        wow_rate * nyquist_factor,
        flutter_rate * nyquist_factor,
        DEFAULT_PITCH_BEND_UPDATE_RATE
    )
    sample_rate_hz = min(50, max(10, int(min_sample_rate)))
    print(f"Calculated sample rate: {sample_rate_hz} Hz")
    
    if duration <= 0:
        print("Duration <= 0, returning empty list")
        return []

    num_samples = int(duration * sample_rate_hz)
    wobble_data: List[tuple[float, int]] = []
    last_emitted_value = 0
    last_emission_time = 0.0

    # Initialize phase offsets
    clamped_randomness = max(0.0, min(1.0, randomness))
    wow_phase = random.random() * 2 * math.pi * clamped_randomness
    flutter_phase = random.random() * 2 * math.pi * clamped_randomness
    
    print(f"\nInitial phases:")
    print(f"  Wow Phase: {wow_phase:.2f} rad")
    print(f"  Flutter Phase: {flutter_phase:.2f} rad")
    
    # Always emit initial center value
    wobble_data.append((0.0, 0))
    print("\nStarting wobble generation...")

    # Debug counters
    total_values = 0
    emitted_values = 0

    for i in range(num_samples):
        total_values += 1
        t = i / sample_rate_hz
        
        # Calculate components
        wow = wow_depth * math.sin(2 * math.pi * wow_rate * t + wow_phase)
        flutter = flutter_depth * math.sin(2 * math.pi * flutter_rate * t + flutter_phase)
        total_mod = wow + flutter

        # Convert to pitch bend value
        if depth_units == 'cents':
            semitones = total_mod / 100.0
        else:
            semitones = total_mod

        bend_value = int(round((semitones / SEMITONES_PER_BEND) * 8192))
        bend_value = max(MIDI_PITCH_BEND_MIN, min(MIDI_PITCH_BEND_MAX, bend_value))

        # Determine if we should emit
        time_since_last = t - last_emission_time
        value_change = abs(bend_value - last_emitted_value)
        
        if (time_since_last >= MIN_TIME_BETWEEN_BENDS_MS / 1000.0 and 
            value_change >= PITCH_BEND_THRESHOLD):
            wobble_data.append((t, bend_value))
            last_emitted_value = bend_value
            last_emission_time = t
            emitted_values += 1
            
            if emitted_values <= 5 or emitted_values % 50 == 0:  # Print first 5 and every 50th after
                print(f"t={t:.3f}s: wow={wow:.2f}, flutter={flutter:.2f}, total={total_mod:.2f}, "
                      f"semitones={semitones:.3f}, bend={bend_value}")

    print(f"\nWobble generation complete:")
    print(f"Total values calculated: {total_values}")
    print(f"Values emitted: {emitted_values}")
    print(f"Compression ratio: {total_values/emitted_values:.1f}:1")
    print("=====================================\n")
    return wobble_data


# --- Tape Wobble Effect Class (replaces ShimmerEffect) ---
class TapeWobbleEffect(MidiEffect):
    def __init__(self, 
                 wow_rate_hz: float = DEFAULT_WOW_RATE_HZ,
                 wow_depth: float = DEFAULT_WOW_DEPTH,
                 flutter_rate_hz: float = DEFAULT_FLUTTER_RATE_HZ,
                 flutter_depth: float = DEFAULT_FLUTTER_DEPTH,
                 randomness: float = DEFAULT_RANDOMNESS,
                 depth_units: str = 'cents',
                 pitch_bend_update_rate: float = DEFAULT_PITCH_BEND_UPDATE_RATE
                 ):
        self.wow_rate_hz = wow_rate_hz
        self.wow_depth = wow_depth
        self.flutter_rate_hz = flutter_rate_hz
        self.flutter_depth = flutter_depth
        self.randomness = randomness
        self.depth_units = depth_units
        self.pitch_bend_update_rate = pitch_bend_update_rate
        self.wobble_state = WobbleState()

    def apply(self, event_list: List, options: Dict) -> Union[List[MidiInstruction], List]:
        """
        Applies tape wobble pitch modulation to a list of MIDI events.
        Returns either a list of MidiInstructions (new format) or the original format
        based on the options and compatibility settings.
        """
        generation_type = options.get('generation_type', 'arpeggio')
        use_pitch_bend = options.get('use_pitch_bend', True)  # New option to control behavior
        
        if not use_pitch_bend:
            return self._apply_legacy(event_list, options)
        
        return self._apply_pitch_bend(event_list, options)

    def _apply_pitch_bend(self, event_list: List, options: Dict) -> List[MidiInstruction]:
        print("\n=== Pitch Bend Application Debug ===")
        
        # Setup parameters
        generation_type = options.get('generation_type', 'arpeggio')
        bpm = options.get('bpm', 120)
        total_bars = options.get('bars', 16)
        ticks_per_beat = options.get('ticks_per_beat', DEFAULT_TICKS_PER_BEAT)
        beats_per_bar = 4
        midi_channel = 0

        print(f"Generation Type: {generation_type}")
        print(f"BPM: {bpm}")
        print(f"Total Bars: {total_bars}")
        print(f"Ticks per Beat: {ticks_per_beat}")
        
        # Calculate duration
        max_tick = 0
        if generation_type == 'arpeggio':
            max_tick = total_bars * beats_per_bar * ticks_per_beat
        elif generation_type == 'drone':
            for _, start_tick, duration_tick, _ in event_list:
                max_tick = max(max_tick, start_tick + duration_tick)

        total_duration_seconds = (max_tick / ticks_per_beat) * (60.0 / bpm)
        print(f"Calculated Duration: {total_duration_seconds:.2f} seconds")

        # Generate wobble data
        wobble_options = {
            'duration_sec': total_duration_seconds,
            'wow_rate_hz': self.wow_rate_hz,
            'wow_depth': self.wow_depth,
            'flutter_rate_hz': self.flutter_rate_hz,
            'flutter_depth': self.flutter_depth,
            'randomness': self.randomness,
            'depth_units': self.depth_units
        }
        
        bend_events = tape_wobble(wobble_options)
        print(f"\nGenerated {len(bend_events)} bend events")
        
        if not bend_events:
            print("No bend events generated, falling back to legacy mode")
            return self._apply_legacy(event_list, options)

        midi_instructions: List[MidiInstruction] = []

        # Add RPN messages
        print("\nAdding RPN messages for pitch bend range configuration...")
        midi_instructions.extend([
            ('control_change', 0, 101, 0, midi_channel),   # RPN MSB
            ('control_change', 0, 100, 0, midi_channel),   # RPN LSB
            ('control_change', 0, 6, 2, midi_channel),     # Data Entry MSB (2 semitones)
            ('control_change', 0, 38, 0, midi_channel),    # Data Entry LSB (0)
            ('control_change', 0, 101, 127, midi_channel), # Exit RPN mode
            ('control_change', 0, 100, 127, midi_channel)  # Exit RPN mode
        ])

        # Process note events
        print("\nProcessing note events...")
        note_events = []
        if generation_type == 'arpeggio':
            steps_per_bar = 16
            for step_index, note_midi in enumerate(event_list):
                if note_midi is not None and note_midi > 0:
                    step_ticks = (step_index * ticks_per_beat) // 4
                    duration_ticks = ticks_per_beat // 4
                    note_events.append((note_midi, step_ticks, duration_ticks, 64))
        else:  # drone
            note_events = event_list

        print(f"Found {len(note_events)} note events")

        # Add note events
        note_count = 0
        for note, start_tick, duration_tick, velocity in note_events:
            if note > 0 and duration_tick > 0:
                midi_instructions.append(('note_on', start_tick, note, velocity, midi_channel))
                midi_instructions.append(('note_off', start_tick + duration_tick, note, 0, midi_channel))
                note_count += 1

        print(f"Added {note_count} notes ({note_count * 2} note on/off events)")

        # Process pitch bends
        print("\nProcessing pitch bend events...")
        bend_count = 0
        for time_sec, bend_value in bend_events:
            tick = int((time_sec * bpm * ticks_per_beat) / 60.0)
            # Convert to 0-16383 range
            converted_bend = bend_value + 8192
            converted_bend = max(0, min(16383, converted_bend))
            midi_instructions.append(('pitch_bend', tick, converted_bend, midi_channel))
            bend_count += 1
            
            if bend_count <= 5 or bend_count % 50 == 0:  # Print first 5 and every 50th
                print(f"Bend at {time_sec:.3f}s (tick {tick}): raw={bend_value}, "
                      f"converted={converted_bend}")

        print(f"\nTotal MIDI instructions generated: {len(midi_instructions)}")
        print(f"  - RPN messages: 6")
        print(f"  - Note events: {note_count * 2}")
        print(f"  - Pitch bends: {bend_count}")
        print("=====================================\n")

        # Sort all instructions by tick
        midi_instructions.sort(key=lambda x: (x[1], x[0] == 'note_on'))
        return midi_instructions

    def _apply_legacy(self, event_list: List, options: Dict) -> List:
        """
        Legacy implementation for backward compatibility.
        """
        generation_type = options.get('generation_type', 'arpeggio')
        bpm = options.get('bpm', 120)
        total_bars = options.get('bars', 16)
        
        ticks_per_beat = options.get('ticks_per_beat', 480) # Get from options or default
        beats_per_bar = 4 # Standard

        total_duration_beats = total_bars * beats_per_bar
        total_duration_seconds = (total_duration_beats / bpm) * 60.0

        # Determine a reasonable internal sample rate for the wobble signal
        # e.g., update pitch roughly every 16th note
        # A 16th note duration in seconds: (60 / bpm / 4)
        # If we want ~1 sample per 16th note, sample_rate_hz = bpm * 4 / 60
        # Let's use a fixed rate or one based on density, e.g. 20-50Hz.
        # For simplicity, let's use a fixed internal sample rate for wobble generation.
        # If we make it too high, wobble_signal will be large.
        # If too low, it won't capture flutter well for short notes.
        # Let's aim for roughly 25-50 updates per second.
        internal_wobble_sample_rate_hz = 30 


        wobble_options = {
            'duration_sec': total_duration_seconds,
            'sample_rate_hz': internal_wobble_sample_rate_hz,
            'wow_rate_hz': self.wow_rate_hz,
            'wow_depth': self.wow_depth,
            'flutter_rate_hz': self.flutter_rate_hz,
            'flutter_depth': self.flutter_depth,
            'randomness': self.randomness,
            'output_units': 'semitones', # We want semitone offsets for direct pitch modification
            'depth_units': self.depth_units
        }
        
        pitch_wobble_signal_semitones = tape_wobble(wobble_options)
        
        num_wobble_samples = len(pitch_wobble_signal_semitones)
        if num_wobble_samples == 0:
            return event_list # No wobble signal generated

        modified_event_list = []

        if generation_type == 'arpeggio':
            # Arpeggio: event_list is List[Optional[int]], representing 16th notes
            steps_per_bar = 16
            total_steps = total_bars * steps_per_bar
            
            for step_index, note_midi in enumerate(event_list):
                if note_midi is not None:
                    # Calculate current time in seconds for this step
                    current_beat = step_index / (steps_per_bar / beats_per_bar)
                    time_sec = (current_beat / bpm) * 60.0
                    
                    # Get corresponding sample from wobble signal
                    wobble_sample_index = int(time_sec * internal_wobble_sample_rate_hz)
                    if 0 <= wobble_sample_index < num_wobble_samples:
                        pitch_offset_semitones = pitch_wobble_signal_semitones[wobble_sample_index]
                        new_note_midi = round(note_midi + pitch_offset_semitones)
                        new_note_midi = max(0, min(127, new_note_midi)) # Clamp
                        modified_event_list.append(new_note_midi)
                    else:
                        modified_event_list.append(note_midi) # Out of bounds, use original
                else:
                    modified_event_list.append(None) # Rest
            return modified_event_list

        elif generation_type == 'drone':
            # Drone: event_list is List[MidiEvent] = List[Tuple[note, start_tick, duration_tick, velocity]]
            for event_tuple in event_list:
                original_note, start_tick, duration_tick, velocity = event_tuple
                
                # Calculate start time in seconds for this event
                current_beat = start_tick / ticks_per_beat
                time_sec = (current_beat / bpm) * 60.0

                wobble_sample_index = int(time_sec * internal_wobble_sample_rate_hz)
                if 0 <= wobble_sample_index < num_wobble_samples:
                    pitch_offset_semitones = pitch_wobble_signal_semitones[wobble_sample_index]
                    new_note_midi = round(original_note + pitch_offset_semitones)
                    new_note_midi = max(0, min(127, new_note_midi)) # Clamp
                    modified_event_list.append(
                        (new_note_midi, start_tick, duration_tick, velocity)
                    )
                else:
                    modified_event_list.append(event_tuple) # Out of bounds, use original
            return modified_event_list
            
        else: # Unknown type
            return event_list


# Remove old HumanizeVelocityEffect if it's not used or if we are simplifying
# For now, let's keep it as it's a different type of effect.
class HumanizeVelocityEffect(MidiEffect):
    def __init__(self, humanization_range: int = 10):
        self.humanization_range = humanization_range

    def apply(self, event_list: List, options: Dict) -> List:
        # This effect is primarily designed for drone MidiEvent tuples
        # but could be adapted if arpeggios also used structured events with velocity.
        generation_type = options.get('generation_type', 'arpeggio')
        if generation_type != 'drone':
            # print("[HumanizeVelocityEffect] Skipping, not a drone.")
            return event_list

        modified_event_list = []
        for event_tuple in event_list:
            if isinstance(event_tuple, tuple) and len(event_tuple) == 4:
                note, start_tick, duration_tick, velocity = event_tuple
                adj_velocity = velocity + random.randint(-self.humanization_range // 2, self.humanization_range // 2)
                adj_velocity = max(1, min(127, adj_velocity)) # MIDI velocity 1-127
                modified_event_list.append((note, start_tick, duration_tick, adj_velocity))
            else:
                # Should not happen for drones, but good to be safe
                modified_event_list.append(event_tuple)
        return modified_event_list
