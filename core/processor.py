"""
Video processing module for editorial highlights
Handles transcript fetching, segment extraction, and thumbnail generation
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter
import requests
from PIL import Image, ImageDraw, ImageFont


class VideoProcessor:
    def __init__(self):
        self.transcript_cache = {}
        
    def get_transcript(self, url: str) -> str:
        """Download transcript using yt-dlp or prompt for manual input"""
        video_id = self.extract_video_id(url)
        
        # Try to download transcript with yt-dlp
        try:
            print("✓ Downloading transcript...")
            result = subprocess.run(
                ['yt-dlp', '--write-subs', '--write-auto-subs', '--sub-lang', 'en', 
                 '--skip-download', '--sub-format', 'vtt', '-o', f'temp_{video_id}', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Look for VTT file
            vtt_files = list(Path('.').glob(f'temp_{video_id}*.vtt'))
            if vtt_files:
                transcript = vtt_files[0].read_text()
                # Clean up temp files
                for f in vtt_files:
                    f.unlink()
                return transcript
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: Ask user to paste transcript
        print("\n⚠ Auto-download failed. Please paste transcript:")
        print("(Paste content, then press Enter twice to finish)")
        
        lines = []
        empty_count = 0
        while True:
            line = input()
            if not line:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        
        transcript = '\n'.join(lines)
        
        # Auto-detect format and convert if needed
        if not self.is_vtt_format(transcript):
            transcript = self.convert_to_vtt(transcript)
            
        return transcript
    
    def is_vtt_format(self, text: str) -> bool:
        """Check if text is in VTT format"""
        return 'WEBVTT' in text or '-->' in text
    
    def convert_to_vtt(self, text: str) -> str:
        """Convert plain text to VTT format with timestamps"""
        lines = text.strip().split('\n')
        vtt_lines = ['WEBVTT', '']
        
        # Simple conversion: Create 30-second segments
        segment_duration = 30
        current_time = 0
        
        words = ' '.join(lines).split()
        words_per_segment = len(words) // 10 or 20  # Rough estimate
        
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i+words_per_segment]
            segment_text = ' '.join(segment_words)
            
            start_time = self.seconds_to_vtt_time(current_time)
            end_time = self.seconds_to_vtt_time(current_time + segment_duration)
            
            vtt_lines.append(f'{start_time} --> {end_time}')
            vtt_lines.append(segment_text)
            vtt_lines.append('')
            
            current_time += segment_duration
        
        return '\n'.join(vtt_lines)
    
    def seconds_to_vtt_time(self, seconds: int) -> str:
        """Convert seconds to VTT timestamp format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f'{hours:02d}:{minutes:02d}:{secs:02d}.000'
    
    def get_video_info(self, url: str) -> Tuple[str, str]:
        """Extract video title and ID"""
        video_id = self.extract_video_id(url)
        
        # Try to get title with yt-dlp
        try:
            result = subprocess.run(
                ['yt-dlp', '--get-title', url],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                title = result.stdout.strip()
                return title, video_id
        except:
            pass
        
        return f"Video {video_id}", video_id
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n]+)',
            r'youtube\.com\/embed\/([^&\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Fallback: use last part of URL
        return url.split('/')[-1].split('?')[0]
    
    def detect_keywords(self, transcript: str) -> List[str]:
        """Auto-detect important keywords from transcript"""
        # Extract just the text from VTT
        text = self.extract_text_from_vtt(transcript)
        
        # Simple keyword extraction: most common meaningful words
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # Filter out common words
        stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'what',
                     'when', 'where', 'which', 'while', 'would', 'could', 'should',
                     'about', 'after', 'before', 'because', 'through', 'there', 'these',
                     'those', 'their', 'them', 'they', 'your', 'very', 'just', 'some'}
        
        filtered_words = [w for w in words if w not in stop_words]
        
        # Get top 10 most common words
        word_counts = Counter(filtered_words)
        top_keywords = [word for word, count in word_counts.most_common(10)]
        
        return top_keywords
    
    def extract_text_from_vtt(self, vtt_content: str) -> str:
        """Extract plain text from VTT content"""
        lines = vtt_content.split('\n')
        text_lines = []
        
        for line in lines:
            # Skip timestamps and metadata
            if '-->' not in line and line.strip() and not line.startswith('WEBVTT'):
                # Remove HTML tags if present
                clean_line = re.sub(r'<[^>]+>', '', line)
                text_lines.append(clean_line)
        
        return ' '.join(text_lines)
    
    def find_segments(self, transcript: str, keywords: List[str], num_segments: int) -> List[Dict]:
        """Find relevant segments based on keywords"""
        # Parse VTT into segments
        vtt_segments = self.parse_vtt_segments(transcript)
        
        if not keywords:
            # If no keywords, take evenly distributed segments
            step = len(vtt_segments) // num_segments
            selected_indices = [i * step for i in range(num_segments)]
            selected_segments = [vtt_segments[i] for i in selected_indices if i < len(vtt_segments)]
        else:
            # Score segments by keyword relevance
            scored_segments = []
            for segment in vtt_segments:
                score = 0
                text_lower = segment['text'].lower()
                for keyword in keywords:
                    score += text_lower.count(keyword.lower())
                
                if score > 0:
                    segment['score'] = score
                    scored_segments.append(segment)
            
            # Sort by score and select top N
            scored_segments.sort(key=lambda x: x['score'], reverse=True)
            selected_segments = scored_segments[:num_segments]
            
            # Sort by timestamp for chronological order
            selected_segments.sort(key=lambda x: x['start_seconds'])
        
        # Format segments
        formatted_segments = []
        for i, seg in enumerate(selected_segments[:num_segments], 1):
            formatted_segments.append({
                'timestamp': seg['timestamp'],
                'text': seg['text'],
                'start_seconds': seg['start_seconds'],
                'title': f"Segment {i}",
                'summary': seg['text'][:100] + '...'  # Placeholder
            })
        
        return formatted_segments
    
    def parse_vtt_segments(self, vtt_content: str) -> List[Dict]:
        """Parse VTT content into segments"""
        segments = []
        lines = vtt_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for timestamp line
            if '-->' in line:
                timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    
                    # Calculate seconds
                    time_parts = timestamp.split(':')
                    seconds = int(time_parts[0])*3600 + int(time_parts[1])*60 + int(time_parts[2])
                    
                    # Get text lines until next timestamp or empty line
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        segments.append({
                            'timestamp': timestamp,
                            'start_seconds': seconds,
                            'text': ' '.join(text_lines)
                        })
                    continue
            
            i += 1
        
        return segments
    
    def create_thumbnail(self, segment: Dict, output_path: Path, index: int):
        """Create a styled thumbnail for a segment"""
        # Create a colorful thumbnail with gradient
        width, height = 400, 225
        
        # Create gradient background
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Different color schemes for variety
        color_schemes = [
            ((102, 126, 234), (118, 75, 162)),   # Purple gradient
            ((251, 113, 133), (254, 202, 87)),   # Warm gradient  
            ((56, 217, 169), (80, 167, 249)),    # Cool gradient
            ((255, 94, 87), (255, 154, 0)),      # Orange gradient
            ((131, 58, 180), (253, 29, 29)),     # Red-purple gradient
        ]
        
        # Select color scheme based on index
        colors = color_schemes[index % len(color_schemes)]
        
        # Draw gradient
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
        
        # Add semi-transparent overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 100))
        img.paste(overlay, (0, 0), overlay)
        
        # Add timestamp
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw segment number
        number_text = f"{index:02d}"
        draw.text((width//2 - 30, height//2 - 40), number_text, 
                 fill=(255, 255, 255), font=font_large)
        
        # Draw timestamp
        draw.text((width//2 - 40, height//2 + 10), segment['timestamp'], 
                 fill=(255, 255, 255, 200), font=font_small)
        
        # Add emphasis indicator if present
        if segment.get('emphasis'):
            draw.rectangle([(0, 0), (width, 5)], fill=(255, 215, 0))
            draw.text((10, 10), "KEY POINT", fill=(255, 215, 0), font=font_small)
        
        # Save as JPEG with compression
        img.save(output_path, 'JPEG', quality=85, optimize=True)
        
        # Ensure file size is reasonable (under 100KB)
        if output_path.stat().st_size > 100000:
            # Re-save with more compression
            img.save(output_path, 'JPEG', quality=60, optimize=True)