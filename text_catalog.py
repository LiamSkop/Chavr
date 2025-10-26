#!/usr/bin/env python3
"""
Text Catalog - Smart text database with fuzzy search for easy text discovery.
Organizes texts by category, tracks popularity, and provides intelligent search.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime


@dataclass
class TextEntry:
    """Represents a single text in the catalog."""
    name: str  # English name
    hebrew_name: str  # Hebrew name
    category: str  # Torah, Mishnah, Talmud, etc.
    subcategory: Optional[str] = None
    popularity: int = 1  # 1-5 stars
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    tags: List[str] = field(default_factory=list)
    sample_references: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        """Ensure popularity is within valid range."""
        self.popularity = max(1, min(5, self.popularity))


class TextCatalog:
    """Smart text catalog with fuzzy search capabilities."""
    
    # Popular Jewish texts database
    TEXTS_DATABASE = [
        # TORAH (Chumash)
        TextEntry(
            name="Genesis",
            hebrew_name="Bereshit",
            category="Torah",
            subcategory="Chumash",
            popularity=5,
            difficulty="beginner",
            tags=["creation", "patriarchs", "joseph", "abraham"],
            sample_references=["Genesis 1", "Genesis 1:1", "Genesis 12", "Genesis 37"],
            description="First book of Torah - Creation and patriarchs"
        ),
        TextEntry(
            name="Exodus",
            hebrew_name="Shemot",
            category="Torah",
            subcategory="Chumash",
            popularity=5,
            difficulty="beginner",
            tags=["moses", "passover", "ten commandments", "red sea"],
            sample_references=["Exodus 12", "Exodus 20"],
            description="Second book of Torah - Story of Moses and Exodus"
        ),
        TextEntry(
            name="Leviticus",
            hebrew_name="Vayikra",
            category="Torah",
            subcategory="Chumash",
            popularity=3,
            difficulty="intermediate",
            tags=["sacrifices", "holiness", "priests"],
            sample_references=["Leviticus 19"],
            description="Third book of Torah - Laws of holiness"
        ),
        TextEntry(
            name="Numbers",
            hebrew_name="Bamidbar",
            category="Torah",
            subcategory="Chumash",
            popularity=3,
            difficulty="intermediate",
            tags=["wanderings", "census", "desert"],
            sample_references=["Numbers 1", "Numbers 13"],
            description="Fourth book of Torah - 40 years in desert"
        ),
        TextEntry(
            name="Deuteronomy",
            hebrew_name="Devarim",
            category="Torah",
            subcategory="Chumash",
            popularity=4,
            difficulty="beginner",
            tags=["shema", "law", "moses farewell"],
            sample_references=["Deuteronomy 6", "Deuteronomy 6:4"],
            description="Fifth book of Torah - Moses' farewell address"
        ),
        
        # NAVI (Prophets)
        TextEntry(
            name="Isaiah",
            hebrew_name="Yeshayahu",
            category="Torah",
            subcategory="Neviim",
            popularity=4,
            difficulty="advanced",
            tags=["prophecy", "messiah", "redemption"],
            sample_references=["Isaiah 6", "Isaiah 40", "Isaiah 53"],
            description="Major prophetic book - Redemption and messiah"
        ),
        
        # MISHNAH
        TextEntry(
            name="Pirkei Avot",
            hebrew_name="Avot",
            category="Mishnah",
            subcategory="Ethics",
            popularity=5,
            difficulty="beginner",
            tags=["ethics", "wisdom", "sayings", "fathers"],
            sample_references=["Pirkei Avot 1", "Pirkei Avot 1:1"],
            description="Ethics of the Fathers - Wisdom of the sages"
        ),
        TextEntry(
            name="Berakhot",
            hebrew_name="Berakhot",
            category="Mishnah",
            subcategory="Blessings",
            popularity=4,
            difficulty="intermediate",
            tags=["blessings", "prayer", "daily practice"],
            sample_references=["Berakhot 1", "Berakhot 1:1"],
            description="Laws of blessings and prayers"
        ),
        TextEntry(
            name="Shabbat",
            hebrew_name="Shabbat",
            category="Mishnah",
            subcategory="Shabbat",
            popularity=5,
            difficulty="intermediate",
            tags=["shabbat", "laws", "daily practice"],
            sample_references=["Shabbat 1", "Shabbat 7"],
            description="Laws of Shabbat observance"
        ),
        
        # HALACHA (Practical Law)
        TextEntry(
            name="Chayei Adam",
            hebrew_name="Chayei Adam",
            category="Halacha",
            subcategory="Daily Practice",
            popularity=4,
            difficulty="intermediate",
            tags=["daily", "practical", "halacha"],
            sample_references=["Chayei Adam 12", "Chayei Adam 1"],
            description="Practical guide to daily Jewish law"
        ),
        TextEntry(
            name="Mishnah Berurah",
            hebrew_name="Mishnah Berurah",
            category="Halacha",
            subcategory="Daily Practice",
            popularity=5,
            difficulty="intermediate",
            tags=["shulchan aruch", "daily", "practical"],
            sample_references=["Mishnah Berurah 1"],
            description="Commentary on daily Jewish practice"
        ),
        
        # COMMENTARIES
        TextEntry(
            name="Rashi",
            hebrew_name="Rashi",
            category="Commentary",
            subcategory="Torah",
            popularity=5,
            difficulty="beginner",
            tags=["commentary", "french", "explanation"],
            sample_references=["Rashi on Genesis", "Rashi on Genesis 1"],
            description="Classic Torah commentary by Rashi (11th century France)"
        ),
        TextEntry(
            name="Ramban",
            hebrew_name="Nachmanides",
            category="Commentary",
            subcategory="Torah",
            popularity=4,
            difficulty="intermediate",
            tags=["commentary", "spain", "mysticism"],
            sample_references=["Ramban on Genesis", "Ramban on Genesis 1"],
            description="Deep Torah commentary by Nachmanides (13th century Spain)"
        ),
        TextEntry(
            name="Mishneh Torah",
            hebrew_name="Mishneh Torah",
            category="Halacha",
            subcategory="Code of Law",
            popularity=5,
            difficulty="advanced",
            tags=["rambam", "law", "codification"],
            sample_references=["Mishneh Torah, Laws of Torah Study 1"],
            description="Comprehensive code of Jewish law by Maimonides"
        ),
    ]
    
    def __init__(self, progress_tracker=None):
        """
        Initialize text catalog.
        
        Args:
            progress_tracker: Optional ProgressTracker for recent/popular tracking
        """
        self.entries = self.TEXTS_DATABASE.copy()
        self.progress_tracker = progress_tracker
        
        # User access tracking (for recent/popular)
        self.access_history_file = Path("sessions/text_access_history.json")
        self.access_history = self._load_access_history()
    
    def _load_access_history(self) -> Dict:
        """Load user's text access history."""
        if not self.access_history_file.exists():
            return {'accesses': [], 'popularity': {}}
        
        try:
            with open(self.access_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'accesses': [], 'popularity': {}}
    
    def _save_access_history(self):
        """Save user's text access history."""
        try:
            self.access_history_file.parent.mkdir(exist_ok=True, parents=True)
            with open(self.access_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.access_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving access history: {e}")
    
    def record_text_access(self, text_name: str):
        """
        Record that user accessed a text.
        
        Args:
            text_name: Name of text accessed
        """
        now = datetime.now().isoformat()
        
        # Add to recent accesses (keep last 50)
        self.access_history['accesses'].append({
            'text': text_name,
            'timestamp': now
        })
        if len(self.access_history['accesses']) > 50:
            self.access_history['accesses'] = self.access_history['accesses'][-50:]
        
        # Update popularity count
        if text_name not in self.access_history['popularity']:
            self.access_history['popularity'][text_name] = 0
        self.access_history['popularity'][text_name] += 1
        
        self._save_access_history()
    
    def search(self, query: str, limit: int = 10) -> List[Tuple[TextEntry, float]]:
        """
        Search for texts using fuzzy matching.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of (TextEntry, score) tuples sorted by score (highest first)
        """
        if not query or len(query) < 2:
            # Return popular texts if query is too short
            return self.get_popular_entries(limit)
        
        query_lower = query.lower()
        results = []
        
        for entry in self.entries:
            score = self._score_result(query_lower, entry)
            if score > 0:
                results.append((entry, score))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def _score_result(self, query: str, entry: TextEntry) -> float:
        """
        Score how well an entry matches a query.
        
        Args:
            query: Search query (lowercase)
            entry: TextEntry to score
            
        Returns:
            Score (0-200)
        """
        score = 0
        
        # Exact match: +100
        if query == entry.name.lower():
            score += 100
        if query == entry.hebrew_name.lower():
            score += 100
        
        # Hebrew name match: +90
        if entry.hebrew_name.lower() in query or query in entry.hebrew_name.lower():
            score += 90
        
        # Starts with: +50
        if entry.name.lower().startswith(query):
            score += 50
        if entry.hebrew_name.lower().startswith(query):
            score += 50
        
        # Contains: +30
        if query in entry.name.lower():
            score += 30
        if query in entry.hebrew_name.lower():
            score += 30
        
        # Tag match: +20 per matching tag
        for tag in entry.tags:
            if query in tag.lower() or tag.lower() in query:
                score += 20
        
        # Description match: +10
        if query in entry.description.lower():
            score += 10
        
        # Popularity bonus: +5 per star
        score += entry.popularity * 5
        
        # User popularity bonus (from access history): +10 per access
        user_popularity = self.access_history.get('popularity', {}).get(entry.name, 0)
        score += user_popularity * 10
        
        return score
    
    def get_popular_entries(self, limit: int = 10) -> List[Tuple[TextEntry, float]]:
        """
        Get most popular texts.
        
        Returns:
            List of (TextEntry, popularity_score) tuples
        """
        results = [(entry, entry.popularity) for entry in self.entries]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get_recent_entries(self, limit: int = 10) -> List[TextEntry]:
        """
        Get recently accessed texts.
        
        Returns:
            List of TextEntry objects
        """
        accesses = self.access_history.get('accesses', [])
        
        # Get unique recent texts (most recent first)
        recent_texts = {}
        for access in reversed(accesses):
            text_name = access['text']
            if text_name not in recent_texts:
                recent_texts[text_name] = access['timestamp']
        
        # Find matching entries
        recent_entries = []
        for text_name in list(recent_texts.keys())[:limit]:
            # Try to find exact match
            for entry in self.entries:
                if entry.name == text_name or text_name in entry.name:
                    recent_entries.append(entry)
                    break
        
        return recent_entries
    
    def get_by_category(self) -> Dict[str, List[TextEntry]]:
        """
        Get all texts organized by category.
        
        Returns:
            Dict mapping category names to lists of TextEntry
        """
        categories = {}
        
        for entry in self.entries:
            if entry.category not in categories:
                categories[entry.category] = []
            categories[entry.category].append(entry)
        
        return categories
    
    def get_entry_by_name(self, name: str) -> Optional[TextEntry]:
        """
        Get a specific text entry by name.
        
        Args:
            name: Text name
            
        Returns:
            TextEntry or None if not found
        """
        for entry in self.entries:
            if entry.name == name or entry.hebrew_name == name:
                return entry
        
        # Try partial match
        name_lower = name.lower()
        for entry in self.entries:
            if name_lower in entry.name.lower() or name_lower in entry.hebrew_name.lower():
                return entry
        
        return None


def test_text_catalog():
    """Test the text catalog."""
    print("Testing TextCatalog...\n")
    
    catalog = TextCatalog()
    
    # Test search
    print("1. Searching for 'gen':")
    results = catalog.search("gen", limit=5)
    for entry, score in results:
        print(f"   {entry.name} ({entry.hebrew_name}) - Score: {score:.1f}")
    
    print("\n2. Searching for 'bereshit':")
    results = catalog.search("bereshit", limit=3)
    for entry, score in results:
        print(f"   {entry.name} ({entry.hebrew_name}) - Score: {score:.1f}")
    
    print("\n3. Searching for 'creation':")
    results = catalog.search("creation", limit=3)
    for entry, score in results:
        print(f"   {entry.name} - Tags: {entry.tags}")
    
    print("\n4. Popular texts:")
    popular = catalog.get_popular_entries(limit=5)
    for entry, score in popular:
        print(f"   {entry.name} - Popularity: {entry.popularity}⭐")
    
    print("\n5. Texts by category:")
    by_category = catalog.get_by_category()
    for category, entries in by_category.items():
        print(f"   {category}: {len(entries)} texts")


if __name__ == "__main__":
    test_text_catalog()

