import random
from midi_gen.effects_base import MidiEffect, NoteContext

class ShimmerEffect(MidiEffect):
    def __init__(self, wobble_range: float = 2.0, smooth_factor: float = 0.1) -> None:
        self.wobble_range = wobble_range
        self.smooth_factor = smooth_factor
        self.current_wobble = 0.0  # Initialize current_wobble

    def _interpolate(self, start: float, end: float, factor: float) -> float:
        """Linear interpolation between start and end values."""
        return start + (end - start) * factor

    def apply(self, current_note_context: NoteContext) -> NoteContext:
        new_wobble = random.uniform(-self.wobble_range, self.wobble_range)
        
        # Smooth the transition from the previous wobble to the new one
        smoothed_wobble = self._interpolate(self.current_wobble, new_wobble, self.smooth_factor)
        
        # Update current_wobble for the next note
        self.current_wobble = smoothed_wobble 
        
        shimmered_note = int(round(current_note_context['note'] + smoothed_wobble))
        
        # Ensure the note stays within MIDI bounds
        current_note_context['note'] = max(0, min(127, shimmered_note))
        return current_note_context

class HumanizeVelocityEffect(MidiEffect):
    def __init__(self, humanization_range: int = 20) -> None:
        self.humanization_range = humanization_range

    def apply(self, current_note_context: NoteContext) -> NoteContext:
        original_velocity = current_note_context['velocity']
        velocity_change = random.randint(-self.humanization_range, self.humanization_range)
        humanized_velocity = original_velocity + velocity_change
        
        # Ensure velocity stays within MIDI bounds
        current_note_context['velocity'] = max(0, min(127, humanized_velocity))
        return current_note_context 
