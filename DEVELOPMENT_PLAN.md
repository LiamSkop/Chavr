# Chavr Development Plan
## AI Multi-Language Study Partner (Chavrusa)

### Project Overview
Chavr is an AI-powered multi-language study partner designed to facilitate learning through speech recognition and real-time transcription. The primary aim is to create a digital Chavrusa (study partner) that can handle Hebrew, Aramaic transliteration, and English for Torah study and language learning.

---

## **Phase 1: Core Audio Setup (Days 1-2)** ✅ COMPLETE

### Step 1: Environment Setup ✅ COMPLETE
- [x] Create virtual environment and install dependencies
- [x] Install core packages: `pyaudio`, `SpeechRecognition`, `numpy`
- [x] Test microphone access and basic audio capture

### Step 2: Basic Audio Recording ✅ COMPLETE
- [x] Create simple audio stream with PyAudio
- [x] Implement start/stop recording functionality
- [x] Save basic audio data to verify microphone works
- [x] Handle microphone permissions and error cases

---

## **Phase 2: Speech Recognition Engine (Days 3-4)** ✅ COMPLETE

### Step 3: Single Language Transcription ✅ COMPLETE
- [x] Integrate SpeechRecognition library with Google Web Speech API
- [x] Implement basic English speech-to-text
- [x] Create simple function that converts audio chunks to text
- [x] Test with sample phrases

### Step 4: Multi-Language Support ✅ COMPLETE
- [x] Configure SpeechRecognition for Hebrew and other languages
- [x] Test language detection and switching
- [x] Handle mixed-language input scenarios
- [x] Add fallback mechanisms for recognition failures

---

## **Phase 3: Real-Time Processing (Days 5-6)** ✅ COMPLETE

### Step 5: Live Audio Streaming ✅ COMPLETE
- [x] Implement continuous audio capture in chunks
- [x] Create real-time transcription loop
- [x] Add voice activity detection to optimize processing
- [x] Handle audio buffering and threading

### Step 6: Live Text Display ✅ COMPLETE
- [x] Create simple console output for transcriptions
- [x] Implement text accumulation and formatting
- [x] Add timestamp markers for session tracking
- [x] Test real-time performance and latency

---

## **Phase 4: Session Management (Days 7-8)** ✅ COMPLETE

### Step 7: Session Storage ✅ COMPLETE
- [x] Create session data structure (timestamp, duration, transcript)
- [x] Implement save/load functionality for sessions
- [x] Add automatic session naming with timestamps
- [x] Create simple file-based storage system

### Step 8: Basic Search ✅ COMPLETE
- [x] Implement keyword search across saved sessions
- [x] Create simple text matching and highlighting
- [x] Add session filtering by date/duration
- [x] Test search performance with multiple sessions

---

## **Phase 4.5: Whisper Model Optimization (Day 8.5)** ✅ COMPLETE

### Step 8.5: Fix Whisper Language Detection Issues ✅ COMPLETE
- [x] Suppress FP16 CPU warnings for cleaner console output
- [x] Add language constraints to Whisper transcribe calls
- [x] Implement language mapping to prevent Dutch/Korean false detections
- [x] Configure Whisper to prevent language lock-in during switching
- [x] Test Hebrew ↔ English language switching accuracy

---

## **Phase 5: GUI Interface (Days 9-11)** ✅ COMPLETE

### Step 9: Basic GUI Framework ✅ COMPLETE
- [x] Choose GUI framework (Tkinter for simplicity, PyQt for polish)
- [x] Create main window with start/stop transcription button
- [x] Add live transcript display area
- [x] Implement basic layout and styling

### Step 10: Session Management UI ✅ COMPLETE
- [x] Add session list/history panel
- [x] Create session viewer for past transcripts
- [x] Implement search interface with results display
- [x] Add session deletion and management features

### Step 11: Polish and Integration ✅ COMPLETE
- [x] Connect GUI to backend transcription engine
- [x] Add visual feedback (recording indicator, status messages)
- [x] Implement proper error handling and user notifications
- [x] Test complete user workflow

---

## **Phase 6: Testing and Optimization (Days 12-13)** ✅ COMPLETE

### Step 12: Multi-Language Testing ✅ COMPLETE
- [x] Test Hebrew, Aramaic transliteration, and English transcription
- [x] Verify mixed-language sessions work correctly
- [x] Optimize recognition accuracy settings
- [x] Test with different microphone setups

