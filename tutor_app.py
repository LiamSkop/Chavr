#!/usr/bin/env python3
"""
Chavr AI Tutor - Simplified application for AI-powered Torah study.
Stateless Q&A focused on text learning and AI interactions.
"""

import os
from datetime import datetime
from typing import Optional, Callable, Dict, List, Any

from sefaria_manager import SefariaManager

# AI integration
try:
    from gemini_manager import create_gemini_manager
    GEMINI_AVAILABLE = True
except (ImportError, ValueError):
    GEMINI_AVAILABLE = False
    print("Warning: Gemini API not available. AI features disabled.")


class TutorApp:
    """
    Stateless Chavr application for AI tutoring.
    No session tracking - just Q&A with current text context.
    """
    
    def __init__(self, question_callback: Optional[Callable] = None):
        """
        Initialize the AI Tutor application.
        
        Args:
            question_callback: Optional callback for AI responses
        """
        self.question_callback = question_callback
        
        # Current text context (in-memory only)
        self.current_text: Optional[Dict[str, Any]] = None  # {reference, content, language}
        
        # Conversation history (in-memory only, for context)
        self.conversation_history: List[Dict[str, str]] = []
        
        # Sefaria integration
        self.sefaria_manager = SefariaManager()
        
        # AI tutor (Gemini)
        if GEMINI_AVAILABLE:
            self.gemini_manager = create_gemini_manager()
            if self.gemini_manager:
                print("✓ AI Tutor initialized")
        else:
            self.gemini_manager = None
            print("⚠ AI Tutor disabled (no API key)")
    
    def ask_question(self, question: str) -> Optional[str]:
        """
        Ask the AI tutor a question.
        
        Args:
            question: The question to ask
            
        Returns:
            AI response or None if unavailable
        """
        if not self.gemini_manager:
            return "AI tutor is not available. Please set GEMINI_API_KEY in .env file."
        
        try:
            # Build context from current text and conversation history
            context_transcripts = []
            
            # Add current text context if available
            if self.current_text:
                context_transcripts.append({
                    'text': f"Current text: {self.current_text.get('reference', 'Unknown')}",
                    'language': self.current_text.get('language', 'en'),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Add recent conversation history (last 5 interactions)
            for interaction in self.conversation_history[-5:]:
                qa_text = f"Q: {interaction.get('question', '')}\nA: {interaction.get('response', '')}"
                context_transcripts.append({
                    'text': qa_text,
                    'language': 'en',
                    'timestamp': interaction.get('timestamp', datetime.now().isoformat())
                })
            
            # Set context in AI manager
            self.gemini_manager.add_transcript_context(context_transcripts)
            
            if self.current_text:
                self.gemini_manager.set_sefaria_context(
                    self.current_text.get('reference', 'Unknown'),
                    self.current_text.get('content', ''),
                    self.current_text.get('language', 'en')
                )
            
            # Ask the question
            response = self.gemini_manager.ask_question(question)
            
            if response:
                # Store interaction in conversation history
                self.conversation_history.append({
                    'question': question,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep only last 20 interactions to limit memory
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                # Callback for GUI
                if self.question_callback:
                    self.question_callback('ai', response, datetime.now())
                
                return response
            
        except KeyError as e:
            error_msg = f"Missing key in data structure: {str(e)}"
            print(f"⚠ {error_msg}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            return error_msg
        except Exception as e:
            error_msg = f"AI error: {str(e)}"
            print(f"⚠ {error_msg}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            return error_msg
        
        return "No response from AI tutor."
    
    def load_sefaria_text(self, reference: str, language: str = 'en') -> bool:
        """
        Load a Sefaria text for context.
        
        Args:
            reference: Text reference (e.g., "Genesis 1:1")
            language: 'en' or 'he'
            
        Returns:
            True if successful
        """
        try:
            data = self.sefaria_manager.fetch_text(reference, language)
            if data:
                # Extract text content
                text_content = self.sefaria_manager.extract_text_content(data)
                
                # Store in memory
                self.current_text = {
                    'reference': reference,
                    'content': text_content,
                    'language': language,
                    'loaded_at': datetime.now().isoformat()
                }
                
                # Update AI context
                if self.gemini_manager:
                    self.gemini_manager.set_sefaria_context(reference, text_content, language)
                
                print(f"✓ Loaded text: {reference} ({language})")
                return True
            else:
                print(f"✗ Could not load text: {reference}")
                return False
                
        except Exception as e:
            print(f"✗ Error loading text: {e}")
            return False
    
    def get_current_text_content(self) -> Optional[str]:
        """Get the current Sefaria text content."""
        if not self.current_text:
            return None
        return self.current_text.get('content')
    
    def get_current_text_reference(self) -> Optional[str]:
        """Get the current Sefaria text reference."""
        if not self.current_text:
            return None
        return self.current_text.get('reference')
