# Chavr

A Python speech recognition and audio processing application built with PyAudio, SpeechRecognition, and NumPy.

## Features

- Real-time speech recognition using Google's speech recognition API
- Audio device detection and selection
- Microphone calibration for ambient noise
- Audio data analysis using NumPy
- Interactive command-line interface
- Cross-platform support (macOS, Linux, Windows)

## Requirements

- Python 3.8 or higher
- PortAudio library (for PyAudio)
- Internet connection (for Google Speech Recognition API)

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

If you encounter issues installing PyAudio on macOS, you may need to install PortAudio first:

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PortAudio
brew install portaudio

# Then install the Python packages
pip install -r requirements.txt
```

## Usage

### Running the Application

Activate the virtual environment and run the main application:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

### Interactive Commands

Once the application is running, you can use these commands:

- `listen` - Start listening for speech input
- `quit` or `exit` - Exit the application

### Example Session

```
Chavr Speech Recognition App
========================================
Commands:
  'listen' - Listen for speech
  'quit' or 'exit' - Exit the application
========================================

Enter command: listen
Listening for speech...
Processing speech...
Recognized: Hello, this is a test

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
- **SpeechRecognition** (>=3.10.0): Library for performing speech recognition
- **NumPy** (>=1.24.0): Fundamental package for scientific computing

## Features in Detail

### Speech Recognition
- Uses Google's speech recognition service
- Configurable timeout and phrase time limits
- Automatic microphone calibration for ambient noise

### Audio Processing
- Real-time audio device detection
- Audio data analysis using NumPy
- RMS, amplitude, and statistical analysis

### Error Handling
- Graceful handling of network errors
- Timeout management for speech detection
- Comprehensive error messages

## Troubleshooting

### Common Issues

1. **PyAudio installation fails**: Install PortAudio system library first
2. **No audio devices found**: Check microphone permissions and connections
3. **Speech recognition fails**: Ensure internet connection for Google API
4. **Permission errors**: Grant microphone access to your terminal/IDE

### Getting Help

If you encounter issues:
1. Check that all dependencies are properly installed
2. Verify microphone permissions
3. Test with a simple audio recording first
4. Check internet connectivity for speech recognition

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.
