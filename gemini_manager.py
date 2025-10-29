#!/usr/bin/env python3
"""
GeminiManager - AI Chavruta Integration
Handles all AI interactions using Google's Gemini 2.5 Flash-Lite model.
Free tier: 10,000 requests/minute, 10M tokens/minute.
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
    """Manages AI interactions using Gemini 2.5 Flash-Lite model.
    
    Uses stable production model with generous free tier limits:
    - 10,000 requests per minute
    - 10 million tokens per minute
    """
    
    # System prompt for Chavruta mode (Concise, focused for yeshivish learners)
    CHAVRUTA_SYSTEM_PROMPT = """You are an advanced Torah tutor for yeshivish learners.

CRITICAL: Stay focused - answer ONLY what's asked, nothing more.

Response Guidelines:
- Quick questions → quick answers (1-2 sentences maximum)
- Medium questions → one focused paragraph (50-100 words)
- Detailed questions → 2-3 focused paragraphs (still concise)
- Never explain more than what the question asks
- Use yeshivish/Hebrew terms when directly relevant to the concept (e.g., "peirush", "pshat", "drash")
- Primary language: English for clarity and ease of understanding
- Assume advanced understanding of Torah concepts (no need to explain basics)
- Always reference the current section being studied when relevant
- Citations optional - mention commentators (Rashi, Ramban, etc.) only when directly relevant
- No Socratic questions - just answer directly and clearly

Tone: Yeshivish-aware but clear and accessible. Use Hebrew/yeshivish words naturally when they're the standard term (e.g., "peirush", "chavruta", "gemara"), but explain in English.

Example:
- Question: "What does amen mean?"
- Answer: "'Amen' (אמן) means 'faith' or 'truth'. When you say 'amen' after a blessing, you're affirming belief in what was said."

