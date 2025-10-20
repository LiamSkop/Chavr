# Chavr

A Python speech recognition and audio processing application built with PyAudio, Whisper, and NumPy. **Phase 7 Enhanced** with fine-tuned Hebrew speech recognition.

## Features

- **Phase 7 Enhanced**: Fine-tuned Hebrew Whisper model (`ivrit-ai/whisper-large-v3-ct2`)
- Real-time speech recognition using OpenAI Whisper (faster-whisper optimized)
- Multi-language support (Hebrew/English) with automatic language detection
- Continuous audio streaming with Voice Activity Detection (VAD)
- Session management and transcript storage
- Post-processing filters to reduce hallucinations (e.g., repeated "you")
- Audio device detection and selection
- Interactive command-line interface
- Cross-platform support (macOS, Linux, Windows)

## Requirements

- Python 3.8 or higher
- PortAudio library (for PyAudio)
- ffmpeg (for audio processing with Whisper)
- Internet connection (for model download on first run)

## Installation

1. Clone or download this project
2. Navigate to the project directory:
   ```bash
   cd Chavr
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### macOS Installation Notes

If you encounter issues installing PyAudio on macOS, you may need to install PortAudio and ffmpeg first:

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PortAudio and ffmpeg
brew install portaudio ffmpeg

# Then install the Python packages
pip install -r requirements.txt
```

### Phase 7 Model Download

On first run, the fine-tuned Hebrew Whisper model (`ivrit-ai/whisper-large-v3-ct2`, ~1.5-2.5GB) will be automatically downloaded and cached. This may take a few minutes depending on your internet connection.

## Usage

### Running the Application

Activate the virtual environment and run the main application:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

### Phase 7 CLI Options

```bash
# Basic usage
python main.py

# Use GPU acceleration (if available)
python main.py --device cuda --compute float16

# Force Hebrew-only mode for accuracy testing
python main.py --hebrew-only

# Use different Whisper model size
python main.py --model large
```

### Interactive Commands

Once the application is running, you can use these commands:

- `start` - Begin continuous listening/transcription
- `stop` - Stop continuous listening
- `listen` - Single phrase listening (original mode)
- `status` - Show current listening status
- `sessions` - List all saved sessions
- `load <id>` - Load and display a specific session
- `delete <id>` - Delete a session
- `search <keyword>` - Search across all sessions
- `current` - Show current session info
- `stats` - Show session statistics
- `quit` or `exit` - Exit the application

### Example Session

```
Chavr Speech Recognition App - Phase 7: Enhanced Speech Recognition
====================================================================
Commands:
  'start' - Begin continuous listening/transcription
  'stop' - Stop continuous listening
  'listen' - Single phrase listening (original mode)
  'status' - Show current listening status
  'sessions' - List all saved sessions
  'load <id>' - Load and display a specific session
  'delete <id>' - Delete a session
  'search <keyword>' - Search across all sessions
  'current' - Show current session info
  'stats' - Show session statistics
  'quit' or 'exit' - Exit the application
====================================================================

Phase 7: Initializing faster-whisper with fine-tuned Hebrew model...
✓ Faster-whisper adapter initialized

Enter command: start
✓ Started new session: Session_2025-10-20_14-30-15
✓ Continuous listening started - speak naturally!
[14:30:18] [Hebrew] שלום, איך שלומך?
[14:30:22] [English] How are you doing today?

Enter command: stop
✓ Continuous listening stopped
✓ Session saved: sessions/2025-10-20_14-30-15_a1b2c3d4.json
  Transcripts: 2
  Duration: 8.5s
  Languages: Hebrew, English

Enter command: quit
Goodbye!
```

## Project Structure

```
Chavr/
├── main.py              # Main application file
├── requirements.txt     # Python package dependencies
├── README.md           # This file
└── venv/               # Virtual environment (created during setup)
```

## Dependencies

- **PyAudio** (>=0.2.11): Cross-platform audio I/O library
- **NumPy** (>=1.24.0): Fundamental package for scientific computing
- **openai-whisper** (>=20231117): OpenAI's Whisper speech recognition
- **faster-whisper** (>=1.0.0): Optimized Whisper implementation with CTranslate2
- **webrtcvad** (>=2.0.10): Voice Activity Detection library

## Features in Detail

### Phase 7 Enhanced Speech Recognition
- Fine-tuned Hebrew Whisper model (`ivrit-ai/whisper-large-v3-ct2`) with ~48% WER improvement
- Optimized inference with faster-whisper and CTranslate2
- Hebrew-prioritized language detection for better accuracy
- Post-processing filters to reduce hallucinations
- Support for CPU and GPU acceleration
- Word-level timestamps for precise transcription

### Continuous Audio Processing
- Real-time audio streaming with Voice Activity Detection
- Session management and transcript storage
- Search functionality across all sessions
- Audio device detection and selection

### Error Handling
- Graceful fallback to openai-whisper if faster-whisper fails
- Comprehensive error messages and logging
- Timeout management for speech detection

## Troubleshooting

### Common Issues

1. **PyAudio installation fails**: Install PortAudio system library first
2. **ffmpeg not found**: Install ffmpeg for audio processing (`brew install ffmpeg`)
3. **Model download fails**: Ensure internet connection for initial model download
4. **No audio devices found**: Check microphone permissions and connections
5. **Permission errors**: Grant microphone access to your terminal/IDE
6. **CUDA out of memory**: Use `--device cpu` or `--compute int8` for lower memory usage

### Getting Help

If you encounter issues:
1. Check that all dependencies are properly installed
2. Verify microphone permissions
3. Test with a simple audio recording first
4. Check internet connectivity for model download

## Benchmarking

Run the Phase 7 benchmark suite to compare performance:

```bash
python benchmark_phase7.py
```

This will test both faster-whisper and openai-whisper performance and save results to `bench/phase7_results_*.json`.

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.
