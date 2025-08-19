#!/usr/bin/env python3
"""
YouTube Highlight Generator
Creates beautiful highlight pages from YouTube videos and transcripts
"""

import os
import sys
import re
import argparse
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
from datetime import timedelta

# Video and AI processing
try:
    from pytube import YouTube
    from moviepy import VideoFileClip
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import requests
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Run: pip3 install --user pytube moviepy transformers torch pillow numpy requests")
    sys.exit(1)

class TranscriptParser:
    """Parse WebVTT and SRT transcript files"""
    
    @staticmethod
    def parse_vtt(file_path):
        """Parse WebVTT format with improved handling for YouTube captions"""
        segments = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines to separate cues
        cues = re.split(r'\n\s*\n', content)
        
        for cue in cues:
            lines = cue.strip().split('\n')
            if len(lines) < 2:
                continue
                
            # Look for timestamp line and text lines
            timestamp_line = None
            text_lines = []
            
            for line in lines:
                line = line.strip()
                if ' --> ' in line:
                    # Extract timestamp, ignoring position/alignment info
                    timestamp_line = line.split(' align:')[0].split(' position:')[0]
                elif (line and 
                      not line.startswith('WEBVTT') and 
                      not line.startswith('Kind:') and
                      not line.startswith('Language:') and
                      not line.isdigit() and
                      not ' --> ' in line):
                    # Clean the text: remove inline timestamps and HTML tags
                    clean_text = re.sub(r'<\d+:\d+:\d+\.\d+><c>', '', line)
                    clean_text = re.sub(r'</c>', '', clean_text)
                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                    clean_text = clean_text.strip()
                    
                    if clean_text and clean_text not in text_lines:
                        text_lines.append(clean_text)
            
            if timestamp_line and text_lines:
                try:
                    start_time, end_time = timestamp_line.split(' --> ')
                    start_seconds = TranscriptParser._time_to_seconds(start_time.strip())
                    end_seconds = TranscriptParser._time_to_seconds(end_time.strip())
                    
                    # Join text lines and clean up
                    text = ' '.join(text_lines)
                    if text:
                        segments.append({
                            'start': start_seconds,
                            'end': end_seconds,
                            'text': text
                        })
                except Exception as e:
                    # Debug: print problematic lines
                    # print(f"Failed to parse cue: {cue[:100]}... Error: {e}")
                    continue
        
        return segments
    
    @staticmethod
    def parse_srt(file_path):
        """Parse SRT format"""
        segments = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # Line 0: sequence number
                # Line 1: timestamps
                # Line 2+: text
                timestamp_line = lines[1]
                text_lines = lines[2:]
                
                if ' --> ' in timestamp_line:
                    start_time, end_time = timestamp_line.split(' --> ')
                    start_seconds = TranscriptParser._time_to_seconds(start_time.replace(',', '.'))
                    end_seconds = TranscriptParser._time_to_seconds(end_time.replace(',', '.'))
                    
                    segments.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': ' '.join(text_lines)
                    })
            except:
                continue
        
        return segments
    
    @staticmethod
    def _time_to_seconds(time_str):
        """Convert time string to seconds"""
        # Handle format: HH:MM:SS.mmm or MM:SS.mmm
        time_str = time_str.strip()
        parts = time_str.split(':')
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        else:
            return float(time_str)

