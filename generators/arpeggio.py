"""
Arpeggio pattern generator implementation.
"""

from typing import List, Dict, Any, Optional
import random
from ..core.types import MidiEvent, DEFAULT_TICKS_PER_BEAT
from ..core.music import get_scale
from .base import BaseGenerator

class ArpeggioGenerator(BaseGenerator):
    """Generates arpeggio patterns with various musical variations."""
    
    def __init__(self, bpm: int = 120):
        """Initialize the arpeggio generator.
        
        Args:
            bpm: Beats per minute
        """
        super().__init__(bpm)
        # Default configuration values
        self._min_octave = 4
        self._max_octave = 6
        self._evolution_rate = 0.1
        self._repetition_factor = 5
    
    def validate_params(self, **kwargs) -> bool:
        """Validate generation parameters.
        
        Args:
            **kwargs: Generation parameters including:
                - root: Root note MIDI number or list of root notes
                - mode: Scale mode ('major', 'minor', etc.)
                - length: Number of steps in pattern (4, 8, or 16)
                - bars: Number of bars to generate
                - arp_mode: Arpeggio mode ('up', 'down', 'up_down', 'random')
                - min_octave: Minimum octave
                - max_octave: Maximum octave
                - range_octaves: Number of octaves to span
                - evolution_rate: Rate of pattern evolution (0-1)
                - repetition_factor: How often to repeat notes
                - use_chord_tones: Whether to use only chord tones
        
        Returns:
            True if parameters are valid
        """
        # Required parameters
        root = kwargs.get('root')
        mode = kwargs.get('mode')
        length = kwargs.get('length')
        bars = kwargs.get('bars')
        arp_mode = kwargs.get('arp_mode')
        
        if None in [root, mode, length, bars, arp_mode]:
            return False
        
        # Validate numeric ranges
        if isinstance(root, list):
            if not all(0 <= r <= 127 for r in root):
                return False
        else:
            if not 0 <= root <= 127:
                return False
        if length not in [4, 8, 16]:  # Only allow valid step counts
            return False
        if not 1 <= bars <= 128:
            return False
        if arp_mode not in ['up', 'down', 'up_down', 'random']:
            return False
        
        # Optional parameters
        min_octave = kwargs.get('min_octave', self._min_octave)
        max_octave = kwargs.get('max_octave', self._max_octave)
        range_octaves = kwargs.get('range_octaves', 2)
        evolution_rate = kwargs.get('evolution_rate', self._evolution_rate)
        repetition_factor = kwargs.get('repetition_factor', self._repetition_factor)
        
        if not min_octave <= max_octave:
            return False
        if not 0 <= evolution_rate <= 1:
            return False
        if not 0 <= repetition_factor <= 10:
            return False
        
        return True
    
    def generate(self, **kwargs) -> List[MidiEvent]:
        """Generate an arpeggio pattern.
        
        Args:
            **kwargs: See validate_params for parameters
        
        Returns:
            List of MIDI events
        """
        # Get parameters with defaults
        root = kwargs['root']
        mode = kwargs['mode']
        arp_steps = kwargs['length']  # 4, 8, or 16 steps per pattern
        total_bars = kwargs['bars']
        arp_mode = kwargs['arp_mode']
        min_octave = kwargs.get('min_octave', self._min_octave)
        range_octaves = kwargs.get('range_octaves', 2)
        evolution_rate = kwargs.get('evolution_rate', self._evolution_rate)
        repetition_factor = kwargs.get('repetition_factor', self._repetition_factor)
        use_chord_tones = kwargs.get('use_chord_tones', True)

        # Each bar has 16 16th notes
        steps_per_bar = 16
        ticks_per_beat = DEFAULT_TICKS_PER_BEAT  # Standard MIDI ticks per quarter note
        ticks_per_16th = ticks_per_beat // 4

        # Calculate note length based on number of steps
        # If using 16 steps: each note is a 16th note
        # If using 8 or 4 steps: notes are longer (8th or quarter notes)
        if arp_steps == 16:
            steps_per_note = 1  # 16th notes
            repeats_per_bar = steps_per_bar // arp_steps
        else:
            steps_per_note = steps_per_bar // arp_steps  # 2 for 8 steps, 4 for 4 steps
            repeats_per_bar = 1

        # Prepare full pattern
        full_pattern = []

        # Handle root notes distribution
        if isinstance(root, list):
            root_notes = root
        else:
            root_notes = [root]

        # Calculate bars per root note segment
        bars_per_segment = total_bars // len(root_notes) if len(root_notes) > 0 else total_bars

        # Generate pattern for each root note segment
        for idx, current_root in enumerate(root_notes):
            # Calculate number of bars for this segment
            num_bars_for_segment = bars_per_segment
            if idx == len(root_notes) - 1:
                # Handle any remaining bars in the last segment
                num_bars_for_segment = total_bars - (bars_per_segment * idx)
            if num_bars_for_segment <= 0:
                continue

            # Get the base pitch classes for this root note
            pitch_classes = get_scale(current_root, mode, use_chord_tones=use_chord_tones)
            if not pitch_classes:
                pitch_classes = [current_root % 12]

            # Build source notes across octaves
            arpeggio_source_notes = []
            for octave in range(min_octave, min_octave + range_octaves + 1):
                arpeggio_source_notes.extend([note + (octave * 12) for note in pitch_classes])

            if not arpeggio_source_notes:
                arpeggio_source_notes = [current_root % 12 + min_octave * 12]

            # Generate the base pattern for this root note
            base_pattern = self._generate_base_pattern(
                arpeggio_source_notes, 
                arp_steps,  # Number of actual notes in the pattern
                arp_mode, 
                repetition_factor
            )

            # Apply variations for this pattern
            varied_pattern = self._apply_variations(
                base_pattern,
                arpeggio_source_notes,
                current_root,
                mode,
                min_octave,
                range_octaves,
                evolution_rate
            )
            
            # For each bar in this root note's segment
            for _ in range(num_bars_for_segment):
                # For each repeat in the bar
                for _ in range(repeats_per_bar):
                    # For each note in the pattern
                    for note in varied_pattern:
                        if arp_steps == 16:
                            # When using 16th notes, just add the note
                            full_pattern.append(note)
                        else:
                            # When using longer notes, add None values after each note
                            full_pattern.append(note)  # The note itself
                            full_pattern.extend([None] * (steps_per_note - 1))  # Fill remaining steps with None

        # Ensure total length matches bars * steps_per_bar
        total_expected_steps = total_bars * steps_per_bar
        if len(full_pattern) > total_expected_steps:
            full_pattern = full_pattern[:total_expected_steps]
        elif len(full_pattern) < total_expected_steps:
            # Pad with None if too short
            full_pattern.extend([None] * (total_expected_steps - len(full_pattern)))

        # Convert to MIDI events with proper timing
        self._sequence = self._notes_to_midi_events(full_pattern)
        return self.sequence

    def _generate_base_pattern(
        self, 
        source_notes: List[int], 
        steps: int, 
        arp_mode: str,
        repetition_factor: int
    ) -> List[Optional[int]]:
        """Generate the initial arpeggio pattern."""
        if arp_mode == 'up_down':
            return self._generate_up_down_pattern(source_notes, steps)
        else:
            return self._generate_standard_pattern(
                source_notes, 
                steps, 
                arp_mode, 
                repetition_factor
            )
    
    def _generate_up_down_pattern(
        self,
        source_notes: List[int],
        length: int
    ) -> List[Optional[int]]:
        """Generate an up-down arpeggio pattern."""
        if not source_notes:
            return [None] * length
        
        # Sort notes for up and down sequences
        sorted_notes = sorted(source_notes)
        
        # Create the up sequence (including highest note)
        up_sequence = sorted_notes
        
        # Create the down sequence (excluding highest and lowest notes to avoid repetition)
        down_sequence = sorted_notes[-2:0:-1] if len(sorted_notes) > 2 else []
        
        # Combine into full sequence
        full_sequence = up_sequence + down_sequence
        
        # Generate the pattern by cycling through the sequence
        pattern = []
        while len(pattern) < length:
            pattern.extend(full_sequence[:length - len(pattern)])
        
        return pattern[:length]  # Ensure exact length
    
    def _generate_standard_pattern(
        self,
        source_notes: List[int],
        length: int,
        arp_mode: str,
        repetition_factor: int
    ) -> List[Optional[int]]:
        """Generate a standard arpeggio pattern."""
        if not source_notes:
            return [None] * length
        
        # Sort notes according to the arp_mode
        if arp_mode == 'up':
            base_notes = sorted(source_notes)
        elif arp_mode == 'down':
            base_notes = sorted(source_notes, reverse=True)
        elif arp_mode == 'random':
            base_notes = random.sample(source_notes, len(source_notes))
        else:  # 'order'
            base_notes = source_notes

        # Generate pattern with repetition
        pattern = []
        while len(pattern) < length:
            # Add notes from the sequence
            for note in base_notes:
                # Apply repetition based on repetition_factor
                repeat_count = max(1, int(random.gauss(repetition_factor, 1)))
                pattern.extend([note] * min(repeat_count, length - len(pattern)))
                if len(pattern) >= length:
                    break

        return pattern[:length]  # Ensure exact length
    
    def _apply_variations(
        self,
        base_pattern: List[Optional[int]],
        source_notes: List[int],
        root: int,
        mode: str,
        min_octave: int,
        range_octaves: int,
        evolution_rate: float
    ) -> List[Optional[int]]:
        """Apply musical variations to the pattern."""
        if not base_pattern:
            return []
        
        varied_pattern = list(base_pattern)
        
        # Apply evolution
        for i in range(len(varied_pattern)):
            if varied_pattern[i] is not None and random.random() < evolution_rate:
                # Randomly choose a variation type
                variation_type = random.choice(['octave_shift', 'neighbor_tone', 'skip'])
                
                if variation_type == 'octave_shift':
                    # Shift up or down an octave
                    shift = random.choice([-12, 12])
                    new_note = varied_pattern[i] + shift
                    if min_octave * 12 <= new_note <= (min_octave + range_octaves) * 12:
                        varied_pattern[i] = new_note
                
                elif variation_type == 'neighbor_tone':
                    # Add chromatic neighbor tone
                    shift = random.choice([-1, 1])
                    varied_pattern[i] += shift
                
                elif variation_type == 'skip':
                    # Replace with a rest
                    varied_pattern[i] = None
        
        return varied_pattern
    
    def _notes_to_midi_events(self, notes: List[Optional[int]]) -> List[MidiEvent]:
        """Convert note numbers to MIDI events."""
        events = []
        ticks_per_note = DEFAULT_TICKS_PER_BEAT // 4  # 16th notes
        
        for i, note in enumerate(notes):
            if note is not None:
                # Note-on event
                events.append({
                    'type': 'note_on',
                    'time': i * ticks_per_note,
                    'note': note,
                    'velocity': 64,
                    'channel': 0
                })
                # Note-off event
                events.append({
                    'type': 'note_off',
                    'time': (i + 1) * ticks_per_note,
                    'note': note,
                    'velocity': 0,
                    'channel': 0
                })
        
        return sorted(events, key=lambda x: x['time'])