Stay concise. Don't over-explain.
"""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini 2.5 Flash-Lite model.
        
        Args:
            api_key (str): Google Generative AI API key
        """
        if not api_key:
            raise ValueError("API key is required for GeminiManager")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model - using stable production model (cost-optimized, fast)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Generation configuration (optimized for concise, focused responses)
        self.generation_config = {
            'temperature': 0.7,  # Balanced creativity and focus
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': 300,  # Default medium length (will be overridden per question)
        }
        
        # Context storage
        self.current_sefaria_text: Optional[Dict[str, Any]] = None
        self.recent_transcripts: List[Dict[str, Any]] = []
        
        # Error callback
        self.error_callback: Optional[Callable[[str], None]] = None
        
        print("✓ GeminiManager initialized with Gemini 2.5 Flash-Lite")
    
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
        
        # Detect question type for adaptive response length
        question_type = self._detect_question_type(question)
        print(f"DEBUG: Detected question type: {question_type}")
        
        # Build context-aware prompt with length guidance
        prompt = self._build_chavruta_prompt(question, question_type)
        
        # Adaptive token limits based on question type
        token_limits = {
            'quick': 150,      # 1-2 sentences
            'medium': 300,     # 1 paragraph
            'detailed': 500    # 2-3 paragraphs (still focused)
        }
        max_tokens = token_limits.get(question_type, 300)
        
        # Call Gemini API with adaptive length
        response = self._call_gemini_api(prompt, max_tokens=max_tokens)
        
        if response:
            print(f"✓ Generated AI response ({question_type}) for question: {question[:50]}...")
        
        return response
    
    def _detect_question_type(self, question: str) -> str:
        """
        Detect question type to determine appropriate response length.
        
        Args:
            question: User's question
            
        Returns:
            'quick', 'medium', or 'detailed'
        """
        question_lower = question.lower().strip()
        
        # Quick indicators - definition/meaning questions
        quick_patterns = ["what does", "what is", "define", "meaning of"]
        if any(pattern in question_lower for pattern in quick_patterns):
            # If very short question (likely single word), definitely quick
            if len(question.split()) <= 6:
                return 'quick'
        
        # Single word questions are usually quick
        if len(question.split()) <= 3:
            return 'quick'
        
        # Detailed indicators - explicit requests for depth
        detailed_patterns = [
            "tell me everything",
            "explain in detail",
            "compare",
            "difference between",
            "relationship between"
        ]
        if any(pattern in question_lower for pattern in detailed_patterns):
            return 'detailed'
        
        # "Explain" questions are usually medium
        if "explain" in question_lower:
            return 'medium'
        
        # Default to medium for most questions
        return 'medium'
    
    def _build_chavruta_prompt(self, question: str, question_type: str = 'medium') -> str:
        """
        Build context-aware prompt for Q&A.
        
        Args:
            question (str): User's question
            question_type (str): 'quick', 'medium', or 'detailed'
            
        Returns:
            str: Complete prompt for Gemini
        """
        import traceback
        
        try:
            prompt_parts = [self.CHAVRUTA_SYSTEM_PROMPT, "\n\n"]
            
            # Add length guidance based on question type
            length_guidance = {
                'quick': "Keep your answer to 1-2 sentences maximum. Be concise.",
                'medium': "Keep your answer to one focused paragraph (50-100 words).",
                'detailed': "Provide 2-3 focused paragraphs, but stay concise and on-topic."
            }
            prompt_parts.append(f"Response Length: {length_guidance.get(question_type, length_guidance['medium'])}\n\n")
            
            # Add Sefaria text context if available
            if self.current_sefaria_text:
                try:
                    ref = self.current_sefaria_text.get('reference', 'Unknown')
                    content = self.current_sefaria_text.get('content', '')
                    lang = self.current_sefaria_text.get('language', 'en')
                    
                    print(f"DEBUG: Adding Sefaria context - ref={ref}, lang={lang}, content_len={len(content)}")
                    
                    prompt_parts.append(f"Current Text Being Studied:\n")
                    prompt_parts.append(f"Reference: {ref}\n")
                    prompt_parts.append(f"Language: {lang}\n")
                    prompt_parts.append(f"Text:\n{content}\n\n")
                except Exception as e:
                    print(f"⚠ Error building Sefaria context: {e}")
                    print(f"DEBUG: current_sefaria_text keys: {list(self.current_sefaria_text.keys()) if isinstance(self.current_sefaria_text, dict) else 'not a dict'}")
                    print(f"DEBUG: Traceback:\n{traceback.format_exc()}")
            
            # Add recent conversation context
            if self.recent_transcripts:
                try:
                    prompt_parts.append("Recent Conversation:\n")
                    for idx, t in enumerate(self.recent_transcripts[-5:]):  # Last 5 only
                        # Handle both transcript format and interaction format
                        lang = t.get('language', 'en')  # Default to 'en' if missing
                        text = t.get('text', str(t))  # Fallback to string representation
                        prompt_parts.append(f"[{lang}] {text}\n")
                    prompt_parts.append("\n")
                except Exception as e:
                    print(f"⚠ Error building conversation context: {e}")
                    print(f"DEBUG: recent_transcripts count: {len(self.recent_transcripts)}")
                    print(f"DEBUG: First transcript keys: {list(self.recent_transcripts[0].keys()) if self.recent_transcripts and isinstance(self.recent_transcripts[0], dict) else 'not a dict'}")
                    print(f"DEBUG: Traceback:\n{traceback.format_exc()}")
            
            # Add the question
            prompt_parts.append(f"Student's Question: {question}\n\n")
            prompt_parts.append("Response:")
            
            result = "".join(prompt_parts)
            print(f"DEBUG: Built prompt ({len(result)} chars)")
            return result
            
        except Exception as e:
            print(f"✗ Error building prompt: {e}")
            print(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
            # Return minimal prompt if building fails
            return f"{self.CHAVRUTA_SYSTEM_PROMPT}\n\nStudent's Question: {question}\n\nResponse:"
    
    def _call_gemini_api(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Core API call with error handling and exponential backoff retry for rate limits.
        
        Args:
            prompt (str): Complete prompt for Gemini
            max_tokens (int): Maximum tokens for response
            
        Returns:
            str: AI response or None if failed
        """
        import time
        import traceback
        
        max_retries = 3
        base_delay = 1.0  # Start with 1 second
        
        for attempt in range(max_retries + 1):
            try:
                # Update generation config with token limit
                config = self.generation_config.copy()
                config['max_output_tokens'] = max_tokens
                
                print(f"DEBUG: Calling Gemini API with {len(prompt)} chars, max_tokens={max_tokens}")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=config
                )
                
                if response and response.text:
                    print(f"DEBUG: Gemini response received ({len(response.text)} chars)")
                    return response.text.strip()
                else:
                    print("⚠ Gemini returned empty response")
                    print(f"DEBUG: Response object: {response}")
                    if self.error_callback:
                        self.error_callback("AI returned empty response")
                    return None
                    
            except KeyError as e:
                error_msg = f"KeyError accessing response: {str(e)}"
                print(f"✗ {error_msg}")
                print(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
                if self.error_callback:
                    self.error_callback(f"Data structure error: {error_msg}")
                return None
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                # Check if it's a 429 rate limit error
                is_rate_limit = (
                    "429" in error_msg or 
                    "ResourceExhausted" in error_type or
                    "RATE_LIMIT" in error_msg.upper()
                )
                
                if is_rate_limit:
                    if attempt < max_retries:
                        # Exponential backoff: 1s, 2s, 4s
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠ Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(delay)
                        continue  # Retry
                    else:
                        # Max retries exceeded
                        print(f"✗ Rate limit exceeded after {max_retries + 1} attempts")
                        if self.error_callback:
                            self.error_callback("Rate limit exceeded. Please wait a few minutes and try again.")
                        return None
                
                # Handle other errors
                print(f"✗ Gemini API error: {error_msg}")
                print(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
                
                # Handle specific errors
                if "API_KEY" in error_msg.upper():
                    print("✗ Invalid or missing Gemini API key")
                    if self.error_callback:
                        self.error_callback("API key error. Please check GEMINI_API_KEY.")
                elif "QUOTA" in error_msg.upper():
                    print("✗ API quota exceeded")
                    if self.error_callback:
                        self.error_callback("API quota exceeded. Please check your billing.")
                else:
                    if self.error_callback:
                        self.error_callback(f"AI error: {error_msg[:100]}")
                
                return None
        
        # Should never reach here, but just in case
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
