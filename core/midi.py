"""
Core MIDI functionality for event generation and file creation.
"""

import mido
from typing import Dict, List, Union, Tuple, Optional
from ..effects.base import EffectChain, BaseEffect

class MidiProcessor:
    """Handles MIDI event processing and file creation."""
    
    def __init__(self):
        self.effect_chain = EffectChain()
        
    def add_effect(self, effect: BaseEffect) -> None:
        """Add an effect to the processing chain."""
        self.effect_chain.add_effect(effect)
    
    def process_events(self, 
                      events: List[Dict[str, Union[int, str]]], 
                      options: Dict) -> List[Dict[str, Union[int, str]]]:
        """Process events through the effect chain."""
        return self.effect_chain.process_sequence(events, options)

def create_midi_file(
    events: List[Dict[str, Union[int, str]]],
    options: Dict,
    effects: Optional[List[BaseEffect]] = None
) -> str:
    """Creates a MIDI file from the processed events.
    
    Args:
        events: List of MIDI events
        options: Configuration options including:
            - filename: Output file path
            - bpm: Tempo in beats per minute
            - ticks_per_beat: MIDI resolution
        effects: Optional list of effects to apply
    
    Returns:
        Path to the created MIDI file
    """
    # Initialize processor and add effects
    processor = MidiProcessor()
    if effects:
        for effect in effects:
            processor.add_effect(effect)
    
    # Process events through effects
    processed_events = processor.process_events(events, options)
    
    # Get file creation parameters
    filename = options.get('filename', 'output.mid')
    bpm = options.get('bpm', 120)
    ticks_per_beat = options.get('ticks_per_beat', 480)
    
    # Create MIDI file
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    
    # Convert events to MIDI messages
    last_tick = 0
    for event in processed_events:
        event_type = event['type']
        tick = event['time']
        delta_tick = tick - last_tick
        
        if event_type == 'note_on':
            track.append(mido.Message('note_on',
                                   note=event['note'],
                                   velocity=event['velocity'],
                                   channel=event.get('channel', 0),
                                   time=delta_tick))
        elif event_type == 'note_off':
            track.append(mido.Message('note_off',
                                   note=event['note'],
                                   velocity=event['velocity'],
                                   channel=event.get('channel', 0),
                                   time=delta_tick))
        elif event_type == 'pitch_bend':
            track.append(mido.Message('pitchwheel',
                                   pitch=event['value'],
                                   channel=event.get('channel', 0),
                                   time=delta_tick))
        elif event_type == 'control_change':
            track.append(mido.Message('control_change',
                                   control=event['control'],
                                   value=event['value'],
                                   channel=event.get('channel', 0),
                                   time=delta_tick))
        
        last_tick = tick
    
    # Save file
    mid.save(filename)
    return filename 