class SegmentFinder:
    """Find interesting segments based on keywords"""
    
    def __init__(self, keywords, context_window=5):
        self.keywords = [kw.lower() for kw in keywords]
        self.context_window = context_window
    
    def find_segments(self, transcript_segments, num_cards):
        """Find the most interesting segments"""
        keyword_segments = []
        
        # Find segments containing keywords
        for i, segment in enumerate(transcript_segments):
            text_lower = segment['text'].lower()
            for keyword in self.keywords:
                if keyword in text_lower:
                    # Include context around the keyword
                    start_idx = max(0, i - self.context_window)
                    end_idx = min(len(transcript_segments), i + self.context_window + 1)
                    
                    context_segments = transcript_segments[start_idx:end_idx]
                    combined_text = ' '.join([s['text'] for s in context_segments])
                    
                    keyword_segments.append({
                        'start': context_segments[0]['start'],
                        'end': context_segments[-1]['end'],
                        'text': combined_text,
                        'keyword': keyword,
                        'score': len([kw for kw in self.keywords if kw in text_lower])
                    })
                    break
        
        # Sort by score (most keywords) and remove duplicates
        keyword_segments.sort(key=lambda x: x['score'], reverse=True)
        unique_segments = []
        used_ranges = []
        
        for segment in keyword_segments:
            overlap = False
            for used_start, used_end in used_ranges:
                if not (segment['end'] < used_start or segment['start'] > used_end):
                    overlap = True
                    break
            
            if not overlap:
                unique_segments.append(segment)
                used_ranges.append((segment['start'], segment['end']))
        
        # If we need more segments, split the remaining transcript
        if len(unique_segments) < num_cards:
            remaining_needed = num_cards - len(unique_segments)
            unused_segments = []
            
            # Find unused parts of transcript
            for segment in transcript_segments:
                used = False
                for used_start, used_end in used_ranges:
                    if not (segment['end'] < used_start or segment['start'] > used_end):
                        used = True
                        break
                if not used:
                    unused_segments.append(segment)
            
            # Split unused segments into equal parts
            if unused_segments:
                chunk_size = len(unused_segments) // remaining_needed
                if chunk_size > 0:
                    for i in range(remaining_needed):
                        start_idx = i * chunk_size
                        end_idx = start_idx + chunk_size if i < remaining_needed - 1 else len(unused_segments)
                        
                        if start_idx < len(unused_segments):
                            chunk = unused_segments[start_idx:end_idx]
                            combined_text = ' '.join([s['text'] for s in chunk])
                            
                            unique_segments.append({
                                'start': chunk[0]['start'],
                                'end': chunk[-1]['end'],
                                'text': combined_text,
                                'keyword': 'general',
                                'score': 0
                            })
        
        # Sort by start time and return requested number
        unique_segments.sort(key=lambda x: x['start'])
        return unique_segments[:num_cards]

class AISummarizer:
    """AI-powered text summarization"""
    
    def __init__(self):
        self.summarizer = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the summarization model"""
        try:
            print("🤖 Loading AI summarization model...")
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ AI model loaded successfully!")
        except Exception as e:
            print(f"⚠️  AI model failed to load: {e}")
            print("Falling back to extractive summarization")
            self.summarizer = None
    
    def summarize(self, text, max_length=60):
        """Summarize text using AI or fallback method"""
        if not text or len(text.strip()) < 20:
            return text
        
        if self.summarizer:
            try:
                # BART works best with 100-1024 tokens
                if len(text) > 1024:
                    text = text[:1024]
                
                result = self.summarizer(
                    text,
                    max_length=max_length,
                    min_length=10,
                    do_sample=False
                )
                return result[0]['summary_text']
            except Exception as e:
                print(f"AI summarization failed: {e}")
        
        # Fallback: extractive summarization
        return self._extractive_summary(text, max_length)
    
    def _extractive_summary(self, text, max_length):
        """Simple extractive summarization"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Score sentences by keyword presence and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            # Prefer sentences at beginning and end
            if i == 0 or i == len(sentences) - 1:
                score += 2
            # Prefer sentences with common important words
            important_words = ['important', 'key', 'main', 'first', 'finally', 'conclusion']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and take best sentences
        scored_sentences.sort(reverse=True)
        selected = []
        total_length = 0
        
        for score, sentence in scored_sentences:
            if total_length + len(sentence) <= max_length:
                selected.append(sentence)
                total_length += len(sentence)
            if total_length >= max_length * 0.8:  # 80% of max length
                break
        
        return ' '.join(selected) if selected else sentences[0][:max_length]

