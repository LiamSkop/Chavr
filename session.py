#!/usr/bin/env python3
"""
Session data model for Chavr speech recognition sessions.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class TranscriptEntry:
    """Represents a single transcript entry within a session."""
    
    def __init__(self, text: str, language: str, timestamp: datetime):
        """
        Initialize a transcript entry.
        
        Args:
            text (str): The transcribed text
            language (str): Detected language code
            timestamp (datetime): When the transcription occurred
        """
        self.text = text.strip()
        self.language = language
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'text': self.text,
            'language': self.language,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptEntry':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            text=data['text'],
            language=data['language'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class Session:
    """Represents a complete transcription session."""
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize a new session.
        
        Args:
            title (str, optional): Custom title for the session
        """
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.duration = 0.0  # Will be calculated when session ends
        self.transcripts: List[TranscriptEntry] = []
        self.title = title or self._generate_title()
        self.end_time: Optional[datetime] = None
        
        # Phase 8: Sefaria text integration
        self.sefaria_text: Optional[Dict[str, Any]] = None
        
        # Phase 9: AI integration
        self.ai_summary: Optional[str] = None
        self.ai_interactions: List[Dict[str, Any]] = []
    
    def _generate_title(self) -> str:
        """Generate an automatic title based on timestamp."""
        return f"Study Session - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def add_transcript(self, text: str, language: str, timestamp: Optional[datetime] = None) -> None:
        """
        Add a transcript entry to the session.
        
        Args:
            text (str): The transcribed text
            language (str): Detected language code
            timestamp (datetime, optional): When the transcription occurred (defaults to now)
        """
        if not text.strip():
            return  # Skip empty transcripts
        
        entry = TranscriptEntry(
            text=text,
            language=language,
            timestamp=timestamp or datetime.now()
        )
        self.transcripts.append(entry)
    
    def end_session(self) -> None:
        """Mark the session as ended and calculate duration."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.timestamp).total_seconds()
    
    def get_transcript_count(self) -> int:
        """Get the number of transcript entries."""
        return len(self.transcripts)
    
    def get_total_words(self) -> int:
        """Get the total word count across all transcripts."""
        return sum(len(transcript.text.split()) for transcript in self.transcripts)
    
    def get_languages_used(self) -> List[str]:
        """Get list of languages used in this session."""
        languages = set(transcript.language for transcript in self.transcripts)
        return sorted(list(languages))
    
    def search_transcripts(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for keyword in transcripts.
        
        Args:
            keyword (str): The search term
            
        Returns:
            List of matching transcript entries with context
        """
        keyword_lower = keyword.lower()
        matches = []
        
        for i, transcript in enumerate(self.transcripts):
            if keyword_lower in transcript.text.lower():
                # Get context (previous and next transcript)
                context_start = max(0, i - 1)
                context_end = min(len(self.transcripts), i + 2)
                context = self.transcripts[context_start:context_end]
                
                matches.append({
                    'transcript': transcript,
                    'context': context,
                    'match_index': i
                })
        
        return matches
    
    def set_sefaria_text(self, reference: str, language: str) -> None:
        """
        Set the Sefaria text reference for this session.
        
        Args:
            reference (str): Text reference (e.g., "Genesis 1:1")
            language (str): Language code ('en' or 'he')
        """
        self.sefaria_text = {
            'reference': reference,
            'language': language,
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
    
    def get_ai_interaction_count(self) -> int:
        """Get the number of AI interactions."""
        return len(self.ai_interactions)
    
    def has_ai_summary(self) -> bool:
        """Check if session has an AI summary."""
        return self.ai_summary is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'session_id': self.session_id,
            'title': self.title,
            'timestamp': self.timestamp.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'transcript_count': self.get_transcript_count(),
            'total_words': self.get_total_words(),
            'languages_used': self.get_languages_used(),
            'transcripts': [t.to_dict() for t in self.transcripts],
            'sefaria_text': self.sefaria_text,  # Phase 8: Include Sefaria text metadata
            'ai_summary': self.ai_summary,  # Phase 9: Include AI summary
            'ai_interactions': self.ai_interactions,  # Phase 9: Include AI Q&A
            'ai_interaction_count': self.get_ai_interaction_count()  # Phase 9: Interaction count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create from dictionary (JSON deserialization)."""
        session = cls(title=data.get('title'))
        session.session_id = data['session_id']
        session.timestamp = datetime.fromisoformat(data['timestamp'])
        session.duration = data.get('duration', 0.0)
        
        if data.get('end_time'):
            session.end_time = datetime.fromisoformat(data['end_time'])
        
        # Load transcripts
        session.transcripts = [
            TranscriptEntry.from_dict(t) for t in data.get('transcripts', [])
        ]
        
        # Phase 8: Load Sefaria text metadata (backward compatible)
        session.sefaria_text = data.get('sefaria_text', None)
        
        # Phase 9: Load AI data (backward compatible)
        session.ai_summary = data.get('ai_summary', None)
        session.ai_interactions = data.get('ai_interactions', [])
        
        return session
    
    def __str__(self) -> str:
        """String representation of the session."""
        duration_str = f"{self.duration:.1f}s" if self.duration > 0 else "ongoing"
        return f"Session '{self.title}' ({self.get_transcript_count()} transcripts, {duration_str})"
    
    def __repr__(self) -> str:
        """Detailed representation of the session."""
        return (f"Session(id={self.session_id[:8]}..., "
                f"title='{self.title}', "
                f"transcripts={self.get_transcript_count()}, "
                f"duration={self.duration:.1f}s)")
