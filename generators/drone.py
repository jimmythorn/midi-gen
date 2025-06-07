"""
Drone pattern generator implementation.
"""

from typing import List, Dict, Any, Optional, Tuple
import random
from ..core.types import MidiEvent, DEFAULT_TICKS_PER_BEAT
from ..core.music import get_scale
from .base import BaseGenerator

class DroneGenerator(BaseGenerator):
    """Generates drone patterns with various musical variations."""
    
    def __init__(self, bpm: int = 120):
        """Initialize the drone generator.
        
        Args:
            bpm: Beats per minute
        """
        super().__init__(bpm)
        # Default configuration values
        self._min_octave = 3
        self._max_octave = 5
        self._base_velocity = 70
        self._variation_interval_bars = 1
        self._min_notes_held = 2
        self._octave_doubling_chance = 0.25
        self._allow_octave_shifts = True
        self._octave_shift_chance = 0.1
        self._enable_walkdowns = True
        self._walkdown_num_steps = 2
        self._walkdown_step_ticks = DEFAULT_TICKS_PER_BEAT // 2  # 8th notes
        self._min_target_sustain_ticks = DEFAULT_TICKS_PER_BEAT // 8  # 32nd notes
    
    def validate_params(self, **kwargs) -> bool:
        """Validate generation parameters.
        
        Args:
            **kwargs: Generation parameters including:
                - mode: Scale mode ('major', 'minor', etc.)
                - bars: Number of bars to generate
                - root_notes: List of root notes for progression
                - min_octave: Minimum octave
                - max_octave: Maximum octave
                - base_velocity: Base note velocity
                - variation_interval_bars: Bars between variations
                - min_notes_held: Minimum notes held at once
                - octave_doubling_chance: Chance of octave doubling
                - allow_octave_shifts: Whether to allow octave shifts
                - octave_shift_chance: Chance of octave shift
                - enable_walkdowns: Whether to enable melodic walkdowns
                - walkdown_num_steps: Number of walkdown steps
                - walkdown_step_ticks: Ticks per walkdown step
        
        Returns:
            True if parameters are valid
        """
        # Required parameters
        mode = kwargs.get('mode')
        bars = kwargs.get('bars')
        
        if None in [mode, bars]:
            return False
        
        if not isinstance(mode, str):
            return False
        if not isinstance(bars, int) or bars <= 0:
            return False
        
        # Optional parameters
        min_octave = kwargs.get('min_octave', self._min_octave)
        max_octave = kwargs.get('max_octave', self._max_octave)
        if min_octave > max_octave:
            return False
        
        variation_interval = kwargs.get('variation_interval_bars', self._variation_interval_bars)
        if variation_interval <= 0:
            return False
        
        min_notes = kwargs.get('min_notes_held', self._min_notes_held)
        if min_notes <= 0:
            return False
        
        doubling_chance = kwargs.get('octave_doubling_chance', self._octave_doubling_chance)
        if not 0 <= doubling_chance <= 1:
            return False
        
        shift_chance = kwargs.get('octave_shift_chance', self._octave_shift_chance)
        if not 0 <= shift_chance <= 1:
            return False
        
        return True
    
    def generate(self, **kwargs) -> List[MidiEvent]:
        """Generate a drone sequence.
        
        Args:
            **kwargs: See validate_params for parameters
        
        Returns:
            List of MIDI events
        """
        if not self.validate_params(**kwargs):
            return []
        
        # Extract parameters with defaults
        mode = kwargs['mode']
        total_bars = kwargs['bars']
        root_notes = kwargs.get('root_notes', [48])  # Default to C3
        min_octave = kwargs.get('min_octave', self._min_octave)
        max_octave = kwargs.get('max_octave', self._max_octave)
        base_velocity = kwargs.get('base_velocity', self._base_velocity)
        variation_interval_bars = kwargs.get('variation_interval_bars', self._variation_interval_bars)
        min_notes_held = kwargs.get('min_notes_held', self._min_notes_held)
        octave_doubling_chance = kwargs.get('octave_doubling_chance', self._octave_doubling_chance)
        allow_octave_shifts = kwargs.get('allow_octave_shifts', self._allow_octave_shifts)
        octave_shift_chance = kwargs.get('octave_shift_chance', self._octave_shift_chance)
        enable_walkdowns = kwargs.get('enable_walkdowns', self._enable_walkdowns)
        walkdown_num_steps = kwargs.get('walkdown_num_steps', self._walkdown_num_steps)
        walkdown_step_ticks = kwargs.get('walkdown_step_ticks', self._walkdown_step_ticks)
        
        ticks_per_bar = DEFAULT_TICKS_PER_BEAT * 4
        variation_interval_ticks = variation_interval_bars * ticks_per_bar
        
        events = []
        global_current_tick = 0
        
        # Handle empty root notes case
        if not root_notes:
            return self._generate_fallback_drone(min_octave, total_bars * ticks_per_bar, base_velocity)
        
        # Calculate bars per segment
        bars_per_segment = total_bars // len(root_notes)
        
        # Generate drone for each root note
        for idx, root_note in enumerate(root_notes):
            segment_events = self._generate_segment(
                root_note=root_note,
                mode=mode,
                segment_bars=bars_per_segment if idx < len(root_notes) - 1 else total_bars - (bars_per_segment * idx),
                start_tick=global_current_tick,
                min_octave=min_octave,
                max_octave=max_octave,
                base_velocity=base_velocity,
                variation_interval_ticks=variation_interval_ticks,
                min_notes_held=min_notes_held,
                octave_doubling_chance=octave_doubling_chance,
                allow_octave_shifts=allow_octave_shifts,
                octave_shift_chance=octave_shift_chance,
                enable_walkdowns=enable_walkdowns,
                walkdown_num_steps=walkdown_num_steps,
                walkdown_step_ticks=walkdown_step_ticks
            )
            events.extend(segment_events)
            global_current_tick += bars_per_segment * ticks_per_bar
        
        self._sequence = events
        return self.sequence
    
    def _generate_fallback_drone(self, min_octave: int, duration_ticks: int, velocity: int) -> List[MidiEvent]:
        """Generate a fallback drone when no root notes are provided."""
        c3_midi = 48
        chord_notes = get_scale(c3_midi, 'major', use_chord_tones=True)
        chord_notes_abs = [pc + (min_octave * 12) for pc in chord_notes]
        chord_notes_abs = [max(0, min(127, note)) for note in chord_notes_abs]
        
        events = []
        for note in chord_notes_abs:
            events.append({
                'type': 'note_on',
                'note': note,
                'velocity': velocity,
                'time': 0,
                'channel': 0
            })
            events.append({
                'type': 'note_off',
                'note': note,
                'velocity': 0,
                'time': duration_ticks,
                'channel': 0
            })
        return events
    
    def _generate_segment(
        self,
        root_note: int,
        mode: str,
        segment_bars: int,
        start_tick: int,
        min_octave: int,
        max_octave: int,
        base_velocity: int,
        variation_interval_ticks: int,
        min_notes_held: int,
        octave_doubling_chance: float,
        allow_octave_shifts: bool,
        octave_shift_chance: float,
        enable_walkdowns: bool,
        walkdown_num_steps: int,
        walkdown_step_ticks: int
    ) -> List[MidiEvent]:
        """Generate a segment of the drone sequence."""
        if segment_bars <= 0:
            return []
        
        segment_duration_ticks = segment_bars * DEFAULT_TICKS_PER_BEAT * 4
        events = []
        
        # Get chord tones and full scale
        chord_tones = get_scale(root_note, mode, use_chord_tones=True)
        base_chord_notes = sorted(list(set([
            max(0, min(127, pc + (min_octave * 12))) for pc in chord_tones
        ])))
        
        if not base_chord_notes:
            base_chord_notes = [max(0, min(127, root_note))]
        
        # Get full scale for walkdowns
        full_scale = get_scale(root_note, mode, use_chord_tones=False)
        diatonic_notes = self._generate_diatonic_range(full_scale, min_octave - 1, max_octave + 2)
        
        # Generate variations
        current_tick = 0
        pattern_counter = 0
        
        while current_tick < segment_duration_ticks:
            interval_duration = min(variation_interval_ticks, segment_duration_ticks - current_tick)
            if interval_duration <= 0:
                break
            
            # Generate base pattern
            base_notes = self._generate_base_pattern(
                base_chord_notes,
                min_notes_held,
                pattern_counter
            )
            
            # Apply variations and generate events
            interval_events = self._generate_interval_events(
                base_notes=base_notes,
                start_tick=start_tick + current_tick,
                duration_ticks=interval_duration,
                base_velocity=base_velocity,
                allow_octave_shifts=allow_octave_shifts,
                octave_shift_chance=octave_shift_chance,
                min_octave=min_octave,
                max_octave=max_octave,
                octave_doubling_chance=octave_doubling_chance,
                enable_walkdowns=enable_walkdowns,
                walkdown_num_steps=walkdown_num_steps,
                walkdown_step_ticks=walkdown_step_ticks,
                diatonic_notes=diatonic_notes
            )
            events.extend(interval_events)
            
            current_tick += interval_duration
            pattern_counter += 1
        
        return events
    
    def _generate_diatonic_range(
        self,
        scale: List[int],
        min_octave: int,
        max_octave: int
    ) -> List[int]:
        """Generate diatonic notes across the specified octave range."""
        notes = []
        for pc in scale:
            for oct in range(min_octave, max_octave + 1):
                note = pc + (oct * 12)
                if 0 <= note <= 127:
                    notes.append(note)
        return sorted(list(set(notes)))
    
    def _generate_base_pattern(
        self,
        chord_notes: List[int],
        min_notes: int,
        pattern_counter: int
    ) -> List[int]:
        """Generate the base pattern for a variation interval."""
        if len(chord_notes) < 3 or len(chord_notes) < min_notes:
            return list(chord_notes)
        
        pattern = [chord_notes[0]]  # Always include root
        pattern_idx = pattern_counter % 4
        
        if pattern_idx in [0, 2]:
            pattern.extend(chord_notes[1:])
        elif pattern_idx == 1 and len(chord_notes) > 1:
            pattern.append(chord_notes[-1])  # Add fifth
        elif pattern_idx == 3 and len(chord_notes) > 1:
            pattern.append(chord_notes[1])  # Add third
        
        if len(pattern) < min_notes and len(chord_notes) >= min_notes:
            needed = min_notes - len(pattern)
            potential_adds = [n for n in chord_notes if n not in pattern]
            pattern.extend(potential_adds[:needed])
        
        return sorted(list(set(pattern)))
    
    def _generate_interval_events(
        self,
        base_notes: List[int],
        start_tick: int,
        duration_ticks: int,
        base_velocity: int,
        allow_octave_shifts: bool,
        octave_shift_chance: float,
        min_octave: int,
        max_octave: int,
        octave_doubling_chance: float,
        enable_walkdowns: bool,
        walkdown_num_steps: int,
        walkdown_step_ticks: int,
        diatonic_notes: List[int]
    ) -> List[MidiEvent]:
        """Generate events for a variation interval."""
        events = []
        notes_to_play = list(base_notes)
        
        # Apply octave shift
        if allow_octave_shifts:
            notes_to_play = self._apply_octave_shift(
                notes_to_play,
                octave_shift_chance,
                min_octave,
                max_octave
            )
        
        # Generate main note events
        for note in notes_to_play:
            events.extend(self._create_note_events(
                note=note,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                velocity=base_velocity
            ))
        
        # Apply octave doubling with walkdowns
        if random.random() < octave_doubling_chance:
            doubled_events = self._generate_doubled_note_events(
                source_notes=notes_to_play,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                base_velocity=base_velocity,
                min_octave=min_octave,
                max_octave=max_octave,
                enable_walkdowns=enable_walkdowns,
                walkdown_num_steps=walkdown_num_steps,
                walkdown_step_ticks=walkdown_step_ticks,
                diatonic_notes=diatonic_notes
            )
            events.extend(doubled_events)
        
        return events
    
    def _apply_octave_shift(
        self,
        notes: List[int],
        shift_chance: float,
        min_octave: int,
        max_octave: int
    ) -> List[int]:
        """Apply random octave shift to one note."""
        indices = list(range(len(notes)))
        random.shuffle(indices)
        
        for i in indices:
            if random.random() < shift_chance:
                direction = random.choice([-12, 12])
                shifted = notes[i] + direction
                if min_octave * 12 <= shifted < (max_octave + 1) * 12 and 0 <= shifted <= 127:
                    notes[i] = shifted
                    break
        
        return sorted(notes)
    
    def _generate_doubled_note_events(
        self,
        source_notes: List[int],
        start_tick: int,
        duration_ticks: int,
        base_velocity: int,
        min_octave: int,
        max_octave: int,
        enable_walkdowns: bool,
        walkdown_num_steps: int,
        walkdown_step_ticks: int,
        diatonic_notes: List[int]
    ) -> List[MidiEvent]:
        """Generate events for octave doubled notes with optional walkdowns."""
        events = []
        source = random.choice(source_notes)
        direction = random.choice([-12, 12])
        target = source + direction
        
        if not (min_octave * 12 <= target < (max_octave + 2) * 12 and 0 <= target <= 127):
            return events
        
        if enable_walkdowns and walkdown_num_steps > 0:
            walkdown_events = self._generate_walkdown_events(
                source=source,
                target=target,
                start_tick=start_tick,
                total_duration=duration_ticks,
                num_steps=walkdown_num_steps,
                step_ticks=walkdown_step_ticks,
                velocity=base_velocity - 15,
                diatonic_notes=diatonic_notes
            )
            events.extend(walkdown_events)
        else:
            events.extend(self._create_note_events(
                note=target,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                velocity=base_velocity
            ))
        
        return events
    
    def _generate_walkdown_events(
        self,
        source: int,
        target: int,
        start_tick: int,
        total_duration: int,
        num_steps: int,
        step_ticks: int,
        velocity: int,
        diatonic_notes: List[int]
    ) -> List[MidiEvent]:
        """Generate walkdown events from source to target note."""
        events = []
        walk_notes = []
        
        # Determine direction and find appropriate scale steps
        ascending = target > source
        relevant_notes = [n for n in diatonic_notes if n > target] if ascending else [n for n in diatonic_notes if n < target]
        relevant_notes = sorted(relevant_notes, reverse=not ascending)
        
        # Generate walkdown notes
        for step in range(num_steps):
            if step < len(relevant_notes):
                walk_notes.append(relevant_notes[step])
        
        # Generate events for walkdown notes
        current_tick = start_tick
        for note in walk_notes:
            events.extend(self._create_note_events(
                note=note,
                start_tick=current_tick,
                duration_ticks=step_ticks,
                velocity=velocity
            ))
            current_tick += step_ticks
        
        # Add target note
        remaining_duration = total_duration - (len(walk_notes) * step_ticks)
        if remaining_duration > self._min_target_sustain_ticks:
            events.extend(self._create_note_events(
                note=target,
                start_tick=current_tick,
                duration_ticks=remaining_duration,
                velocity=velocity
            ))
        
        return events
    
    def _create_note_events(
        self,
        note: int,
        start_tick: int,
        duration_ticks: int,
        velocity: int
    ) -> List[MidiEvent]:
        """Create note-on and note-off events for a single note."""
        return [
            {
                'type': 'note_on',
                'note': note,
                'velocity': velocity,
                'time': start_tick,
                'channel': 0
            },
            {
                'type': 'note_off',
                'note': note,
                'velocity': 0,
                'time': start_tick + duration_ticks,
                'channel': 0
            }
        ]
