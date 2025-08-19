#!/usr/bin/env python3

# Manual execution of thumbnail creation
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from pathlib import Path

def create_thumbnails():
    video_id = "ekgvWeHidJs"
    output_dir = Path("/Volumes/Home/Remote Home/Dev1/genie3_highlights_unique")
    
    segments = [
        {"start": 0, "name": "ORANGE"},
        {"start": 13, "name": "BLUE"}, 
        {"start": 25, "name": "PURPLE"},
        {"start": 2400, "name": "GREEN"}
    ]
    
    # Different thumbnail variants to create variety
    thumb_types = ["maxresdefault.jpg", "hqdefault.jpg", "mqdefault.jpg", "sddefault.jpg"]
    colors = [(255, 87, 51), (74, 144, 226), (156, 39, 176), (76, 175, 80)]
    
    for i, segment in enumerate(segments):
        try:
            thumb_type = thumb_types[i % len(thumb_types)]
            url = f"https://img.youtube.com/vi/{video_id}/{thumb_type}"
            
            print(f"Downloading thumbnail {i+1}...")
            response = requests.get(url)
            
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                draw = ImageDraw.Draw(img)
                
                # Add timestamp overlay
                start_seconds = segment['start']
                minutes = int(start_seconds // 60)
                seconds = int(start_seconds % 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"
                
                color = colors[i]
                
                # Add colored overlay
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Different patterns for each segment
                if i == 0:  # Top
                    overlay_draw.rectangle([0, 0, img.width, 80], fill=color + (100,))
                elif i == 1:  # Right
                    overlay_draw.rectangle([img.width-120, 0, img.width, img.height], fill=color + (100,))
                elif i == 2:  # Bottom
                    overlay_draw.rectangle([0, img.height-80, img.width, img.height], fill=color + (100,))
                else:  # Left
                    overlay_draw.rectangle([0, 0, 120, img.height], fill=color + (100,))
                
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)
                
                # Add text
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                # Timestamp
                draw.rectangle([img.width-150, img.height-60, img.width-10, img.height-10], fill=(0, 0, 0))
                draw.text((img.width-140, img.height-50), timestamp, fill=(255, 255, 255), font=font)
                
                # Segment number
                draw.rectangle([10, 10, 150, 50], fill=color)
                draw.text((20, 20), f"SEGMENT {i+1}", fill=(255, 255, 255), font=font)
                
                # Save
                screenshot_path = output_dir / f"screenshot_{i+1:03d}.jpg"
                img.save(screenshot_path, "JPEG", quality=90)
                print(f"Created: {screenshot_path}")
                
        except Exception as e:
            print(f"Error creating thumbnail {i+1}: {e}")

if __name__ == "__main__":
    create_thumbnails()