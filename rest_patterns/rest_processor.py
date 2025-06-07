"""
Rest pattern processor effect for MIDI sequences.
"""

from typing import List, Union, Tuple, Dict
from .rest_config import RestPatternConfig
from ..effects_base import MidiEffect, EffectConfiguration, EffectType, MidiInstruction

class RestPatternConfiguration(EffectConfiguration):
    """Configuration for rest pattern effect."""
    def __init__(self, config_dict: Dict):
        super().__init__()
        self.rest_config = RestPatternConfig.from_dict(config_dict)
        
    def __post_init__(self):
        """Set effect type and priority."""
        self.effect_type = EffectType.SEQUENCE_PROCESSOR
        self.priority = 100  # Run before other effects

class RestPatternEffect(MidiEffect):
    """Effect that applies rest patterns to a sequence."""
    
    def __init__(self, config: RestPatternConfiguration):
        super().__init__(config)
        self.rest_config = config.rest_config
        
    def _validate_configuration(self) -> None:
        """Validate the configuration."""
        if not isinstance(self.config, RestPatternConfiguration):
            raise ValueError("Configuration must be a RestPatternConfiguration")
    
    def _process_note_impl(self, ctx: Dict) -> Dict:
        """Not used for rest patterns."""
        return ctx
    
    def _process_sequence_impl(self, 
                             events: List[Union[MidiInstruction, Tuple]], 
                             options: Dict) -> List[Union[MidiInstruction, Tuple]]:
        """Apply rest pattern to the sequence."""
        if not events or not self.rest_config.enabled:
            return events
            
        # Get sequence parameters
        ticks_per_beat = options.get('ticks_per_beat', 480)
        ticks_per_step = ticks_per_beat // 4  # 16th notes
        arp_steps = options.get('arp_steps', 8)  # Get the arp cycle length
        
        print(f"\n[DEBUG] Rest Pattern Processing:")
        print(f"[DEBUG] Steps between rests: {self.rest_config.steps_between_rests}")
        print(f"[DEBUG] Arp steps: {arp_steps}")
        print(f"[DEBUG] Ticks per step: {ticks_per_step}")
        
        # First pass: identify which notes to remove
        notes_to_remove = set()  # Set of (note_number, channel) tuples
        
        for event in events:
            if isinstance(event, tuple) and event[0] == 'note_on':
                tick = event[1]
                current_step = tick // ticks_per_step
                
                # Calculate position within arp cycle
                step_in_cycle = current_step % arp_steps
                
                # If this step should be a rest within the cycle
                if step_in_cycle % self.rest_config.steps_between_rests == self.rest_config.steps_between_rests - 1:
                    note_number = event[2]
                    channel = event[4]
                    notes_to_remove.add((note_number, channel))
                    print(f"[DEBUG] Marking note {note_number} at step {current_step} (cycle pos {step_in_cycle}) for rest")
        
        # Second pass: remove both note_on and corresponding note_off events
        processed_events = []
        
        for event in events:
            if isinstance(event, tuple):
                if event[0] in ('note_on', 'note_off'):
                    note_number = event[2]
                    channel = event[4]
                    if (note_number, channel) in notes_to_remove:
                        tick = event[1]
                        current_step = tick // ticks_per_step
                        step_in_cycle = current_step % arp_steps
                        print(f"[DEBUG] Removing {event[0]} event for note {note_number} at step {current_step} (cycle pos {step_in_cycle})")
                        continue
                
                processed_events.append(event)
        
        return processed_events 
