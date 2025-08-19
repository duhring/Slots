#!/usr/bin/env python3
"""
Simple script to create visually distinct thumbnails
"""

import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from pathlib import Path

def create_distinct_thumbnails(video_id, output_dir, segments):
    """Create visually distinct thumbnails for each segment"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Download base thumbnail from YouTube
    base_thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    try:
        response = requests.get(base_thumbnail_url, timeout=10)
        base_image = Image.open(io.BytesIO(response.content))
        print(f"✅ Downloaded base thumbnail: {base_image.size}")
    except:
        print("❌ Failed to download base thumbnail")
        return []
    
    # Color schemes for each segment
    color_schemes = [
        {"color": (255, 87, 51), "name": "ORANGE"},      # Orange
        {"color": (74, 144, 226), "name": "BLUE"},       # Blue  
        {"color": (156, 39, 176), "name": "PURPLE"},     # Purple
        {"color": (76, 175, 80), "name": "GREEN"},       # Green
    ]
    
    thumbnails = []
    
    for i, segment in enumerate(segments):
        try:
            # Create a copy of the base image
            img = base_image.copy()
            
            # Get color scheme
            scheme = color_schemes[i % len(color_schemes)]
            color = scheme["color"]
            name = scheme["name"]
            
            # Create a very obvious overlay
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Make VERY obvious overlays
            alpha = 120  # More visible
            if i == 0:  # Top section - Orange
                overlay_draw.rectangle([0, 0, img.width, img.height//2], 
                                     fill=color + (alpha,))
            elif i == 1:  # Right section - Blue
                overlay_draw.rectangle([img.width//2, 0, img.width, img.height], 
                                     fill=color + (alpha,))
            elif i == 2:  # Bottom section - Purple
                overlay_draw.rectangle([0, img.height//2, img.width, img.height], 
                                     fill=color + (alpha,))
            else:  # Left section - Green
                overlay_draw.rectangle([0, 0, img.width//2, img.height], 
                                     fill=color + (alpha,))
            
            # Apply the overlay
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
            # Add text overlays
            draw = ImageDraw.Draw(img)
            
            # Format timestamp
            timestamp = f"{int(segment['start']//60):02d}:{int(segment['start']%60):02d}"
            
            # Use default font since we're keeping it simple
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
                small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Big timestamp in bottom-right with theme color
            margin = 40
            draw.rectangle([img.width - 200, img.height - 120, img.width - 20, img.height - 20], 
                         fill=color)
            draw.text((img.width - 180, img.height - 100), timestamp, fill=(255, 255, 255), font=font)
            
            # Segment number in top-left
            segment_text = f"SEGMENT {i+1}"
            draw.rectangle([20, 20, 320, 90], fill=(255, 255, 255))
            draw.text((30, 30), segment_text, fill=color, font=small_font)
            
            # Color name in top-right
            draw.rectangle([img.width - 200, 20, img.width - 20, 90], fill=(0, 0, 0))
            draw.text((img.width - 180, 30), name, fill=color, font=small_font)
            
            # Save thumbnail
            thumbnail_path = output_path / f"thumbnail_{i+1:03d}.png"
            img.save(thumbnail_path, "PNG")
            thumbnails.append(str(thumbnail_path))
            print(f"✅ Created thumbnail {i+1}: {thumbnail_path}")
            
        except Exception as e:
            print(f"❌ Failed to create thumbnail {i+1}: {e}")
            thumbnails.append(None)
    
    return thumbnails

if __name__ == "__main__":
    # Test with DeepMind video
    segments = [
        {"start": 0, "end": 10},
        {"start": 13, "end": 25}, 
        {"start": 25, "end": 30},
        {"start": 2400, "end": 2410}
    ]
    
    thumbnails = create_distinct_thumbnails(
        "ekgvWeHidJs", 
        "genie3_manual_thumbs",
        segments
    )
    
    print(f"\n✅ Created {len([t for t in thumbnails if t])} distinct thumbnails")
    print("Files created:")
    for thumb in thumbnails:
        if thumb:
            print(f"  - {thumb}")