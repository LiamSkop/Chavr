#!/usr/bin/env python3
"""
Chavr - Speech Recognition and Audio Processing Project
Main entry point for the application.
"""

import numpy as np
import pyaudio
import sys
import os
import wave
import threading
import queue
from datetime import datetime
import whisper
import tempfile
import webrtcvad
import warnings
from session import Session
from storage import SessionStorage

# Phase 7: Enhanced Speech Recognition
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not available, falling back to openai-whisper")


class FasterWhisperAdapter:
    """Adapter for faster-whisper with fine-tuned Hebrew model."""
    
    def __init__(self, device="cpu", compute_type="int8", hebrew_only=False):
        """
        Initialize the faster-whisper adapter.
        
        Args:
            device (str): Device to use ("cpu" or "cuda")
            compute_type (str): Compute type ("int8" or "float16")
            hebrew_only (bool): Force Hebrew-only mode
        """
        self.device = device
        self.compute_type = compute_type
        self.hebrew_only = hebrew_only
        self.model = None
        self.model_name = "ivrit-ai/whisper-large-v3-ct2"  # Fine-tuned Hebrew model
        
        # Post-processing filters (lean)
        self.noise_threshold = 0.01  # RMS threshold for noise detection
        self.hallucination_words = {"you", "yeah", "uh", "um", "ah"}
        self.min_text_length = 3
        
        # Language mapping
        self.language_mapping = {
            'en': 'en', 'he': 'he', 'iw': 'he',  # Hebrew variants
            'nl': 'en',  # Dutch → English fallback
            'ko': 'en',  # Korean → English fallback
            'unknown': 'en'  # Default to English
        }
    
    def load_model(self):
        """Load the faster-whisper model."""
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError("faster-whisper not available")
        
        try:
            print(f"Loading faster-whisper model: {self.model_name}")
            print(f"Device: {self.device}, Compute: {self.compute_type}")
            
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            print("✓ Faster-whisper model loaded successfully")
            
        except Exception as e:
            print(f"Error loading faster-whisper model: {e}")
            raise
    
    def transcribe(self, audio_data_or_path, language=None):
        """
        Transcribe audio using faster-whisper.
        
        Args:
            audio_data_or_path: Raw audio data (bytes) or file path
            language: Language code (None for auto-detect)
            
        Returns:
            tuple: (text, detected_language, segments, info) or (None, None, None, None) if failed
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Determine if input is file path or raw data
            if isinstance(audio_data_or_path, str):
                audio_path = audio_data_or_path
            else:
                # Save raw audio data to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    audio_path = temp_file.name
                    with wave.open(audio_path, 'wb') as wf:
                        wf.setnchannels(1)  # Mono
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(16000)  # 16kHz
                        wf.writeframes(audio_data_or_path)
            
            # Set language for transcription - prioritize Hebrew for fine-tuned model
            transcribe_language = language
            if self.hebrew_only:
                transcribe_language = "he"
            elif transcribe_language is None:
                # For ivrit-ai model, default to Hebrew for better accuracy
                transcribe_language = "he"
            
            # Transcribe with faster-whisper using fine-tuned Hebrew model
            segments, info = self.model.transcribe(
                audio_path,
                language=transcribe_language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 400},
                # Additional parameters for better Hebrew transcription
                word_timestamps=True,  # Enable word-level timestamps
                condition_on_previous_text=True  # Use context for better mixed-language handling
            )
            
            # Extract text from segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            text = " ".join(text_parts).strip()
            
            # Clean up temporary file if we created it
            if not isinstance(audio_data_or_path, str):
                os.unlink(audio_path)
            
            # Post-process the text
            text = self._post_process_text(text, audio_data_or_path)
            
            # Map detected language
            detected_language = info.language if hasattr(info, 'language') else "unknown"
            mapped_language = self.language_mapping.get(detected_language, 'en')
            
            return text, mapped_language, segments, info
            
        except Exception as e:
            print(f"Error during faster-whisper transcription: {e}")
            # Clean up temporary file if we created it
            if not isinstance(audio_data_or_path, str) and 'audio_path' in locals():
                try:
                    os.unlink(audio_path)
                except:
                    pass
            return None, None, None, None
    
    def _post_process_text(self, text, audio_data):
        """
        Apply post-processing filters to reduce hallucinations.
        
        Args:
            text (str): Raw transcribed text
            audio_data: Original audio data for RMS calculation
            
        Returns:
            str: Filtered text or None if filtered out
        """
        if not text:
            return None
        
        # Calculate RMS for noise detection
        if isinstance(audio_data, bytes):
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2)) / 32768.0  # Normalize to 0-1
        else:
            rms = 0.1  # Default if we can't calculate
        
        # Filter 1: Drop very short text unless high SNR
        if len(text) < self.min_text_length and rms < self.noise_threshold * 2:
            return None
        
        # Filter 2: Suppress common hallucinations on near-silence
        text_lower = text.lower().strip()
        if rms < self.noise_threshold and text_lower in self.hallucination_words:
            return None

        return text



class StreamingRecorder:
    
    def __init__(self, sample_rate=16000, frame_duration_ms=30, vad_aggressiveness=1):
        """
        Initialize the streaming recorder.
        
        Args:
            sample_rate (int): Audio sample rate in Hz
            frame_duration_ms (int): Frame duration in milliseconds
            vad_aggressiveness (int): VAD aggressiveness (0-3)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        
        # Audio parameters
        self.channels = 1
        self.format = pyaudio.paInt16
        self.chunk_size = self.frame_size
        
        # State management
        self.is_recording = False
        self.is_streaming = False
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        
        # Threading
        self.capture_thread = None
        self.transcription_thread = None
        self.stop_event = threading.Event()
        
        # Audio buffer for accumulating speech - optimized for faster response
        self.speech_buffer = []
        self.silence_frames = 0
        self.min_speech_frames = int(0.2 * sample_rate / self.frame_size)  # 0.2 seconds - faster trigger
        self.max_silence_frames = int(0.5 * sample_rate / self.frame_size)  # 0.5 seconds - quicker response
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def start_streaming(self):
        """Start continuous audio streaming."""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stop_event.clear()
        
        # Start audio capture thread
        self.capture_thread = threading.Thread(target=self._capture_audio)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        print("✓ Continuous audio streaming started")
    
    def stop_streaming(self):
        """Stop continuous audio streaming."""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        if self.transcription_thread and self.transcription_thread.is_alive():
            self.transcription_thread.join(timeout=2)
        
        print("✓ Continuous audio streaming stopped")
    
    def _capture_audio(self):
        """Capture audio in a separate thread."""
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_streaming and not self.stop_event.is_set():
                try:
                    # Read audio frame
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Check for voice activity
                    is_speech = self.vad.is_speech(data, self.sample_rate)
                    
                    if is_speech:
                        self.speech_buffer.append(data)
                        self.silence_frames = 0
                    else:
                        self.silence_frames += 1
                        
                        # If we have accumulated speech and hit silence threshold
                        if (len(self.speech_buffer) >= self.min_speech_frames and 
                            self.silence_frames >= self.max_silence_frames):
                            
                            # Queue audio for transcription
                            audio_data = b''.join(self.speech_buffer)
                            self.transcription_queue.put(audio_data)
                            
                            # Reset buffer
                            self.speech_buffer = []
                            self.silence_frames = 0
                    
                except Exception as e:
                    print(f"Error in audio capture: {e}")
                    break
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
    
    def get_transcription_queue(self):
        """Get the transcription queue for processing."""
        return self.transcription_queue


