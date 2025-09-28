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
import wave
import threading
import time
from datetime import datetime


class AudioRecorder:
    """Simple audio recorder using PyAudio for direct microphone access."""
    
    def __init__(self, sample_rate=44100, channels=1, chunk_size=1024):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate (int): Sample rate in Hz
            channels (int): Number of audio channels
            chunk_size (int): Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.recording_thread = None
        self.audio_data = []
        
        # Check microphone permissions and availability
        self._check_microphone_availability()
    
    def _check_microphone_availability(self):
        """Check if microphone is available and accessible."""
        try:
            # Try to get default input device info
            default_device = self.audio.get_default_input_device_info()
            print(f"Default input device: {default_device['name']}")
            
            # Test if we can open a stream
            test_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            test_stream.close()
            print("✓ Microphone access verified")
            
        except Exception as e:
            print(f"✗ Microphone access error: {e}")
            print("Please check microphone permissions in System Preferences > Security & Privacy > Microphone")
            raise
    
    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.is_recording:
            print("Already recording!")
            return
        
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_recording = True
            self.audio_data = []
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()
            
            print("🔴 Recording started...")
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording and return the recorded audio data."""
        if not self.is_recording:
            print("Not currently recording!")
            return None
        
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        print("⏹️ Recording stopped")
        
        if self.audio_data:
            # Convert list of chunks to single audio data
            audio_bytes = b''.join(self.audio_data)
            return audio_bytes
        else:
            print("No audio data recorded")
            return None
    
    def _record_audio(self):
        """Internal method to record audio in a separate thread."""
        try:
            while self.is_recording:
                if self.stream:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data.append(data)
        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_recording = False
    
    def save_audio_to_file(self, audio_data, filename=None):
        """
        Save recorded audio data to a WAV file.
        
        Args:
            audio_data: Raw audio data bytes
            filename (str): Output filename (optional)
            
        Returns:
            str: Path to saved file
        """
        if not audio_data:
            print("No audio data to save")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            print(f"✓ Audio saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error saving audio: {e}")
            return None
    
    def get_audio_info(self, audio_data):
        """
        Get basic information about recorded audio.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            dict: Audio information
        """
        if not audio_data:
            return None
        
        # Convert to numpy array for analysis
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        duration = len(audio_array) / self.sample_rate
        
        info = {
            'duration_seconds': duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'samples': len(audio_array),
            'max_amplitude': np.max(np.abs(audio_array)),
            'rms': np.sqrt(np.mean(audio_array**2)),
            'file_size_bytes': len(audio_data)
        }
        
        return info
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.is_recording:
            self.stop_recording()
        
        if self.audio:
            self.audio.terminate()


class ChavrApp:
    """Main application class for Chavr speech recognition."""
    
    def __init__(self):
        """Initialize the Chavr application."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio = pyaudio.PyAudio()
        
        # Initialize audio recorder
        try:
            self.audio_recorder = AudioRecorder()
        except Exception as e:
            print(f"Warning: Could not initialize audio recorder: {e}")
            self.audio_recorder = None
        
        # Language support configuration
        self.supported_languages = {
            'en': 'English',
            'he': 'Hebrew', 
            'iw': 'Hebrew (alternative)'
        }
        self.current_language = 'en'
        
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
    
    def listen_for_speech(self, language='en', timeout=5, phrase_time_limit=5):
        """
        Listen for speech input from the microphone in specified language.
        
        Args:
            language (str): Language code ('en' for English, 'he' for Hebrew)
            timeout (int): Maximum time to wait for speech to start
            phrase_time_limit (int): Maximum time to record a phrase
            
        Returns:
            str: Recognized speech text or None if no speech detected
        """
        try:
            lang_name = self.supported_languages.get(language, language)
            print(f"Listening for {lang_name} speech...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("Processing speech...")
            # Recognize speech using Google's speech recognition with specified language
            text = self.recognizer.recognize_google(audio, language=language)
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
    
    def detect_language(self, audio):
        """
        Try to detect language by attempting recognition in multiple languages.
        
        Args:
            audio: Audio data from microphone
            
        Returns:
            tuple: (language_code, recognized_text) or (None, None) if failed
        """
        languages_to_try = ['he', 'en']  # Hebrew first, then English
        
        for lang in languages_to_try:
            try:
                text = self.recognizer.recognize_google(audio, language=lang)
                if text and text.strip():  # Ensure we got meaningful text
                    return lang, text
            except:
                continue
        
        return None, None
    
    def smart_listen(self, timeout=5, phrase_time_limit=5):
        """
        Listen and automatically detect language.
        
        Args:
            timeout (int): Maximum time to wait for speech to start
            phrase_time_limit (int): Maximum time to record a phrase
            
        Returns:
            tuple: (language_code, recognized_text) or (None, None) if failed
        """
        try:
            print("Listening for speech (auto-detecting language)...")
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("Processing speech...")
            language, text = self.detect_language(audio)
            
            if language and text:
                lang_name = self.supported_languages.get(language, language)
                print(f"[{lang_name}] {text}")
                return language, text
            else:
                print("Could not recognize speech in any supported language.")
                return None, None
                
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period.")
            return None, None
        except Exception as e:
            print(f"Error during smart listening: {e}")
            return None, None
    
    def record_audio(self, duration=5):
        """
        Record audio for a specified duration and save to file.
        
        Args:
            duration (int): Recording duration in seconds
        """
        if not self.audio_recorder:
            print("Audio recorder not available!")
            return
        
        print(f"Recording for {duration} seconds...")
        
        # Start recording
        self.audio_recorder.start_recording()
        
        # Wait for specified duration
        time.sleep(duration)
        
        # Stop recording and get audio data
        audio_data = self.audio_recorder.stop_recording()
        
        if audio_data:
            # Save to file
            filename = self.audio_recorder.save_audio_to_file(audio_data)
            
            # Get and display audio info
            info = self.audio_recorder.get_audio_info(audio_data)
            if info:
                print("\nAudio Information:")
                print(f"  Duration: {info['duration_seconds']:.2f} seconds")
                print(f"  Sample Rate: {info['sample_rate']} Hz")
                print(f"  Channels: {info['channels']}")
                print(f"  Max Amplitude: {info['max_amplitude']}")
                print(f"  RMS: {info['rms']:.2f}")
                print(f"  File Size: {info['file_size_bytes']} bytes")
            
            return filename
        else:
            print("Failed to record audio")
            return None
    
    def test_microphone(self):
        """Test microphone functionality with a short recording."""
        if not self.audio_recorder:
            print("Audio recorder not available!")
            return
        
        print("Testing microphone...")
        print("Please speak for 3 seconds...")
        
        # Record for 3 seconds
        filename = self.record_audio(duration=3)
        
        if filename:
            print(f"✓ Microphone test successful! Audio saved to: {filename}")
        else:
            print("✗ Microphone test failed!")
    
    def run_interactive_mode(self):
        """Run the application in interactive mode."""
        print("Chavr Speech Recognition App")
        print("=" * 40)
        print("Commands:")
        print("  'listen' - Listen for speech (English)")
        print("  'hebrew' - Listen for Hebrew speech")
        print("  'english' - Listen for English speech")
        print("  'smart' - Auto-detect language and listen")
        print("  'record <seconds>' - Record audio for specified duration")
        print("  'test' - Test microphone with 3-second recording")
        print("  'quit' or 'exit' - Exit the application")
        print("=" * 40)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                elif command == 'listen':
                    text = self.listen_for_speech(language='en')
                    if text:
                        print(f"English: {text}")
                    else:
                        print("No speech recognized.")
                elif command == 'hebrew':
                    text = self.listen_for_speech(language='he')
                    if text:
                        print(f"Hebrew: {text}")
                    else:
                        print("No Hebrew speech recognized.")
                elif command == 'english':
                    text = self.listen_for_speech(language='en')
                    if text:
                        print(f"English: {text}")
                    else:
                        print("No English speech recognized.")
                elif command == 'smart':
                    language, text = self.smart_listen()
                    if not language:
                        print("No speech recognized in any supported language.")
                elif command == 'test':
                    self.test_microphone()
                elif command.startswith('record '):
                    try:
                        duration = int(command.split()[1])
                        if duration > 0:
                            self.record_audio(duration)
                        else:
                            print("Duration must be positive!")
                    except (ValueError, IndexError):
                        print("Usage: record <seconds>")
                else:
                    print("Unknown command. Try 'listen', 'hebrew', 'english', 'smart', 'record <seconds>', 'test', 'quit', or 'exit'.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self.audio_recorder:
            self.audio_recorder.cleanup()
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