class VideoProcessor:
    """Handle video download and frame extraction"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.video_id = None
        self.youtube_url = None
    
    def _has_ffmpeg(self):
        """Check if ffmpeg is available"""
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def download_video(self, youtube_url):
        """Download video from YouTube"""
        self.youtube_url = youtube_url  # Store for thumbnail extraction
        try:
            print("📥 Downloading video...")
            yt = YouTube(youtube_url)
            
            # Extract video ID for thumbnail fallbacks
            import re
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/v/([^&\n?#]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, youtube_url)
                if match:
                    self.video_id = match.group(1)
                    break
            
            # Get best available stream
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if not stream:
                stream = yt.streams.filter(file_extension='mp4').first()
            
            if not stream:
                raise Exception("No suitable video stream found")
            
            video_path = self.output_dir / "video.mp4"
            stream.download(filename=str(video_path))
            
            print(f"✅ Video downloaded: {video_path}")
            return str(video_path), yt.title
            
        except Exception as e:
            print(f"❌ Video download failed: {e}")
            # Still extract video ID for thumbnail fallbacks
            if not self.video_id:
                import re
                patterns = [
                    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                    r'youtube\.com/v/([^&\n?#]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, youtube_url)
                    if match:
                        self.video_id = match.group(1)
                        break
            return None, None
    
    def extract_thumbnails(self, video_path, segments):
        """Extract thumbnail images from video segments using smart frame selection"""
        thumbnails = []
        
        # Try smart extraction first using FFmpeg
        if self.youtube_url and self._has_ffmpeg():
            try:
                print("🎯 Using smart thumbnail extraction...")
                from core.video_screenshot import VideoScreenshotExtractor
                extractor = VideoScreenshotExtractor()
                
                for i, segment in enumerate(segments):
                    thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.jpg"
                    
                    # Use smart extraction for better frame selection
                    success = extractor.extract_smart_screenshot(
                        self.youtube_url,
                        int(segment['start']),
                        int(segment['end']),
                        thumbnail_path,
                        fallback_on_error=True
                    )
                    
                    if success and thumbnail_path.exists():
                        thumbnails.append(str(thumbnail_path))
                    else:
                        # Try simple extraction at segment start
                        success = extractor.extract_screenshot(
                            self.youtube_url,
                            int(segment['start']),
                            thumbnail_path,
                            fallback_on_error=True
                        )
                        if success:
                            thumbnails.append(str(thumbnail_path))
                        else:
                            thumbnails.append(None)
                
                # If we got some thumbnails, return them
                if any(thumbnails):
                    print(f"✅ Extracted {len([t for t in thumbnails if t])} smart thumbnails")
                    return thumbnails
                    
            except Exception as e:
                print(f"⚠️ Smart extraction not available: {e}")
        
        # Fallback to MoviePy extraction from downloaded video
        if video_path:
            try:
                print("🖼️  Extracting thumbnails from video...")
                video = VideoFileClip(video_path)
                
                for i, segment in enumerate(segments):
                    try:
                        # Get frame from start of segment (more accurate than middle)
                        start_time = segment['start']
                        start_time = min(start_time, video.duration - 1)  # Ensure within video bounds
                        
                        frame = video.get_frame(start_time)
                        
                        # Convert to PIL Image and save
                        img = Image.fromarray(frame)
                        thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                        img.save(thumbnail_path)
                        
                        thumbnails.append(str(thumbnail_path))
                        
                    except Exception as e:
                        print(f"Failed to extract thumbnail {i+1}: {e}")
                        thumbnails.append(None)
                
                video.close()
                print(f"✅ Extracted {len([t for t in thumbnails if t])} thumbnails")
                return thumbnails
                
            except Exception as e:
                print(f"❌ Thumbnail extraction failed: {e}")
        
        # Method 2: Generate custom thumbnails with timestamps
        if self.video_id:
            try:
                print("🎨 Generating custom thumbnails...")
                return self._generate_custom_thumbnails(segments)
            except Exception as e:
                print(f"❌ Custom thumbnail generation failed: {e}")
        
        # Method 3: Fallback to None (will use YouTube API in HTML)
        return [None] * len(segments)
    
    def _generate_custom_thumbnails(self, segments):
        """Generate visually distinct thumbnail images for each segment"""
        import requests
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance
        import io
        
        thumbnails = []
        
        # Download base thumbnail from YouTube
        base_thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/maxresdefault.jpg"
        try:
            response = requests.get(base_thumbnail_url, timeout=10)
            base_image = Image.open(io.BytesIO(response.content))
        except:
            # Fallback to lower resolution
            base_thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/hqdefault.jpg"
            try:
                response = requests.get(base_thumbnail_url, timeout=10)
                base_image = Image.open(io.BytesIO(response.content))
            except:
                return [None] * len(segments)
        
        # Color schemes for each segment to make them visually distinct
        color_schemes = [
            {"gradient": (255, 87, 51), "name": "ORANGE", "brightness": 1.2},      # Orange - brighter
            {"gradient": (74, 144, 226), "name": "BLUE", "brightness": 0.8},      # Blue - darker
            {"gradient": (156, 39, 176), "name": "PURPLE", "brightness": 1.15},   # Purple - bright
            {"gradient": (76, 175, 80), "name": "GREEN", "brightness": 0.85},     # Green - darker
        ]
        
        for i, segment in enumerate(segments):
            try:
                # Create a copy of the base image
                img = base_image.copy()
                
                # Apply different visual effects based on segment
                color_scheme = color_schemes[i % len(color_schemes)]
                gradient_color = color_scheme["gradient"]
                
                # Apply brightness adjustment to make segments look different
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(color_scheme["brightness"])
                
                # Apply color tint
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.8 + (i * 0.1))  # Vary color saturation
                
                # Create a colored overlay
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Different overlay patterns for each segment - make them much more visible
                overlay_alpha = 80  # Much more visible overlay
                if i == 0:  # Top band
                    overlay_draw.rectangle([0, 0, img.width, img.height//3], 
                                         fill=gradient_color + (overlay_alpha,))
                elif i == 1:  # Right band
                    overlay_draw.rectangle([2*img.width//3, 0, img.width, img.height], 
                                         fill=gradient_color + (overlay_alpha,))
                elif i == 2:  # Bottom band
                    overlay_draw.rectangle([0, 2*img.height//3, img.width, img.height], 
                                         fill=gradient_color + (overlay_alpha,))
                else:  # Left band
                    overlay_draw.rectangle([0, 0, img.width//3, img.height], 
                                         fill=gradient_color + (overlay_alpha,))
                
                # Apply the colored overlay
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                
                draw = ImageDraw.Draw(img)
                
                # Add timestamp overlay
                timestamp = self._format_timestamp(segment['start'])
                
                # Try to use a nice font, fallback to default
                font_size = 64
                small_font_size = 42
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                    small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", small_font_size)
                except:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", small_font_size)
                    except:
                        font = ImageFont.load_default()
                        small_font = ImageFont.load_default()
                
                # Add large timestamp in bottom-right with theme color
                text_bbox = draw.textbbox((0, 0), timestamp, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                margin = 30
                x = img.width - text_width - margin
                y = img.height - text_height - margin
                
                # Draw background with segment color
                draw.rectangle([
                    x - 20, y - 15,
                    x + text_width + 20, y + text_height + 15
                ], fill=gradient_color)
                
                # Draw timestamp text
                draw.text((x, y), timestamp, fill=(255, 255, 255), font=font)
                
                # Add large segment indicator
                segment_text = f"SEGMENT {i+1}"
                segment_bbox = draw.textbbox((0, 0), segment_text, font=small_font)
                segment_width = segment_bbox[2] - segment_bbox[0]
                segment_height = segment_bbox[3] - segment_bbox[1]
                
                # Position in top-left
                seg_x = margin
                seg_y = margin
                
                # Draw background for segment indicator with contrasting color
                contrast_color = (255 - gradient_color[0], 255 - gradient_color[1], 255 - gradient_color[2])
                draw.rectangle([
                    seg_x - 20, seg_y - 15,
                    seg_x + segment_width + 20, seg_y + segment_height + 15
                ], fill=contrast_color)
                
                # Draw segment text
                draw.text((seg_x, seg_y), segment_text, fill=gradient_color, font=small_font)
                
                # Add color theme name in top-right
                color_name = color_scheme["name"]
                color_bbox = draw.textbbox((0, 0), color_name, font=small_font)
                color_width = color_bbox[2] - color_bbox[0]
                color_height = color_bbox[3] - color_bbox[1]
                
                color_x = img.width - color_width - margin
                color_y = margin
                
                # Semi-transparent background
                draw.rectangle([
                    color_x - 15, color_y - 10,
                    color_x + color_width + 15, color_y + color_height + 10
                ], fill=(0, 0, 0, 150))
                
                draw.text((color_x, color_y), color_name, fill=gradient_color, font=small_font)
                
                # Save the customized thumbnail
                thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                img.save(thumbnail_path, "PNG")
                thumbnails.append(str(thumbnail_path))
                
            except Exception as e:
                print(f"Failed to generate custom thumbnail {i+1}: {e}")
                thumbnails.append(None)
        
        print(f"✅ Generated {len([t for t in thumbnails if t])} visually distinct thumbnails")
        return thumbnails
    
    def _format_timestamp(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        if seconds < 3600:
            return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

class HTMLGenerator:
    """Generate the final HTML page"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
    
    def generate(self, youtube_url, video_title, description, segments, thumbnails):
        """Generate the HTML highlight page"""
        video_id = self._extract_video_id(youtube_url)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description} - Video Highlights</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .video-container {{
            margin-bottom: 40px;
            text-align: center;
        }}
        
        .video-wrapper {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .video-wrapper iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }}
        
        .highlights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }}
        
        .highlight-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            color: white;
            cursor: pointer;
            position: relative;
        }}
        
        .highlight-card:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }}
        
        .highlight-card:active {{
            transform: translateY(-3px);
        }}
        
        .thumbnail {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .placeholder-thumbnail {{
            width: 100%;
            height: 180px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            opacity: 0.7;
        }}
        
        .summary {{
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 15px;
            min-height: 80px;
        }}
        
        .timestamp {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 10px;
        }}
        
        .watch-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
        }}
        
        .watch-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4);
        }}
        
        .youtube-thumbnail {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .watch-btn {{
            background: none;
            border: none;
            font: inherit;
            cursor: pointer;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 60px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .highlights-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{description}</h1>
            <p>Key highlights from the video</p>
        </div>
        
        <div class="video-container">
            <div class="video-wrapper">
                <iframe id="youtube-player" src="https://www.youtube.com/embed/{video_id}?enablejsapi=1" 
                        allowfullscreen></iframe>
            </div>
        </div>
        
        <div class="highlights-grid">
"""
        
        # Add highlight cards
        # Ensure thumbnails list is at least as long as segments
        thumbnails_padded = thumbnails + [None] * (len(segments) - len(thumbnails))
        
        for i, segment in enumerate(segments):
            start_time = int(segment['start'])
            timestamp_display = self._format_timestamp(segment['start'])
            thumbnail = thumbnails_padded[i] if i < len(thumbnails_padded) else None
            
            # Use local thumbnail if available, otherwise fallback to YouTube API
            if thumbnail and Path(thumbnail).exists():
                thumbnail_html = f'<img src="{Path(thumbnail).name}" alt="Thumbnail {i+1}" class="thumbnail">'
            else:
                # Use YouTube's thumbnail API as final fallback
                youtube_thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                thumbnail_html = f'<img src="{youtube_thumb_url}" alt="Thumbnail {i+1}" class="youtube-thumbnail">'
            
            html_content += f"""
            <div class="highlight-card" data-timestamp="{start_time}">
                {thumbnail_html}
                <div class="summary">{segment.get('summary', segment['text'][:200] + '...')}</div>
                <div class="timestamp">Starts at {timestamp_display}</div>
                <button class="watch-btn">Watch Segment</button>
            </div>
"""
        
        html_content += """
        </div>
        
        <div class="footer">
            <p>Generated with YouTube Highlight Generator</p>
        </div>
    </div>
    
    <script>
        let player;
        let playerReady = false;
        
        // Load YouTube IFrame API
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        
        // YouTube API callback
        function onYouTubeIframeAPIReady() {
            player = new YT.Player('youtube-player', {
                events: {
                    'onReady': onPlayerReady,
                    'onError': onPlayerError
                }
            });
        }
        
        function onPlayerReady(event) {
            playerReady = true;
            console.log('YouTube player ready');
            setupCardClickHandlers();
        }
        
        function onPlayerError(event) {
            console.error('YouTube player error:', event.data);
            // Fall back to basic method
            playerReady = false;
        }
        
        function seekToTime(seconds) {
            console.log('Seeking to:', seconds, 'seconds');
            
            if (playerReady && player && player.seekTo) {
                // Use YouTube API
                player.seekTo(seconds, true);
                player.playVideo();
            } else {
                // Fallback: reload iframe with timestamp
                const iframe = document.getElementById('youtube-player');
                const src = iframe.src;
                const baseUrl = src.split('?')[0];
                iframe.src = baseUrl + '?enablejsapi=1&start=' + seconds + '&autoplay=1';
            }
            
            // Smooth scroll to video
            document.querySelector('.video-container').scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
        
        function setupCardClickHandlers() {
            // Make entire cards clickable
            document.querySelectorAll('.highlight-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    // Don't trigger if clicking a link inside the card
                    if (e.target.tagName === 'A') return;
                    
                    const timestamp = parseInt(this.getAttribute('data-timestamp'));
                    if (!isNaN(timestamp)) {
                        seekToTime(timestamp);
                    }
                });
            });
        }
        
        // Set up handlers when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            // Try to set up handlers immediately
            setupCardClickHandlers();
            
            // Also try again after a delay in case player loads slowly
            setTimeout(setupCardClickHandlers, 2000);
        });
    </script>
