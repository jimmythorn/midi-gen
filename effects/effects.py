"""
Implementation of MIDI effects.
"""

import random
import math
from typing import List, Dict, Optional
from .base import BaseEffect, NoteContext
from ..core.types import (
    MidiEvent,
    MIDI_PITCH_BEND_MIN,
    MIDI_PITCH_BEND_MAX,
    MIDI_PITCH_BEND_CENTER,
    SEMITONES_PER_BEND,
    DEFAULT_TICKS_PER_BEAT
)

class TapeWobbleEffect(BaseEffect):
    """Simulates the pitch wobble of a worn tape machine."""
    
    def _validate_config(self) -> None:
        """Validate effect configuration."""
        self.config.setdefault('rate_hz', 5.0)  # Wobble frequency
        self.config.setdefault('depth', 0.3)  # Wobble depth in semitones
        self.config.setdefault('phase_variation', 0.2)  # Random phase variation
        
        if not 0.1 <= self.config['rate_hz'] <= 20.0:
            raise ValueError("rate_hz must be between 0.1 and 20.0")
        if not 0.0 <= self.config['depth'] <= 2.0:
            raise ValueError("depth must be between 0.0 and 2.0")
        if not 0.0 <= self.config['phase_variation'] <= 1.0:
            raise ValueError("phase_variation must be between 0.0 and 1.0")
    
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Process individual notes (not used for this effect)."""
        return ctx
    
    def _process_sequence_impl(self, events: List[MidiEvent], options: Dict) -> List[MidiEvent]:
        """Apply tape wobble to the sequence."""
        if not events:
            return events
        
        # Get sequence parameters
        bpm = options.get('bpm', 120)
        ticks_per_beat = options.get('ticks_per_beat', DEFAULT_TICKS_PER_BEAT)
        
        # Find sequence duration
        max_tick = max(event['time'] for event in events)
        duration_seconds = (max_tick / ticks_per_beat) * (60.0 / bpm)
        
        # Generate wobble curve
        wobble_events = self._generate_wobble_curve(
            duration_seconds,
            bpm,
            ticks_per_beat
        )
        
        # Combine original events with wobble
        result_events = list(events)  # Copy original events
        
        # Add pitch bend messages
        for time_sec, bend_value in wobble_events:
            tick = int((time_sec * bpm * ticks_per_beat) / 60.0)
            result_events.append({
                'type': 'pitch_bend',
                'time': tick,
                'value': bend_value,
                'channel': 0
            })
        
        # Add RPN messages for pitch bend range at start
        result_events.extend([
            {
                'type': 'control_change',
                'time': 0,
                'control': 101,  # RPN MSB
                'value': 0,
                'channel': 0
            },
            {
                'type': 'control_change',
                'time': 0,
                'control': 100,  # RPN LSB
                'value': 0,
                'channel': 0
            },
            {
                'type': 'control_change',
                'time': 0,
                'control': 6,    # Data Entry MSB
                'value': int(SEMITONES_PER_BEND),  # Convert float to int
                'channel': 0
            },
            {
                'type': 'control_change',
                'time': 0,
                'control': 38,   # Data Entry LSB
                'value': 0,
                'channel': 0
            }
        ])
        
        return sorted(result_events, key=lambda x: x['time'])
    
    def _generate_wobble_curve(
        self,
        duration_seconds: float,
        bpm: int,
        ticks_per_beat: int
    ) -> List[tuple[float, int]]:
        """Generate the wobble curve data."""
        rate_hz = self.config['rate_hz']
        depth = self.config['depth']
        phase_variation = self.config['phase_variation']
        
        # Calculate parameters
        points_per_second = 50  # Resolution of the curve
        num_points = int(duration_seconds * points_per_second)
        phase_offset = random.uniform(0, 2 * math.pi * phase_variation)
        
        # Generate curve points
        curve_points = []
        for i in range(num_points):
            time = i / points_per_second
            # Basic sine wave
            value = math.sin(2 * math.pi * rate_hz * time + phase_offset)
            # Add some randomness
            value += random.uniform(-0.1, 0.1)
            # Scale to pitch bend range
            bend_range = MIDI_PITCH_BEND_MAX - MIDI_PITCH_BEND_MIN
            bend_value = int(
                MIDI_PITCH_BEND_CENTER +
                (value * depth * bend_range / SEMITONES_PER_BEND)
            )
            bend_value = max(MIDI_PITCH_BEND_MIN, min(MIDI_PITCH_BEND_MAX, bend_value))
            
            curve_points.append((time, bend_value))
        
        return curve_points

class HumanizeVelocityEffect(BaseEffect):
    """Adds human-like velocity variations to notes."""
    
    def _validate_config(self) -> None:
        """Validate effect configuration."""
        self.config.setdefault('intensity', 0.3)  # Overall intensity of humanization
        self.config.setdefault('beat_emphasis', 0.6)  # Emphasis on strong beats
        self.config.setdefault('trend_inertia', 0.4)  # How much to follow velocity trends
        
        if not 0.0 <= self.config['intensity'] <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        if not 0.0 <= self.config['beat_emphasis'] <= 1.0:
            raise ValueError("beat_emphasis must be between 0.0 and 1.0")
        if not 0.0 <= self.config['trend_inertia'] <= 1.0:
            raise ValueError("trend_inertia must be between 0.0 and 1.0")
        
        # Initialize state
        self._reset_state()
    
    def _reset_state(self) -> None:
        """Reset the internal state."""
        self.last_velocity = 64
        self.velocity_trend = 0
        self.notes_processed = 0
    
    def _process_note_impl(self, ctx: NoteContext) -> NoteContext:
        """Apply humanization to a single note."""
        if ctx['velocity'] <= 0:  # Don't process note-off events
            return ctx
        
        # Get base velocity
        base_velocity = ctx['velocity']
        
        # Calculate various influences
        position_emphasis = self._calculate_position_emphasis(ctx)
        beat_emphasis = self._calculate_beat_emphasis(ctx)
        trend_influence = self._calculate_trend_influence(base_velocity)
        
        # Calculate random variation
        intensity = self.config['intensity']
        random_range = int(20 * intensity)
        random_variation = random.randint(-random_range, random_range)
        
        # Combine all influences
        total_adjustment = int(
            position_emphasis +
            beat_emphasis +
            trend_influence +
            random_variation
        )
        
        # Create new context with adjusted velocity
        new_ctx = ctx.copy()
        new_velocity = max(1, min(127, base_velocity + total_adjustment))
        new_ctx['velocity'] = new_velocity
        
        # Update state
        self.last_velocity = new_velocity
        self.velocity_trend = (new_velocity - base_velocity) * self.config['trend_inertia']
        self.notes_processed += 1
        
        return new_ctx
    
    def _process_sequence_impl(self, events: List[MidiEvent], options: Dict) -> List[MidiEvent]:
        """Process the complete sequence."""
        self._reset_state()
        
        result_events = []
        for event in events:
            if event['type'] == 'note_on':
                # Create note context
                ctx = NoteContext(
                    note=event['note'],
                    velocity=event['velocity'],
                    channel=event.get('channel', 0),
                    time=event['time'],
                    duration=None,
                    time_seconds=0.0,  # Will be calculated
                    bpm=options.get('bpm', 120),
                    beat_position=0.0,  # Will be calculated
                    bar_position=0,  # Will be calculated
                    generation_type=options.get('generation_type', 'unknown'),
                    is_first_note=False,
                    is_last_note=False,
                    processed_by=[]
                )
                
                # Process through note-level humanization
                new_ctx = self._process_note_impl(ctx)
                
                # Create new event with adjusted velocity
                new_event = event.copy()
                new_event['velocity'] = new_ctx['velocity']
                result_events.append(new_event)
            else:
                result_events.append(event)
        
        return result_events
    
    def _calculate_position_emphasis(self, ctx: NoteContext) -> int:
        """Calculate emphasis based on note position."""
        if ctx['is_first_note']:
            return int(10 * self.config['intensity'])
        return 0
    
    def _calculate_beat_emphasis(self, ctx: NoteContext) -> int:
        """Calculate emphasis based on beat position."""
        beat_pos = ctx['beat_position']
        if beat_pos < 0.1:  # On the beat
            return int(15 * self.config['beat_emphasis'])
        return 0
    
    def _calculate_trend_influence(self, current_velocity: int) -> int:
        """Calculate influence based on velocity trend."""
        if abs(self.velocity_trend) < 2:
            return 0
        
        # Tendency to return to middle velocities
        if current_velocity > 100 and self.velocity_trend > 0:
            return -int(self.velocity_trend)
        if current_velocity < 30 and self.velocity_trend < 0:
            return -int(self.velocity_trend)
        
        return int(self.velocity_trend) 
