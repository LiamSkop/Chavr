#!/usr/bin/env python3
"""
Learning Features - Concept extraction and follow-up suggestions.
Implements learning science features for the AI tutor.
"""

import re
from typing import List, Dict, Optional


class LearningFeatures:
    """Features for enhancing learning with the AI tutor."""
    
    # Common Torah/Jewish learning concepts
    COMMON_CONCEPTS = [
        "bereshit", "creation", "midrash", "halacha", "gemara", "mishna",
        "rashi", "ramban", "commentary", "interpretation", "pshat", "drash",
        "kabbalah", "mysticism", "chassidut", "philosophy", "ethics",
        "commandments", "mitzvot", "talmud", "torah", "tanakh", "prophets"
    ]
    
    @staticmethod
    def extract_concepts(text: str, question: Optional[str] = None) -> List[str]:
        """
        Extract key concepts from AI response or user question.
        
        Args:
            text: The text to analyze
            question: Optional question for context
            
        Returns:
            List of concept keywords
        """
        concepts = []
        text_lower = text.lower()
        
        # Check for common Torah concepts
        for concept in LearningFeatures.COMMON_CONCEPTS:
            if concept in text_lower:
                concepts.append(concept)
        
        # Look for Hebrew words (basic pattern)
        hebrew_pattern = r'[\u0590-\u05FF]+'
        hebrew_words = re.findall(hebrew_pattern, text)
        concepts.extend(hebrew_words[:3])  # Limit to first 3
        
        # Look for commentator names
        commentators = ["Rashi", "Ramban", "Ibn Ezra", "Rambam", "Nachmanides"]
        for commentator in commentators:
            if commentator.lower() in text_lower:
                concepts.append(commentator.lower())
        
        return concepts[:5]  # Return top 5 concepts
    
    @staticmethod
    def generate_followup_suggestions(context: Dict) -> List[str]:
        """
        Generate follow-up question suggestions based on context.
        
        Args:
            context: Dict with 'question', 'response', 'current_text' keys
            
        Returns:
            List of suggested follow-up questions
        """
        suggestions = []
        question = context.get('question', '').lower()
        response = context.get('response', '').lower()
        current_text = context.get('current_text', '')
        
        # Generic exploratory questions
        generic_suggestions = [
            "Can you explain this further?",
            "What are some other perspectives on this?",
            "How does this connect to other parts of the text?",
            "Why is this important?",
            "What should I study next?"
        ]
        
        # Context-aware suggestions based on keywords
        if 'rashi' in response or 'rash' in question:
            suggestions.append("What does Rashi say about this?")
        
        if 'meaning' in question or 'what does' in question:
            suggestions.append("What is the significance of this?")
        
        if 'happened' in question or 'why' in question:
            suggestions.append("What are the broader implications?")
        
        if 'compare' in question or 'similar' in question:
            suggestions.append("How does this differ from other interpretations?")
        
        # Text-specific suggestions
        if current_text:
            suggestions.append(f"Expand on this section from {current_text[:30]}...")
        
        # Add generic suggestions if we don't have enough
        if len(suggestions) < 3:
            suggestions.extend(generic_suggestions[:3 - len(suggestions)])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    @staticmethod
    def improve_response_pedagogy(response: str) -> str:
        """
        Post-process AI response to ensure pedagogical quality.
        
        Args:
            response: The AI response
            
        Returns:
            Improved response
        """
        # Ensure response ends with a question if it's too short
        if len(response) < 200 and not response.rstrip().endswith('?'):
            response += "\n\nWhat do you think about this?"
        
        # Add transliteration if Hebrew is mentioned without it
        # (This is a simple check - could be improved)
        
        return response


def test_learning_features():
    """Test the learning features."""
    test_text = """
    The word 'bereshit' (בתחילה) means 'in the beginning' and is the first word
    of Genesis. Rashi explains that this refers to the creation of the world.
    """
    
    features = LearningFeatures()
    concepts = LearningFeatures.extract_concepts(test_text)
    print(f"Extracted concepts: {concepts}")
    
    context = {
        'question': "What does bereshit mean?",
        'response': test_text,
        'current_text': 'Genesis 1:1'
    }
    
    suggestions = LearningFeatures.generate_followup_suggestions(context)
    print(f"Follow-up suggestions: {suggestions}")


if __name__ == "__main__":
    test_learning_features()

