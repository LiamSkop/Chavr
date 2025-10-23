#!/usr/bin/env python3
"""
Phase 7 Benchmarking Script for Chavr Enhanced Speech Recognition
Compares faster-whisper vs openai-whisper performance
"""

import os
import json
import time
import numpy as np
from datetime import datetime
from main import ChavrApp, FASTER_WHISPER_AVAILABLE

class BenchmarkHarness:
    """Simple benchmarking harness for Phase 7."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'faster_whisper_available': FASTER_WHISPER_AVAILABLE,
            'tests': []
        }
    
    def create_test_audio(self, duration=3, sample_rate=16000):
        """Create synthetic test audio (silence + noise)."""
        # Generate silence with some background noise
        samples = int(duration * sample_rate)
        noise = np.random.normal(0, 0.01, samples).astype(np.float32)
        audio_data = (noise * 32767).astype(np.int16).tobytes()
        return audio_data
    
    def benchmark_model(self, app, test_name, audio_data, expected_text=""):
        """Benchmark a single model configuration."""
        print(f"Benchmarking {test_name}...")
        
        start_time = time.time()
        text, language = app._transcribe_audio_data(audio_data)
        end_time = time.time()
        
        result = {
            'test_name': test_name,
            'expected_text': expected_text,
            'actual_text': text or "",
            'detected_language': language or "unknown",
            'processing_time': end_time - start_time,
            'audio_duration': len(audio_data) / (16000 * 2),  # 16kHz, 16-bit
            'model_type': 'faster-whisper' if app.faster_whisper_adapter else 'openai-whisper'
        }
        
        self.results['tests'].append(result)
        print(f"  Result: '{text}' (lang: {language}, time: {result['processing_time']:.2f}s)")
        
        return result
    
    def run_benchmark_suite(self):
        """Run the complete benchmark suite."""
        print("Phase 7 Benchmark Suite")
        print("=" * 50)
        
        # Create test audio samples
        test_audio_silence = self.create_test_audio(2)  # 2 seconds of silence/noise
        test_audio_short = self.create_test_audio(1)     # 1 second
        
        # Test 1: Fine-tuned Hebrew Whisper (if available)
        if FASTER_WHISPER_AVAILABLE:
            try:
                app_faster = ChavrApp(device="cpu", compute_type="int8", hebrew_only=True)
                self.benchmark_model(app_faster, "ivrit-ai-hebrew-model", test_audio_silence)
                self.benchmark_model(app_faster, "ivrit-ai-short", test_audio_short)
                app_faster.cleanup()
            except Exception as e:
                print(f"Fine-tuned Hebrew model test failed: {e}")
        
        # Test 2: OpenAI Whisper fallback
        try:
            app_openai = ChavrApp(model_size="medium")
            self.benchmark_model(app_openai, "openai-whisper-medium", test_audio_silence)
            self.benchmark_model(app_openai, "openai-whisper-short", test_audio_short)
            app_openai.cleanup()
        except Exception as e:
            print(f"OpenAI Whisper test failed: {e}")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save benchmark results to file."""
        os.makedirs('bench', exist_ok=True)
        filename = f"bench/phase7_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nBenchmark results saved to: {filename}")
        
        # Print summary
        print("\nBenchmark Summary:")
        print("-" * 30)
        for test in self.results['tests']:
            print(f"{test['test_name']}: {test['processing_time']:.2f}s")
        
        if FASTER_WHISPER_AVAILABLE:
            faster_tests = [t for t in self.results['tests'] if 'faster-whisper' in t['test_name']]
            openai_tests = [t for t in self.results['tests'] if 'openai-whisper' in t['test_name']]
            
            if faster_tests and openai_tests:
                faster_avg = np.mean([t['processing_time'] for t in faster_tests])
                openai_avg = np.mean([t['processing_time'] for t in openai_tests])
                speedup = openai_avg / faster_avg
                print(f"\nSpeedup: {speedup:.2f}x faster with faster-whisper")


def main():
    """Run the benchmark suite."""
    benchmark = BenchmarkHarness()
    benchmark.run_benchmark_suite()


if __name__ == "__main__":
    main()
