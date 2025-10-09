#!/usr/bin/env python3
"""
Session storage manager for Chavr speech recognition sessions.
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from session import Session


class SessionStorage:
    """Manages storage and retrieval of transcription sessions."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the session storage manager.
        
        Args:
            sessions_dir (str): Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Create backup directory
        self.backup_dir = self.sessions_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def save_session(self, session: Session) -> str:
        """
        Save a session to disk.
        
        Args:
            session (Session): The session to save
            
        Returns:
            str: The filename where the session was saved
        """
        # Generate filename from timestamp
        filename = f"{session.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{session.session_id[:8]}.json"
        filepath = self.sessions_dir / filename
        
        # Create backup if file exists
        if filepath.exists():
            backup_path = self.backup_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            shutil.copy2(filepath, backup_path)
        
        # Save session data
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save session: {e}")
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load a session by ID.
        
        Args:
            session_id (str): The session ID to load
            
        Returns:
            Session or None if not found
        """
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('session_id') == session_id:
                    return Session.from_dict(data)
            except Exception:
                continue  # Skip corrupted files
        
        return None
    
    def load_session_by_filename(self, filename: str) -> Optional[Session]:
        """
        Load a session by filename.
        
        Args:
            filename (str): The filename to load
            
        Returns:
            Session or None if not found
        """
        filepath = self.sessions_dir / filename
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception as e:
            print(f"Error loading session {filename}: {e}")
            return None
    
    def list_sessions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Args:
            limit (int, optional): Maximum number of sessions to return
            
        Returns:
            List of session metadata dictionaries
        """
        sessions = []
        
        for filepath in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Add file info
                data['filename'] = filepath.name
                data['file_size'] = filepath.stat().st_size
                sessions.append(data)
                
                if limit and len(sessions) >= limit:
                    break
                    
            except Exception:
                continue  # Skip corrupted files
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id (str): The session ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('session_id') == session_id:
                    # Move to backup before deleting
                    backup_path = self.backup_dir / f"deleted_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filepath.name}"
                    shutil.move(str(filepath), str(backup_path))
                    return True
            except Exception:
                continue
        
        return False
    
    def search_sessions(self, keyword: str, 
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None,
                       min_duration: Optional[float] = None,
                       max_duration: Optional[float] = None,
                       languages: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search sessions with various filters.
        
        Args:
            keyword (str): Search term for transcripts
            date_from (datetime, optional): Start date filter
            date_to (datetime, optional): End date filter
            min_duration (float, optional): Minimum duration in seconds
            max_duration (float, optional): Maximum duration in seconds
            languages (List[str], optional): Language filter
            
        Returns:
            List of matching sessions with search results
        """
        results = []
        keyword_lower = keyword.lower() if keyword else ""
        
        for session_data in self.list_sessions():
            session = Session.from_dict(session_data)
            
            # Apply filters
            if date_from and session.timestamp < date_from:
                continue
            if date_to and session.timestamp > date_to:
                continue
            if min_duration and session.duration < min_duration:
                continue
            if max_duration and session.duration > max_duration:
                continue
            if languages and not any(lang in session.get_languages_used() for lang in languages):
                continue
            
            # Search transcripts if keyword provided
            matches = []
            if keyword_lower:
                matches = session.search_transcripts(keyword)
                if not matches:
                    continue
            
            results.append({
                'session': session,
                'session_data': session_data,
                'matches': matches,
                'match_count': len(matches)
            })
        
        # Sort by relevance (number of matches) then by date
        results.sort(key=lambda x: (-x['match_count'], -x['session'].timestamp.timestamp()))
        
        return results
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all sessions.
        
        Returns:
            Dictionary with session statistics
        """
        sessions = self.list_sessions()
        
        if not sessions:
            return {
                'total_sessions': 0,
                'total_transcripts': 0,
                'total_words': 0,
                'total_duration': 0.0,
                'languages_used': [],
                'date_range': None
            }
        
        total_transcripts = sum(s.get('transcript_count', 0) for s in sessions)
        total_words = sum(s.get('total_words', 0) for s in sessions)
        total_duration = sum(s.get('duration', 0) for s in sessions)
        
        # Get all languages used
        all_languages = set()
        for session in sessions:
            all_languages.update(session.get('languages_used', []))
        
        # Get date range
        timestamps = [datetime.fromisoformat(s['timestamp']) for s in sessions]
        date_range = {
            'earliest': min(timestamps),
            'latest': max(timestamps)
        }
        
        return {
            'total_sessions': len(sessions),
            'total_transcripts': total_transcripts,
            'total_words': total_words,
            'total_duration': total_duration,
            'languages_used': sorted(list(all_languages)),
            'date_range': date_range
        }
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Clean up old backup files.
        
        Args:
            days_to_keep (int): Number of days to keep backups
            
        Returns:
            int: Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for filepath in self.backup_dir.glob("*"):
            if filepath.stat().st_mtime < cutoff_date.timestamp():
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception:
                    continue
        
        return deleted_count
