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
from datetime import datetime
import whisper
import tempfile


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
        
        # Print available audio devices
        self.print_audio_devices()
    
    def print_audio_devices(self):
        """Print available audio input devices."""
        print("Available audio input devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']}")
    
    def listen(self, timeout=5, phrase_time_limit=5):
        """
        Listen for speech using Whisper with PyAudio recording.
        
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
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(self.audio.get_sample_size(format))
                    wf.setframerate(sample_rate)
                    wf.writeframes(b''.join(frames))
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_filename)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            # Extract text and language
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            if text:
                lang_name = self.supported_languages.get(detected_language, detected_language)
                print(f"[{lang_name}] {text}")
                return text, detected_language
            else:
                print("No speech recognized")
                return None, None
                
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None, None
    
    def run_interactive_mode(self):
        """Run the application in interactive mode."""
        print("Chavr Speech Recognition App")
        print("=" * 40)
        print("Commands:")
        print("  'listen' - Listen for speech (Whisper with auto language detection)")
        print("  'quit' or 'exit' - Exit the application")
        print("=" * 40)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                elif command == 'listen':
                    text, language = self.listen()
                    if not text:
                        print("No speech recognized.")
                else:
                    print("Unknown command. Try 'listen', 'quit', or 'exit'.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def cleanup(self):
        """Clean up resources."""
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