</body>
</html>
"""
        
        # Save HTML file
        html_path = self.output_dir / "index.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML page generated: {html_path}")
        return str(html_path)
    
    def _extract_video_id(self, youtube_url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return "unknown"
    
    def _format_timestamp(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        if seconds < 3600:
            return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def main():
    parser = argparse.ArgumentParser(description="Generate YouTube video highlights")
    parser.add_argument("youtube_url", help="YouTube video URL")
    parser.add_argument("transcript_file", help="Path to transcript file (.vtt or .srt)")
    parser.add_argument("--description", default="Video Highlights", help="Page description")
    parser.add_argument("--keywords", nargs="+", default=["introduction", "conclusion"], help="Keywords to find interesting segments")
    parser.add_argument("--cards", type=int, default=4, help="Number of highlight cards to generate")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    print("🎬 YouTube Highlight Generator")
    print("=" * 40)
    
    # Parse transcript
    print(f"📄 Parsing transcript: {args.transcript_file}")
    transcript_path = Path(args.transcript_file)
    
    if not transcript_path.exists():
        print(f"❌ Transcript file not found: {args.transcript_file}")
        sys.exit(1)
    
    if transcript_path.suffix.lower() == '.vtt':
        transcript_segments = TranscriptParser.parse_vtt(args.transcript_file)
    elif transcript_path.suffix.lower() == '.srt':
        transcript_segments = TranscriptParser.parse_srt(args.transcript_file)
    else:
        print("❌ Unsupported transcript format. Use .vtt or .srt files.")
        sys.exit(1)
    
    if not transcript_segments:
        print("❌ No transcript segments found. Check your transcript file.")
        sys.exit(1)
    
    print(f"✅ Parsed {len(transcript_segments)} transcript segments")
    
    # Find interesting segments
    print(f"🔍 Finding segments with keywords: {', '.join(args.keywords)}")
    segment_finder = SegmentFinder(args.keywords)
    interesting_segments = segment_finder.find_segments(transcript_segments, args.cards)
    
    if not interesting_segments:
        print("❌ No interesting segments found. Try different keywords.")
        sys.exit(1)
    
    print(f"✅ Found {len(interesting_segments)} interesting segments")
    
    # Initialize AI summarizer
    summarizer = AISummarizer()
    
    # Summarize segments
    print("📝 Summarizing segments...")
    for segment in interesting_segments:
        segment['summary'] = summarizer.summarize(segment['text'])
    
    # Process video
    video_processor = VideoProcessor(args.output_dir)
    video_path, video_title = video_processor.download_video(args.youtube_url)
    
    # Always try to extract/generate thumbnails
    thumbnails = video_processor.extract_thumbnails(video_path, interesting_segments)
    
    # Generate HTML
    print("🌐 Generating HTML page...")
    html_generator = HTMLGenerator(args.output_dir)
    html_path = html_generator.generate(
        args.youtube_url,
        video_title or "Unknown Video",
        args.description,
        interesting_segments,
        thumbnails
    )
    
    print("\n🎉 Success!")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"🌐 HTML file: {html_path}")
    print(f"📦 Ready to deploy to Netlify!")
    
    # Show segment info
    print(f"\n📊 Generated {len(interesting_segments)} highlight cards:")
    for i, segment in enumerate(interesting_segments):
        timestamp = video_processor._format_timestamp if hasattr(video_processor, '_format_timestamp') else HTMLGenerator(args.output_dir)._format_timestamp
        print(f"  {i+1}. {timestamp(segment['start'])} - {segment.get('keyword', 'general')}")

if __name__ == "__main__":
    main()