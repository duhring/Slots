"""
Enhanced video processing module with real screenshot extraction
Combines original processor functionality with actual video screenshots
"""

from pathlib import Path
from typing import List, Dict, Optional
from .processor import VideoProcessor
from .video_screenshot import VideoScreenshotExtractor
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class EnhancedVideoProcessor(VideoProcessor):
    """Enhanced processor that extracts real video screenshots"""
    
    def __init__(self):
        super().__init__()
        self.screenshot_extractor = VideoScreenshotExtractor()
        self.screenshots_cache = {}
    
    def create_thumbnail_with_screenshot(self, segment: Dict, output_path: Path, 
                                       index: int, video_url: str) -> bool:
        """
        Create thumbnail using actual video screenshot if possible,
        fall back to generated thumbnail if screenshot extraction fails
        
        Args:
            segment: Segment dictionary with timestamp info
            output_path: Path to save the thumbnail
            index: Segment index (1-based)
            video_url: YouTube video URL
            
        Returns:
            True if real screenshot was used, False if generated thumbnail was used
        """
        # Try to extract real screenshot first
        if self.screenshot_extractor.can_extract_screenshots():
            timestamp_seconds = segment.get('start_seconds', 0)
            
            # Check cache first
            cache_key = f"{video_url}_{timestamp_seconds}"
            if cache_key in self.screenshots_cache:
                # Copy cached screenshot to output path
                cached_path = self.screenshots_cache[cache_key]
                if cached_path.exists():
                    Image.open(cached_path).save(output_path, 'JPEG', quality=85, optimize=True)
                    return True
            
            # Try to extract screenshot
            success = self.screenshot_extractor.extract_screenshot(
                video_url,
                timestamp_seconds,
                output_path,
                fallback_on_error=True
            )
            
            if success:
                # Post-process the screenshot to add overlays
                self._enhance_screenshot(output_path, segment, index)
                # Cache the screenshot
                self.screenshots_cache[cache_key] = output_path
                return True
        
        # Fall back to generated thumbnail
        self.create_thumbnail(segment, output_path, index)
        return False
    
    def _enhance_screenshot(self, image_path: Path, segment: Dict, index: int):
        """
        Enhance extracted screenshot with overlays and styling
        
        Args:
            image_path: Path to the screenshot image
            segment: Segment dictionary
            index: Segment index (1-based)
        """
        try:
            # Open the screenshot
            img = Image.open(image_path)
            
            # Resize if too large (max width 800px)
            if img.width > 800:
                ratio = 800 / img.width
                new_size = (800, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Create a semi-transparent overlay for better text visibility
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Add gradient overlay at bottom for text
            gradient_height = img.height // 3
            for y in range(gradient_height):
                alpha = int(180 * (y / gradient_height))  # Gradient from 180 to 0
                draw.rectangle(
                    [(0, img.height - gradient_height + y), (img.width, img.height - gradient_height + y + 1)],
                    fill=(0, 0, 0, alpha)
                )
            
            # Composite the overlay
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')
            
            # Add text overlays
            draw = ImageDraw.Draw(img)
            
            # Try to use system fonts
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            except:
                try:
                    # Fallback for Linux/Windows
                    font_large = ImageFont.truetype("arial.ttf", 32)
                    font_small = ImageFont.truetype("arial.ttf", 16)
                except:
                    font_large = ImageFont.load_default()
                    font_small = ImageFont.load_default()
            
            # Add timestamp in bottom left
            timestamp_text = segment['timestamp']
            padding = 20
            text_y = img.height - padding - 20
            
            # Draw timestamp with shadow for better visibility
            shadow_offset = 2
            draw.text((padding + shadow_offset, text_y + shadow_offset), 
                     timestamp_text, fill=(0, 0, 0, 128), font=font_small)
            draw.text((padding, text_y), 
                     timestamp_text, fill=(255, 255, 255, 230), font=font_small)
            
            # Add segment number in top right corner with semi-transparent background
            number_text = f"#{index}"
            bbox = draw.textbbox((0, 0), number_text, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Draw background box for number
            box_padding = 10
            box_x = img.width - text_width - padding - box_padding * 2
            box_y = padding
            
            # Semi-transparent black background
            draw.rectangle(
                [(box_x, box_y), 
                 (box_x + text_width + box_padding * 2, box_y + text_height + box_padding * 2)],
                fill=(0, 0, 0, 180)
            )
            
            # Draw number
            draw.text((box_x + box_padding, box_y + box_padding), 
                     number_text, fill=(255, 255, 255), font=font_large)
            
            # Add emphasis indicator if present
            if segment.get('emphasis'):
                # Draw golden bar at top
                draw.rectangle([(0, 0), (img.width, 5)], fill=(255, 215, 0))
                
                # Add "KEY POINT" label
                key_text = "KEY POINT"
                bbox = draw.textbbox((0, 0), key_text, font=font_small)
                text_width = bbox[2] - bbox[0]
                
                # Background for KEY POINT
                draw.rectangle(
                    [(padding, padding + 5), 
                     (padding + text_width + 20, padding + 5 + text_height + 10)],
                    fill=(255, 215, 0)
                )
                
                # Text for KEY POINT
                draw.text((padding + 10, padding + 10), 
                         key_text, fill=(0, 0, 0), font=font_small)
            
            # Save the enhanced screenshot
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            
            # Ensure file size is reasonable (under 200KB for real screenshots)
            if image_path.stat().st_size > 200000:
                # Re-save with more compression
                img.save(image_path, 'JPEG', quality=70, optimize=True)
                
        except Exception as e:
            print(f"  ⚠️  Error enhancing screenshot: {e}")
            # Screenshot remains unmodified if enhancement fails
    
    def extract_all_screenshots(self, video_url: str, segments: List[Dict], 
                              output_dir: Path) -> Dict[int, bool]:
        """
        Extract screenshots for all segments
        
        Args:
            video_url: YouTube video URL
            segments: List of segment dictionaries
            output_dir: Directory to save screenshots
            
        Returns:
            Dictionary mapping segment index to success status
        """
        results = {}
        
        print("📸 Processing thumbnails...")
        
        for i, segment in enumerate(segments, 1):
            thumbnail_path = output_dir / f"thumb_{i:02d}.jpg"
            
            # Try to create thumbnail with real screenshot
            used_screenshot = self.create_thumbnail_with_screenshot(
                segment, thumbnail_path, i, video_url
            )
            
            results[i] = used_screenshot
            
            if used_screenshot:
                print(f"  ✅ Segment {i}: Real screenshot extracted")
            else:
                print(f"  📝 Segment {i}: Generated thumbnail created")
        
        # Summary
        real_count = sum(1 for used in results.values() if used)
        if real_count == len(segments):
            print(f"✨ All {len(segments)} segments have real screenshots!")
        elif real_count > 0:
            print(f"📊 {real_count}/{len(segments)} segments use real screenshots")
        else:
            print("📝 Using generated thumbnails (install yt-dlp and ffmpeg for real screenshots)")
        
        return results