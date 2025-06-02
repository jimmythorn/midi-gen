import random
import math
from typing import List, Optional, Dict, Union
from .effects_base import MidiEffect, NoteContext

# Assuming MidiEvent is defined elsewhere, e.g., in midi.py or a common types file
# For now, let's expect it as Tuple[int, int, int, int] if used for drones
MidiEvent = tuple[int, int, int, int]

# --- Tape Wobble Generation Function ---
def tape_wobble(options: dict) -> list:
    """
    Generates a simulated "tape wobble" modulation signal over time.
    """
    duration = options.get('duration_sec', 5.0)
    sample_rate_hz = options.get('sample_rate_hz', 50) # Internal sample rate for the wobble signal
    wow_rate = options.get('wow_rate_hz', 0.5)
    wow_depth = options.get('wow_depth', 10.0) # In depth_units
    flutter_rate = options.get('flutter_rate_hz', 7.0)
    flutter_depth = options.get('flutter_depth', 3.0) # In depth_units
    randomness = options.get('randomness', 0.1)
    output_units = options.get('output_units', 'semitones') # 'cents', 'semitones', 'pitchBend'
    depth_units = options.get('depth_units', 'cents') # 'cents', 'semitones'

    if not isinstance(sample_rate_hz, int) or sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be a positive integer.")
    if duration <= 0:
        raise ValueError("duration_sec must be positive.")

    num_samples = int(duration * sample_rate_hz)
    wobble_data = [0.0] * num_samples # Initialize with zeros

    clamped_randomness = max(0.0, min(1.0, randomness))
    wow_initial_phase_offset = random.random() * 2 * math.pi * clamped_randomness
    flutter_initial_phase_offset = random.random() * 2 * math.pi * clamped_randomness
    phase_noise_max_amplitude = 0.05 * clamped_randomness # Increased slightly from 0.01

    for i in range(num_samples):
        t = i / sample_rate_hz

        wow_phase_noise = (random.random() - 0.5) * 2 * phase_noise_max_amplitude
        flutter_phase_noise = (random.random() - 0.5) * 2 * phase_noise_max_amplitude

        wow = wow_depth * math.sin(
            2 * math.pi * wow_rate * t + wow_initial_phase_offset + wow_phase_noise
        )
        flutter = flutter_depth * math.sin(
            2 * math.pi * flutter_rate * t + flutter_initial_phase_offset + flutter_phase_noise
        )

        pitch_mod_in_depth_units = wow + flutter

        # Convert to semitones first, as this is our primary internal unit for direct pitch change
        pitch_mod_semitones = 0.0
        if depth_units == 'cents':
            pitch_mod_semitones = pitch_mod_in_depth_units / 100.0
        elif depth_units == 'semitones':
            pitch_mod_semitones = pitch_mod_in_depth_units
        else:
            raise ValueError(f"Unsupported depth_units: {depth_units}")

        if output_units == 'pitchBend':
            # Assumes ±2 semitone range for MIDI pitch bend = ±8192
            bend_value = (pitch_mod_semitones / 2.0) * 8192.0
            wobble_data[i] = round(max(-8192.0, min(8191.0, bend_value)))
        elif output_units == 'semitones':
            wobble_data[i] = pitch_mod_semitones
        elif output_units == 'cents':
            wobble_data[i] = pitch_mod_semitones * 100.0
        else:
            raise ValueError(f"Unsupported output_units: {output_units}")
            
    return wobble_data


# --- Tape Wobble Effect Class (replaces ShimmerEffect) ---
class TapeWobbleEffect(MidiEffect):
    def __init__(self, 
                 wow_rate_hz: float = 0.5, 
                 wow_depth: float = 10.0, # Default in cents
                 flutter_rate_hz: float = 7.0, 
                 flutter_depth: float = 3.0, # Default in cents
                 randomness: float = 0.1,
                 depth_units: str = 'cents', # 'cents' or 'semitones' for depth input
                 # internal_sample_rate_hz: int = 25 # How often to sample the wobble for note changes
                 ):
        self.wow_rate_hz = wow_rate_hz
        self.wow_depth = wow_depth
        self.flutter_rate_hz = flutter_rate_hz
        self.flutter_depth = flutter_depth
        self.randomness = randomness
        self.depth_units = depth_units
        # self.internal_sample_rate_hz = internal_sample_rate_hz # Decided to calculate this in apply

    def apply(self, event_list: List, options: Dict) -> List:
        """
        Applies tape wobble pitch modulation to a list of MIDI events.
        The modulation is applied by quantizing it to the nearest semitone and
        adjusting the MIDI note numbers directly.
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
