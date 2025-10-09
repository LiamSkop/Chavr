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
            'transcripts': [t.to_dict() for t in self.transcripts]
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
