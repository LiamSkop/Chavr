#!/usr/bin/env python3
"""
Progress Tracker - Learning analytics and progress tracking for Chavr AI Tutor.
Tracks texts studied, concepts explored, and mastery over time.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ProgressTracker:
    """Tracks learning progress across sessions."""
    
    def __init__(self, data_dir: str = "sessions"):
        """
        Initialize the progress tracker.
        
        Args:
            data_dir: Directory where sessions are stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Progress data file
        self.progress_file = self.data_dir / "progress.json"
        self.progress_data = self._load_progress_data()
    
    def _load_progress_data(self) -> Dict:
        """Load progress data from file."""
        if not self.progress_file.exists():
            return {
                'texts_studied': {},
                'concepts_explored': {},
                'session_history': []
            }
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading progress data: {e}")
            return {
                'texts_studied': {},
                'concepts_explored': {},
                'session_history': []
            }
    
    def _save_progress_data(self):
        """Save progress data to file."""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress data: {e}")
    
    def update_from_session(self, session):
        """
        Update progress data from a session.
        
        Args:
            session: Session object with ai_interactions and concepts_explored
        """
        # Update texts studied
        if session.text_reference:
            text_ref = session.text_reference
            if text_ref not in self.progress_data['texts_studied']:
                self.progress_data['texts_studied'][text_ref] = {
                    'study_count': 0,
                    'first_studied': None,
                    'last_studied': None,
                    'total_duration': 0
                }
            
            text_data = self.progress_data['texts_studied'][text_ref]
            text_data['study_count'] += 1
            if text_data['first_studied'] is None:
                text_data['first_studied'] = session.start_time.isoformat()
            text_data['last_studied'] = datetime.now().isoformat()
            text_data['total_duration'] += session.duration
        
        # Update concepts explored
        for concept in session.concepts_explored:
            concept_lower = concept.lower()
            if concept_lower not in self.progress_data['concepts_explored']:
                self.progress_data['concepts_explored'][concept_lower] = {
                    'first_studied': datetime.now().isoformat(),
                    'last_studied': datetime.now().isoformat(),
                    'review_count': 0,
                    'confidence': 'new'
                }
            
            concept_data = self.progress_data['concepts_explored'][concept_lower]
            concept_data['last_studied'] = datetime.now().isoformat()
            concept_data['review_count'] += 1
            
            # Update confidence based on review count
            if concept_data['review_count'] >= 10:
                concept_data['confidence'] = 'mastered'
            elif concept_data['review_count'] >= 5:
                concept_data['confidence'] = 'confident'
            elif concept_data['review_count'] >= 2:
                concept_data['confidence'] = 'familiar'
        
        # Add to session history (keep last 100 sessions)
        self.progress_data['session_history'].append({
            'session_id': session.session_id,
            'start_time': session.start_time.isoformat(),
            'duration': session.duration,
            'text_reference': session.text_reference,
            'interactions': session.get_ai_interaction_count(),
            'concepts': session.concepts_explored
        })
        
        # Keep only last 100 sessions
        if len(self.progress_data['session_history']) > 100:
            self.progress_data['session_history'] = self.progress_data['session_history'][-100:]
        
        # Save progress
        self._save_progress_data()
    
    def get_texts_studied(self, days: int = 30) -> List[Tuple[str, Dict]]:
        """
        Get texts studied in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of (text_reference, stats) tuples sorted by frequency
        """
        cutoff = datetime.now() - timedelta(days=days)
        texts = []
        
        for text_ref, stats in self.progress_data['texts_studied'].items():
            last_studied = datetime.fromisoformat(stats['last_studied'])
            if last_studied > cutoff:
                texts.append((text_ref, stats))
        
        # Sort by study count (most studied first)
        return sorted(texts, key=lambda x: x[1]['study_count'], reverse=True)
    
    def get_concepts_explored(self) -> List[Tuple[str, Dict]]:
        """
        Get all concepts explored with confidence levels.
        
        Returns:
            List of (concept, stats) tuples sorted by confidence
        """
        concepts = list(self.progress_data['concepts_explored'].items())
        
        # Sort by confidence: mastered > confident > familiar > new
        confidence_order = {'mastered': 0, 'confident': 1, 'familiar': 2, 'new': 3}
        
        return sorted(
            concepts,
            key=lambda x: (
                confidence_order.get(x[1]['confidence'], 3),
                x[1]['review_count']
            ),
            reverse=True
        )
    
    def get_concepts_for_review(self) -> List[str]:
        """
        Get concepts that should be reviewed based on spaced repetition.
        
        Returns:
            List of concept names that need review
        """
        review_concepts = []
        now = datetime.now()
        
        for concept, stats in self.progress_data['concepts_explored'].items():
            last_studied = datetime.fromisoformat(stats['last_studied'])
            days_since = (now - last_studied).days
            
            # Spaced repetition intervals: 1, 3, 7, 14, 30 days
            intervals = [1, 3, 7, 14, 30]
            
            if days_since in intervals:
                review_concepts.append(concept)
            elif days_since > 30 and days_since % 7 == 0:
                # After 30 days, review weekly
                review_concepts.append(concept)
        
        return review_concepts
    
    def get_recommendations(self) -> Dict[str, List[str]]:
        """
        Get personalized study recommendations.
        
        Returns:
            Dict with 'review', 'continue', 'explore' keys
        """
        recommendations = {
            'review': [],  # Concepts to review
            'continue': [],  # Texts to continue studying
            'explore': []  # Suggested texts to explore
        }
        
        # Concepts to review (spaced repetition)
        review_concepts = self.get_concepts_for_review()
        if review_concepts:
            recommendations['review'] = review_concepts[:5]
        
        # Texts studied recently (continue with)
        recent_texts = self.get_texts_studied(days=7)
        for text_ref, stats in recent_texts:
            if stats['study_count'] < 5:  # Haven't studied enough
                recommendations['continue'].append(text_ref)
        
        # Suggested texts to explore (random if no history)
        all_texts = list(self.progress_data['texts_studied'].keys())
        if len(all_texts) < 5:
            # Suggest common texts if user is new
            suggestions = [
                "Genesis 1", "Exodus 20", "Deuteronomy 6",
                "Rashi on Genesis 1", "Chayei Adam 12"
            ]
            recommendations['explore'].extend(suggestions)
        
        return recommendations
    
    def get_stats_summary(self) -> Dict:
        """
        Get overall learning statistics.
        
        Returns:
            Dict with summary stats
        """
        total_sessions = len(self.progress_data['session_history'])
        total_texts = len(self.progress_data['texts_studied'])
        total_concepts = len(self.progress_data['concepts_explored'])
        
        total_duration = sum(
            s.get('duration', 0) for s in self.progress_data['session_history']
        )
        
        mastered_concepts = sum(
            1 for c in self.progress_data['concepts_explored'].values()
            if c['confidence'] == 'mastered'
        )
        
        return {
            'total_sessions': total_sessions,
            'total_texts_studied': total_texts,
            'total_concepts': total_concepts,
            'mastered_concepts': mastered_concepts,
            'total_study_hours': total_duration / 3600,
            'avg_session_duration_minutes': (total_duration / total_sessions / 60) if total_sessions > 0 else 0
        }
    
    def export_progress_report(self) -> str:
        """
        Generate a formatted progress report.
        
        Returns:
            Formatted markdown report
        """
        stats = self.get_stats_summary()
        texts = self.get_texts_studied()
        concepts = self.get_concepts_explored()
        recommendations = self.get_recommendations()
        
        report = f"""# Learning Progress Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview

- Total Sessions: {stats['total_sessions']}
- Texts Studied: {stats['total_texts_studied']}
- Concepts Explored: {stats['total_concepts']}
- Mastered Concepts: {stats['mastered_concepts']}
- Total Study Time: {stats['total_study_hours']:.1f} hours

## Recently Studied Texts (Last 30 Days)

"""
        
        for text_ref, text_stats in texts[:10]:
            report += f"- **{text_ref}**: {text_stats['study_count']} sessions\n"
        
        report += "\n## Concepts Explored\n\n"
        
        for concept, concept_stats in concepts[:15]:
            confidence_emoji = {
                'mastered': '✅',
                'confident': '💪',
                'familiar': '📚',
                'new': '🌱'
            }.get(concept_stats['confidence'], '📝')
            
            report += f"- {confidence_emoji} **{concept}**: {concept_stats['confidence']} ({concept_stats['review_count']} reviews)\n"
        
        if recommendations['review']:
            report += "\n## Recommended Reviews\n\n"
            for concept in recommendations['review']:
                report += f"- Review: {concept}\n"
        
        if recommendations['continue']:
            report += "\n## Continue Your Learning\n\n"
            for text in recommendations['continue'][:3]:
                report += f"- Continue studying: {text}\n"
        
        if recommendations['explore']:
            report += "\n## Explore New Texts\n\n"
            for text in recommendations['explore'][:3]:
                report += f"- Explore: {text}\n"
        
        return report


def test_progress_tracker():
    """Test the progress tracker."""
    from session import Session
    
    tracker = ProgressTracker()
    
    # Create a test session
    session = Session()
    session.text_reference = "Genesis 1:1"
    session.concepts_explored = ["bereshit", "creation", "rashi"]
    session.add_ai_interaction("What does bereshit mean?", "Bereshit means...")
    session.add_ai_interaction("What does Rashi say?", "Rashi explains...")
    session.end_session()
    session.duration = 300  # 5 minutes
    
    # Update tracker
    tracker.update_from_session(session)
    
    # Get stats
    stats = tracker.get_stats_summary()
    print(f"\nStats: {stats}")
    
    texts = tracker.get_texts_studied()
    print(f"\nRecent texts: {texts}")
    
    concepts = tracker.get_concepts_explored()
    print(f"\nConcepts: {concepts}")
    
    report = tracker.export_progress_report()
    print(f"\nReport:\n{report}")


if __name__ == "__main__":
    test_progress_tracker()

