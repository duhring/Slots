#!/usr/bin/env python3
"""
Manually update HTML to use different YouTube thumbnail variants
This creates visual variety without needing external tools
"""

def update_html_with_youtube_variants():
    """Update HTML to use different YouTube thumbnail variants for visual variety"""
    
    html_file = "/Volumes/Home/Remote Home/Dev1/genie3_highlights_unique/index.html"
    video_id = "ekgvWeHidJs"
    
    # Different YouTube thumbnail APIs for variety
    thumbnail_variants = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",     # Segment 1 - High res default
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",        # Segment 2 - High quality
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",        # Segment 3 - Medium quality  
        f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",        # Segment 4 - Standard def
    ]
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Replace each thumbnail with different variant
    replacements = [
        ('src="thumbnail_001.png"', f'src="{thumbnail_variants[0]}"'),
        ('src="thumbnail_002.png"', f'src="{thumbnail_variants[1]}"'),
        ('src="thumbnail_003.png"', f'src="{thumbnail_variants[2]}"'),  
        ('src="thumbnail_004.png"', f'src="{thumbnail_variants[3]}"'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
        print(f"✅ Updated: {old} -> {new}")
    
    # Save updated HTML
    with open(html_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated HTML file: {html_file}")
    print("\nNow each segment uses a different YouTube thumbnail variant:")
    print("- Segment 1 (Orange): maxresdefault.jpg")
    print("- Segment 2 (Blue): hqdefault.jpg") 
    print("- Segment 3 (Purple): mqdefault.jpg")
    print("- Segment 4 (Green): sddefault.jpg")

if __name__ == "__main__":
    update_html_with_youtube_variants()