class ChavrApp:
    """Main application class for Chavr speech recognition."""
    
    def __init__(self, transcript_callback=None, model_size="medium", device="cpu", compute_type="int8", hebrew_only=False):
        """Initialize the Chavr application."""
        self.transcript_callback = transcript_callback
        self.model_size = model_size  # "tiny", "base", "small", "medium", "large"
        self.device = device
        self.compute_type = compute_type
        self.hebrew_only = hebrew_only
        self.audio = pyaudio.PyAudio()
        
        # Language support configuration (single source of truth)
        self.supported_languages = {
            'en': 'English',
            'he': 'Hebrew',
            'iw': 'Hebrew'
        }
        
        # Initialize Speech Recognition Model (Phase 7: Enhanced)
        self.whisper_model = None
        self.faster_whisper_adapter = None
        
        # Try faster-whisper first (Phase 7)
        if FASTER_WHISPER_AVAILABLE:
            try:
                print("Phase 7: Initializing faster-whisper with optimized model...")
                self.faster_whisper_adapter = FasterWhisperAdapter(
                    device=self.device,
                    compute_type=self.compute_type,
                    hebrew_only=self.hebrew_only
                )
                # Test the adapter by loading the model
                self.faster_whisper_adapter.load_model()
                print("✓ Faster-whisper adapter initialized and tested")
            except Exception as e:
                print(f"Warning: Could not initialize faster-whisper: {e}")
                print("Falling back to openai-whisper...")
                self.faster_whisper_adapter = None
        
        # Fallback to openai-whisper if faster-whisper fails
        if self.faster_whisper_adapter is None:
            try:
                print("Loading openai-whisper model...")
                # Try to load model with SSL verification disabled for corporate networks
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                self.whisper_model = whisper.load_model(self.model_size)
                print("✓ OpenAI Whisper model loaded successfully")
                
                # Suppress FP16 warnings for CPU usage
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
                print("✓ FP16 warnings suppressed")
            except Exception as e:
                print(f"Error: Could not load any Whisper model: {e}")
                print("Please ensure openai-whisper is installed: pip3 install openai-whisper")
                sys.exit(1)
        
        # Initialize streaming recorder
        self.streaming_recorder = StreamingRecorder()
        self.is_continuous_mode = False
        self.transcription_thread = None
        self.stop_transcription_event = threading.Event()
        
        # Initialize session management
        self.session_storage = SessionStorage()
        self.current_session = None
        
        # Phase 9: AI integration
        from gemini_manager import create_gemini_manager
        self.gemini_manager = create_gemini_manager()
        
        if self.gemini_manager:
            print("✓ AI Chavruta partner initialized")
        else:
            print("⚠ AI features disabled (no API key)")
        
        # AI processing queue for non-blocking execution
        self.ai_queue = queue.Queue()
        self.ai_worker_thread = None
        self.ai_processing = False
        
        # Optionally print available audio devices once (lean runtime)
        try:
            print("Available audio input devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  {i}: {info['name']}")
        except Exception:
            pass
    
    def start_continuous_listening(self):
        """Start continuous listening mode."""
        if self.is_continuous_mode:
            print("Continuous listening is already active")
            return
        
        self.is_continuous_mode = True
        self.stop_transcription_event.clear()
        
        # Create new session
        self.current_session = Session()
        print(f"✓ Started new session: {self.current_session.title}")
        
        # Start streaming recorder
        self.streaming_recorder.start_streaming()
        
        # Start transcription worker thread
        self.transcription_thread = threading.Thread(target=self._transcription_worker)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        print("✓ Continuous listening started - speak naturally!")
    
    def stop_continuous_listening(self):
        """Stop continuous listening mode."""
        if not self.is_continuous_mode:
            print("Continuous listening is not active")
            return
        
        self.is_continuous_mode = False
        self.stop_transcription_event.set()
        
        # Stop streaming recorder
        self.streaming_recorder.stop_streaming()
        
        # Wait for transcription thread to finish
        if self.transcription_thread and self.transcription_thread.is_alive():
            self.transcription_thread.join(timeout=3)
        
        # Phase 9: Stop AI worker if running
        if self.ai_processing:
            self.ai_processing = False
            if self.ai_worker_thread and self.ai_worker_thread.is_alive():
                self.ai_worker_thread.join(timeout=5)
        
        # End and save current session
        if self.current_session:
            self.current_session.end_session()
            
            # Phase 9: Generate session summary (only if >5 transcripts)
            if self.gemini_manager and self.current_session.get_transcript_count() > 5:
                print("\n[AI] Generating session summary...")
                try:
                    summary = self.gemini_manager.generate_session_summary(self.current_session)
                    if summary:
                        self.current_session.set_ai_summary(summary)
                        print(f"\n{'='*60}")
                        print(f"[Session Summary]")
                        print(f"{'='*60}")
                        print(summary)
                        print(f"{'='*60}\n")
                    else:
                        print("⚠ Could not generate summary")
                except Exception as e:
                    print(f"Error generating summary: {e}")
            
            try:
                filename = self.session_storage.save_session(self.current_session)
                print(f"✓ Session saved: {filename}")
                print(f"  Transcripts: {self.current_session.get_transcript_count()}")
                print(f"  Duration: {self.current_session.duration:.1f}s")
                print(f"  Languages: {', '.join(self.current_session.get_languages_used())}")
                
                # Phase 9: Display AI statistics if available
                if self.current_session.get_ai_interaction_count() > 0:
                    print(f"  AI Interactions: {self.current_session.get_ai_interaction_count()}")
                if self.current_session.has_ai_summary():
                    print(f"  Summary: Generated ✓")
                    
            except Exception as e:
                print(f"Error saving session: {e}")
            self.current_session = None
        
        print("✓ Continuous listening stopped")
    
    def _transcription_worker(self):
        """Worker thread that processes audio from the transcription queue."""
        transcription_queue = self.streaming_recorder.get_transcription_queue()
        
        while self.is_continuous_mode and not self.stop_transcription_event.is_set():
            try:
                # Get audio data from queue (with timeout)
                audio_data = transcription_queue.get(timeout=1.0)
                
                # Process the audio
                text, language = self._transcribe_audio_data(audio_data)
                
                if text:
                    lang_name = self.supported_languages.get(language, language)
                    timestamp = datetime.now()
                    timestamp_str = timestamp.strftime("%H:%M:%S")
                    print(f"[{timestamp_str}] [{lang_name}] {text}")
                    
                    # Add to current session
                    if self.current_session:
                        self.current_session.add_transcript(text, language)
                    
                    # Call GUI callback if available
                    if self.transcript_callback:
                        self.transcript_callback(text, language, timestamp)
                    
                    # Phase 9: Detect AI command
                    if self._detect_ai_command(text):
                        question = self._extract_question(text)
                        if question:
                            print(f"[AI] Detected question: {question}")
                            self._handle_ai_question(question, timestamp)
                
                transcription_queue.task_done()
                
            except queue.Empty:
                # No audio data available, continue
                continue
            except Exception as e:
                print(f"Error in transcription worker: {e}")
                break
    
    def _transcribe_audio_data(self, audio_data):
        """
        Transcribe audio data using faster-whisper or fallback to openai-whisper.
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            tuple: (recognized_text, detected_language) or (None, None) if failed
        """
        try:
            # Phase 7: Use faster-whisper adapter if available
            if self.faster_whisper_adapter:
                text, language, segments, info = self.faster_whisper_adapter.transcribe(audio_data)
                return text, language
            
            # Fallback to openai-whisper
            if self.whisper_model:
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_filename = temp_file.name
                    with wave.open(temp_filename, 'wb') as wf:
                        wf.setnchannels(1)  # Mono
                        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                        wf.setframerate(16000)  # 16kHz
                        wf.writeframes(audio_data)
                
                # Multilingual prompt to help with code-switching
                multilingual_prompt = (
                    "This is a conversation that may contain both Hebrew and English. "
                    "Some sentences mix both languages. "
                    "שלום hello מה שלומך how are you תודה thank you"
                )
                
                # Transcribe with Whisper - optimized for mixed-language support
                result = self.whisper_model.transcribe(
                    temp_filename,
                    language=None,  # Auto-detect
                    initial_prompt=multilingual_prompt,  # Guide for mixed languages
                    condition_on_previous_text=True,  # Use context for better mixed-language handling
                    word_timestamps=False  # Faster processing
                )
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                # Extract text and language
                text = result["text"].strip()
                detected_language = result.get("language", "unknown")
                
                # Normalize language code to our supported set
                normalized = 'he' if detected_language in ('he', 'iw') else 'en'
                return text, normalized if text else None
            
            return None, None
                
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None, None
    
    def _detect_ai_command(self, text: str) -> bool:
        """
        Detect if text contains an AI command trigger.
        
        Supported triggers:
        - "Chavr,"
        - "Chaver,"
        - "Hey Chavr,"
        - "Hey Chaver,"
        - "Chavr" (without comma)
        - "Chaver" (without comma)
        
        Args:
            text (str): Transcribed text
            
        Returns:
            bool: True if AI command detected
        """
        text_lower = text.lower().strip()
        
        triggers = [
            'hey chavr,',
            'hey chaver,',
            'chavr,',
            'chaver,',
            'hey chavr',
            'hey chaver',
            'chavr',
            'chaver'
        ]
        
        for trigger in triggers:
            if text_lower.startswith(trigger):
                return True
        
        return False
    
    def _extract_question(self, text: str) -> str:
        """
        Extract question from AI command by removing trigger phrase.
        
        Args:
            text (str): Full transcribed text with trigger
            
        Returns:
            str: Question without trigger phrase
        """
        text_lower = text.lower().strip()
        
        # Remove trigger phrases (order matters - longer first)
        triggers = [
            'hey chavr,',
            'hey chaver,',
            'chavr,',
            'chaver,',
            'hey chavr',
            'hey chaver',
            'chavr',
            'chaver'
        ]
        
        for trigger in triggers:
            if text_lower.startswith(trigger):
                # Remove trigger and return rest
                question = text[len(trigger):].strip()
                # Remove leading comma if present
                if question.startswith(','):
                    question = question[1:].strip()
                return question
        
        return text.strip()
    
    def _handle_ai_question(self, question: str, timestamp: datetime):
        """
        Process AI question in background thread (non-blocking).
        
        Args:
            question (str): User's question
            timestamp (datetime): When question was asked
        """
        if not self.gemini_manager:
            print("⚠ AI not available (no API key)")
            return
        
        # Queue the question for background processing
        self.ai_queue.put({
            'question': question,
            'timestamp': timestamp
        })
        
        # Start AI worker thread if not running
        if not self.ai_processing:
            self._start_ai_worker()
    
    def _start_ai_worker(self):
        """Start background thread for AI processing."""
        if self.ai_worker_thread and self.ai_worker_thread.is_alive():
            return
        
        self.ai_processing = True
        self.ai_worker_thread = threading.Thread(target=self._ai_worker)
        self.ai_worker_thread.daemon = True
        self.ai_worker_thread.start()
    
    def _ai_worker(self):
        """Background worker for processing AI requests."""
        while self.ai_processing or not self.ai_queue.empty():
            try:
                # Get question from queue (with timeout)
                ai_request = self.ai_queue.get(timeout=1.0)
                
                question = ai_request['question']
                timestamp = ai_request['timestamp']
                
                print(f"[AI] Processing: {question[:50]}...")
                
                # Update context with recent transcripts (efficient)
                if self.current_session:
                    # Convert transcript entries to dict format
                    transcript_context = [
                        {'text': t.text, 'language': t.language}
                        for t in self.current_session.transcripts[-10:]
                    ]
                    self.gemini_manager.add_transcript_context(transcript_context)
                
                # Get AI response
                response = self.gemini_manager.ask_question(question)
                
                if response:
                    # Store in session
                    if self.current_session:
                        self.current_session.add_ai_interaction(
                            question=question,
                            response=response,
                            timestamp=timestamp
                        )
                    
                    # Display in CLI with special formatting
                    print(f"\n{'='*60}")
                    print(f"[AI Chavruta Response]")
                    print(f"{'='*60}")
                    print(response)
                    print(f"{'='*60}\n")
                    
                    # Send to GUI callback with language='ai'
                    if self.transcript_callback:
                        self.transcript_callback(response, 'ai', timestamp)
                else:
                    print("⚠ AI did not return a response")
                
                self.ai_queue.task_done()
                
            except queue.Empty:
                # No more requests, exit worker
                break
            except Exception as e:
                print(f"Error in AI worker: {e}")
                continue
        
        self.ai_processing = False
    
    # Removed single-phrase listen mode to keep code lean (continuous mode covers core use case)
    
    def run_interactive_mode(self):
        """Run the application in interactive mode."""
        print("Chavr Speech Recognition App - Lean CLI")
        print("=" * 60)
        print("Commands:")
        print("  'start' - Begin continuous listening/transcription")
        print("  'stop' - Stop continuous listening")
        print("  'sessions' - List saved sessions")
        print("  'quit' or 'exit' - Exit the application")
        print("=" * 60)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command in ['quit', 'exit']:
                    # Ensure continuous listening is stopped
                    if self.is_continuous_mode:
                        self.stop_continuous_listening()
                    print("Goodbye!")
                    break
                elif command == 'start':
                    self.start_continuous_listening()
                elif command == 'stop':
                    self.stop_continuous_listening()
                elif command == 'sessions':
                    self._list_sessions()
                else:
                    print("Unknown command. Try 'start', 'stop', 'sessions', 'quit', or 'exit'.")
                    
            except KeyboardInterrupt:
                print("\nStopping continuous listening...")
                if self.is_continuous_mode:
                    self.stop_continuous_listening()
                print("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _list_sessions(self):
        """List all saved sessions."""
        sessions = self.session_storage.list_sessions(limit=20)
        
        if not sessions:
            print("No saved sessions found.")
            return
        
        print(f"\nSaved Sessions ({len(sessions)}):")
        print("-" * 80)
        
        for i, session_data in enumerate(sessions, 1):
            timestamp = datetime.fromisoformat(session_data['timestamp'])
            duration = session_data.get('duration', 0)
            transcript_count = session_data.get('transcript_count', 0)
            languages = ', '.join(session_data.get('languages_used', []))
            
            print(f"{i:2d}. {session_data['title']}")
            print(f"    ID: {session_data['session_id'][:8]}...")
            print(f"    Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Duration: {duration:.1f}s | Transcripts: {transcript_count} | Languages: {languages}")
            print()
    
    # Removed CLI session operations and performance toggles to keep code lean
    
    def cleanup(self):
        """Clean up resources."""
        # Stop continuous listening if active
        if self.is_continuous_mode:
            self.stop_continuous_listening()
        
        # Phase 9: Stop AI worker
        if hasattr(self, 'ai_processing') and self.ai_processing:
            self.ai_processing = False
            if hasattr(self, 'ai_worker_thread') and self.ai_worker_thread and self.ai_worker_thread.is_alive():
                self.ai_worker_thread.join(timeout=2)
        
        # Clean up streaming recorder
        if hasattr(self, 'streaming_recorder'):
            self.streaming_recorder.stop_streaming()
        
        # Terminate PyAudio
        self.audio.terminate()


def main():
    """Main function to run the Chavr application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chavr Speech Recognition App - Phase 7 Enhanced")
    parser.add_argument('--gui', action='store_true', help='Launch GUI mode')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                       default='medium', help='Whisper model size (default: medium)')
    # Phase 7: Enhanced Speech Recognition arguments
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                       help='Device to use for faster-whisper (default: cpu)')
    parser.add_argument('--compute', choices=['int8', 'float16'], default='int8',
                       help='Compute type for faster-whisper (default: int8)')
    parser.add_argument('--hebrew-only', action='store_true',
                       help='Force Hebrew-only mode for accuracy testing')
    args = parser.parse_args()
    
    if args.gui:
        try:
            from gui import ChavrGUI
            gui = ChavrGUI(
                model_size=args.model,
                device=args.device,
                compute_type=args.compute,
                hebrew_only=args.hebrew_only
            )
            gui.run()
        except Exception as e:
            print(f"Failed to start GUI: {e}")
            sys.exit(1)
    else:
        app = None
        try:
            app = ChavrApp(
                model_size=args.model,
                device=args.device,
                compute_type=args.compute,
                hebrew_only=args.hebrew_only
            )
            app.run_interactive_mode()
        except Exception as e:
            print(f"Failed to initialize Chavr: {e}")
            sys.exit(1)
        finally:
            if app:
                app.cleanup()


if __name__ == "__main__":
    main()
