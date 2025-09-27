#!/usr/bin/env python3
"""
Chavr - Speech Recognition and Audio Processing Project
Main entry point for the application.
"""

import speech_recognition as sr
import numpy as np
import pyaudio
import sys
import os


class ChavrApp:
    """Main application class for Chavr speech recognition."""
    
    def __init__(self):
        """Initialize the Chavr application."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio = pyaudio.PyAudio()
        
        # Print available audio devices
        self.print_audio_devices()
        
        # Adjust for ambient noise
        self.calibrate_microphone()
    
    def print_audio_devices(self):
        """Print available audio input devices."""
        print("Available audio input devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']}")
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        print("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated!")
    
    def listen_for_speech(self, timeout=5, phrase_time_limit=5):
        """
        Listen for speech input from the microphone.
        
        Args:
            timeout (int): Maximum time to wait for speech to start
            phrase_time_limit (int): Maximum time to record a phrase
            
        Returns:
            str: Recognized speech text or None if no speech detected
        """
        try:
            print("Listening for speech...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("Processing speech...")
            # Recognize speech using Google's speech recognition
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from speech recognition service; {e}")
            return None
    
    def process_audio_data(self, audio_data):
        """
        Process audio data using numpy for analysis.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            dict: Audio analysis results
        """
        if audio_data is None:
            return None
        
        # Convert to numpy array for analysis
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Basic audio analysis
        analysis = {
            'length': len(audio_array),
            'max_amplitude': np.max(np.abs(audio_array)),
            'rms': np.sqrt(np.mean(audio_array**2)),
            'mean': np.mean(audio_array),
            'std': np.std(audio_array)
        }
        
        return analysis
    
    def run_interactive_mode(self):
        """Run the application in interactive mode."""
        print("Chavr Speech Recognition App")
        print("=" * 40)
        print("Commands:")
        print("  'listen' - Listen for speech")
        print("  'quit' or 'exit' - Exit the application")
        print("=" * 40)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                elif command == 'listen':
                    text = self.listen_for_speech()
                    if text:
                        print(f"Recognized: {text}")
                    else:
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
