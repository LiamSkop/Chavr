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
        For Chayei Adam, uses structured extraction to preserve Klal/Siman structure.
        
        Args:
            data: Sefaria API response dictionary
            
        Returns:
            Extracted text content as string
        """
        if not data:
            return ""
        
        # Check if this is Chayei Adam with Klal/Siman structure
        if self._detect_chayei_adam_structure(data):
            # Use structured extraction and flatten for backward compatibility
            structured = self.extract_structured_content(data)
            if structured and structured.get('simanim'):
                # Join Simanim with double newline for separation
                text_parts = [siman.get('text', '') for siman in structured['simanim']]
                return "\n\n".join(text_parts)
        
        # Fall back to flat extraction for other texts
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
    
    def _detect_chayei_adam_structure(self, data: Dict[str, Any]) -> bool:
        """
        Check if text uses Klal/Siman structure (Chayei Adam).
        
        Args:
            data: Sefaria API response dictionary
            
        Returns:
            True if text has Klal/Siman structure
        """
        if not data:
            return False
        
        # Check sectionNames for ["Klal", "Siman"]
        section_names = data.get('sectionNames', [])
        if section_names == ["Klal", "Siman"]:
            return True
        
        # Check book name
        book = data.get('book', '')
        index_title = data.get('indexTitle', '')
        if 'chayei adam' in book.lower() or 'chayei adam' in index_title.lower():
            return True
        
        # Check if text array structure suggests Simanim
        text_array = data.get('text', [])
        he_array = data.get('he', [])
        if isinstance(text_array, list) and len(text_array) > 0:
            # If text is a list of strings, likely Simanim
            if all(isinstance(item, str) for item in text_array):
                return True
        if isinstance(he_array, list) and len(he_array) > 0:
            if all(isinstance(item, str) for item in he_array):
                return True
        
        return False
    
    def _parse_siman_numbers(self, text: str, language: str = 'he') -> Optional[int]:
        """
        Extract Siman number from text. Looks for markers anywhere in the text.
        
        Args:
            text: Text content that may contain Siman marker
            language: Language code ('he' or 'en')
            
        Returns:
            Siman number if found, None otherwise
        """
        import re
        
        if language == 'he':
            # Hebrew patterns: "סימן ח'", "(סימן ח')", "סי' ח'", "סימן ח':"
            # More comprehensive patterns to catch markers anywhere in text
            # Priority: Look for Siman markers at start of paragraph or after "דין"
            patterns = [
                # At start of text or after "דין" - most likely to be a Siman marker
                r'(?:^|דין\s+)[^:]*?סימן\s+([א-ת]+)[\'׳]',  # דין...סימן ח'
                r'(?:^|דין\s+)[^:]*?\(סימן\s+([א-ת]+)[\'׳]\)',  # דין...(סימן ח')
                r'(?:^|דין\s+)[^:]*?סי[\'׳]\s*([א-ת]+)[\'׳]',  # דין...סי' ח'
                # Standard patterns
                r'סימן\s+([א-ת]+)[\'׳]',  # סימן ח'
                r'\(סימן\s+([א-ת]+)[\'׳]\)',  # (סימן ח')
                r'סי[\'׳]\s*([א-ת]+)[\'׳]',  # סי' ח'
                r'סימן\s*(\d+)',  # סימן 8
                r'סי[\'׳]\s*(\d+)',  # סי' 8
                # Also catch without final quote sometimes
                r'סימן\s+([א-ת]+)(?:\s|:|\)|$)',  # סימן ח (without quote)
                r'סי[\'׳]\s*([א-ת]+)(?:\s|:|\)|$)',  # סי' ח (without quote)
            ]
        else:
            # English patterns: "Siman 8", "Siman 8:", "§8"
            patterns = [
                r'Siman\s+(\d+)',
                r'§\s*(\d+)',
                r'siman\s+(\d+)',
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num_str = match.group(1)
                # Convert Hebrew letters to numbers if needed
                if language == 'he' and num_str.isalpha():
                    siman_num = self._hebrew_to_number(num_str)
                    if siman_num:
                        return siman_num
                elif num_str.isdigit():
                    return int(num_str)
        
        return None
    
    def _hebrew_to_number(self, hebrew_str: str) -> Optional[int]:
        """
        Convert Hebrew letter representation to number.
        Handles א-ט (1-9), י-יט (10-19), כ-צט (20-99), etc.
        
        Args:
            hebrew_str: Hebrew letter(s) representing a number
            
        Returns:
            Integer value or None if invalid
        """
        # Basic Hebrew letters for 1-9
        basic = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5,
            'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9
        }
        
        # 10-19
        teens = {
            'י': 10, 'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14,
            'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19
        }
        
        # 20-90 (tens)
        tens = {
            'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50,
            'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90
        }
        
        # Check if it's a basic number (1-9)
        if hebrew_str in basic:
            return basic[hebrew_str]
        
        # Check if it's a teen (10-19)
        if hebrew_str in teens:
            return teens[hebrew_str]
        
        # Check if it's a multiple of 10 (20, 30, etc.)
        if hebrew_str in tens:
            return tens[hebrew_str]
        
        # Try to parse composite numbers (e.g., כא = 21, כב = 22)
        if len(hebrew_str) >= 2:
            # Check if starts with a tens digit
            for ten_letter, ten_value in tens.items():
                if hebrew_str.startswith(ten_letter):
                    remainder = hebrew_str[1:]
                    if remainder in basic:
                        return ten_value + basic[remainder]
                    elif remainder in teens:
                        return ten_value + teens[remainder]
        
        # Try common abbreviations (like תפ for תפ"ט = 489, but we'll just return None for complex ones)
        # For now, return None if we can't parse it
        return None
    
    def _extract_siman_from_paragraph(self, paragraph: str, language: str = 'he') -> Optional[int]:
        """
        Extract Siman number from a paragraph. Looks for markers anywhere in the text.
        
        Args:
            paragraph: Paragraph text (may contain HTML)
            language: Language code
            
        Returns:
            Siman number if found, None otherwise
        """
        # Clean HTML first
        import re
        clean_text = re.sub(r'<[^>]+>', '', paragraph)
        
        # Look for Siman marker
        return self._parse_siman_numbers(clean_text, language)
    
    def _find_siman_header(self, text: str, language: str = 'he') -> Optional[int]:
        """
        Find Siman marker that is a HEADER (not a reference).
        Headers appear at start of paragraph, references appear mid-paragraph.
        
        Args:
            text: Clean paragraph text
            language: Language code
            
        Returns:
            Siman number if header marker found, None otherwise
        """
        import re
        
        # Check first 300 characters for header-like patterns
        header_text = text[:300]
        
        if language == 'he':
            # Negative patterns - if these appear before marker, it's a reference
            reference_indicators = [
                r'עיין',
                r'כדלקמן',
                r'בסימן',
                r'לקמן.*?סי',
            ]
            
            # Check first 100 chars for reference indicators
            for indicator in reference_indicators:
                if re.search(indicator, header_text[:100]):
                    # This looks like a reference, not a header
                    return None
            
            # Positive patterns for headers
            # 1. At very start: "דין...סימן ח':" or "סימן ח':"
            # 2. After "דין" at start: "דין ברכת...סימן ח'"
            header_patterns = [
                r'^דין[^:]*?סימן\s+([א-ת]+)[\'׳]\s*:',  # דין...סימן ח':
                r'^סימן\s+([א-ת]+)[\'׳]\s*:',  # סימן ח':
                r'^\(סימן\s+([א-ת]+)[\'׳]\)\s*:',  # (סימן ח'):
            ]
            
            for pattern in header_patterns:
                match = re.search(pattern, header_text)
                if match:
                    num_str = match.group(1)
                    siman_num = self._hebrew_to_number(num_str)
                    if siman_num and 1 <= siman_num <= 200:
                        return siman_num
        
        return None
    
    def extract_structured_content(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract structured content with Klal/Siman information for Chayei Adam.
        Groups paragraphs by Siman - when a Siman marker is found, it starts a new Siman.
        All subsequent paragraphs without markers belong to that Siman until the next marker.
        
        Args:
            data: Sefaria API response dictionary
            
        Returns:
            Structured content dict with klal and simanim, or None if not Chayei Adam
        """
        if not self._detect_chayei_adam_structure(data):
            return None
        
        # Extract Klal number from sections or reference
        klal = None
        sections = data.get('sections', [])
        if sections:
            klal = sections[0]
        else:
            # Try to extract from reference
            ref = data.get('ref', '') or data.get('sectionRef', '')
            import re
            match = re.search(r'(\d+)', ref)
            if match:
                klal = int(match.group(1))
        
        # Get text array (prefer 'text', fall back to 'he')
        text_array = data.get('text', [])
        if not text_array or not isinstance(text_array, list):
            text_array = data.get('he', [])
        
        if not text_array or not isinstance(text_array, list):
            return None
        
        # Determine language
        language = 'he' if data.get('he') else 'en'
        
        # First pass: Find all Siman markers and their positions
        siman_markers = []  # List of (index, siman_num) tuples
        for idx, paragraph in enumerate(text_array):
            if not isinstance(paragraph, str):
                continue
            
            import re
            clean_text = re.sub(r'<[^>]+>', '', paragraph).strip()
            if not clean_text:
                continue
            
            siman_num = self._find_siman_header(clean_text, language)
            if siman_num:
                siman_markers.append((idx, siman_num))
        
        # Group paragraphs by Siman
        simanim = []
        current_siman = None
        current_paragraphs = []
        current_pos = 0
        
        # If no markers found, treat each paragraph as a separate Siman (sequential)
        if not siman_markers:
            # No Siman markers - use sequential numbering
            for idx, paragraph in enumerate(text_array):
                if not isinstance(paragraph, str):
                    continue
                
                import re
                clean_text = re.sub(r'<[^>]+>', '', paragraph).strip()
                if not clean_text:
                    continue
                
                simanim.append({
                    'siman': idx + 1,
                    'text': clean_text,
                    'start_pos': current_pos,
                    'end_pos': current_pos + len(clean_text),
                    'has_number': False,
                    'index': idx
                })
                current_pos += len(clean_text) + 2
        else:
            # We have markers - group paragraphs accordingly
            marker_idx = 0  # Index into siman_markers list
            
            for idx, paragraph in enumerate(text_array):
                if not isinstance(paragraph, str):
                    continue
                
                import re
                clean_text = re.sub(r'<[^>]+>', '', paragraph).strip()
                if not clean_text:
                    continue
                
                # Check if this is a marker position
                if marker_idx < len(siman_markers) and siman_markers[marker_idx][0] == idx:
                    # Found a Siman marker - start a new Siman
                    # First, save the previous Siman if it exists
                    if current_siman is not None:
                        combined_text = ' '.join(current_paragraphs)
                        start_pos = current_pos - len(combined_text) - (len(current_paragraphs) - 1) * 2
                        end_pos = current_pos - 2
                        
                        simanim.append({
                            'siman': current_siman,
                            'text': combined_text,
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'has_number': True,
                            'index': len(simanim)
                        })
                    
                    # Start new Siman
                    current_siman = siman_markers[marker_idx][1]
                    current_paragraphs = [clean_text]
                    current_pos += len(clean_text) + 2
                    marker_idx += 1
                else:
                    # No marker found - this paragraph belongs to current Siman
                    if current_siman is not None:
                        # Add to current Siman
                        current_paragraphs.append(clean_text)
                        current_pos += len(clean_text) + 2
                    else:
                        # First paragraph without marker - start with Siman 1
                        current_siman = 1
                        current_paragraphs = [clean_text]
                        current_pos += len(clean_text) + 2
            
            # Don't forget the last Siman
            if current_siman is not None and current_paragraphs:
                combined_text = ' '.join(current_paragraphs)
                start_pos = current_pos - len(combined_text) - (len(current_paragraphs) - 1) * 2
                end_pos = current_pos - 2
                
                simanim.append({
                    'siman': current_siman,
                    'text': combined_text,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'has_number': True,
                    'index': len(simanim)
                })
        
        if not simanim:
            return None
        
        # Fill gaps by fetching missing Simanim individually
        simanim = self._fill_siman_gaps(klal, simanim, language)
        
        # Sort by Siman number to ensure correct order
        simanim.sort(key=lambda x: x.get('siman', 0))
        
        return {
            'klal': klal,
            'simanim': simanim,
            'siman_count': len(simanim)
        }
    
    def _fill_siman_gaps(self, klal: int, simanim: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """
        Fill gaps in Simanim by fetching missing ones individually from Sefaria API.
        Uses direct API calls to avoid recursion issues.
        Only runs when we have confirmed headers (not sequential fallback).
        
        Args:
            klal: Klal number
            simanim: List of Simanim already found
            language: Language code
            
        Returns:
            Updated list of Simanim with gaps filled
        """
        if not simanim or klal is None:
            return simanim
        
        # If most Simanim don't have numbers (has_number=False), skip gap-filling
        # This means we're in sequential mode, not header-detection mode
        has_numbers_count = sum(1 for s in simanim if s.get('has_number', False))
        if has_numbers_count < len(simanim) * 0.5:  # Less than 50% have numbers
            return simanim  # Sequential mode - don't fill gaps
        
        # Get all Siman numbers found
        siman_nums = [s.get('siman') for s in simanim if s.get('siman')]
        if not siman_nums:
            return simanim
        
        # Find gaps
        sorted_nums = sorted(set(siman_nums))
        min_siman = min(sorted_nums)
        max_siman = max(sorted_nums)
        
        # Check for gaps
        expected_range = list(range(min_siman, max_siman + 1))
        missing_nums = [n for n in expected_range if n not in sorted_nums]
        
        if not missing_nums:
            # No gaps - return as is
            return simanim
        
        # Try to fetch missing Simanim using direct API call to avoid recursion
        filled_simanim = list(simanim)  # Copy existing
        
        for siman_num in missing_nums:
            try:
                # Direct API call - bypass fetch_text to avoid recursion
                import requests
                ref = f"Chayei Adam {klal}:{siman_num}"
                url = f"https://www.sefaria.org/api/texts/{ref}"
                params = {'lang': language}
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    siman_data = response.json()
                    
                    # Extract text content directly (bypass structured content extraction)
                    text_array = siman_data.get('text', [])
                    if not text_array or not isinstance(text_array, list):
                        text_array = siman_data.get('he', []) if language == 'he' else siman_data.get('en', [])
                    
                    if text_array and isinstance(text_array, list):
                        # Combine all paragraphs into single text
                        import re
                        text_parts = []
                        for para in text_array:
                            if isinstance(para, str):
                                clean_text = re.sub(r'<[^>]+>', '', para).strip()
                                if clean_text:
                                    text_parts.append(clean_text)
                        
                        text_content = ' '.join(text_parts)
                        
                        if text_content:
                            # Create Siman entry
                            filled_simanim.append({
                                'siman': siman_num,
                                'text': text_content,
                                'start_pos': 0,  # Will be recalculated if needed
                                'end_pos': len(text_content),
                                'has_number': False,  # Fetched individually, no marker in Klal
                                'index': len(filled_simanim),
                                'fetched_individually': True  # Flag to indicate this was fetched separately
                            })
                            print(f"  ✓ Fetched missing Siman {siman_num} for Klal {klal}")
            except Exception as e:
                # If fetch fails, skip this Siman (might not exist)
                # Only print if it's not a recursion error
                if "recursion" not in str(e).lower():
                    print(f"  ⚠ Could not fetch Siman {siman_num} for Klal {klal}: {e}")
                continue
        
        return filled_simanim
    
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
