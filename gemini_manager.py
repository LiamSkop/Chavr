#!/usr/bin/env python3
"""
GeminiManager - AI Chavruta Integration
Handles all AI interactions using Google's Gemini 2.0 Flash Experimental model.
"""

import os
import google.generativeai as genai
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system environment variables


class GeminiManager:
    """Manages AI interactions using Gemini 2.0 Flash Experimental model."""
    
    # System prompt for Chavruta mode
    CHAVRUTA_SYSTEM_PROMPT = """You are a Chavruta (study partner) for Torah and Jewish text study.

Your role is to be a balanced study partner:
- Sometimes ask Socratic questions to deepen understanding
- Sometimes explain concepts clearly and concisely
- Sometimes challenge assumptions to promote critical thinking
- Always reference specific parts of the text when relevant

Guidelines:
- Keep responses concise (2-3 paragraphs maximum)
- Use both Hebrew and English naturally when appropriate
- Be respectful of traditional interpretations while encouraging analysis
- Avoid giving definitive answers to complex questions - guide discovery instead

You are studying with a partner who values thoughtful dialogue over quick answers."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini 2.0 Flash Experimental model.
        
        Args:
            api_key (str): Google Generative AI API key
        """
        if not api_key:
            raise ValueError("API key is required for GeminiManager")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model - using latest experimental flash model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Generation configuration
        self.generation_config = {
            'temperature': 0.7,  # Balanced creativity
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': 500,  # ~2-3 paragraphs
        }
        
        # Context storage
        self.current_sefaria_text: Optional[Dict[str, Any]] = None
        self.recent_transcripts: List[Dict[str, Any]] = []
        
        # Error callback
        self.error_callback: Optional[Callable[[str], None]] = None
        
        print("✓ GeminiManager initialized with Gemini 2.0 Flash Experimental")
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback function for error notifications."""
        self.error_callback = callback
    
    def set_sefaria_context(self, reference: str, text_content: str, language: str):
        """
        Store current Sefaria text for context.
        
        Args:
            reference (str): Text reference (e.g., "Genesis 1:1")
            text_content (str): Text content from Sefaria API
            language (str): Language code ('en' or 'he')
        """
        # Extract first 2000 characters for context
        truncated_content = self._truncate_text(text_content, max_chars=2000)
        
        self.current_sefaria_text = {
            'reference': reference,
            'content': truncated_content,
            'language': language
        }
        
        print(f"✓ Set Sefaria context: {reference} ({language})")
    
    def add_transcript_context(self, transcripts: List[Dict[str, Any]]):
        """
        Store recent transcript entries for context.
        
        Args:
            transcripts (List[Dict]): List of transcript entries with 'text' and 'language' keys
        """
        # Keep only last 10 transcripts to avoid context bloat
        self.recent_transcripts = transcripts[-10:] if len(transcripts) > 10 else transcripts
        
        print(f"✓ Added {len(self.recent_transcripts)} transcript entries to context")
    
    def ask_question(self, question: str) -> Optional[str]:
        """
        Send question to Gemini and return response.
        
        Args:
            question (str): User's question
            
        Returns:
            str: AI response or None if failed
        """
        if not question.strip():
            if self.error_callback:
                self.error_callback("Please enter a question")
            return None
        
        # Build context-aware prompt
        prompt = self._build_chavruta_prompt(question)
        
        # Call Gemini API
        response = self._call_gemini_api(prompt)
        
        if response:
            print(f"✓ Generated AI response for question: {question[:50]}...")
        
        return response
    
    def generate_session_summary(self, session) -> Optional[str]:
        """
        Generate summary of completed study session.
        
        Args:
            session: Session object with transcripts and metadata
            
        Returns:
            str: Session summary or None if failed
        """
        # Build summary prompt
        prompt = self._build_summary_prompt(session)
        
        # Call Gemini API with higher token limit for summaries
        response = self._call_gemini_api(prompt, max_tokens=800)
        
        if response:
            print(f"✓ Generated session summary for: {session.title}")
        
        return response
    
    def _build_chavruta_prompt(self, question: str) -> str:
        """
        Build context-aware prompt for Q&A.
        
        Args:
            question (str): User's question
            
        Returns:
            str: Complete prompt for Gemini
        """
        prompt_parts = [self.CHAVRUTA_SYSTEM_PROMPT, "\n\n"]
        
        # Add Sefaria text context if available
        if self.current_sefaria_text:
            ref = self.current_sefaria_text['reference']
            content = self.current_sefaria_text['content']
            lang = self.current_sefaria_text['language']
            
            prompt_parts.append(f"Current Text Being Studied:\n")
            prompt_parts.append(f"Reference: {ref}\n")
            prompt_parts.append(f"Language: {lang}\n")
            prompt_parts.append(f"Text:\n{content}\n\n")
        
        # Add recent conversation context
        if self.recent_transcripts:
            prompt_parts.append("Recent Conversation:\n")
            for t in self.recent_transcripts[-5:]:  # Last 5 only
                prompt_parts.append(f"[{t['language']}] {t['text']}\n")
            prompt_parts.append("\n")
        
        # Add the question
        prompt_parts.append(f"Student's Question: {question}\n\n")
        prompt_parts.append("Response:")
        
        return "".join(prompt_parts)
    
    def _build_summary_prompt(self, session) -> str:
        """
        Build prompt for session summarization.
        
        Args:
            session: Session object
            
        Returns:
            str: Complete prompt for Gemini
        """
        summary_prompt = """Please analyze this study session and provide a concise summary.

