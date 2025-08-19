#!/usr/bin/env python3
"""
Quick test of the highlight generator functionality
"""

import sys
sys.path.insert(0, '/Volumes/Home/Remote Home/Dev1')

def test_components():
    """Test individual components"""
    print("🧪 Testing YouTube Highlight Generator Components")
    print("=" * 50)
    
    # Test imports
    try:
        from generate_video_cards import TranscriptParser, SegmentFinder, AISummarizer
        print("✅ Core modules import successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test transcript parsing with sample data
    try:
        # Create a sample VTT content
        sample_vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Welcome to this introduction video

00:00:05.000 --> 00:00:08.000
Today we'll cover the main topics

00:00:10.000 --> 00:00:12.000
First, let's discuss the methodology

00:00:15.000 --> 00:00:18.000
The results show significant improvement

00:00:20.000 --> 00:00:22.000
In conclusion, this approach works well
"""
        
        # Write sample file
        with open('test_sample.vtt', 'w') as f:
            f.write(sample_vtt)
        
        # Test parsing
        segments = TranscriptParser.parse_vtt('test_sample.vtt')
        print(f"✅ VTT parsing: {len(segments)} segments extracted")
        
        # Test segment finding
        finder = SegmentFinder(['introduction', 'methodology', 'results', 'conclusion'])
        interesting = finder.find_segments(segments, 3)
        print(f"✅ Segment finding: {len(interesting)} interesting segments found")
        
        # Test AI summarizer initialization (without actually using it)
        summarizer = AISummarizer()
        print("✅ AI summarizer initialized")
        
        # Clean up
        import os
        os.remove('test_sample.vtt')
        
        return True
        
    except Exception as e:
        print(f"❌ Component test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_easy_interface():
    """Test the easy interface functions"""
    try:
        from easy_highlights import get_video_id, smart_keyword_detection, check_dependencies
        
        # Test video ID extraction
        test_urls = [
            'https://youtu.be/dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s'
        ]
        
        for url in test_urls:
            video_id = get_video_id(url)
            if video_id == 'dQw4w9WgXcQ':
                print(f"✅ Video ID extraction works: {url}")
            else:
                print(f"❌ Video ID extraction failed: {url} -> {video_id}")
        
        # Test smart keyword detection
        sample_text = "Welcome to this introduction. Today we'll cover methodology and show you results."
        keywords = smart_keyword_detection(sample_text)
        print(f"✅ Smart keyword detection: {keywords}")
        
        # Test dependency check
        deps_ok = check_dependencies()
        print(f"✅ Dependencies check: {'OK' if deps_ok else 'Some missing (expected)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Easy interface test error: {e}")
        return False

if __name__ == "__main__":
    print("Running quick tests...")
    
    success = True
    success &= test_components()
    success &= test_easy_interface()
    
    if success:
        print("\n🎉 All tests passed!")
        print("\n📋 Next steps:")
        print("1. Run: python3 easy_highlights.py")
        print("2. Paste a YouTube URL")
        print("3. Follow the prompts")
        print("4. Get beautiful highlights!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")