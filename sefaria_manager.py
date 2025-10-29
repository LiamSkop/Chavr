#!/usr/bin/env python3
"""
Sefaria Text Integration Manager for Chavr
Handles fetching, caching, and managing Sefaria texts for study sessions.
"""

import os
import json
import requests
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Callable, List
import re
from text_catalog import TextCatalog, TextEntry


class SefariaManager:
    """Manages Sefaria text fetching, caching, and error handling."""
    
    def __init__(self, cache_dir: str = "sefaria_cache"):
        """
        Initialize the Sefaria manager.
        
        Args:
            cache_dir (str): Directory to store cached texts
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Sefaria API configuration
        self.base_url = "https://www.sefaria.org/api/texts"
        self.timeout = 10  # seconds
        
        # Cache for last text reference
        self.last_text_file = self.cache_dir / "last_text.json"
        
        # Error handling
        self.error_callback: Optional[Callable[[str], None]] = None
        
        # Text catalog for smart search
        self.text_catalog = TextCatalog()
        
        print(f"✓ SefariaManager initialized with cache directory: {self.cache_dir}")
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback function for error notifications."""
        self.error_callback = callback
    
    def _sanitize_reference(self, ref: str) -> str:
        """
        Convert text reference to filesystem-safe filename.
        
        Args:
            ref (str): Text reference like "Genesis 1:1" or "Bava Metzia 21a"
            
        Returns:
            str: Sanitized filename
        """
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', ref)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.lower()
    
    def _get_cache_filename(self, reference: str, language: str) -> Path:
        """Get cache filename for a reference and language."""
        sanitized_ref = self._sanitize_reference(reference)
        return self.cache_dir / f"{sanitized_ref}_{language}.json"
    
    def _is_cached(self, reference: str, language: str) -> bool:
        """
        Check if text is cached locally.
        
        Args:
            reference (str): Text reference
            language (str): Language code ('en' or 'he')
            
        Returns:
            bool: True if cached
        """
        cache_file = self._get_cache_filename(reference, language)
        return cache_file.exists()
    
    def _load_from_cache(self, reference: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Load text from local cache.
        
        Args:
            reference (str): Text reference
            language (str): Language code
            
        Returns:
            dict: Cached text data or None if not found
        """
        cache_file = self._get_cache_filename(reference, language)
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✓ Loaded text from cache: {reference} ({language})")
            return data
        except Exception as e:
            print(f"Error loading from cache: {e}")
            return None
    
    def _save_to_cache(self, reference: str, language: str, text_data: Dict[str, Any]) -> None:
        """
        Save text to local cache.
        
        Args:
            reference (str): Text reference
            language (str): Language code
            text_data (dict): Text data to cache
        """
        cache_file = self._get_cache_filename(reference, language)
        
        try:
            # Add metadata to cached data
            cached_data = {
                'reference': reference,
                'language': language,
                'cached_at': datetime.now().isoformat(),
                'text_data': text_data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Cached text: {reference} ({language})")
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def _fetch_from_api(self, reference: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Fetch text from Sefaria API.
        
        Args:
            reference (str): Text reference
            language (str): Language code
            
        Returns:
            dict: Text data or None if failed
        """
        try:
            print(f"Fetching from Sefaria API: {reference} ({language})")
            
            # Convert reference to Sefaria format
            # Sefaria API accepts spaces, but we need to handle colons and other special chars
            sefaria_ref = reference.replace(":", ".")
            
            # URL encode the reference to handle spaces and special characters properly
            import urllib.parse
            sefaria_ref = urllib.parse.quote(sefaria_ref, safe='.')
            
            # Prepare API URL with correct format
            url = f"{self.base_url}/{sefaria_ref}"
            params = {'lang': language}
            
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                headers={'User-Agent': 'Chavr/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check for error in response
                if 'error' in data:
                    error_msg = f"Text not found: {data['error']}"
                    print(f"✗ {error_msg}")
                    if self.error_callback:
                        self.error_callback(error_msg)
                    return None
                print(f"✓ Successfully fetched from API: {reference}")
                return data
            else:
                error_msg = f"API error {response.status_code}: {response.text[:200]}"
                print(f"✗ {error_msg}")
                if self.error_callback:
                    self.error_callback(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            error_msg = f"API timeout for {reference}"
            print(f"✗ {error_msg}")
            if self.error_callback:
                self.error_callback(error_msg)
            return None
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            print(f"✗ {error_msg}")
            if self.error_callback:
                self.error_callback(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error fetching {reference}: {e}"
            print(f"✗ {error_msg}")
            if self.error_callback:
                self.error_callback(error_msg)
            return None
    
    def fetch_text(self, reference: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Fetch text from Sefaria API or cache.
        
        Args:
            reference (str): Text reference (e.g., "Genesis 1:1")
            language (str): Language code ('en' or 'he')
            
        Returns:
            dict: Text data or None if failed
        """
        if not reference or not reference.strip():
            if self.error_callback:
                self.error_callback("Please enter a text reference")
            return None
        
        reference = reference.strip()
        
        # Check cache first
        if self._is_cached(reference, language):
            cached_data = self._load_from_cache(reference, language)
            if cached_data:
                return cached_data.get('text_data')
        
        # Fetch from API
        text_data = self._fetch_from_api(reference, language)
        
        # Cache successful responses
        if text_data:
            self._save_to_cache(reference, language, text_data)
            # Record text access for recent/popular tracking
            self.text_catalog.record_text_access(reference)
            return text_data
        
        return None
    
    def fetch_text_async(self, reference: str, language: str, callback: Callable[[Optional[Dict[str, Any]]], None]):
        """
        Fetch text asynchronously in a background thread.
        
        Args:
            reference (str): Text reference
            language (str): Language code
            callback (callable): Function to call with result
        """
        def fetch_worker():
            result = self.fetch_text(reference, language)
            callback(result)
        
        thread = threading.Thread(target=fetch_worker, daemon=True)
        thread.start()
    
    def save_last_text(self, reference: str, language: str) -> None:
        """
        Save last studied text reference.
        
        Args:
            reference (str): Text reference
            language (str): Language code
        """
        try:
            last_text_data = {
                'reference': reference,
                'language': language,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.last_text_file, 'w', encoding='utf-8') as f:
                json.dump(last_text_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved last text: {reference} ({language})")
        except Exception as e:
            print(f"Error saving last text: {e}")
    
    def load_last_text(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Load last studied text reference.
        
        Returns:
            tuple: (reference, language) or (None, None) if not found
        """
        try:
            if not self.last_text_file.exists():
                return None, None
            
            with open(self.last_text_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            reference = data.get('reference')
            language = data.get('language')
            
            if reference and language:
                print(f"✓ Loaded last text: {reference} ({language})")
                return reference, language
            
        except Exception as e:
            print(f"Error loading last text: {e}")
        
        return None, None
    
    def get_cached_texts(self) -> list:
        """
        Get list of all cached texts.
        
        Returns:
            list: List of cached text references
        """
        cached_texts = []
        
        for cache_file in self.cache_dir.glob("*_en.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cached_texts.append({
                    'reference': data.get('reference'),
                    'language': 'en',
                    'cached_at': data.get('cached_at')
                })
            except Exception:
                continue
        
        for cache_file in self.cache_dir.glob("*_he.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cached_texts.append({
                    'reference': data.get('reference'),
                    'language': 'he',
                    'cached_at': data.get('cached_at')
                })
            except Exception:
                continue
        
        return sorted(cached_texts, key=lambda x: x.get('cached_at', ''), reverse=True)
    
    def clear_cache(self) -> int:
        """
        Clear all cached texts.
        
        Returns:
            int: Number of files deleted
        """
        deleted_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name != "last_text.json":  # Keep last text file
                try:
                    cache_file.unlink()
                    deleted_count += 1
                except Exception:
                    continue
        
        print(f"✓ Cleared {deleted_count} cached texts")
        return deleted_count
    
    def search_texts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Smart search for texts using TextCatalog.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of text dictionaries with metadata
        """
        results = self.text_catalog.search(query, limit=limit)
        
        # Convert to dictionary format
        return [
            {
                'name': entry.name,
                'hebrew_name': entry.hebrew_name,
                'category': entry.category,
                'subcategory': entry.subcategory,
                'description': entry.description,
                'popularity': entry.popularity,
                'tags': entry.tags,
                'score': score
            }
            for entry, score in results
        ]
    
    def get_popular_texts(self, limit: int = 10) -> List[Dict]:
        """
        Get most popular texts.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of popular text dictionaries
        """
        results = self.text_catalog.get_popular_entries(limit=limit)
        
        return [
            {
                'name': entry.name,
                'hebrew_name': entry.hebrew_name,
                'category': entry.category,
                'description': entry.description,
                'popularity': entry.popularity,
                'tags': entry.tags
            }
            for entry, score in results
        ]
    
    def get_recent_texts(self, limit: int = 10) -> List[Dict]:
        """
        Get recently accessed texts.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of recent text dictionaries
        """
        entries = self.text_catalog.get_recent_entries(limit=limit)
        
        return [
            {
                'name': entry.name,
                'hebrew_name': entry.hebrew_name,
                'category': entry.category,
                'description': entry.description
            }
            for entry in entries
        ]
    
    def get_categories(self) -> Dict[str, List[Dict]]:
        """
        Get texts organized by category.
        
        Returns:
            Dict mapping category names to lists of text dictionaries
        """
        by_category = self.text_catalog.get_by_category()
        
        return {
            category: [
                {
                    'name': entry.name,
                    'hebrew_name': entry.hebrew_name,
                    'description': entry.description,
                    'popularity': entry.popularity
                }
                for entry in entries
            ]
            for category, entries in by_category.items()
        }
    
    def load_text_by_name(self, text_name: str, language: str = "en") -> Optional[str]:
        """
        Load text using catalog entry name instead of exact reference.
        
        Args:
            text_name: Name of text from catalog
            language: 'en' or 'he'
            
        Returns:
            Sample reference string or None
        """
        entry = self.text_catalog.get_entry_by_name(text_name)
        
        if not entry:
            return None
        
        # Return first sample reference
        if entry.sample_references:
            return entry.sample_references[0]
        
        # Fallback to name
        return entry.name
    
    def extract_text_content(self, data: Dict[str, Any]) -> str:
        """
        Extract plain text content from Sefaria API response.
        
        Args:
            data: Sefaria API response dictionary
            
        Returns:
            Extracted text content as string
        """
        if not data:
            return ""
        
        # Handle different response formats from Sefaria
        text_parts = []
        
        def extract_text_helper(obj):
            """Recursively extract text from nested structure."""
            if isinstance(obj, str):
                # Remove HTML tags
                import re
                clean_text = re.sub(r'<[^>]+>', '', obj)
                if clean_text.strip():
                    text_parts.append(clean_text.strip())
            elif isinstance(obj, dict):
                # Check for 'he' or 'text' keys
                if 'he' in obj:
                    extract_text_helper(obj['he'])
                elif 'text' in obj:
                    extract_text_helper(obj['text'])
                # Recurse through all values
                for value in obj.values():
                    extract_text_helper(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_helper(item)
        
        extract_text_helper(data)
        
        # Join all text parts with paragraph breaks
        result = "\n\n".join(text_parts)
        
        # Clean up extra whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def search_text_names(self, query: str, limit: int = 10) -> list:
        """
        Search for text names using a predefined list of common Jewish texts.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            list: List of matching text names
        """
        if not query or len(query) < 2:
            return []
        
        # Common Jewish texts for autocomplete
        common_texts = [
            # Tanakh
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Samuel", "Kings", "Isaiah", "Jeremiah", 
            "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", 
            "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", 
            "Zechariah", "Malachi", "Psalms", "Proverbs", "Job", 
            "Song of Songs", "Ruth", "Lamentations", "Ecclesiastes", 
            "Esther", "Daniel", "Ezra", "Nehemiah", "Chronicles",
            
            # Mishnah
            "Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim",
            "Yoma", "Sukkah", "Beitzah", "Rosh Hashanah", "Taanit",
            "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
            "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin",
            "Bava Kamma", "Bava Metzia", "Bava Batra", "Sanhedrin",
            "Makkot", "Shevuot", "Avodah Zarah", "Horayot", "Zevachim",
            "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah",
            "Keritot", "Meilah", "Tamid", "Niddah",
            
            # Major Halachic Works
            "Mishneh Torah", "Shulchan Arukh", "Aruch HaShulchan",
            "Mishnah Berurah", "Kitzur Shulchan Arukh", "Chayei Adam",
            "Chochmat Adam", "Shulchan Aruch HaRav", "Ben Ish Chai",
            "Magen Avraham", "Taz", "Shach", "Levush", "Bach",
            
            # Major Commentaries
            "Rashi", "Rambam", "Ramban", "Rashba", "Ritva", "Ran",
            "Tosafot", "Rabbeinu Bachya", "Ibn Ezra", "Sforno",
            "Radak", "Metzudat David", "Malbim", "Ohr HaChaim",
            "Kli Yakar", "Siftei Chachamim", "Gur Aryeh", "Maharsha",
            
            # Kabbalah/Chassidut
            "Zohar", "Tanya", "Likutei Moharan", "Noam Elimelech",
            "Sefat Emet", "Kedushat Levi", "Mei HaShiloach",
            "Torah Ohr", "Likutei Torah", "Siddur HaRashash",
            
            # Midrash
            "Midrash Rabbah", "Tanchuma", "Pirkei DeRabbi Eliezer",
            "Midrash Tehillim", "Yalkut Shimoni", "Sifra", "Sifrei",
            "Mechilta", "Pesikta Rabbati", "Avot DeRabbi Natan",
            
            # Ethics/Mussar
            "Pirkei Avot", "Ethics of the Fathers", "Mesillat Yesharim",
            "Orchot Tzaddikim", "Chovot HaLevavot", "Sha'arei Teshuvah",
            "Sefer HaChinuch", "Derech Hashem", "Tomer Devorah",
            "Reshit Chochmah", "Chovot HaTalmidim", "Michtav MeEliyahu",
            
            # Other Important Works
            "Kuzari", "Moreh Nevuchim", "Guide for the Perplexed",
            "Sefer HaIkkarim", "Emunot v'Deot", "Nefesh HaChaim",
            "Tiferet Yisrael", "Maharal", "Netziv", "Chatam Sofer",
            "Chazon Ish", "Rav Kook", "Rav Soloveitchik"
        ]
        
        query_lower = query.lower()
        matches = []
        
        for text in common_texts:
            if query_lower in text.lower():
                matches.append(text)
                if len(matches) >= limit:
                    break
        
        return matches


def test_sefaria_manager():
    """Test function for SefariaManager."""
    print("Testing SefariaManager...")
    
    manager = SefariaManager()
    
    # Test basic functionality
    test_ref = "Genesis 1:1"
    
    print(f"\nTesting fetch_text for {test_ref}:")
    result = manager.fetch_text(test_ref, "en")
    
    if result:
        print("✓ Successfully fetched text")
        print(f"Text preview: {str(result)[:100]}...")
    else:
        print("✗ Failed to fetch text")
    
    # Test caching
    print(f"\nTesting cache for {test_ref}:")
    if manager._is_cached(test_ref, "en"):
        print("✓ Text is cached")
    else:
        print("✗ Text is not cached")
    
    # Test last text persistence
    print(f"\nTesting last text persistence:")
    manager.save_last_text(test_ref, "en")
    last_ref, last_lang = manager.load_last_text()
    print(f"Last text: {last_ref} ({last_lang})")


if __name__ == "__main__":
    test_sefaria_manager()