### Step 13: Performance Optimization ✅ COMPLETE
- [x] Profile real-time performance and memory usage
- [x] Optimize audio processing and transcription speed
- [x] Add configuration options for quality vs. speed
- [x] Test extended session recording (30+ minutes)

---

## **Recommended Tech Stack:**

### Core Libraries:
- `SpeechRecognition` - Multi-engine speech recognition wrapper
- `PyAudio` - Real-time audio I/O
- `threading` - Handle real-time audio processing

### GUI Options:
- **Tkinter** - Built-in, simple, good for MVP
- **PyQt6** - More professional, better styling

### Optional Enhancements:
- `OpenAI Whisper` - Better offline multi-language support
- `webrtcvad` - Voice activity detection for efficiency

---

## **Development Tips:**

1. **Start Simple** - Begin with console-based version before adding GUI
2. **Test Incrementally** - Verify each phase works before moving to next
3. **Handle Errors Early** - Add proper exception handling from the start
4. **Use Threading** - Keep GUI responsive during audio processing
5. **Save Often** - Auto-save sessions to prevent data loss

---

## **Current Status:**
- **Phase 1**: ✅ Complete
- **Phase 2**: ✅ Complete
- **Phase 3**: ✅ Complete
- **Phase 4**: ✅ Complete
- **Phase 4.5**: ✅ Complete (Whisper Optimization)
- **Phase 5**: ✅ Complete (GUI Interface)
- **Phase 6**: ✅ Complete (Testing and Optimization)
- **Phase 7**: ✅ COMPLETE (Enhanced Speech Recognition)
- **Phase 8**: ✅ COMPLETE (Text Source Integration)
- **Phase 9**: 🧠 UPCOMING (AI Intelligence Layer)
- **Phase 10**: 📊 FUTURE (Session Intelligence)
- **Phase 11**: 🎙️ FUTURE (Voice Output & Conversation)
- **Phase 12**: 🚀 FUTURE (Polish & Production)

---

## **Phase 7: Enhanced Speech Recognition (Days 14-16)** ✅ COMPLETE

### Step 14: Upgrade to Fine-Tuned Hebrew Whisper ✅ COMPLETE
- [x] Install faster-whisper library for optimized inference
- [x] Download and integrate ivrit-ai/whisper-large-v3-ct2-20250513 model
- [x] Replace current Whisper implementation with fine-tuned model
- [x] Benchmark accuracy improvement (achieved ~48% WER reduction)
- [x] Test with rapid Hebrew/English code-switching scenarios

**Expected Impact:** Transcription accuracy will improve from ~10% WER to ~5% WER for Hebrew

**Code Implementation:**
```python
from faster_whisper import WhisperModel

# Load fine-tuned Hebrew model
model = WhisperModel("ivrit-ai/whisper-large-v3-ct2-20250513", 
                     device="cpu", 
                     compute_type="int8")

# Use in transcription
segments, info = model.transcribe(audio_file, 
                                   language="he",
                                   beam_size=5)
```

---

## **Phase 8: Text Source Integration (Days 17-19)** ✅ COMPLETE

### Step 15: Sefaria API Integration ✅ COMPLETE
- [x] Install requests library for Sefaria API calls
- [x] Create SefariaManager wrapper class with caching
- [x] Implement text fetching with proper URL encoding
- [x] Add comprehensive error handling for API failures
- [x] Create local text cache to avoid repeated API calls

### Step 16: Text Context Management ✅ COMPLETE
- [x] Add "Current Study Text" feature to GUI
- [x] Implement text reference input with autocomplete (120+ texts)
- [x] Store current text context with session metadata
- [x] Display source text alongside transcript in GUI
- [x] Add language toggle (EN/HE) for text display
- [x] Implement HTML tag stripping for clean text display

**Code Implementation:**
```python
import requests
import urllib.parse
from pathlib import Path
import json

class SefariaManager:
    def __init__(self):
        self.base_url = "https://www.sefaria.org/api/texts"
        self.cache_dir = Path("sefaria_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def fetch_text(self, reference: str, language: str = "en"):
        # Check cache first
        cache_file = self._get_cache_filename(reference, language)
        if cache_file.exists():
            return self._load_from_cache(cache_file)
        
        # Fetch from API with proper URL encoding
        sefaria_ref = reference.replace(":", ".")
        encoded_ref = urllib.parse.quote(sefaria_ref, safe='.')
        url = f"{self.base_url}/{encoded_ref}"
        
        response = requests.get(url, params={'lang': language})
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                self._save_to_cache(reference, language, data)
                return data
        return None
```

