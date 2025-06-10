# MIDI Generator

A Python-based MIDI generation tool that creates musical sequences with customizable effects, including arpeggios, drones, and tape-like pitch modulation effects.

## Features

### Generation Types

- **Arpeggios**: Create melodic sequences with configurable patterns
- **Drones**: Generate sustained notes with customizable durations

### Effects

- **Tape Wobble Effect**: Simulates vintage tape machine pitch instability
  - Wow effect (slow pitch modulation)
  - Flutter effect (faster pitch modulation)
  - Configurable depth and rate for both effects
  - Randomness parameter for organic variation
- **Velocity Humanization**: Adds natural velocity variations to notes

## Technical Implementation

### 1. Core MIDI Generation

- Uses `mido` library for MIDI file creation
- Implements flexible event system supporting both legacy and modern MIDI instruction formats
- Configurable parameters:
  - BPM (tempo)
  - Number of bars
  - Ticks per beat
  - Note patterns

### 2. Effect System

- Modular effect architecture using base classes
- Each effect can process both individual notes and complete sequences
- Effects can be chained and ordered
- MIDI pitch bend implementation:
  - RPN messages for pitch bend range configuration
  - 14-bit resolution (0-16383)
  - Optimized bend event generation

### 3. Tape Wobble Implementation

- Mathematically accurate simulation of tape machine characteristics
- Configurable parameters:
  - Wow Rate (0.1-1.0 Hz)
  - Wow Depth (5-50 cents)
  - Flutter Rate (3-12 Hz)
  - Flutter Depth (1-10 cents)
  - Randomness (0.0-1.0)
- Efficient event generation with adaptive sampling
- Proper MIDI pitch bend range configuration via RPN messages

## Usage

1. **Setup Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Generator**

   ```bash
   python -m midi_gen
   ```

4. **Configure Generation**
   - Follow the prompts to select:
     - Generation type (arpeggio/drone)
     - BPM
     - Number of bars
     - Effect parameters

## Effect Parameters

### Tape Wobble Effect

- **Wow Rate**: Speed of primary pitch modulation (Hz)
  - Range: 0.1-1.0 Hz
  - Default: 0.5 Hz
- **Wow Depth**: Amount of primary pitch variation
  - Range: 5-50 cents
  - Default: 25 cents
- **Flutter Rate**: Speed of secondary pitch modulation
  - Range: 3-12 Hz
  - Default: 8 Hz
- **Flutter Depth**: Amount of secondary pitch variation
  - Range: 1-10 cents
  - Default: 5 cents
- **Randomness**: Amount of random variation
  - Range: 0.0-1.0
  - Default: 0.5

### Velocity Humanization

- **Range**: Maximum velocity variation
  - Default: ±10 units

## Development Process

1. **Initial Setup**

   - Created basic MIDI generation framework
   - Implemented arpeggio and drone generation modes
   - Set up configuration system

2. **Effect System Development**

   - Designed modular effect architecture
   - Implemented base effect classes
   - Created effect chaining system

3. **Tape Wobble Implementation**

   - Researched tape machine characteristics
   - Implemented mathematical models for wow and flutter
   - Added pitch bend message generation
   - Optimized event generation and timing

4. **Refinements**
   - Added proper MIDI channel handling
   - Implemented RPN messages for pitch bend range
   - Added debug logging system
   - Optimized performance

## Technical Notes

- MIDI pitch bend uses 14-bit resolution (0-16383)
- RPN messages configure ±2 semitone range
- Event timing uses MIDI ticks (default 480 per quarter note)
- Efficient event generation with threshold-based filtering
- Proper handling of MIDI channels and message types

## Requirements

- Python 3.8+
- mido
- python-rtmidi (optional, for real-time MIDI output)

## Future Enhancements

- Additional effect types
- Real-time MIDI output
- More complex arpeggio patterns
- GUI interface
- MIDI input processing
- Additional humanization options
