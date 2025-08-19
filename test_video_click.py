#!/usr/bin/env python3
"""
Test script to verify that video card clicks work properly
"""

import os
from pathlib import Path
from generate_video_cards import HTMLGenerator

def test_html_generation():
    """Test that HTML is generated with proper click handlers"""
    
    # Create test data
    test_segments = [
        {
            'start': 0,
            'text': 'Introduction to the video',
            'summary': 'This is the introduction'
        },
        {
            'start': 30,
            'text': 'Main content begins',
            'summary': 'The main content starts here'
        },
        {
            'start': 120,
            'text': 'Conclusion of the video',
            'summary': 'Wrapping up the discussion'
        }
    ]
    
    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate HTML
    generator = HTMLGenerator(str(output_dir))
    html_path = generator.generate(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        video_title="Test Video",
        description="Testing video card clicks",
        segments=test_segments,
        thumbnails=[]
    )
    
    # Read generated HTML
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Check for key improvements
    checks = [
        ('data-timestamp=' in html_content, "✅ Cards have data-timestamp attributes"),
        ('cursor: pointer' in html_content, "✅ Cards have pointer cursor"),
        ('onYouTubeIframeAPIReady' in html_content, "✅ YouTube IFrame API is integrated"),
        ('playerReady' in html_content, "✅ Player ready state tracking"),
        ('setupCardClickHandlers' in html_content, "✅ Card click handlers setup"),
        ('highlight-card:active' in html_content, "✅ Active state styling added"),
        ('fallback' in html_content.lower(), "✅ Fallback mechanism included")
    ]
    
    print("🧪 Testing HTML Generation:")
    print("=" * 40)
    
    all_passed = True
    for check, message in checks:
        if check:
            print(message)
        else:
            print(f"❌ Failed: {message}")
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("✨ All tests passed! Video cards should now be clickable.")
        print(f"📁 Test HTML generated at: {html_path}")
        print("\nTo test in browser:")
        print(f"  cd {output_dir} && python3 -m http.server 8000")
        print("  Then open http://localhost:8000")
    else:
        print("⚠️ Some tests failed. Check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    test_html_generation()