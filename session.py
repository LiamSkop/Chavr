#!/usr/bin/env python3
"""
Session data model for Chavr AI Tutor sessions.
Simplified to focus on learning, not transcription.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class Session:
    """Represents a learning session with AI tutor."""
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize a new study session.
        
        Args:
            title (str, optional): Custom title for the session
        """
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration = 0.0  # Will be calculated when session ends
        self.title = title or self._generate_title()
        
        # Sefaria text being studied
        self.sefaria_text: Optional[Dict[str, Any]] = None
        self.text_reference: Optional[str] = None
        
        # AI tutor interactions
        self.ai_interactions: List[Dict[str, Any]] = []
        self.ai_summary: Optional[str] = None
        
        # Learning analytics (for future features)
        self.concepts_explored: List[str] = []
        self.notes: str = ""
    
    def _generate_title(self) -> str:
        """Generate an automatic title based on timestamp."""
        return f"Study Session - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def end_session(self) -> None:
        """Mark the session as ended and calculate duration."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
    
    def get_ai_interaction_count(self) -> int:
        """Get the number of AI interactions."""
        return len(self.ai_interactions)
    
    def has_ai_summary(self) -> bool:
        """Check if session has an AI summary."""
        return self.ai_summary is not None
    
    def set_sefaria_text(self, reference: str, language: str, text_content: Optional[str] = None) -> None:
        """
        Set the Sefaria text reference for this session.
        
        Args:
            reference (str): Text reference (e.g., "Genesis 1:1")
            language (str): Language code ('en' or 'he')
            text_content (str, optional): The actual text content
        """
        self.text_reference = reference
        self.sefaria_text = {
            'reference': reference,
            'language': language,
            'content': text_content,
            'loaded_at': datetime.now().isoformat()
        }
    
    def get_sefaria_text_info(self) -> Optional[Dict[str, Any]]:
        """
        Get Sefaria text information for this session.
        
        Returns:
            dict: Sefaria text info or None if not set
        """
        return self.sefaria_text
    
    def has_sefaria_text(self) -> bool:
        """
        Check if this session has Sefaria text associated.
        
        Returns:
            bool: True if Sefaria text is set
        """
        return self.sefaria_text is not None
    
    def add_ai_interaction(self, question: str, response: str, timestamp: Optional[datetime] = None):
        """
        Add an AI Q&A interaction to the session.
        
        Args:
            question (str): The user's question
            response (str): The AI's response
            timestamp (datetime, optional): When the interaction occurred
        """
        interaction = {
            'question': question,
            'response': response,
            'timestamp': (timestamp or datetime.now()).isoformat()
        }
        self.ai_interactions.append(interaction)
    
    def set_ai_summary(self, summary: str):
        """
        Set the AI-generated session summary.
        
        Args:
            summary (str): The session summary
        """
        self.ai_summary = summary
    
    def get_ai_summary(self) -> Optional[str]:
        """Get the AI summary if available."""
        return self.ai_summary
    
    def add_concept(self, concept: str):
        """
        Add a concept explored in this session.
        
        Args:
            concept (str): The concept name
        """
        if concept not in self.concepts_explored:
            self.concepts_explored.append(concept)
    
    def get_concepts_explored(self) -> List[str]:
        """Get list of concepts explored in this session."""
        return self.concepts_explored
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'session_id': self.session_id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'text_reference': self.text_reference,
            'sefaria_text': self.sefaria_text,
            'ai_summary': self.ai_summary,
            'ai_interactions': self.ai_interactions,
            'ai_interaction_count': self.get_ai_interaction_count(),
            'concepts_explored': self.concepts_explored,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create from dictionary (JSON deserialization)."""
        session = cls(title=data.get('title'))
        session.session_id = data.get('session_id', session.session_id)
        session.start_time = datetime.fromisoformat(data.get('start_time', session.start_time.isoformat()))
        
        if data.get('end_time'):
            session.end_time = datetime.fromisoformat(data['end_time'])
        
        session.duration = data.get('duration', 0.0)
        session.text_reference = data.get('text_reference')
        session.sefaria_text = data.get('sefaria_text')
        session.ai_summary = data.get('ai_summary')
        session.ai_interactions = data.get('ai_interactions', [])
        session.concepts_explored = data.get('concepts_explored', [])
        session.notes = data.get('notes', '')
        
        return session
    
    def __str__(self) -> str:
        """String representation of the session."""
        duration_str = f"{self.duration:.1f}s" if self.duration > 0 else "ongoing"
        interactions = self.get_ai_interaction_count()
        return f"Session '{self.title}' ({interactions} interactions, {duration_str})"
    
    def __repr__(self) -> str:
        """Detailed representation of the session."""
        return (f"Session(id={self.session_id[:8]}..., "
                f"title='{self.title}', "
                f"interactions={self.get_ai_interaction_count()}, "
                f"duration={self.duration:.1f}s)")
