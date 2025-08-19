"""
AI-powered summarization module for editorial highlights
Uses BART model with fallback to extractive summarization
"""

import re
from typing import List, Optional


class SummaryGenerator:
    def __init__(self):
        self.model_loaded = False
        self.summarizer = None
        self.load_model()
    
    def load_model(self):
        """Try to load BART model for AI summarization"""
        try:
            from transformers import pipeline
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            self.model_loaded = True
            print("✓ AI summarization ready")
        except Exception:
            # Model loading failed, will use fallback
            self.model_loaded = False
    
    def summarize(self, text: str, max_length: int = 60, min_length: int = 20) -> str:
        """Generate a concise summary of the text"""
        # Clean the input text
        text = self.clean_text(text)
        
        if not text:
            return "Segment content"
        
        # Try AI summarization first
        if self.model_loaded and self.summarizer:
            try:
                # Ensure text is long enough
                if len(text.split()) > 10:
                    result = self.summarizer(
                        text, 
                        max_length=max_length, 
                        min_length=min_length,
                        do_sample=False
                    )
                    summary = result[0]['summary_text']
                    return self.polish_summary(summary)
            except Exception:
                pass
        
        # Fallback to extractive summarization
        return self.extractive_summarize(text, max_length)
    
    def clean_text(self, text: str) -> str:
        """Clean transcript text for summarization"""
        # Remove speaker labels if present
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove filler words
        filler_words = ['um', 'uh', 'like', 'you know', 'I mean', 'basically', 'actually']
        for filler in filler_words:
            text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
        
        # Clean up whitespace again
        text = ' '.join(text.split())
        
        return text
    
    def extractive_summarize(self, text: str, max_words: int = 60) -> str:
        """Simple extractive summarization as fallback"""
        sentences = self.split_sentences(text)
        
        if not sentences:
            return text[:200] + "..."
        
        # Score sentences by keyword density and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            # Prefer earlier sentences and longer ones
            position_score = 1.0 / (i + 1)
            length_score = min(len(sentence.split()) / 20, 1.0)
            
            # Check for important keywords
            keyword_score = 0
            important_words = ['important', 'key', 'critical', 'essential', 'significant',
                              'main', 'primary', 'focus', 'highlight', 'demonstrate',
                              'show', 'reveal', 'discover', 'innovation', 'breakthrough']
            
            sentence_lower = sentence.lower()
            for word in important_words:
                if word in sentence_lower:
                    keyword_score += 0.5
            
            total_score = position_score + length_score + keyword_score
            scored_sentences.append((sentence, total_score))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Build summary from top sentences
        summary_sentences = []
        word_count = 0
        
        for sentence, score in scored_sentences:
            sentence_words = sentence.split()
            if word_count + len(sentence_words) <= max_words:
                summary_sentences.append(sentence)
                word_count += len(sentence_words)
            else:
                # Add partial sentence if room
                remaining = max_words - word_count
                if remaining > 5:
                    partial = ' '.join(sentence_words[:remaining]) + '...'
                    summary_sentences.append(partial)
                break
        
        # Sort selected sentences by original order
        summary_sentences = sorted(summary_sentences, 
                                  key=lambda s: text.find(s) if s in text else float('inf'))
        
        return ' '.join(summary_sentences)
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Filter out very short sentences
        sentences = [s for s in sentences if len(s.split()) >= 5]
        
        return sentences
    
    def polish_summary(self, summary: str) -> str:
        """Polish the generated summary"""
        # Ensure proper capitalization
        if summary and summary[0].islower():
            summary = summary[0].upper() + summary[1:]
        
        # Ensure ends with period
        if summary and summary[-1] not in '.!?':
            summary += '.'
        
        # Remove duplicate words
        words = summary.split()
        cleaned_words = []
        prev_word = None
        for word in words:
            if word.lower() != prev_word:
                cleaned_words.append(word)
                prev_word = word.lower()
        
        return ' '.join(cleaned_words)