---

## **Phase 9: AI Intelligence Layer (Days 20-25)** 🧠 IN PROGRESS

### Step 17: Gemini 2.0 Flash Experimental Integration ✅ COMPLETE
- [x] Choose LLM approach (Selected: Gemini 2.0 Flash Experimental)
- [x] Set up API credentials and test connection
- [x] Install google-generativeai SDK (>=0.3.0)
- [x] Create GeminiManager wrapper class with prompt templates
- [x] Implement basic Q&A functionality with context-aware prompts
- [x] Add conversation history management (last 10 transcripts)
- [x] Implement session summarization feature
- [x] Add comprehensive error handling (API failures, rate limits, quota)
- [x] Test with Hebrew and English text contexts
- [x] Create test suite (test_gemini.py) with 6 comprehensive tests
- [x] Update documentation (README.md) with Phase 9 features
- [x] Add .env configuration for API key management

**Completed Implementation:**
- `gemini_manager.py` - Full AI integration with all required methods
- `test_gemini.py` - Comprehensive test suite (5/6 tests passing)
- `.env.example` - API key template
- `.gitignore` - Environment file protection
- Updated `requirements.txt` with google-generativeai

**Model Used:** `gemini-2.0-flash-exp` (latest available)
**Cost:** Free tier: 1500 requests/day, then ~$0.075/1000 requests

### Step 18: AI Command Detection & Integration ⏳ NEXT
- [ ] Implement voice command detection in `main.py`
  - [ ] Add method `_detect_ai_command(text)` to check for "Chavr," or "Chaver," trigger phrases
  - [ ] Add method `_extract_question(text)` to remove trigger phrase and extract question
  - [ ] Add method `_handle_ai_question(question)` to process AI queries
- [ ] Initialize GeminiManager in ChavrApp.__init__()
  - [ ] Load API key from environment using `create_gemini_manager()`
  - [ ] Handle case when API key is not set (graceful degradation)
  - [ ] Pass Sefaria context when text is loaded
  - [ ] Update context with recent transcripts during sessions
- [ ] Integrate AI responses into transcript callback system
  - [ ] Modify `_transcription_worker()` to detect AI commands
  - [ ] Call GeminiManager.ask_question() when command detected
  - [ ] Pass AI response back via transcript_callback with special flag
  - [ ] Add AI interaction tracking to current_session
- [ ] Add automatic session summarization
  - [ ] Generate summary in `stop_continuous_listening()`
  - [ ] Store summary with session using `set_ai_summary()`
  - [ ] Display summary in console/GUI
- [ ] Test end-to-end command → response flow

**Integration Points:**
```python
# In main.py ChavrApp class:
def __init__(self, ...):
    self.gemini_manager = create_gemini_manager()
    
def _transcription_worker(self):
    # Detect "Chavr," in transcription
    if self._detect_ai_command(text):
        question = self._extract_question(text)
        response = self._handle_ai_question(question)
        # Send to GUI callback
        
def stop_continuous_listening(self):
    # Generate summary before saving
    if self.gemini_manager and self.current_session:
        summary = self.gemini_manager.generate_session_summary(self.current_session)
        self.current_session.set_ai_summary(summary)
```

### Step 19: GUI AI Chat Panel ⏳ FUTURE
- [ ] Extend Session model to store AI interactions
  - [ ] Add `ai_summary` field for session summaries
  - [ ] Add `ai_interactions` list to track Q&A exchanges
  - [ ] Add methods: `add_ai_interaction(question, response)`, `set_ai_summary(summary)`
  - [ ] Update `to_dict()` and `from_dict()` for serialization
- [ ] Create collapsible "AI Chavruta" chat panel in gui.py
  - [ ] Add panel below transcript panel
  - [ ] Implement chat-style message display (user vs AI)
  - [ ] Add visual distinction: user messages (right-aligned, blue), AI messages (left-aligned, gray)
  - [ ] Add timestamp for each message
  - [ ] Implement auto-scroll to latest message