Include:
1. Main topics or passages studied
2. Key questions raised
3. Notable insights or interpretations discussed
4. Suggested areas for further exploration

Keep the summary to 3-4 paragraphs maximum.

---

"""
        
        # Add session metadata
        summary_prompt += f"Study Session: {session.title}\n"
        summary_prompt += f"Duration: {session.duration:.1f} seconds\n"
        summary_prompt += f"Languages: {', '.join(session.get_languages_used())}\n\n"
        
        # Add Sefaria text if present
        if session.has_sefaria_text():
            text_info = session.get_sefaria_text_info()
            summary_prompt += f"Text Studied: {text_info['reference']}\n\n"
        
        # Add full transcript (or truncate if too long)
        summary_prompt += "Transcript:\n"
        for entry in session.transcripts:
            timestamp = entry.timestamp.strftime("%H:%M:%S")
            summary_prompt += f"[{timestamp}] {entry.text}\n"
        
        summary_prompt += "\n---\n\nSummary:"
        
        return summary_prompt
    
    def _call_gemini_api(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Core API call with error handling.
        
        Args:
            prompt (str): Complete prompt for Gemini
            max_tokens (int): Maximum tokens for response
            
        Returns:
            str: AI response or None if failed
        """
        try:
            # Update generation config with token limit
            config = self.generation_config.copy()
            config['max_output_tokens'] = max_tokens
            
            response = self.model.generate_content(
                prompt,
                generation_config=config
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                print("⚠ Gemini returned empty response")
                if self.error_callback:
                    self.error_callback("AI returned empty response")
                return None
                
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific errors
            if "API_KEY" in error_msg.upper():
                print("✗ Invalid or missing Gemini API key")
                if self.error_callback:
                    self.error_callback("API key error. Please check GEMINI_API_KEY.")
            elif "RATE_LIMIT" in error_msg.upper() or "429" in error_msg:
                print("✗ Rate limit exceeded")
                if self.error_callback:
                    self.error_callback("Rate limit exceeded. Please wait and try again.")
            elif "QUOTA" in error_msg.upper():
                print("✗ API quota exceeded")
                if self.error_callback:
                    self.error_callback("API quota exceeded. Please check your billing.")
            else:
                print(f"✗ Gemini API error: {error_msg}")
                if self.error_callback:
                    self.error_callback(f"AI error: {error_msg[:100]}")
            
            return None
    
    def _truncate_text(self, text: str, max_chars: int = 2000) -> str:
        """
        Truncate text intelligently at sentence boundaries.
        
        Args:
            text (str): Text to truncate
            max_chars (int): Maximum characters
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_chars:
            return text
        
        # Try to truncate at last sentence boundary before max_chars
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclaim = truncated.rfind('!')
        
        boundary = max(last_period, last_question, last_exclaim)
        if boundary > max_chars * 0.7:  # At least 70% of desired length
            return truncated[:boundary + 1]
        
        return truncated + "..."


def create_gemini_manager() -> Optional[GeminiManager]:
    """
    Create GeminiManager instance with API key from environment.
    
    Returns:
        GeminiManager: Initialized manager or None if API key missing
    """
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("✗ GEMINI_API_KEY environment variable not set")
        print("Please set your API key:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        return None
    
    try:
        return GeminiManager(api_key)
    except Exception as e:
        print(f"✗ Failed to initialize GeminiManager: {e}")
        return None


if __name__ == "__main__":
    # Test the GeminiManager
    manager = create_gemini_manager()
    
    if manager:
        print("\n=== Testing Basic Q&A ===")
        response = manager.ask_question("What is a Chavruta?")
        if response:
            print(f"Response: {response}")
        else:
            print("Failed to get response")
    else:
        print("GeminiManager not initialized - check API key")
