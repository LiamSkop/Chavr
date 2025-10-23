#!/usr/bin/env python3
"""Test AI integration in main.py - Step 18"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ChavrApp


def test_command_detection():
    """Test AI command detection."""
    print("\n=== Test 1: Command Detection ===")
    app = ChavrApp()
    
    # Test various trigger phrases
    test_cases = [
        ("Chavr, what does this mean?", True),
        ("Chaver, explain this", True),
        ("Hey Chavr, help me", True),
        ("Hey Chaver, what is this?", True),
        ("Chavr explain", True),
        ("Chaver please help", True),
        ("Just talking", False),
        ("This is a regular sentence", False),
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = app._detect_ai_command(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")
        if result == expected:
            passed += 1
    
    print(f"Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_question_extraction():
    """Test question extraction."""
    print("\n=== Test 2: Question Extraction ===")
    app = ChavrApp()
    
    test_cases = [
        ("Chavr, what is this?", "what is this?"),
        ("Hey Chaver, help me", "help me"),
        ("Chavr explain this", "explain this"),
        ("Hey Chavr what does it mean", "what does it mean"),
        ("Chaver, can you help?", "can you help?"),
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = app._extract_question(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> '{result}' (expected '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_gemini_initialization():
    """Test GeminiManager initialization."""
    print("\n=== Test 3: GeminiManager Initialization ===")
    app = ChavrApp()
    
    # Check if gemini_manager exists
    if hasattr(app, 'gemini_manager'):
        if app.gemini_manager:
            print("✓ GeminiManager initialized successfully")
            return True
        else:
            print("⚠ GeminiManager is None (no API key - expected in test environment)")
            return True  # This is expected if no API key
    else:
        print("✗ GeminiManager attribute not found")
        return False


def test_ai_queue_system():
    """Test AI queue and worker system."""
    print("\n=== Test 4: AI Queue System ===")
    app = ChavrApp()
    
    # Check if AI queue exists
    if hasattr(app, 'ai_queue'):
        print("✓ AI queue initialized")
    else:
        print("✗ AI queue not found")
        return False
    
    # Check if worker thread attributes exist
    if hasattr(app, 'ai_worker_thread') and hasattr(app, 'ai_processing'):
        print("✓ AI worker thread attributes initialized")
        return True
    else:
        print("✗ AI worker thread attributes not found")
        return False


def test_session_ai_methods():
    """Test Session AI-related methods."""
    print("\n=== Test 5: Session AI Methods ===")
    from session import Session
    from datetime import datetime
    
    session = Session(title="Test Session")
    
    # Test add_ai_interaction
    session.add_ai_interaction("Test question", "Test response")
    if session.get_ai_interaction_count() == 1:
        print("✓ add_ai_interaction() works")
    else:
        print("✗ add_ai_interaction() failed")
        return False
    
    # Test set_ai_summary
    session.set_ai_summary("Test summary")
    if session.has_ai_summary():
        print("✓ set_ai_summary() and has_ai_summary() work")
    else:
        print("✗ set_ai_summary() failed")
        return False
    
    # Test serialization
    session_dict = session.to_dict()
    if 'ai_summary' in session_dict and 'ai_interactions' in session_dict:
        print("✓ Session serialization includes AI data")
    else:
        print("✗ Session serialization missing AI data")
        return False
    
    # Test deserialization
    new_session = Session.from_dict(session_dict)
    if new_session.has_ai_summary() and new_session.get_ai_interaction_count() == 1:
        print("✓ Session deserialization preserves AI data")
        return True
    else:
        print("✗ Session deserialization failed")
        return False


def main():
    """Run all tests."""
    print("Step 18: AI Integration Tests")
    print("=" * 50)
    
    tests = [
        test_command_detection,
        test_question_extraction,
        test_gemini_initialization,
        test_ai_queue_system,
        test_session_ai_methods
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Step 18 integration is working.")
    else:
        print("✗ Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

