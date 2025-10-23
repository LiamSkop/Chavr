#!/usr/bin/env python3
"""Test script for GeminiManager."""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_manager import GeminiManager, create_gemini_manager
from session import Session


def test_basic_qa():
    """Test basic Q&A functionality."""
    print("\n=== Test 1: Basic Question ===")
    manager = create_gemini_manager()
    if not manager:
        print("✗ Cannot test - API key not set")
        return False
    
    response = manager.ask_question("What is a Chavruta?")
    if response:
        print(f"✓ Response received: {response[:100]}...")
        return True
    else:
        print("✗ No response received")
        return False


def test_sefaria_context():
    """Test Q&A with Sefaria context."""
    print("\n=== Test 2: With Sefaria Context ===")
    manager = create_gemini_manager()
    if not manager:
        print("✗ Cannot test - API key not set")
        return False
    
    # Set Sefaria context
    manager.set_sefaria_context(
        reference="Genesis 1:1",
        text_content="In the beginning God created the heaven and the earth. And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
        language="en"
    )
    
    response = manager.ask_question("What does 'bereishit' mean here?")
    if response:
        print(f"✓ Response received: {response[:100]}...")
        return True
    else:
        print("✗ No response received")
        return False


def test_transcript_context():
    """Test Q&A with transcript context."""
    print("\n=== Test 3: With Transcript Context ===")
    manager = create_gemini_manager()
    if not manager:
        print("✗ Cannot test - API key not set")
        return False
    
    # Add transcript context
    manager.add_transcript_context([
        {'text': 'We are studying the creation story', 'language': 'en'},
        {'text': 'Why does it start with the letter Bet?', 'language': 'en'},
        {'text': 'The letter Bet represents blessing', 'language': 'en'}
    ])
    
    response = manager.ask_question("Can you explain the significance of the letter Bet?")
    if response:
        print(f"✓ Response received: {response[:100]}...")
        return True
    else:
        print("✗ No response received")
        return False


def test_session_summary():
    """Test session summarization."""
    print("\n=== Test 4: Session Summary ===")
    manager = create_gemini_manager()
    if not manager:
        print("✗ Cannot test - API key not set")
        return False
    
    # Create mock session
    session = Session(title="Test Study Session")
    session.set_sefaria_text("Genesis 1:1", "en")
    session.add_transcript("In the beginning God created", "en")
    session.add_transcript("What does created mean?", "en")
    session.add_transcript("Does it mean ex nihilo?", "en")
    session.add_transcript("Yes, creation from nothing", "en")
    session.end_session()
    
    summary = manager.generate_session_summary(session)
    if summary:
        print(f"✓ Summary generated: {summary[:100]}...")
        return True
    else:
        print("✗ No summary generated")
        return False


def test_error_handling():
    """Test error handling."""
    print("\n=== Test 5: Error Handling ===")
    
    # Test with invalid API key
    try:
        manager = GeminiManager("invalid_key")
        print("✗ Should have failed with invalid key")
        return False
    except Exception as e:
        print(f"✓ Correctly failed with invalid key: {str(e)[:50]}...")
    
    # Test with empty question
    manager = create_gemini_manager()
    if manager:
        response = manager.ask_question("")
        if response is None:
            print("✓ Correctly handled empty question")
            return True
        else:
            print("✗ Should have returned None for empty question")
            return False
    
    return True


def test_text_truncation():
    """Test text truncation functionality."""
    print("\n=== Test 6: Text Truncation ===")
    manager = create_gemini_manager()
    if not manager:
        print("✗ Cannot test - API key not set")
        return False
    
    # Test with very long text
    long_text = "This is a very long text. " * 200  # Much longer than 2000 chars
    
    manager.set_sefaria_context(
        reference="Test",
        text_content=long_text,
        language="en"
    )
    
    # Check if text was truncated
    if len(manager.current_sefaria_text['content']) <= 2000:
        print("✓ Text correctly truncated")
        return True
    else:
        print("✗ Text not properly truncated")
        return False


def main():
    """Run all tests."""
    print("GeminiManager Test Suite")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("✗ GEMINI_API_KEY not set")
        print("Please set your API key:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        print("3. Run: source .env")
        return
    
    print(f"✓ API key found: {api_key[:10]}...")
    
    # Run tests
    tests = [
        test_basic_qa,
        test_sefaria_context,
        test_transcript_context,
        test_session_summary,
        test_error_handling,
        test_text_truncation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! GeminiManager is ready to use.")
    else:
        print("✗ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
