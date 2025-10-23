# Chavr

A Python speech recognition and audio processing application built with PyAudio, Whisper, and NumPy. **Phase 9 Enhanced** with AI Chavruta partner powered by Gemini 2.0 Flash Experimental.

## Features

- **Phase 9 Enhanced**: AI Chavruta partner powered by Gemini 2.0 Flash Experimental
- **Phase 8 Enhanced**: Sefaria text integration with intelligent autocomplete
- **Phase 7 Enhanced**: Fine-tuned Hebrew Whisper model (`ivrit-ai/whisper-large-v3-ct2`)
- Real-time speech recognition using OpenAI Whisper (faster-whisper optimized)
- Multi-language support (Hebrew/English) with automatic language detection
- **NEW**: AI-powered Q&A during study sessions (voice command: "Chavr, [question]")
- **NEW**: Automatic session summarization with key insights
- **NEW**: Context-aware AI responses using current Sefaria text and conversation history
- **NEW**: Balanced Chavruta responses (Socratic questions, explanations, challenges)
- Sefaria API integration for Jewish text fetching
- Intelligent autocomplete with 120+ Jewish texts (Tanakh, Mishnah, Halachic works, etc.)
- Text context management with session integration
- Language toggle (EN/HE) for text display
- Local text caching for offline access
- Continuous audio streaming with Voice Activity Detection (VAD)
- Session management and transcript storage
- Post-processing filters to reduce hallucinations (e.g., repeated "you")
- Audio device detection and selection
- Interactive GUI interface with Tkinter
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

### Phase 8 Sefaria Integration

The application now includes Sefaria API integration for fetching Jewish texts. Text references are cached locally in the `sefaria_cache/` directory for offline access.

### Phase 9 AI Chavruta Partner

Chavr now includes an AI study partner powered by Google's Gemini 2.0 Flash Experimental model.

#### Setup

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. The AI will be available during study sessions

#### Features

- **Real-time Q&A**: Ask questions by saying "Chavr, [your question]" during study sessions
- **Session Summaries**: Generate study session summaries automatically when sessions end
- **Context-aware**: AI uses your current Sefaria text and recent conversation history
- **Balanced responses**: Mix of Socratic questions, explanations, and challenges
- **Multilingual**: Supports Hebrew and English naturally

#### Cost

Gemini 2.0 Flash Experimental is very affordable:
- First 1500 requests/day: Free
- After: ~$0.075 per 1000 requests
- Typical usage: 10-50 requests per study session

## Usage

### Running the Application

Activate the virtual environment and run the GUI application:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python gui.py
```

The GUI provides an intuitive interface for:
- Loading Jewish texts from Sefaria with autocomplete
- Recording and transcribing speech in Hebrew/English
- Managing study sessions with text context
- Switching between English and Hebrew text display
- **NEW**: AI-powered Q&A during study sessions
- **NEW**: Session summaries and insights

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
- **requests** (>=2.25.0): HTTP library for Sefaria API calls
- **google-generativeai** (>=0.3.0): Google's Gemini AI model integration

## Features in Detail

### Phase 7 Enhanced Speech Recognition
- Fine-tuned Hebrew Whisper model (`ivrit-ai/whisper-large-v3-ct2`) with ~48% WER improvement
- Optimized inference with faster-whisper and CTranslate2
- Hebrew-prioritized language detection for better accuracy
- Post-processing filters to reduce hallucinations
- Support for CPU and GPU acceleration
- Word-level timestamps for precise transcription

### Phase 8 Sefaria Integration
- Real-time text fetching from Sefaria API
- Intelligent autocomplete with 120+ Jewish texts
- Local caching for offline access
- Language toggle (EN/HE) for text display
- HTML tag stripping for clean text display

### Phase 9 AI Chavruta Partner
- Gemini 2.0 Flash Experimental model integration
- Context-aware responses using current Sefaria text and conversation history
- Balanced Chavruta responses (Socratic questions, explanations, challenges)
- Automatic session summarization with key insights
- Voice command activation ("Chavr, [question]")
- Multilingual support (Hebrew and English)
- Comprehensive error handling for API failures

### Continuous Audio Processing
- Real-time audio streaming with Voice Activity Detection
- Session management and transcript storage
- Search functionality across all sessions
- Audio device detection and selection

### Error Handling
- Graceful fallback to openai-whisper if faster-whisper fails
- Comprehensive error messages and logging
- Timeout management for speech detection
- AI API error handling with user-friendly messages

## Troubleshooting

### Common Issues

1. **PyAudio installation fails**: Install PortAudio system library first
2. **ffmpeg not found**: Install ffmpeg for audio processing (`brew install ffmpeg`)
3. **Model download fails**: Ensure internet connection for initial model download
4. **No audio devices found**: Check microphone permissions and connections
5. **Permission errors**: Grant microphone access to your terminal/IDE
6. **CUDA out of memory**: Use `--device cpu` or `--compute int8` for lower memory usage
7. **AI not responding**: Check that GEMINI_API_KEY is set correctly in .env file
8. **API quota exceeded**: Check your Google AI Studio billing and usage limits
9. **Rate limit errors**: Wait a moment and try again, or check your API key permissions

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
