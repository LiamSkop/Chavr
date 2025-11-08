# Chavr - AI Torah Tutor

A lightweight, stateless Python application for Torah study with AI-powered Q&A. Focused on quick question-answering while reading Jewish texts.

## Features

- **AI-Powered Q&A**: Get instant answers to questions about Jewish texts using Google's Gemini 2.5 Flash-Lite
- **Sefaria Integration**: Load any Jewish text from Sefaria's vast library with intelligent search
- **Challenging Terms Extraction**: Automatically identifies and explains difficult terms before you start reading
- **Chapter Navigation**: Quick navigation between chapters with keyboard shortcuts
- **Smart Text Search**: Fuzzy search to find texts by name, Hebrew name, or partial matches
- **Context-Aware**: AI understands the current text you're studying and recent conversation
- **Concise Responses**: Adaptive response length based on question complexity
- **Yeshivish-Aware**: Understands yeshivish terminology and provides culturally appropriate explanations

## Requirements

- Python 3.8 or higher
- Internet connection (for Sefaria API and Gemini API)

## Installation

1. Clone or download this project:
   ```bash
   cd Chavr
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Gemini API key:
   - Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the project root:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```
   - Optional: Install `python-dotenv` for automatic `.env` loading:
     ```bash
     pip install python-dotenv
     ```

## Usage

### Running the Application

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run_tutor.py
```

### Basic Workflow

1. **Load a Text**: Click "Change Text" button, search for a text (e.g., "Chayei Adam"), and select it
2. **View Challenging Terms**: Click "▼ Challenging Terms" to see difficult terms explained before reading
3. **Ask Questions**: Type your question in the input field and press Enter or click "Ask"
4. **Navigate Chapters**: Use keyboard shortcuts or buttons to move between chapters

### Keyboard Shortcuts

- **Cmd/Ctrl + K**: Focus question input field
- **Cmd/Ctrl + Left Arrow**: Previous chapter
- **Cmd/Ctrl + Right Arrow**: Next chapter
- **Enter**: Send question (when input is focused)

### Example Usage

1. Load "Chayei Adam 6"
2. Review challenging terms (if available)
3. Read the text in your physical book
4. Ask questions like:
   - "What does amen mean?"
   - "Explain the hekesh here"
   - "What's the halacha?"
5. Get concise, yeshivish-aware answers instantly

## Features in Detail

### AI Q&A System

- **Adaptive Response Length**: Quick questions get quick answers (1-2 sentences), detailed questions get focused paragraphs
- **Question Type Detection**: Automatically detects if you're asking for a definition, explanation, or detailed analysis
- **Context Awareness**: Remembers your current text and recent conversation history
- **Yeshivish-Aware**: Uses Hebrew/yeshivish terms naturally when relevant, but explains in English

### Challenging Terms Feature

When you load a chapter, the app automatically:
1. Analyzes the text for difficult terms
2. Extracts 5-8 challenging words/phrases
3. Provides brief explanations for each
4. Caches results for instant loading next time

Terms are displayed in an expandable panel that you can reference while reading.

### Text Search

Smart search capabilities:
- **Fuzzy Matching**: Finds texts even with typos or partial names
- **Hebrew Support**: Search by Hebrew names
- **Popular Texts**: Quick access to frequently studied texts
- **Recent Texts**: Easy access to recently loaded texts

### Chapter Navigation

- Previous/Next chapter buttons
- Keyboard shortcuts for quick navigation
- Automatically loads text context for AI

## Project Structure

```
Chavr/
├── run_tutor.py           # Main entry point
├── tutor_gui.py           # GUI interface
├── tutor_app.py           # Core application logic
├── gemini_manager.py      # AI integration (Gemini 2.5 Flash-Lite)
├── sefaria_manager.py    # Sefaria API integration
├── text_catalog.py       # Text search and catalog
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── sefaria_cache/        # Cached texts and terms
└── venv/                 # Virtual environment
```

## Dependencies

- **requests** (>=2.25.0): HTTP library for Sefaria API calls
- **google-generativeai** (>=0.3.0): Google's Gemini AI model integration
- **python-dotenv** (optional): For `.env` file support

## API Costs

**Gemini 2.5 Flash-Lite (Free Tier):**
- 10,000 requests per minute
- 10 million tokens per minute
- More than enough for personal use

**Sefaria API:**
- Free and open source
- Rate limits apply but generous for normal usage

## Troubleshooting

### Common Issues

1. **"AI tutor is not available"**: 
   - Check that `GEMINI_API_KEY` is set in `.env` file
   - Verify API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **"Rate limit exceeded"**: 
   - The app automatically retries with exponential backoff
   - Wait a few seconds and try again
   - Free tier has generous limits (10K req/min)

3. **Text not loading**:
   - Check internet connection
   - Verify text reference is correct (e.g., "Genesis 1:1")
   - Try a different text to test Sefaria API

4. **Challenging terms not appearing**:
   - Terms are extracted asynchronously (may take 2-5 seconds)
   - Check if extraction completed (button will show count)
   - Cached terms load instantly on subsequent visits

5. **Import errors**:
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

## Design Philosophy

**Stateless & Simple:**
- No session persistence - just Q&A
- Fast startup, minimal overhead
- Focus on the current study session

**Text-First:**
- You read from your physical book
- App provides AI context and Q&A
- No text display clutter

**Speed Matters:**
- Optimized for quick question-answering
- Cached challenging terms for instant access
- Minimal UI, maximum functionality

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.
