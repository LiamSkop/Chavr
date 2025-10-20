# Chavr GUI Usage Guide

## Quick Start

### Launch GUI Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Launch GUI
python main.py --gui
```

### Launch CLI Mode (Original)
```bash
# Activate virtual environment
source venv/bin/activate

# Launch CLI
python main.py
```

## GUI Features

### Main Interface
- **Large Record Button**: Click to start/stop recording
- **Live Transcript**: Real-time display of speech recognition
- **Status Indicator**: Shows recording status (●)
- **Status Bar**: Session duration and transcript count

### Keyboard Shortcuts
- **Space Bar**: Toggle recording on/off
- **Cmd+Q** (Mac) / **Ctrl+Q** (Windows/Linux): Quit application

### Visual Design
- Clean, minimal interface inspired by Apple Notes
- Color-coded language detection (Hebrew/English)
- Auto-scrolling transcript display
- Responsive layout that works on different screen sizes

## How It Works

1. **Start Recording**: Click the large "START" button
2. **Speak Naturally**: The app detects speech and transcribes in real-time
3. **Language Detection**: Automatically detects Hebrew and English
4. **Auto-Save**: Sessions are automatically saved when you stop recording
5. **View Transcripts**: All transcripts appear in the live display area

## Troubleshooting

### GUI Won't Start
- Ensure virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Try CLI mode first: `python main.py`

### Recording Issues
- Check microphone permissions
- Ensure microphone is not being used by another application
- Try the CLI mode to test audio: `python main.py`

### Hebrew Text Display
- The GUI supports Hebrew text display
- If Hebrew appears incorrectly, check your system's font support

## Technical Details

- **Framework**: Tkinter (built-in Python GUI)
- **Threading**: Uses background threads for audio processing
- **Session Management**: Automatic saving to `sessions/` directory
- **Language Support**: English and Hebrew with automatic detection
- **File Format**: Sessions saved as JSON files with timestamps
