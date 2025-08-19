#!/usr/bin/env python3
"""
Smart Thumbnail Extractor using FFmpeg's intelligent frame selection
Finds the clearest, most interesting frames within video segments
"""

import subprocess
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import tempfile
import shutil
from PIL import Image
import numpy as np

class SmartThumbnailExtractor:
    """Extract high-quality, representative thumbnails from video segments"""
    
    def __init__(self):
        self.has_ffmpeg = self._check_ffmpeg()
        self.has_yt_dlp = self._check_yt_dlp()
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_yt_dlp(self) -> bool:
        """Check if yt-dlp is available"""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def extract_smart_thumbnail(self, 
                              video_source: str, 
                              segment_start: float,
                              segment_end: float,
                              output_path: Path,
                              video_url: Optional[str] = None) -> bool:
        """
        Extract the best thumbnail from a video segment using multiple strategies
        
        Args:
            video_source: Local video path or URL
            segment_start: Start time in seconds
            segment_end: End time in seconds  
            output_path: Where to save the thumbnail
            video_url: Optional YouTube URL for fallback download
            
        Returns:
            True if successful, False otherwise
        """
        if not self.has_ffmpeg:
            print("❌ FFmpeg not found. Install with: brew install ffmpeg")
            return False
        
        # Calculate segment duration
        duration = min(segment_end - segment_start, 10)  # Max 10 seconds to analyze
        
        # Try multiple extraction strategies in order of preference
        strategies = [
            self._extract_with_thumbnail_filter,
            self._extract_with_scene_detection,
            self._extract_middle_frame,
            self._extract_start_frame
        ]
        
        for strategy in strategies:
            try:
                if strategy(video_source, segment_start, duration, output_path):
                    # Validate the extracted frame
                    if self._validate_frame_quality(output_path):
                        return True
                    else:
                        # Poor quality, try next strategy
                        output_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"  Strategy failed: {e}")
                continue
        
        return False
    
    def _extract_with_thumbnail_filter(self, 
                                      video_source: str,
                                      start_time: float,
                                      duration: float,
                                      output_path: Path) -> bool:
        """
        Use FFmpeg's thumbnail filter to find the most representative frame
        This analyzes multiple frames and selects the best one
        """
        print(f"  🎯 Using thumbnail filter (analyzing frames)...")
        
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', video_source,
            '-vf', 'thumbnail=n=50',  # Analyze 50 frames in the segment
            '-frames:v', '1',
            '-q:v', '2',  # High quality
            '-y',  # Overwrite
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    
    def _extract_with_scene_detection(self,
                                     video_source: str,
                                     start_time: float,
                                     duration: float,
                                     output_path: Path) -> bool:
        """
        Extract first frame after a scene change (usually clearer)
        """
        print(f"  🎬 Using scene detection...")
        
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', video_source,
            '-vf', "select='gt(scene,0.3)',showinfo",  # Detect scene changes
            '-frames:v', '1',
            '-vsync', 'vfr',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    
    def _extract_middle_frame(self,
                             video_source: str,
                             start_time: float,
                             duration: float,
                             output_path: Path) -> bool:
        """
        Extract frame from middle of segment
        """
        print(f"  📍 Extracting middle frame...")
        
        middle_time = start_time + (duration / 2)
        
        cmd = [
            'ffmpeg',
            '-ss', str(middle_time),
            '-i', video_source,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    
    def _extract_start_frame(self,
                            video_source: str,
                            start_time: float,
                            duration: float,
                            output_path: Path) -> bool:
        """
        Extract frame from start of segment (fallback)
        """
        print(f"  ⏰ Extracting start frame...")
        
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_source,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    
    def _validate_frame_quality(self, image_path: Path) -> bool:
        """
        Validate that the extracted frame is of good quality
        Checks for: black frames, excessive blur, low contrast
        """
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert('L'))  # Convert to grayscale
            
            # Check for black frame (mean brightness too low)
            mean_brightness = np.mean(img_array)
            if mean_brightness < 20:
                print(f"    ⚠️  Frame too dark (brightness: {mean_brightness:.1f})")
                return False
            
            # Check for white/overexposed frame
            if mean_brightness > 235:
                print(f"    ⚠️  Frame too bright (brightness: {mean_brightness:.1f})")
                return False
            
            # Check for blur using Laplacian variance
            # Higher variance = sharper image
            laplacian = np.array([[0,1,0],[1,-4,1],[0,1,0]])
            convolved = np.abs(np.convolve(img_array.flatten(), laplacian.flatten(), mode='same'))
            blur_measure = np.var(convolved)
            
            if blur_measure < 100:
                print(f"    ⚠️  Frame too blurry (sharpness: {blur_measure:.1f})")
                return False
            
            # Check contrast (standard deviation of pixel values)
            contrast = np.std(img_array)
            if contrast < 20:
                print(f"    ⚠️  Frame has low contrast ({contrast:.1f})")
                return False
            
            print(f"    ✅ Frame quality good (brightness: {mean_brightness:.1f}, sharpness: {blur_measure:.1f})")
            return True
            
        except Exception as e:
            print(f"    ⚠️  Could not validate frame: {e}")
            return True  # Assume it's okay if we can't check
    
    def extract_thumbnails_for_segments(self,
                                       video_url: str,
                                       segments: List[dict],
                                       output_dir: Path) -> List[Optional[Path]]:
        """
        Extract smart thumbnails for multiple segments
        
        Args:
            video_url: YouTube URL or local video path
            segments: List of segment dictionaries with 'start' and 'end' times
            output_dir: Directory to save thumbnails
            
        Returns:
            List of thumbnail paths (or None for failed extractions)
        """
        output_dir.mkdir(exist_ok=True)
        thumbnails = []
        
        # Download video once if needed
        video_source = video_url
        temp_video = None
        
        if video_url.startswith('http'):
            if self.has_yt_dlp:
                print("📥 Downloading video for thumbnail extraction...")
                temp_video = output_dir / "temp_video.mp4"
                
                cmd = [
                    'yt-dlp',
                    '-f', 'best[ext=mp4]/best',
                    '-o', str(temp_video),
                    '--no-playlist',
                    video_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and temp_video.exists():
                    video_source = str(temp_video)
                    print("✅ Video downloaded for processing")
                else:
                    print("❌ Video download failed, will try direct extraction")
        
        # Extract thumbnail for each segment
        for i, segment in enumerate(segments):
            print(f"\n📸 Extracting thumbnail {i+1}/{len(segments)}...")
            
            segment_start = segment.get('start', 0)
            segment_end = segment.get('end', segment_start + 10)
            output_path = output_dir / f"thumbnail_{i+1:03d}.jpg"
            
            success = self.extract_smart_thumbnail(
                video_source,
                segment_start,
                segment_end,
                output_path,
                video_url
            )
            
            if success and output_path.exists():
                thumbnails.append(output_path)
                print(f"  ✅ Thumbnail {i+1} saved: {output_path.name}")
            else:
                thumbnails.append(None)
                print(f"  ❌ Failed to extract thumbnail {i+1}")
        
        # Clean up temp video
        if temp_video and temp_video.exists():
            temp_video.unlink()
            print("🧹 Cleaned up temporary video")
        
        return thumbnails


def main():
    """Test the smart thumbnail extractor"""
    if len(sys.argv) < 2:
        print("Usage: python smart_thumbnail_extractor.py <video_url_or_path>")
        sys.exit(1)
    
    video_source = sys.argv[1]
    output_dir = Path("smart_thumbnails")
    output_dir.mkdir(exist_ok=True)
    
    # Test segments
    segments = [
        {'start': 0, 'end': 30},
        {'start': 60, 'end': 90},
        {'start': 120, 'end': 150}
    ]
    
    extractor = SmartThumbnailExtractor()
    thumbnails = extractor.extract_thumbnails_for_segments(
        video_source,
        segments,
        output_dir
    )
    
    print(f"\n✨ Extracted {len([t for t in thumbnails if t])} thumbnails")
    for i, thumb in enumerate(thumbnails):
        if thumb:
            print(f"  Segment {i+1}: {thumb}")


if __name__ == "__main__":
    main()