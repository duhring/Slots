#!/usr/bin/env python3
"""
One-Command YouTube Highlight Generator
Handles everything: transcript conversion, highlight generation, and screenshot extraction
"""

import os
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime

# Set environment variable to avoid tokenizers parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import our existing modules
from transcript_converter import convert_raw_transcript_to_vtt
from improved_summarizer import ImprovedSummarizer
from generate_video_cards import (
    TranscriptParser, SegmentFinder, VideoProcessor, HTMLGenerator
)

def one_command_highlights():
    """Single command to create complete highlight page"""
    
    print("🚀 One-Command YouTube Highlight Generator")
    print("=" * 50)
    
    # Step 1: Get YouTube URL
    youtube_url = input("📺 Enter YouTube URL: ").strip()
    if not youtube_url:
        print("❌ YouTube URL required")
        return
    
    # Step 2: Get raw transcript
    print("\n📝 Paste your YouTube transcript below.")
    print("(Any format - with or without timestamps)")
    print("Press Enter twice when done:\n")
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    if not lines:
        print("❌ No transcript provided")
        return
    
    raw_transcript = '\n'.join(lines)
    
    # Step 3: Get options
    title = input("\n📰 Page title (or press Enter for auto-detect): ").strip()
    
    print("\n🔍 Keywords to find interesting segments:")
    print("Examples: introduction, conclusion, demo, important, key, amazing")
    keywords_input = input("Enter keywords (comma-separated) or press Enter for defaults: ").strip()
    
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(',')]
    else:
        keywords = ['introduction', 'conclusion', 'important', 'key', 'amazing', 'demo', 'show']
    
    num_cards_input = input("\n🎴 Number of highlight cards (default: 4): ").strip()
    num_cards = int(num_cards_input) if num_cards_input.isdigit() else 4
    
    # Step 4: Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"highlights_{timestamp}"
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📁 Creating output directory: {output_dir}")
    
    try:
        # Step 5: Convert transcript to VTT
        print("📄 Converting transcript to VTT format...")
        vtt_file = output_path / "transcript.vtt"
        convert_raw_transcript_to_vtt(raw_transcript, str(vtt_file))
        
        # Step 6: Parse transcript
        print("📖 Parsing transcript...")
        transcript_segments = TranscriptParser.parse_vtt(str(vtt_file))
        
        if not transcript_segments:
            print("❌ Failed to parse transcript")
            return
        
        print(f"✅ Parsed {len(transcript_segments)} transcript segments")
        
        # Step 7: Find interesting segments
        print(f"🔍 Finding segments with keywords: {', '.join(keywords)}")
        segment_finder = SegmentFinder(keywords)
        interesting_segments = segment_finder.find_segments(transcript_segments, num_cards)
        
        if not interesting_segments:
            print("❌ No interesting segments found")
            return
        
        print(f"✅ Found {len(interesting_segments)} interesting segments")
        
        # Step 8: AI Summarization
        print("🤖 Generating AI summaries...")
        summarizer = ImprovedSummarizer()
        
        for segment in interesting_segments:
            segment['summary'] = summarizer.summarize(segment['text'])
        
        # Step 9: Process video and extract screenshots
        print("📸 Processing video and extracting screenshots...")
        video_processor = VideoProcessor(str(output_path))
        video_path, video_title = video_processor.download_video(youtube_url)
        
        # Always try to extract/generate thumbnails
        thumbnails = video_processor.extract_thumbnails(video_path, interesting_segments)
        
        # Use video title if not provided
        if not title:
            title = video_title or "Video Highlights"
        
        # Step 10: Generate HTML
        print("🌐 Generating HTML page...")
        html_generator = HTMLGenerator(str(output_path))
        html_path = html_generator.generate(
            youtube_url,
            video_title or "Unknown Video",
            title,
            interesting_segments,
            thumbnails
        )
        
        # Step 11: Run screenshot extraction if tools are available
        print("🖼️  Extracting real video screenshots...")
        try:
            # Check if we have the tools
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            
            # Extract real screenshots
            screenshots = extract_real_screenshots(youtube_url, interesting_segments, str(output_path))
            
            # Update HTML to use real screenshots
            if screenshots and any(screenshots):
                update_html_with_real_screenshots(html_path, screenshots)
                print("✅ Updated HTML with real video screenshots")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  yt-dlp/ffmpeg not available - using fallback thumbnails")
            print("💡 Install with: brew install yt-dlp ffmpeg")
        
        # Step 12: Success!
        print("\n🎉 SUCCESS! Your highlight page is ready!")
        print("=" * 50)
        print(f"📁 Output directory: {output_dir}/")
        print(f"🌐 HTML file: {html_path}")
        print(f"📦 Ready to deploy!")
        
        # Show segment info
        print(f"\n📊 Generated {len(interesting_segments)} highlight cards:")
        for i, segment in enumerate(interesting_segments):
            minutes = int(segment['start'] // 60)
            seconds = int(segment['start'] % 60)
            keyword = segment.get('keyword', 'general')
            print(f"  {i+1}. {minutes:02d}:{seconds:02d} - {keyword}")
        
        # Offer to open the file
        open_now = input(f"\n🚀 Open the highlight page now? (y/n): ").strip().lower()
        if open_now in ['y', 'yes']:
            os.system(f'open "{html_path}"')
        
        return output_dir
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_real_screenshots(youtube_url, segments, output_dir):
    """Extract real video screenshots using yt-dlp and ffmpeg"""
    
    screenshots = []
    output_path = Path(output_dir)
    
    for i, segment in enumerate(segments):
        try:
            # Calculate mid-point of segment
            start_time = segment['start']
            end_time = segment.get('end', start_time + 10)
            mid_time = (start_time + end_time) / 2
            
            # Format timestamp for ffmpeg
            hours = int(mid_time // 3600)
            minutes = int((mid_time % 3600) // 60)
            seconds = int(mid_time % 60)
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            screenshot_path = output_path / f"screenshot_{i+1:03d}.jpg"
            temp_video = output_path / f"temp_segment_{i+1}.mp4"
            
            print(f"📸 Extracting screenshot {i+1} at {timestamp}...")
            
            # Download small video segment
            download_cmd = [
                'yt-dlp', 
                '-f', 'worst[ext=mp4]',
                '--external-downloader', 'ffmpeg',
                '--external-downloader-args', f'-ss {max(0, mid_time-2)} -t 4',
                '-o', str(temp_video),
                youtube_url
            ]
            
            result = subprocess.run(download_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and temp_video.exists():
                # Extract frame
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', str(temp_video),
                    '-ss', '2',
                    '-frames:v', '1',
                    '-q:v', '2',
                    '-y',
                    str(screenshot_path)
                ]
                
                ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if ffmpeg_result.returncode == 0 and screenshot_path.exists():
                    screenshots.append(str(screenshot_path))
                    print(f"✅ Screenshot {i+1} saved")
                    temp_video.unlink()  # Clean up
                else:
                    screenshots.append(None)
            else:
                screenshots.append(None)
                
        except Exception as e:
            print(f"❌ Failed to extract screenshot {i+1}: {e}")
            screenshots.append(None)
    
    return screenshots

def update_html_with_real_screenshots(html_path, screenshots):
    """Update HTML to use real screenshot files"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace thumbnail references
    for i, screenshot in enumerate(screenshots):
        if screenshot and Path(screenshot).exists():
            # Look for existing img tags and update them
            old_patterns = [
                f'src="thumbnail_{i+1:03d}.png"',
                f'src="https://img.youtube.com/vi/',
            ]
            
            screenshot_name = Path(screenshot).name
            new_src = f'src="{screenshot_name}"'
            
            # Replace various possible patterns
            import re
            pattern = f'<img[^>]*alt="[^"]*{i+1}[^"]*"[^>]*>'
            matches = re.findall(pattern, content)
            
            if matches:
                old_img = matches[0]
                new_img = re.sub(r'src="[^"]*"', new_src, old_img)
                new_img = re.sub(r'alt="[^"]*"', f'alt="Screenshot {i+1}"', new_img)
                content = content.replace(old_img, new_img)
    
    # Save updated HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    one_command_highlights()

if __name__ == "__main__":
    main()