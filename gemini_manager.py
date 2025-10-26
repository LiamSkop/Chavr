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
    
    # System prompt for Chavruta mode (Enhanced for AI Tutor)
    CHAVRUTA_SYSTEM_PROMPT = """You are an expert Torah tutor with deep knowledge of Jewish texts, commentary, and tradition. Your teaching style balances:

1. CLARITY: Explain concepts in accessible language, avoiding jargon without explanation
2. DEPTH: Reference multiple commentaries and perspectives (Rashi, Ramban, modern scholars)
3. SOCRATIC METHOD: Guide discovery with thoughtful questions rather than just answering
4. CONTEXT: Connect ideas across texts, themes, and historical periods
5. RESPECT: Honor both traditional and modern interpretations

Guidelines:
- Responses should be 3-5 paragraphs (300-500 words) to ensure thorough explanation
- Always cite specific commentators when relevant (e.g., "Rashi explains...", "According to Ramban...")
- When appropriate, provide Hebrew/Aramaic text with transliteration and translation
- End complex explanations with a reflective question to deepen understanding
- Track what the student has learned in this session and build on previous knowledge

Pedagogical Approach:
- Start with what the student already knows or has mentioned
- Use examples from the current text being studied
- Draw connections to related concepts or passages
- When appropriate, pose Socratic questions: "Why might the Torah use this specific word?", "How does this connect to what we discussed earlier?"

You are not just answering questions - you are building understanding, one question at a time.
"""
    
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
        
        # Generation configuration (optimized for teaching)
        self.generation_config = {
            'temperature': 0.8,  # More creative for engaging teaching
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': 1500,  # 3-5 paragraphs for thorough explanation
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
        
        # Call Gemini API with extended length for thorough responses
        response = self._call_gemini_api(prompt, max_tokens=1500)
        
        if response:
            print(f"✓ Generated AI response for question: {question[:50]}...")
        
        return response
    
    def generate_session_summary(self, session) -> Optional[str]:
        """
        Generate summary of completed study session.
        
        Args:
            session: Session object with AI interactions and metadata
            
        Returns:
            str: Session summary or None if failed
        """
        # Build summary prompt
        prompt = self._build_summary_prompt(session)
        
        # Call Gemini API with higher token limit for detailed summaries
        response = self._call_gemini_api(prompt, max_tokens=1000)
        
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
        
        # Add Sefaria text if present
        if session.has_sefaria_text():
            text_info = session.get_sefaria_text_info()
            summary_prompt += f"Text Studied: {text_info['reference']}\n\n"
        
        # Add AI interactions
        summary_prompt += "Questions and Answers:\n"
        for interaction in session.ai_interactions:
            timestamp = interaction.get('timestamp', 'N/A')
            summary_prompt += f"Q: {interaction['question']}\n"
            summary_prompt += f"A: {interaction['response']}\n\n"
        
        summary_prompt += "---\n\nSummary:"
        
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
