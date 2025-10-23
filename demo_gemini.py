#!/usr/bin/env python3
"""
Demo script for GeminiManager - Step 17 Implementation
Shows how to use the AI Chavruta partner functionality.
"""

import os
from gemini_manager import create_gemini_manager
from session import Session

def demo_gemini_manager():
    """Demonstrate GeminiManager functionality."""
    print("Chavr Phase 9: AI Chavruta Partner Demo")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠ No API key found. This is a demo of the interface.")
        print("To test with real AI responses:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        print("3. Run: source .env")
        print()
        
        # Show interface without API calls
        print("Demo: Interface without API key")
        print("-" * 30)
        
        # Create manager (will fail gracefully)
        manager = create_gemini_manager()
        if not manager:
            print("✓ Error handling works correctly")
            return
        
    else:
        print(f"✓ API key found: {api_key[:10]}...")
        
        # Create manager
        manager = create_gemini_manager()
        if not manager:
            print("✗ Failed to create GeminiManager")
            return
        
        print("✓ GeminiManager created successfully")
        
        # Demo 1: Basic Q&A
        print("\nDemo 1: Basic Q&A")
        print("-" * 20)
        response = manager.ask_question("What is a Chavruta?")
        if response:
            print(f"AI Response: {response[:100]}...")
        else:
            print("No response (expected without API key)")
        
        # Demo 2: With Sefaria context
        print("\nDemo 2: With Sefaria Context")
        print("-" * 30)
        manager.set_sefaria_context(
            reference="Genesis 1:1",
            text_content="In the beginning God created the heaven and the earth.",
            language="en"
        )
        response = manager.ask_question("What does 'bereishit' mean?")
        if response:
            print(f"AI Response: {response[:100]}...")
        else:
            print("No response (expected without API key)")
        
        # Demo 3: Session summary
        print("\nDemo 3: Session Summary")
        print("-" * 25)
        session = Session(title="Demo Study Session")
        session.set_sefaria_text("Genesis 1:1", "en")
        session.add_transcript("In the beginning God created", "en")
        session.add_transcript("What does created mean?", "en")
        session.end_session()
        
        summary = manager.generate_session_summary(session)
        if summary:
            print(f"Summary: {summary[:100]}...")
        else:
            print("No summary (expected without API key)")
    
    print("\n" + "=" * 50)
    print("✓ Step 17 Implementation Complete!")
    print("\nFeatures implemented:")
    print("- GeminiManager class with all required methods")
    print("- Context-aware prompt building")
    print("- Error handling for API failures")
    print("- Session summarization")
    print("- Text truncation and context management")
    print("- Comprehensive test suite")
    print("\nNext steps:")
    print("- Step 18: Integrate command detection in main.py")
    print("- Step 19: Build AI chat panel in gui.py")

if __name__ == "__main__":
    demo_gemini_manager()
