#!/usr/bin/env python3
"""
Chavr AI Tutor - Simplified application for AI-powered Torah study.
Focuses on text learning and AI Q&A without speech transcription.
"""

import os
from datetime import datetime
from typing import Optional, Callable
from session import Session
from storage import SessionStorage
from sefaria_manager import SefariaManager

# Phase 9: AI integration
try:
    from gemini_manager import create_gemini_manager
    GEMINI_AVAILABLE = True
except (ImportError, ValueError):
    GEMINI_AVAILABLE = False
    print("Warning: Gemini API not available. AI features disabled.")


class TutorApp:
    """
    Simplified Chavr application for AI tutoring.
    No speech recognition - just text display and AI Q&A.
    """
    
    def __init__(self, question_callback: Optional[Callable] = None):
        """
        Initialize the AI Tutor application.
        
        Args:
            question_callback: Optional callback for AI responses
        """
        # Session management
        self.storage = SessionStorage()
        self.current_session: Optional[Session] = None
        self.question_callback = question_callback
        
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
    
    def start_session(self, title: Optional[str] = None) -> Session:
        """
        Start a new study session.
        
        Args:
            title: Optional session title
            
        Returns:
            Session: The new session
        """
        session = Session(title=title)
        self.current_session = session
        print(f"✓ Started new session: {session.title}")
        return session
    
    def end_current_session(self) -> Optional[Session]:
        """
        End the current session and save it.
        
        Returns:
            Session if one was active, None otherwise
        """
        if not self.current_session:
            print("No active session to end")
            return None
        
        # Generate summary if AI is available and session has interactions
        if self.gemini_manager and self.current_session.get_ai_interaction_count() >= 3:
            print("Generating session summary...")
            try:
                summary = self.gemini_manager.generate_session_summary(self.current_session)
                if summary:
                    self.current_session.set_ai_summary(summary)
                    print("✓ Session summary generated")
            except Exception as e:
                print(f"⚠ Could not generate summary: {e}")
        
        # End session
        self.current_session.end_session()
        
        # Save session
        session_id = self.storage.save_session(self.current_session)
        print(f"✓ Session saved: {session_id}")
        print(f"  Duration: {self.current_session.duration:.1f}s")
        print(f"  AI Interactions: {self.current_session.get_ai_interaction_count()}")
        
        ended_session = self.current_session
        self.current_session = None
        
        return ended_session
    
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
        
        if not self.current_session:
            return "No active session. Please start a session first."
        
        try:
            # Get context from current session
            context_transcripts = []
            if self.current_session.sefaria_text:
                # Provide Sefaria context if available
                text_info = self.current_session.sefaria_text
                context_transcripts.append({
                    'text': f"Current text: {text_info.get('reference', 'Unknown')}",
                    'timestamp': text_info.get('loaded_at', datetime.now().isoformat())
                })
            
            # Add recent AI interactions for context
            for interaction in self.current_session.ai_interactions[-5:]:  # Last 5 interactions
                context_transcripts.append(interaction)
            
            # Set context in AI manager
            self.gemini_manager.add_transcript_context(context_transcripts)
            if self.current_session.sefaria_text:
                self.gemini_manager.set_sefaria_context(
                    self.current_session.text_reference or "Unknown",
                    self.current_session.sefaria_text.get('content', ''),
                    self.current_session.sefaria_text.get('language', 'en')
                )
            
            # Ask the question
            response = self.gemini_manager.ask_question(question)
            
            if response:
                # Save interaction to session
                self.current_session.add_ai_interaction(question, response)
                
                # Callback for GUI
                if self.question_callback:
                    self.question_callback('ai', response, datetime.now())
                
                return response
            
        except Exception as e:
            error_msg = f"AI error: {str(e)}"
            print(f"⚠ {error_msg}")
            return error_msg
        
        return "No response from AI tutor."
    
    def load_sefaria_text(self, reference: str, language: str = 'en') -> bool:
        """
        Load a Sefaria text for the current session.
        
        Args:
            reference: Text reference (e.g., "Genesis 1:1")
            language: 'en' or 'he'
            
        Returns:
            True if successful
        """
        if not self.current_session:
            print("No active session. Start a session first.")
            return False
        
        try:
            data = self.sefaria_manager.fetch_text(reference, language)
            if data:
                # Extract text content
                text_content = self.sefaria_manager.extract_text_content(data)
                
                # Store in session
                self.current_session.set_sefaria_text(reference, language, text_content)
                
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
        if not self.current_session or not self.current_session.sefaria_text:
            return None
        return self.current_session.sefaria_text.get('content')
    
    def get_studied_texts(self) -> list:
        """
        Get list of recently studied texts.
        
        Returns:
            List of text references
        """
        sessions = self.storage.list_sessions()
        texts = {}
        
        for session in sessions:
            if session.sefaria_text:
                ref = session.sefaria_text.get('reference')
                if ref:
                    texts[ref] = texts.get(ref, 0) + 1
        
        # Return sorted by frequency
        return sorted(texts.items(), key=lambda x: x[1], reverse=True)
    
    def get_stats(self) -> dict:
        """
        Get application statistics.
        
        Returns:
            Dictionary with stats
        """
        sessions = self.storage.list_sessions()
        
        total_sessions = len(sessions)
        total_interactions = sum(s.get_ai_interaction_count() for s in sessions)
        total_duration = sum(s.duration for s in sessions)
        
        return {
            'total_sessions': total_sessions,
            'total_interactions': total_interactions,
            'total_duration_hours': total_duration / 3600,
            'avg_interactions_per_session': total_interactions / total_sessions if total_sessions > 0 else 0
        }

