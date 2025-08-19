#!/usr/bin/env python3
"""
Test script for smart thumbnail extraction
"""

import sys
from pathlib import Path
from generate_video_cards import VideoProcessor, SegmentFinder, TranscriptParser

def test_smart_extraction(video_url=None):
    """Test the smart thumbnail extraction"""
    
    # Test video URL (you can change this to any YouTube video)
    if not video_url:
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Create test segments
    test_segments = [
        {'start': 0, 'end': 30, 'text': 'Introduction segment'},
        {'start': 60, 'end': 90, 'text': 'Main content segment'},
        {'start': 120, 'end': 150, 'text': 'Conclusion segment'}
    ]
    
    # Create output directory
    output_dir = Path("test_smart_output")
    output_dir.mkdir(exist_ok=True)
    
    print("🧪 Testing Smart Thumbnail Extraction")
    print("=" * 40)
    print(f"Video URL: {video_url}")
    print(f"Segments: {len(test_segments)}")
    print()
    
    # Initialize video processor
    processor = VideoProcessor(str(output_dir))
    processor.youtube_url = video_url  # Set the URL for smart extraction
    
    # Test extraction
    print("📸 Extracting thumbnails...")
    thumbnails = processor.extract_thumbnails(None, test_segments)
    
    # Check results
    print("\n📊 Results:")
    print("-" * 40)
    
    success_count = 0
    for i, thumb in enumerate(thumbnails):
        if thumb and Path(thumb).exists():
            file_size = Path(thumb).stat().st_size / 1024  # KB
            print(f"✅ Segment {i+1}: {Path(thumb).name} ({file_size:.1f} KB)")
            success_count += 1
        else:
            print(f"❌ Segment {i+1}: Failed to extract")
    
    print("-" * 40)
    print(f"Success rate: {success_count}/{len(test_segments)} thumbnails")
    
    if success_count == len(test_segments):
        print("\n✨ All thumbnails extracted successfully!")
        print(f"📁 Check the '{output_dir}' folder to see the thumbnails")
        return True
    elif success_count > 0:
        print(f"\n⚠️ Partial success: {success_count} thumbnails extracted")
        return True
    else:
        print("\n❌ Thumbnail extraction failed")
        print("\nTroubleshooting:")
        print("1. Ensure ffmpeg is installed: brew install ffmpeg")
        print("2. Ensure yt-dlp is installed: brew install yt-dlp")
        print("3. Check internet connection")
        print("4. Try a different video URL")
        return False

if __name__ == "__main__":
    # Allow custom video URL as argument
    video_url = None
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        print(f"Using custom URL: {video_url}")
    
    success = test_smart_extraction(video_url)
    sys.exit(0 if success else 1)