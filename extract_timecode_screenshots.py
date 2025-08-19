#!/usr/bin/env python3
"""
Extract actual video screenshots at specific timecodes using yt-dlp and ffmpeg
"""

import os
import sys
import subprocess
from pathlib import Path
import json

def extract_timecode_screenshots(video_url, segments, output_dir):
    """Extract screenshots from YouTube video at specific timecodes"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"🎬 Extracting screenshots from: {video_url}")
    
    # Check if yt-dlp is available
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        print("✅ yt-dlp found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp not found. Install with: brew install yt-dlp")
        return []
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ ffmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Install with: brew install ffmpeg")
        return []
    
    screenshots = []
    
    for i, segment in enumerate(segments):
        try:
            # Calculate the middle timestamp of the segment
            start_time = segment['start']
            end_time = segment.get('end', start_time + 10)  # Default 10 second segment
            mid_time = (start_time + end_time) / 2
            
            # Format timestamp for ffmpeg (HH:MM:SS)
            hours = int(mid_time // 3600)
            minutes = int((mid_time % 3600) // 60)
            seconds = int(mid_time % 60)
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            screenshot_path = output_path / f"screenshot_{i+1:03d}.jpg"
            
            print(f"📸 Extracting screenshot {i+1} at {timestamp}...")
            
            # Use yt-dlp to extract screenshot at specific timestamp
            cmd = [
                'yt-dlp',
                '--no-download',
                '--write-thumbnail',
                '--skip-download',
                f'--external-downloader-args=-ss {timestamp} -frames:v 1',
                '--external-downloader', 'ffmpeg',
                '-o', str(screenshot_path.with_suffix('')),
                video_url
            ]
            
            # Alternative approach: download video segment and extract frame
            # This is more reliable for getting exact timestamps
            temp_video = output_path / f"temp_segment_{i+1}.mp4"
            
            # Download a small segment around the timestamp
            download_cmd = [
                'yt-dlp', 
                '-f', 'worst[ext=mp4]',  # Use lowest quality for speed
                '--external-downloader', 'ffmpeg',
                '--external-downloader-args', f'-ss {max(0, mid_time-2)} -t 4',  # 4 second segment
                '-o', str(temp_video),
                video_url
            ]
            
            result = subprocess.run(download_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and temp_video.exists():
                # Extract frame from the middle of this segment
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', str(temp_video),
                    '-ss', '2',  # 2 seconds into our 4-second clip (the middle)
                    '-frames:v', '1',
                    '-q:v', '2',  # High quality
                    '-y',  # Overwrite existing
                    str(screenshot_path)
                ]
                
                ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if ffmpeg_result.returncode == 0 and screenshot_path.exists():
                    print(f"✅ Screenshot {i+1} saved: {screenshot_path}")
                    screenshots.append(str(screenshot_path))
                    
                    # Clean up temp video
                    temp_video.unlink()
                else:
                    print(f"❌ Failed to extract screenshot {i+1}: {ffmpeg_result.stderr}")
                    screenshots.append(None)
            else:
                print(f"❌ Failed to download video segment {i+1}: {result.stderr}")
                screenshots.append(None)
                
        except Exception as e:
            print(f"❌ Error extracting screenshot {i+1}: {e}")
            screenshots.append(None)
    
    successful_screenshots = len([s for s in screenshots if s])
    print(f"\n✅ Extracted {successful_screenshots}/{len(segments)} screenshots")
    
    return screenshots

def update_html_with_screenshots(html_file, screenshots):
    """Update HTML file to use the new screenshots"""
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Replace thumbnail references
    for i, screenshot in enumerate(screenshots):
        if screenshot and Path(screenshot).exists():
            old_img = f'<img src="thumbnail_{i+1:03d}.png" alt="Thumbnail {i+1}" class="thumbnail">'
            new_img = f'<img src="{Path(screenshot).name}" alt="Screenshot {i+1}" class="thumbnail">'
            content = content.replace(old_img, new_img)
            print(f"✅ Updated HTML for screenshot {i+1}")
        else:
            print(f"⚠️  Keeping fallback thumbnail for segment {i+1}")
    
    # Save updated HTML
    with open(html_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated HTML file: {html_file}")

def main():
    # Configuration for the DeepMind Genie video
    video_url = "https://www.youtube.com/watch?v=ekgvWeHidJs"
    
    # Segments from the transcript (start times in seconds)
    segments = [
        {"start": 0, "end": 12},      # "The world exclusive of what is..."
        {"start": 13, "end": 24},     # "I think it's very hard to exactly measure..."
        {"start": 25, "end": 39},     # "Google DeepMind has been slaying so hard..."
        {"start": 2400, "end": 2420}  # "I spoke to a startup recently..." (40:00)
    ]
    
    output_dir = "/Volumes/Home/Remote Home/Dev1/genie3_highlights_unique"
    html_file = f"{output_dir}/index.html"
    
    print("🎬 YouTube Screenshot Extractor")
    print("=" * 40)
    
    # Extract screenshots
    screenshots = extract_timecode_screenshots(video_url, segments, output_dir)
    
    # Update HTML if we got screenshots
    if any(screenshots):
        update_html_with_screenshots(html_file, screenshots)
        print("\n🎉 Screenshot extraction complete!")
        print(f"📁 Screenshots saved to: {output_dir}")
        print(f"🌐 Updated HTML: {html_file}")
    else:
        print("\n❌ No screenshots were successfully extracted")
        print("Make sure yt-dlp and ffmpeg are installed:")
        print("  brew install yt-dlp ffmpeg")

if __name__ == "__main__":
    main()