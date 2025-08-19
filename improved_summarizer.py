#!/usr/bin/env python3
"""
Improved AI Summarizer with better readability and conciseness
"""

import os
import re
import sys
from pathlib import Path

# Set environment variable to avoid tokenizers parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Try to import transformers
try:
    from transformers import pipeline
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class ImprovedSummarizer:
    """Enhanced AI-powered text summarization with focus on readability"""
    
    def __init__(self):
        self.summarizer = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the summarization model with better parameters"""
        if not HAS_TRANSFORMERS:
            print("⚠️  Transformers not available, using enhanced extractive summarization")
            self.summarizer = None
            return
            
        try:
            print("🤖 Loading enhanced AI summarization model...")
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Enhanced AI model loaded successfully!")
        except Exception as e:
            print(f"⚠️  AI model failed to load: {e}")
            print("Using enhanced extractive summarization")
            self.summarizer = None
    
    def summarize(self, text, max_length=80, target_sentences=1):
        """
        Create concise, readable summaries
        
        Args:
            text: Input text to summarize
            max_length: Maximum characters in summary
            target_sentences: Preferred number of sentences
        """
        if not text or len(text.strip()) < 20:
            return self._clean_text(text)
        
        # Clean input text first
        clean_text = self._clean_text(text)
        
        if self.summarizer and len(clean_text) > 50:
            try:
                # Use AI with better parameters
                result = self.summarizer(
                    clean_text,
                    max_length=min(60, len(clean_text.split()) + 20),  # Adaptive max length
                    min_length=15,
                    do_sample=False,
                    truncation=True,
                    clean_up_tokenization_spaces=True
                )
                
                summary = result[0]['summary_text'].strip()
                
                # Post-process AI summary for better readability
                summary = self._post_process_summary(summary, max_length)
                return summary
                
            except Exception as e:
                print(f"AI summarization failed: {e}")
        
        # Enhanced extractive summarization
        return self._enhanced_extractive_summary(clean_text, max_length, target_sentences)
    
    def _clean_text(self, text):
        """Clean and normalize input text"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove filler words and phrases common in transcripts
        filler_patterns = [
            r'\b(um|uh|ah|er|like|you know|sort of|kind of|basically|actually)\b',
            r'\b(so|well|yeah|okay|right|now)\s+',
            r'\[.*?\]',  # Remove bracket annotations
            r'\(.*?\)',  # Remove parenthetical asides
        ]
        
        for pattern in filler_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Clean up punctuation
        text = re.sub(r'\s+([.!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*([.!?])+', r'\1', text)  # Remove duplicate punctuation
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _post_process_summary(self, summary, max_length):
        """Post-process AI-generated summary for better readability"""
        
        # Ensure it starts with capital letter
        if summary and summary[0].islower():
            summary = summary[0].upper() + summary[1:]
        
        # Ensure it ends with proper punctuation
        if summary and summary[-1] not in '.!?':
            summary += '.'
        
        # Truncate if too long while preserving sentence structure
        if len(summary) > max_length:
            sentences = re.split(r'[.!?]+', summary)
            result = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(result + sentence) + 1 <= max_length:  # +1 for punctuation
                    result = result + sentence if not result else result + ". " + sentence
                else:
                    break
            
            summary = result + "." if result and result[-1] not in '.!?' else result
        
        return summary
    
    def _enhanced_extractive_summary(self, text, max_length, target_sentences):
        """Enhanced extractive summarization with better sentence selection"""
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        if len(sentences) == 1:
            return self._truncate_sentence(sentences[0], max_length)
        
        # Score sentences with enhanced criteria
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # Position scoring (beginning and end are important)
            if i == 0:
                score += 3  # First sentence often contains key info
            elif i == len(sentences) - 1:
                score += 2  # Last sentence often contains conclusions
            elif i == 1:
                score += 1  # Second sentence often expands on the topic
            
            # Content scoring - look for key indicators
            key_indicators = [
                'introduce', 'present', 'show', 'demonstrate', 'explain',
                'important', 'key', 'main', 'primary', 'significant',
                'first', 'second', 'finally', 'conclusion', 'result',
                'because', 'therefore', 'however', 'but', 'although',
                'new', 'revolutionary', 'breakthrough', 'innovative',
                'problem', 'solution', 'challenge', 'opportunity'
            ]
            
            for indicator in key_indicators:
                if indicator in sentence_lower:
                    score += 2
            
            # Prefer sentences with numbers, proper nouns, or technical terms
            if re.search(r'\d+', sentence):
                score += 1
            if re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence):  # Proper nouns
                score += 1
            if re.search(r'\b(?:AI|ML|API|GPU|CPU|algorithm|model|system|technology)\b', sentence, re.IGNORECASE):
                score += 2
            
            # Penalty for very long sentences (harder to read)
            if len(sentence) > 150:
                score -= 1
            
            # Penalty for sentences with too many conjunctions (rambling)
            conjunctions = len(re.findall(r'\b(and|or|but|so|because|since|while|although)\b', sentence_lower))
            if conjunctions > 2:
                score -= conjunctions
            
            scored_sentences.append((score, sentence, len(sentence)))
        
        # Sort by score and select best sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        selected_sentences = []
        total_length = 0
        
        for score, sentence, length in scored_sentences:
            if len(selected_sentences) >= target_sentences and total_length >= max_length * 0.7:
                break
                
            if total_length + length + 2 <= max_length:  # +2 for punctuation and space
                selected_sentences.append(sentence)
                total_length += length + 2
        
        # If no sentences fit, take the best one and truncate
        if not selected_sentences:
            best_sentence = scored_sentences[0][1]
            return self._truncate_sentence(best_sentence, max_length)
        
        # Join sentences and ensure proper formatting
        result = '. '.join(selected_sentences)
        if not result.endswith('.'):
            result += '.'
        
        return result
    
    def _truncate_sentence(self, sentence, max_length):
        """Truncate a sentence intelligently at word boundaries"""
        if len(sentence) <= max_length:
            return sentence + '.' if not sentence.endswith('.') else sentence
        
        words = sentence.split()
        result = []
        length = 0
        
        for word in words:
            if length + len(word) + 1 > max_length - 3:  # -3 for "..."
                break
            result.append(word)
            length += len(word) + 1
        
        return ' '.join(result) + '...' if result else sentence[:max_length-3] + '...'

