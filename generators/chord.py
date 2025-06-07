"""
Chord progression generator implementation.
"""

from typing import List, Dict, Any, Optional, Tuple
import random
from ..core.types import MidiEvent, DEFAULT_TICKS_PER_BEAT
from ..core.music import get_scale, note_str_to_midi
from .base import BaseGenerator

class ChordGenerator(BaseGenerator):
    """Generates chord progressions with various voicings and rhythmic patterns."""
    
    def __init__(self, bpm: int = 120):
        """Initialize the chord generator.
        
        Args:
            bpm: Beats per minute
        """
        super().__init__(bpm)
        # Default configuration values
        self._min_octave = 3
        self._max_octave = 5
        self._base_velocity = 80
        self._voicing_complexity = 0.5  # 0.0 to 1.0
        self._rhythmic_variation = 0.3  # 0.0 to 1.0
        self._voice_leading_strength = 0.7  # 0.0 to 1.0
        self._extension_probability = 0.3  # Probability of adding 7ths, 9ths
        
        # Common chord progressions in scale degrees (1-based)
        self._common_progressions = [
            [1, 4, 5, 1],  # I-IV-V-I
            [1, 6, 4, 5],  # I-vi-IV-V
            [2, 5, 1],     # ii-V-I
            [1, 4, 6, 5],  # I-IV-vi-V
            [6, 2, 5, 1],  # vi-ii-V-I
        ]
    
    def validate_params(self, **kwargs) -> bool:
        """Validate generation parameters.
        
        Args:
            **kwargs: Generation parameters including:
                - root: Root note (MIDI number or note string e.g., 'C4')
                - mode: Scale mode ('major', 'minor', etc.)
                - bars: Number of bars to generate
                - progression: Optional list of scale degrees (1-based)
                - min_octave: Minimum octave
                - max_octave: Maximum octave
                - base_velocity: Base note velocity
                - voicing_complexity: Complexity of chord voicings (0-1)
                - rhythmic_variation: Amount of rhythmic variation (0-1)
                - voice_leading_strength: Strength of voice leading (0-1)
                - extension_probability: Probability of chord extensions
        
        Returns:
            True if parameters are valid
        """
        # Required parameters
        root = kwargs.get('root')
        mode = kwargs.get('mode')
        bars = kwargs.get('bars')
        
        if None in [root, mode, bars]:
            return False
        
        # Convert string note to MIDI if needed
        if isinstance(root, str):
            root = note_str_to_midi(root)
        
        if not isinstance(root, int) or not 0 <= root <= 127:
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
        
        # Validate probability parameters
        for param in ['voicing_complexity', 'rhythmic_variation', 
                     'voice_leading_strength', 'extension_probability']:
            value = kwargs.get(param, getattr(self, f'_{param}'))
            if not 0 <= value <= 1:
                return False
        
        # Validate progression if provided
        progression = kwargs.get('progression', None)
        if progression is not None:
            if not isinstance(progression, list):
                return False
            if not all(isinstance(deg, int) and 1 <= deg <= 7 for deg in progression):
                return False
        
        return True
    
    def generate(self, **kwargs) -> List[MidiEvent]:
        """Generate a chord progression.
        
        Args:
            **kwargs: See validate_params for parameters
        
        Returns:
            List of MIDI events
        """
        if not self.validate_params(**kwargs):
            return []
        
        # Extract parameters with defaults
        root = kwargs.get('root')
        if isinstance(root, str):
            root = note_str_to_midi(root)
            
        mode = kwargs['mode']
        bars = kwargs['bars']
        min_octave = kwargs.get('min_octave', self._min_octave)
        max_octave = kwargs.get('max_octave', self._max_octave)
        base_velocity = kwargs.get('base_velocity', self._base_velocity)
        voicing_complexity = kwargs.get('voicing_complexity', self._voicing_complexity)
        rhythmic_variation = kwargs.get('rhythmic_variation', self._rhythmic_variation)
        voice_leading_strength = kwargs.get('voice_leading_strength', self._voice_leading_strength)
        extension_probability = kwargs.get('extension_probability', self._extension_probability)
        
        # Get or generate progression
        progression = kwargs.get('progression')
        if progression is None:
            progression = self._select_progression(bars)
        
        # Generate the chord sequence
        chord_sequence = self._generate_chord_sequence(
            root=root,
            mode=mode,
            progression=progression,
            min_octave=min_octave,
            max_octave=max_octave,
            voicing_complexity=voicing_complexity,
            extension_probability=extension_probability
        )
        
        # Apply voice leading
        if voice_leading_strength > 0:
            chord_sequence = self._apply_voice_leading(
                chord_sequence,
                voice_leading_strength
            )
        
        # Generate events with rhythm
        events = self._generate_events(
            chord_sequence=chord_sequence,
            bars=bars,
            base_velocity=base_velocity,
            rhythmic_variation=rhythmic_variation
        )
        
        self._sequence = events
        return self.sequence
    
    def _select_progression(self, bars: int) -> List[int]:
        """Select an appropriate chord progression."""
        progression = random.choice(self._common_progressions)
        
        # Extend progression if needed
        while len(progression) < bars:
            progression.extend(progression)
        
        return progression[:bars]
    
    def _generate_chord_sequence(
        self,
        root: int,
        mode: str,
        progression: List[int],
        min_octave: int,
        max_octave: int,
        voicing_complexity: float,
        extension_probability: float
    ) -> List[List[int]]:
        """Generate a sequence of chord voicings."""
        # Get scale degrees
        scale = get_scale(root, mode)
        if not scale:
            return []
        
        chord_sequence = []
        for degree in progression:
            # Get basic triad
            chord_root = scale[(degree - 1) % len(scale)]
            chord_third = scale[(degree + 1) % len(scale)]
            chord_fifth = scale[(degree + 3) % len(scale)]
            
            # Basic triad in root position
            chord = [
                chord_root + (min_octave * 12),
                chord_third + (min_octave * 12),
                chord_fifth + (min_octave * 12)
            ]
            
            # Add extensions based on probability
            if random.random() < extension_probability:
                # Add seventh
                chord_seventh = scale[(degree + 5) % len(scale)]
                chord.append(chord_seventh + (min_octave * 12))
                
                # Maybe add ninth
                if random.random() < extension_probability * 0.5:
                    chord_ninth = scale[(degree + 7) % len(scale)]
                    chord.append(chord_ninth + ((min_octave + 1) * 12))
            
            # Apply voicing variations based on complexity
            if random.random() < voicing_complexity:
                # Randomly shift some notes up an octave
                for i in range(1, len(chord)):
                    if random.random() < voicing_complexity:
                        octave_shift = random.randint(1, max_octave - min_octave)
                        chord[i] += octave_shift * 12
            
            # Ensure all notes are within range and unique
            chord = sorted(list(set([
                max(0, min(127, note)) for note in chord
            ])))
            
            chord_sequence.append(chord)
        
        return chord_sequence
    
    def _apply_voice_leading(
        self,
        chord_sequence: List[List[int]],
        strength: float
    ) -> List[List[int]]:
        """Apply voice leading to minimize movement between chords."""
        if len(chord_sequence) < 2:
            return chord_sequence
        
        result = [chord_sequence[0]]
        
        for i in range(1, len(chord_sequence)):
            prev_chord = result[-1]
            current_chord = list(chord_sequence[i])
            
            # Try to minimize movement for each voice
            for j in range(min(len(prev_chord), len(current_chord))):
                # Find closest pitch class in current chord to previous note
                prev_note = prev_chord[j]
                current_note = current_chord[j]
                
                # Only adjust if the movement is large and random check passes
                if abs(current_note - prev_note) > 7 and random.random() < strength:
                    # Try octave adjustments to minimize movement
                    while current_note + 12 < 127 and abs(current_note + 12 - prev_note) < abs(current_note - prev_note):
                        current_note += 12
                    while current_note - 12 > 0 and abs(current_note - 12 - prev_note) < abs(current_note - prev_note):
                        current_note -= 12
                    
                    current_chord[j] = current_note
            
            result.append(current_chord)
        
        return result
    
    def _generate_events(
        self,
        chord_sequence: List[List[int]],
        bars: int,
        base_velocity: int,
        rhythmic_variation: float
    ) -> List[MidiEvent]:
        """Generate MIDI events with rhythmic patterns."""
        events = []
        ticks_per_bar = DEFAULT_TICKS_PER_BEAT * 4
        
        for bar, chord in enumerate(chord_sequence):
            # Generate rhythmic pattern for this bar
            if random.random() < rhythmic_variation:
                # Complex rhythm
                divisions = random.choice([2, 3, 4])
                ticks_per_div = ticks_per_bar // divisions
                
                for div in range(divisions):
                    if random.random() < 0.8:  # 80% chance of playing on this division
                        start_tick = bar * ticks_per_bar + div * ticks_per_div
                        duration = int(ticks_per_div * random.uniform(0.5, 1.0))
                        
                        # Add note events
                        for note in chord:
                            # Slight velocity variation
                            velocity = min(127, max(1, int(
                                base_velocity * random.uniform(0.9, 1.1)
                            )))
                            
                            events.extend(self._create_note_events(
                                note=note,
                                start_tick=start_tick,
                                duration_ticks=duration,
                                velocity=velocity
                            ))
            else:
                # Simple whole bar
                start_tick = bar * ticks_per_bar
                duration = ticks_per_bar
                
                # Add note events
                for note in chord:
                    events.extend(self._create_note_events(
                        note=note,
                        start_tick=start_tick,
                        duration_ticks=duration,
                        velocity=base_velocity
                    ))
        
        return sorted(events, key=lambda x: x['time'])
    
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
