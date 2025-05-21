from typing import TypedDict, Protocol

class NoteContext(TypedDict):
    note: int
    velocity: int
    # Future properties like duration, time_since_last_note, bpm, etc., can be added here.

class MidiEffect(Protocol):
    def __init__(self, **kwargs) -> None:
        # Allows effects to be initialized with their specific parameters.
        ...

    def apply(self, current_note_context: NoteContext) -> NoteContext:
        # Takes the current NoteContext, applies the effect's logic,
        # and returns the modified NoteContext.
        ... 