def update_existing_files():
    """Update the main generate_video_cards.py to use improved summarizer"""
    
    main_file = Path("generate_video_cards.py")
    one_command_file = Path("one_command_highlights.py")
    
    # Read the current files
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Replace the AISummarizer class with our improved version
        # Find the class definition
        import_section = """# Video and AI processing
try:
    from pytube import YouTube
    from moviepy import VideoFileClip
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import requests
    from improved_summarizer import ImprovedSummarizer
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Run: pip3 install --user pytube moviepy transformers torch pillow numpy requests")
    sys.exit(1)"""
        
        # Replace import section
        content = re.sub(
            r'# Video and AI processing.*?sys\.exit\(1\)',
            import_section,
            content,
            flags=re.DOTALL
        )
        
        # Replace AISummarizer with ImprovedSummarizer
        content = content.replace('class AISummarizer:', 'class AISummarizer(ImprovedSummarizer):')
        content = content.replace('AISummarizer()', 'ImprovedSummarizer()')
        
        # Write back
        with open(main_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated generate_video_cards.py")
    
    # Update one_command_highlights.py
    if one_command_file.exists():
        with open(one_command_file, 'r') as f:
            content = f.read()
        
        # Add import
        if 'from improved_summarizer import ImprovedSummarizer' not in content:
            content = content.replace(
                'from generate_video_cards import (',
                'from improved_summarizer import ImprovedSummarizer\nfrom generate_video_cards import ('
            )
            
            content = content.replace(
                'summarizer = AISummarizer()',
                'summarizer = ImprovedSummarizer()'
            )
        
        with open(one_command_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated one_command_highlights.py")

if __name__ == "__main__":
    # Test the improved summarizer
    if len(sys.argv) > 1:
        test_text = sys.argv[1]
        summarizer = ImprovedSummarizer()
        summary = summarizer.summarize(test_text)
        print(f"Original: {test_text}")
        print(f"Summary: {summary}")
    else:
        update_existing_files()
        print("\n🎉 Enhanced summarizer installed!")
        print("Your summaries will now be much more concise and readable!")