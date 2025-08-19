#!/usr/bin/env python3
"""
Create timestamp-specific thumbnails from YouTube using different thumbnail APIs
"""

import requests
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

def download_youtube_thumbnails(video_id, segments, output_dir):
    """Download different YouTube thumbnail variants for each segment"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"📸 Creating timestamp-specific thumbnails for video: {video_id}")
    
    # Different YouTube thumbnail endpoints
    thumbnail_types = [
        "maxresdefault.jpg",  # High resolution default
        "hqdefault.jpg",      # High quality default
        "mqdefault.jpg",      # Medium quality default
        "sddefault.jpg",      # Standard definition default
    ]
    
    # Try to get video info for more specific thumbnails
    thumbnails = []
    
    for i, segment in enumerate(segments):
        try:
            # Use different thumbnail types for variety
            thumb_type = thumbnail_types[i % len(thumbnail_types)]
            base_url = f"https://img.youtube.com/vi/{video_id}/{thumb_type}"
            
            print(f"📥 Downloading thumbnail {i+1} ({thumb_type})...")
            
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                # Load the image
                img = Image.open(io.BytesIO(response.content))
                
                # Create timestamp overlay to make it unique
                img_with_overlay = create_timestamp_overlay(img, segment, i+1)
                
                # Save with timestamp-specific filename
                thumbnail_path = output_path / f"screenshot_{i+1:03d}.jpg"
                img_with_overlay.save(thumbnail_path, "JPEG", quality=90)
                
                thumbnails.append(str(thumbnail_path))
                print(f"✅ Created thumbnail {i+1}: {thumbnail_path}")
            else:
                print(f"❌ Failed to download thumbnail {i+1}")
                thumbnails.append(None)
                
        except Exception as e:
            print(f"❌ Error creating thumbnail {i+1}: {e}")
            thumbnails.append(None)
    
    return thumbnails

def create_timestamp_overlay(img, segment, segment_num):
    """Add timestamp and segment info overlay to make thumbnails unique"""
    
    # Make a copy to avoid modifying original
    img = img.copy()
    draw = ImageDraw.Draw(img)
    
    # Format timestamp
    start_seconds = segment['start']
    hours = int(start_seconds // 3600)
    minutes = int((start_seconds % 3600) // 60)
    seconds = int(start_seconds % 60)
    
    if hours > 0:
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        timestamp = f"{minutes:02d}:{seconds:02d}"
    
    # Color schemes for each segment
    color_schemes = [
        {"color": (255, 87, 51), "name": "ORANGE"},      # Orange
        {"color": (74, 144, 226), "name": "BLUE"},       # Blue  
        {"color": (156, 39, 176), "name": "PURPLE"},     # Purple
        {"color": (76, 175, 80), "name": "GREEN"},       # Green
    ]
    
    scheme = color_schemes[(segment_num-1) % len(color_schemes)]
    color = scheme["color"]
    name = scheme["name"]
    
    # Try to load a font
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 48)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 36)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 24)
    except:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Add semi-transparent overlay for better text visibility
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Different overlay patterns for each segment
    if segment_num == 1:  # Top band
        overlay_draw.rectangle([0, 0, img.width, 100], fill=color + (80,))
    elif segment_num == 2:  # Right band
        overlay_draw.rectangle([img.width-150, 0, img.width, img.height], fill=color + (80,))
    elif segment_num == 3:  # Bottom band
        overlay_draw.rectangle([0, img.height-100, img.width, img.height], fill=color + (80,))
    else:  # Left band
        overlay_draw.rectangle([0, 0, 150, img.height], fill=color + (80,))
    
    # Apply overlay
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Add large timestamp in bottom-right corner
    margin = 20
    bbox = draw.textbbox((0, 0), timestamp, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = img.width - text_width - margin
    y = img.height - text_height - margin
    
    # Background for timestamp
    draw.rectangle([x-15, y-10, x+text_width+15, y+text_height+10], fill=(0, 0, 0, 200))
    draw.text((x, y), timestamp, fill=(255, 255, 255), font=font_large)
    
    # Add segment identifier in top-left
    segment_text = f"SEGMENT {segment_num}"
    bbox = draw.textbbox((0, 0), segment_text, font=font_medium)
    seg_width = bbox[2] - bbox[0]
    seg_height = bbox[3] - bbox[1]
    
    draw.rectangle([margin, margin, margin+seg_width+20, margin+seg_height+15], fill=color)
    draw.text((margin+10, margin+7), segment_text, fill=(255, 255, 255), font=font_medium)
    
    # Add color name in top-right
    color_bbox = draw.textbbox((0, 0), name, font=font_small)
    color_width = color_bbox[2] - color_bbox[0]
    color_height = color_bbox[3] - color_bbox[1]
    
    color_x = img.width - color_width - margin - 10
    color_y = margin + 5
    
    draw.rectangle([color_x-10, color_y-5, color_x+color_width+10, color_y+color_height+5], 
                  fill=(255, 255, 255, 200))
    draw.text((color_x, color_y), name, fill=color, font=font_small)
    
    return img

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
    video_id = "ekgvWeHidJs"
    
    # Segments from the transcript (start times in seconds)
    segments = [
        {"start": 0, "end": 12},      # "The world exclusive of what is..."
        {"start": 13, "end": 24},     # "I think it's very hard to exactly measure..."
        {"start": 25, "end": 39},     # "Google DeepMind has been slaying so hard..."
        {"start": 2400, "end": 2420}  # "I spoke to a startup recently..." (40:00)
    ]
    
    output_dir = "/Volumes/Home/Remote Home/Dev1/genie3_highlights_unique"
    html_file = f"{output_dir}/index.html"
    
    print("📸 YouTube Timestamp Thumbnail Creator")
    print("=" * 45)
    
    # Create timestamp-specific thumbnails
    screenshots = download_youtube_thumbnails(video_id, segments, output_dir)
    
    # Update HTML if we got screenshots
    if any(screenshots):
        update_html_with_screenshots(html_file, screenshots)
        print("\n🎉 Timestamp thumbnail creation complete!")
        print(f"📁 Thumbnails saved to: {output_dir}")
        print(f"🌐 Updated HTML: {html_file}")
        
        # List created files
        print("\nCreated files:")
        for screenshot in screenshots:
            if screenshot:
                print(f"  ✅ {screenshot}")
    else:
        print("\n❌ No thumbnails were successfully created")

if __name__ == "__main__":
    main()