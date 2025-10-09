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


class StreamingRecorder:
    """Handles continuous audio streaming with voice activity detection."""
    
    def __init__(self, sample_rate=16000, frame_duration_ms=30, vad_aggressiveness=2):
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
        
        # Audio buffer for accumulating speech
        self.speech_buffer = []
        self.silence_frames = 0
        self.min_speech_frames = int(0.3 * sample_rate / self.frame_size)  # 0.3 seconds
        self.max_silence_frames = int(1.0 * sample_rate / self.frame_size)  # 1 second
        
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
    
    def __init__(self):
        """Initialize the Chavr application."""
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
            self.whisper_model = whisper.load_model("medium")  # Balanced speed/accuracy
            print("✓ Whisper model loaded successfully")
        except Exception as e:
            print(f"Error: Could not load Whisper model: {e}")
            print("Please ensure openai-whisper is installed: pip3 install openai-whisper")
            sys.exit(1)
        
        # Initialize streaming recorder
        self.streaming_recorder = StreamingRecorder()
        self.is_continuous_mode = False
        self.transcription_thread = None
        self.stop_transcription_event = threading.Event()
        
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
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] [{lang_name}] {text}")
                
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
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_filename)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            # Extract text and language
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
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
        print("Chavr Speech Recognition App - Phase 3: Real-Time Streaming")
        print("=" * 60)
        print("Commands:")
        print("  'start' - Begin continuous listening/transcription")
        print("  'stop' - Stop continuous listening")
        print("  'listen' - Single phrase listening (original mode)")
        print("  'status' - Show current listening status")
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
                else:
                    print("Unknown command. Try 'start', 'stop', 'listen', 'status', 'quit', or 'exit'.")
                    
            except KeyboardInterrupt:
                print("\nStopping continuous listening...")
                if self.is_continuous_mode:
                    self.stop_continuous_listening()
                print("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
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
    try:
        app = ChavrApp()
        app.run_interactive_mode()
    except Exception as e:
        print(f"Failed to initialize Chavr: {e}")
        sys.exit(1)
    finally:
        if 'app' in locals():
            app.cleanup()


if __name__ == "__main__":
    main()