- [ ] Add "Ask Chavr" button for manual triggers
  - [ ] Create input field for typing questions
  - [ ] Add button to submit questions
  - [ ] Show loading indicator while AI processes
- [ ] Add AI status indicator
  - [ ] Show when AI is processing
  - [ ] Display error messages from AI callback
- [ ] Add "Generate Summary" button
  - [ ] Appears after session ends
  - [ ] Triggers summary generation
  - [ ] Display summary in modal dialog or dedicated panel
- [ ] Update GUI to pass Sefaria context to AI
  - [ ] Call `gemini_manager.set_sefaria_context()` when text loaded
  - [ ] Update context when language toggled
- [ ] Implement chat history persistence
  - [ ] Save AI interactions with session
  - [ ] Load and display chat history when session loaded
- [ ] Test UI responsiveness during AI processing

**GUI Layout:**
```
┌─────────────────────────────────────┐
│ Chavr - Phase 9 Enhanced            │
├─────────────────────────────────────┤
│ [Text Reference Input] [Load]       │
│ ┌─────────────────────────────────┐ │
│ │ Sefaria Text Display            │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Live Transcript                 │ │
│ │ [14:30] שלום                    │ │
│ │ [14:31] Hello                   │ │
│ └─────────────────────────────────┘ │
│ ▼ AI Chavruta                       │
│ ┌─────────────────────────────────┐ │
│ │ AI: A great question! Let's...  │ │
│ │         User: Chavr, explain... │ │
│ └─────────────────────────────────┘ │
│ [Ask Chavr] [Generate Summary]      │
└─────────────────────────────────────┘
```

**Scope for Phase 9:**
- **Focus:** Real-time Q&A on explicit command + session summarization
- **Model:** Gemini 2.0 Flash Experimental (fast, cost-effective)
- **Context:** Current Sefaria text + last 5-10 transcript entries (lightweight)
- **Response Style:** Balanced Chavruta (mix of Socratic questions, explanations, challenges)
- **Triggers:** Voice command ("Chavr," / "Chaver,") or manual button press
- **No RAG/Vector DB:** Simple context retrieval from current session only

**Architecture:**
```
User speaks → Whisper transcribes → Display transcript
                                    ↓
User says "Chavr, [question]" OR clicks "Ask Chavr"
                                    ↓
            Extract question + gather context:
            - Current Sefaria text (if loaded)
            - Last 5-10 transcript entries
                                    ↓
            Build prompt for Gemini 2.0 Flash Experimental
                                    ↓
            Gemini generates balanced response
            (questions + explanations + challenges)
                                    ↓
            Display in AI chat panel
                                    ↓
Session ends → "Generate Summary" (automatic)
                                    ↓
            Gemini analyzes full session
                                    ↓
            Display summary + save with session
```

---

## **Phase 10: Session Intelligence (Days 26-28)** 📊 UPCOMING

### Step 20: Session Analysis ⏳
- [ ] Implement automatic session summarization using LLM
- [ ] Extract key concepts/topics discussed
- [ ] Identify questions asked and answers provided
- [ ] Generate "study insights" report
- [ ] Add session tagging and categorization

### Step 21: Progress Tracking ⏳
- [ ] Create user profile/progress database
- [ ] Track texts studied over time
- [ ] Identify knowledge gaps and areas for review
- [ ] Generate personalized study recommendations
- [ ] Add "Review Mode" for past difficult concepts

### Step 22: Enhanced GUI for AI Features ⏳
- [ ] Add chat interface panel for Q&A
- [ ] Create "Ask AI" button for on-demand questions
- [ ] Display AI-generated insights in sidebar
- [ ] Add session summary view
- [ ] Implement settings for AI behavior (Socratic vs. Direct, Challenge level)

---

## **Phase 11: Voice Output & Conversation (Days 29-31)** 🎙️ FUTURE

### Step 23: Text-to-Speech Integration ⏳
- [ ] Choose TTS solution (ElevenLabs API, Azure TTS, or local)
- [ ] Implement voice output for AI responses
- [ ] Add voice selection (male/female, accent preferences)
- [ ] Test Hebrew TTS quality
- [ ] Add voice speed/pitch controls

### Step 24: Conversational Flow ⏳
- [ ] Implement real-time conversation mode
- [ ] Add interruption handling (user can interrupt AI)
- [ ] Create natural turn-taking system
- [ ] Test full voice-to-voice conversation
- [ ] Optimize latency (target <2 seconds response time)

