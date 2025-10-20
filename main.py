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
import time
import queue
from datetime import datetime
import whisper
import tempfile
import webrtcvad
import warnings
from session import Session
from storage import SessionStorage


class StreamingRecorder:
    """Handles continuous audio streaming with voice activity detection."""
    
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
    
    def __init__(self, transcript_callback=None, model_size="medium"):
        """Initialize the Chavr application."""
        self.transcript_callback = transcript_callback
        self.model_size = model_size  # "tiny", "base", "small", "medium", "large"
        self.audio = pyaudio.PyAudio()
        
        # Language support configuration
        self.supported_languages = {
            'en': 'English',
            'he': 'Hebrew', 
            'iw': 'Hebrew (alternative)'
        }
        
        # Initialize Whisper model
        try:
            print("Loading Whisper model...")
            # Try to load model with SSL verification disabled for corporate networks
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.whisper_model = whisper.load_model(self.model_size)  # Configurable model size
            print("✓ Whisper model loaded successfully")
            
            # Suppress FP16 warnings for CPU usage
            warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
            print("✓ FP16 warnings suppressed")
        except Exception as e:
            print(f"Error: Could not load Whisper model: {e}")
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
        
        # Print available audio devices
        self.print_audio_devices()
    
    def print_audio_devices(self):
        """Print available audio input devices."""
        print("Available audio input devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']}")
    
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
        
        # End and save current session
        if self.current_session:
            self.current_session.end_session()
            try:
                filename = self.session_storage.save_session(self.current_session)
                print(f"✓ Session saved: {filename}")
                print(f"  Transcripts: {self.current_session.get_transcript_count()}")
                print(f"  Duration: {self.current_session.duration:.1f}s")
                print(f"  Languages: {', '.join(self.current_session.get_languages_used())}")
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
                
                transcription_queue.task_done()
                
            except queue.Empty:
                # No audio data available, continue
                continue
            except Exception as e:
                print(f"Error in transcription worker: {e}")
                break
    
    def _transcribe_audio_data(self, audio_data):
        """
        Transcribe audio data using Whisper.
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            tuple: (recognized_text, detected_language) or (None, None) if failed
        """
        try:
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
            
            # Map detected languages to supported set (English/Hebrew only)
            language_mapping = {
                'en': 'en', 'he': 'he', 'iw': 'he',  # Hebrew variants
                'nl': 'en',  # Dutch → English fallback
                'ko': 'en',  # Korean → English fallback
                'unknown': 'en'  # Default to English
            }
            detected_language = language_mapping.get(detected_language, 'en')
            
            return text, detected_language if text else None
                
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None, None
    
    def listen(self, timeout=5, phrase_time_limit=5):
        """
        Listen for speech using Whisper with PyAudio recording (single phrase mode).
        
        Args:
            timeout (int): Maximum time to wait for speech to start
            phrase_time_limit (int): Maximum time to record a phrase
            
        Returns:
            tuple: (recognized_text, detected_language) or (None, None) if failed
        """
        try:
            print("Listening for speech...")
            
            # Audio parameters
            sample_rate = 16000  # Whisper works best with 16kHz
            channels = 1
            chunk_size = 1024
            format = pyaudio.paInt16
            
            # Open audio stream
            stream = self.audio.open(
                format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size
            )
            
            print("Speak now...")
            frames = []
            
            # Record audio
            for _ in range(0, int(sample_rate / chunk_size * phrase_time_limit)):
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            print("Processing speech with Whisper...")
            
            # Convert frames to audio data
            audio_data = b''.join(frames)
            text, language = self._transcribe_audio_data(audio_data)
            
            if text:
                lang_name = self.supported_languages.get(language, language)
                print(f"[{lang_name}] {text}")
                return text, language
            else:
                print("No speech recognized")
                return None, None
                
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None, None
    
    def run_interactive_mode(self):
        """Run the application in interactive mode."""
        print("Chavr Speech Recognition App - Phase 4: Session Management")
        print("=" * 60)
        print("Commands:")
        print("  'start' - Begin continuous listening/transcription")
        print("  'stop' - Stop continuous listening")
        print("  'listen' - Single phrase listening (original mode)")
        print("  'status' - Show current listening status")
        print("  'sessions' - List all saved sessions")
        print("  'load <id>' - Load and display a specific session")
        print("  'delete <id>' - Delete a session")
        print("  'search <keyword>' - Search across all sessions")
        print("  'current' - Show current session info")
        print("  'stats' - Show session statistics")
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
                elif command == 'listen':
                    text, language = self.listen()
                    if not text:
                        print("No speech recognized.")
                elif command == 'status':
                    status = "ACTIVE" if self.is_continuous_mode else "INACTIVE"
                    print(f"Continuous listening: {status}")
                elif command == 'sessions':
                    self._list_sessions()
                elif command.startswith('load '):
                    session_id = command[5:].strip()
                    self._load_session(session_id)
                elif command.startswith('delete '):
                    session_id = command[7:].strip()
                    self._delete_session(session_id)
                elif command.startswith('search '):
                    keyword = command[7:].strip()
                    self._search_sessions(keyword)
                elif command == 'current':
                    self._show_current_session()
                elif command == 'stats':
                    self._show_session_stats()
                else:
                    print("Unknown command. Try 'start', 'stop', 'listen', 'status', 'sessions', 'load', 'delete', 'search', 'current', 'stats', 'quit', or 'exit'.")
                    
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
    
    def _load_session(self, session_id):
        """Load and display a specific session."""
        if not session_id:
            print("Please provide a session ID. Use 'sessions' to see available IDs.")
            return
        
        session = self.session_storage.load_session(session_id)
        if not session:
            print(f"Session not found: {session_id}")
            return
        
        print(f"\nSession: {session.title}")
        print(f"ID: {session.session_id}")
        print(f"Date: {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {session.duration:.1f}s")
        print(f"Transcripts: {session.get_transcript_count()}")
        print(f"Languages: {', '.join(session.get_languages_used())}")
        print("-" * 60)
        
        for i, transcript in enumerate(session.transcripts, 1):
            lang_name = self.supported_languages.get(transcript.language, transcript.language)
            print(f"{i:3d}. [{transcript.timestamp.strftime('%H:%M:%S')}] [{lang_name}] {transcript.text}")
    
    def _delete_session(self, session_id):
        """Delete a session."""
        if not session_id:
            print("Please provide a session ID. Use 'sessions' to see available IDs.")
            return
        
        # Confirm deletion
        session = self.session_storage.load_session(session_id)
        if not session:
            print(f"Session not found: {session_id}")
            return
        
        print(f"Are you sure you want to delete session '{session.title}'?")
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        
        if confirm == 'yes':
            if self.session_storage.delete_session(session_id):
                print("✓ Session deleted successfully")
            else:
                print("Failed to delete session")
        else:
            print("Deletion cancelled")
    
    def _search_sessions(self, keyword):
        """Search across all sessions."""
        if not keyword:
            print("Please provide a search keyword.")
            return
        
        print(f"Searching for '{keyword}'...")
        results = self.session_storage.search_sessions(keyword)
        
        if not results:
            print("No matching sessions found.")
            return
        
        print(f"\nFound {len(results)} matching session(s):")
        print("-" * 80)
        
        for result in results:
            session = result['session']
            matches = result['matches']
            match_count = result['match_count']
            
            print(f"\nSession: {session.title}")
            print(f"Date: {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {session.duration:.1f}s | Matches: {match_count}")
            print("-" * 40)
            
            for match in matches[:3]:  # Show first 3 matches
                transcript = match['transcript']
                lang_name = self.supported_languages.get(transcript.language, transcript.language)
                print(f"[{transcript.timestamp.strftime('%H:%M:%S')}] [{lang_name}] {transcript.text}")
            
            if len(matches) > 3:
                print(f"... and {len(matches) - 3} more matches")
    
    def _show_current_session(self):
        """Show current session information."""
        if not self.current_session:
            print("No active session.")
            return
        
        print(f"\nCurrent Session: {self.current_session.title}")
        print(f"ID: {self.current_session.session_id}")
        print(f"Started: {self.current_session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.current_session.duration:.1f}s")
        print(f"Transcripts: {self.current_session.get_transcript_count()}")
        print(f"Languages: {', '.join(self.current_session.get_languages_used())}")
        
        if self.current_session.transcripts:
            print("\nRecent transcripts:")
            print("-" * 40)
            for transcript in self.current_session.transcripts[-5:]:  # Show last 5
                lang_name = self.supported_languages.get(transcript.language, transcript.language)
                print(f"[{transcript.timestamp.strftime('%H:%M:%S')}] [{lang_name}] {transcript.text}")
    
    def _show_session_stats(self):
        """Show session statistics."""
        stats = self.session_storage.get_session_stats()
        
        print("\nSession Statistics:")
        print("-" * 30)
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Total Transcripts: {stats['total_transcripts']}")
        print(f"Total Words: {stats['total_words']}")
        print(f"Total Duration: {stats['total_duration']:.1f}s ({stats['total_duration']/60:.1f} minutes)")
        print(f"Languages Used: {', '.join(stats['languages_used'])}")
        
        if stats['date_range']:
            date_range = stats['date_range']
            print(f"Date Range: {date_range['earliest'].strftime('%Y-%m-%d')} to {date_range['latest'].strftime('%Y-%m-%d')}")
    
    def configure_performance(self, speed_priority=True):
        """
        Configure performance settings.
        
        Args:
            speed_priority (bool): If True, optimize for speed. If False, optimize for accuracy.
        """
        if speed_priority:
            # Fast settings - already optimized in __init__
            print("✓ Performance mode: Speed optimized")
        else:
            # Accurate settings - revert to slower but more accurate
            self.streaming_recorder.max_silence_frames = int(1.0 * 16000 / self.streaming_recorder.frame_size)
            self.streaming_recorder.min_speech_frames = int(0.4 * 16000 / self.streaming_recorder.frame_size)
            print("✓ Performance mode: Accuracy optimized")
    
    def cleanup(self):
        """Clean up resources."""
        # Stop continuous listening if active
        if self.is_continuous_mode:
            self.stop_continuous_listening()
        
        # Clean up streaming recorder
        if hasattr(self, 'streaming_recorder'):
            self.streaming_recorder.stop_streaming()
        
        # Terminate PyAudio
        self.audio.terminate()


def main():
    """Main function to run the Chavr application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chavr Speech Recognition App")
    parser.add_argument('--gui', action='store_true', help='Launch GUI mode')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                       default='medium', help='Whisper model size (default: medium)')
    args = parser.parse_args()
    
    if args.gui:
        try:
            from gui import ChavrGUI
            gui = ChavrGUI(model_size=args.model)
            gui.run()
        except Exception as e:
            print(f"Failed to start GUI: {e}")
            sys.exit(1)
    else:
        # Existing CLI mode
        try:
            app = ChavrApp(model_size=args.model)
            app.run_interactive_mode()
        except Exception as e:
            print(f"Failed to initialize Chavr: {e}")
            sys.exit(1)
        finally:
            if 'app' in locals():
                app.cleanup()


if __name__ == "__main__":
    main()
