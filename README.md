# midi-gen

MIDI Arpeggio Generator that creates evolving musical patterns and outputs them as MIDI files.

## Features

- Generates arpeggios based on various musical scales and modes.
- Customizable parameters including root note(s), tempo, octaves, and arpeggio patterns.
- Supports effects like pitch shimmer and velocity humanization.
- Interactive Command Line Interface (CLI) for easy configuration.

## Setup

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <repository-url>
    cd midi-gen
    ```

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    Make sure you have Python 3 installed. Then run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the script and generate a MIDI file, navigate to the project's root directory and execute:

```bash
python main.py
```

The script will launch an interactive command-line interface that will guide you through the configuration options step-by-step. Answer the prompts to customize the arpeggio generation.

The generated MIDI files will be saved in the `generated/` directory.