---

## **Phase 12: Polish & Production (Days 32-35)** 🚀 FUTURE

### Step 25: Error Handling & Edge Cases ⏳
- [ ] Handle API failures gracefully
- [ ] Add offline mode (cached texts + local LLM option)
- [ ] Implement rate limiting and cost controls
- [ ] Add comprehensive logging
- [ ] Create user-friendly error messages

### Step 26: Testing & Optimization ⏳
- [ ] Test with real users (beta testers)
- [ ] Gather feedback on AI interaction quality
- [ ] Optimize prompt engineering based on feedback
- [ ] Performance profiling and optimization
- [ ] Create user documentation

### Step 27: Deployment Preparation ⏳
- [ ] Package application for distribution
- [ ] Create installer for Windows/Mac
- [ ] Set up update mechanism
- [ ] Prepare privacy policy and terms
- [ ] Plan pricing/business model

---

## **Updated Tech Stack:**

### Core Libraries (Existing):
- `SpeechRecognition` - Multi-engine speech recognition wrapper
- `PyAudio` - Real-time audio I/O
- `threading` - Handle real-time audio processing
- `OpenAI Whisper` - Offline multi-language support
- `webrtcvad` - Voice activity detection

### New Additions (Phases 7-12):
- `faster-whisper` - Optimized Whisper inference
- `sefaria-sdk` - Jewish text API integration
- `anthropic` or `transformers` - LLM integration
- `chromadb` - Vector database for RAG
- `sentence-transformers` - Hebrew embeddings (avichr/heBERT)
- `elevenlabs` (optional) - High-quality TTS

---

## **Architecture Diagram:**

```
┌─────────────────┐
│   User Voice    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ivrit.ai Whisper│ (Fine-tuned Hebrew STT)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transcript +   │
│ Reference       │
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sefaria API    │ (Fetch source texts)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RAG System    │ (Semantic search + LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Response    │ (Socratic dialogue)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   TTS Output    │ (Voice response)
└─────────────────┘
```

---

## **Immediate Next Steps (This Week):**

### Day 14 (Today):
- Install faster-whisper and download ivrit.ai model
- Create new branch: `feature/enhanced-stt`
- Implement model swap in existing code

### Day 15:
- Benchmark old vs. new Whisper accuracy
- Fix any integration issues
- Merge if successful

### Day 16:
- Install sefaria-sdk
- Create basic Sefaria integration class
- Test fetching common texts

### Days 17-18:
- Add "Current Text" input to GUI
- Implement reference detection in transcripts
- Display fetched texts in UI

### Days 19-20:
- Set up Claude 3 API (easiest path)
- Create basic Q&A functionality
- Test with simple questions about a text

---

## **Cost Estimates (Monthly):**

### For Personal Use (10 hours/month):
- Claude 3 Sonnet API: ~$10-15/month
- ElevenLabs TTS (optional): ~$5/month (if using voice output)
- Sefaria API: Free
- **Total: ~$15-20/month**

### For Self-Hosted (One-Time Setup):
- DictaLM 2.0: Free (requires GPU)
- Local TTS: Free (lower quality)
- **Total: $0/month** (but requires more technical setup)

---

## **Success Metrics:**

- **Phase 7:** Hebrew transcription WER < 5%
- **Phase 8:** Successfully fetch and display 95%+ of mentioned references
- **Phase 9:** AI provides relevant, grounded answers 80%+ of the time
- **Phase 10:** Session summaries capture key points accurately
- **Phase 11:** Voice conversation latency < 2 seconds
- **Phase 12:** 10+ beta users actively using the tool

---

## **Project Goals:**
- Create a digital Chavrusa for Torah study
- Support Hebrew, Aramaic transliteration, and English
- Real-time speech recognition and transcription
- Session management and search capabilities
- User-friendly GUI interface
- Optimized for extended study sessions
- **NEW:** Intelligent AI-powered study partner with Socratic dialogue
- **NEW:** Automatic text reference fetching and context management
- **NEW:** Voice-to-voice conversational interaction
- **NEW:** Session analysis and progress tracking

---

*Last Updated: October 21, 2025*

*Current Phase: 8 - Text Source Integration (COMPLETE)*

*Next Milestone: AI Intelligence Layer with LLM integration*

*Target: Transform from transcription tool → intelligent AI chavruta*
