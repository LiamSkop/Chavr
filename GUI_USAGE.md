# Chavr GUI Usage Guide - Phase 8 Enhanced

## Quick Start

### Launch GUI Mode (Recommended)
```bash
# Activate virtual environment
source venv/bin/activate

# Launch GUI with Sefaria integration
python gui.py
```

### Launch CLI Mode (Legacy)
```bash
# Activate virtual environment
source venv/bin/activate

# Launch CLI
python main.py
```

## GUI Features - Phase 8 Enhanced

### Text Input Section
- **Text Reference Field**: Type to search 120+ Jewish texts with autocomplete
- **Load Text Button**: Fetch text from Sefaria API
- **Language Toggle (EN/HE)**: Switch between English and Hebrew text display
- **Record Button**: Start/stop speech recording

### Main Text Display
- **Scrollable Text Area**: Shows loaded Sefaria text
- **Clean HTML Rendering**: Strips formatting for readability
- **Hebrew Font Support**: Proper right-to-left text display
- **Verse Numbering**: Automatic numbering for verse lists

### Transcript Panel (Collapsible)
- **Live Transcript**: Real-time display of speech recognition
- **Session Management**: Auto-save with text context
- **Language Detection**: Color-coded Hebrew/English detection
- **Toggle Button**: Show/hide transcript panel

### Keyboard Shortcuts
- **Cmd/Ctrl+L**: Load text from reference field
- **Cmd/Ctrl+T**: Toggle language (EN/HE)
- **Space Bar**: Toggle recording on/off
- **Cmd+Q** (Mac) / **Ctrl+Q** (Windows/Linux): Quit application

### Visual Design
- Clean, minimal interface inspired by Apple Notes
- Professional autocomplete dropdown with proper contrast
- Responsive layout optimized for study sessions
- Color-coded language detection (Hebrew/English)

## How It Works - Phase 8 Enhanced

1. **Load Text**: Type a text reference (e.g., "Genesis", "Chayei Adam") and select from autocomplete
2. **Choose Language**: Toggle between English and Hebrew text display
3. **Start Recording**: Click the record button to begin speech recognition
4. **Speak Naturally**: The app detects speech and transcribes in real-time
5. **Language Detection**: Automatically detects Hebrew and English
6. **Auto-Save**: Sessions are automatically saved with text context
7. **View Results**: All transcripts appear in the collapsible panel

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
