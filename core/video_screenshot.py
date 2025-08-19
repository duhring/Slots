"""
Video screenshot extraction module
Captures actual screenshots from YouTube videos at specific timestamps
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
import shutil


class VideoScreenshotExtractor:
    def __init__(self):
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if required tools are installed"""
        self.has_ytdlp = self._check_command(['yt-dlp', '--version'])
        self.has_ffmpeg = self._check_command(['ffmpeg', '-version'])
        
        if not self.has_ytdlp:
            print("⚠️  yt-dlp not found. Screenshots will use generated thumbnails.")
            print("   Install with: brew install yt-dlp")
        
        if not self.has_ffmpeg:
            print("⚠️  ffmpeg not found. Screenshots will use generated thumbnails.")
            print("   Install with: brew install ffmpeg")
    
    def _check_command(self, cmd: List[str]) -> bool:
        """Check if a command is available"""
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def can_extract_screenshots(self) -> bool:
        """Check if screenshot extraction is available"""
        return self.has_ytdlp and self.has_ffmpeg
    
    def extract_smart_screenshot(self, video_url: str, segment_start: int, segment_end: int,
                                output_path: Path, fallback_on_error: bool = True) -> bool:
        """
        Extract the best screenshot from a video segment using intelligent frame selection
        
        Args:
            video_url: YouTube URL or direct video URL
            segment_start: Start of segment in seconds
            segment_end: End of segment in seconds
            output_path: Path where to save the screenshot
            fallback_on_error: If True, silently fail and return False
            
        Returns:
            True if screenshot was extracted successfully
        """
        if not self.can_extract_screenshots():
            return False
        
        # Calculate duration to analyze (max 10 seconds)
        duration = min(segment_end - segment_start, 10)
        
        print(f"  🎯 Analyzing frames for best thumbnail...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                temp_video = temp_path / f"segment_{segment_start}.mp4"
                
                # Download video segment
                download_cmd = [
                    'yt-dlp',
                    '-f', 'best[ext=mp4]/best',
                    '--no-playlist',
                    '--external-downloader', 'ffmpeg',
                    '--external-downloader-args', f'-ss {segment_start} -t {duration}',
                    '-o', str(temp_video),
                    '--quiet',
                    '--no-warnings',
                    video_url
                ]
                
                download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=60)
                
                if download_result.returncode == 0 and temp_video.exists():
                    # Use thumbnail filter to find best frame
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-i', str(temp_video),
                        '-vf', 'thumbnail=n=50,scale=800:-1',  # Analyze 50 frames, scale to 800px width
                        '-frames:v', '1',
                        '-q:v', '2',
                        '-y',
                        str(output_path)
                    ]
                    
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and output_path.exists():
                        print(f"  ✅ Smart thumbnail extracted")
                        return True
                
                # Fall back to regular extraction at segment start
                print(f"  ⚠️ Smart extraction failed, using simple extraction")
                return self.extract_screenshot(video_url, segment_start, output_path, fallback_on_error)
                
        except Exception as e:
            print(f"  ⚠️ Smart extraction error: {e}")
            if not fallback_on_error:
                raise
            # Fall back to simple extraction
            return self.extract_screenshot(video_url, segment_start, output_path, fallback_on_error)
    
    def extract_screenshot(self, video_url: str, timestamp_seconds: int, 
                         output_path: Path, fallback_on_error: bool = True) -> bool:
        """
        Extract a single screenshot from video at specified timestamp
        
        Args:
            video_url: YouTube video URL
            timestamp_seconds: Timestamp in seconds
            output_path: Path to save the screenshot
            fallback_on_error: If True, returns False on error instead of raising
            
        Returns:
            True if screenshot was extracted successfully
        """
        if not self.can_extract_screenshots():
            return False
        
        try:
            # Create a temporary directory for intermediate files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Format timestamp for ffmpeg
                hours = int(timestamp_seconds // 3600)
                minutes = int((timestamp_seconds % 3600) // 60)
                seconds = int(timestamp_seconds % 60)
                timestamp_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Download a small segment of the video
                temp_video = temp_path / "segment.mp4"
                
                # Calculate segment boundaries (5 seconds around the timestamp)
                start_time = max(0, timestamp_seconds - 2)
                duration = 5
                
                print(f"  📸 Extracting screenshot at {timestamp_str}...")
                
                # Download video segment using yt-dlp
                download_cmd = [
                    'yt-dlp',
                    '-f', 'worst[ext=mp4]/worst',  # Use lowest quality for speed
                    '--no-playlist',
                    '--external-downloader', 'ffmpeg',
                    '--external-downloader-args', f'-ss {start_time} -t {duration}',
                    '-o', str(temp_video),
                    '--quiet',
                    '--no-warnings',
                    video_url
                ]
                
                result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0 or not temp_video.exists():
                    if not fallback_on_error:
                        raise RuntimeError(f"Failed to download video segment: {result.stderr}")
                    return False
                
                # Extract frame from the segment
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', str(temp_video),
                    '-ss', '2',  # 2 seconds into the segment (middle of our 5-second clip)
                    '-frames:v', '1',
                    '-q:v', '2',  # High quality JPEG
                    '-vf', 'scale=800:-1',  # Scale to 800px width, maintain aspect ratio
                    '-y',  # Overwrite if exists
                    str(output_path)
                ]
                
                ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
                
                if ffmpeg_result.returncode != 0:
                    if not fallback_on_error:
                        raise RuntimeError(f"Failed to extract frame: {ffmpeg_result.stderr}")
                    return False
                
                return output_path.exists()
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Timeout extracting screenshot at {timestamp_str}")
            if not fallback_on_error:
                raise
            return False
        except Exception as e:
            print(f"  ⚠️  Error extracting screenshot: {e}")
            if not fallback_on_error:
                raise
            return False
    
    def extract_multiple_screenshots(self, video_url: str, segments: List[Dict], 
                                   output_dir: Path) -> Dict[int, Path]:
        """
        Extract screenshots for multiple segments
        
        Args:
            video_url: YouTube video URL
            segments: List of segment dictionaries with 'start_seconds' key
            output_dir: Directory to save screenshots
            
        Returns:
            Dictionary mapping segment index to screenshot path
        """
        screenshots = {}
        
        if not self.can_extract_screenshots():
            print("⚠️  Screenshot extraction not available, using generated thumbnails")
            return screenshots
        
        print("📸 Extracting video screenshots...")
        
        for i, segment in enumerate(segments):
            screenshot_path = output_dir / f"screenshot_{i+1:02d}.jpg"
            
            # Get timestamp from segment
            timestamp = segment.get('start_seconds', 0)
            
            # Try to extract screenshot
            success = self.extract_screenshot(
                video_url, 
                timestamp, 
                screenshot_path,
                fallback_on_error=True
            )
            
            if success:
                screenshots[i] = screenshot_path
                print(f"  ✅ Screenshot {i+1} saved")
            else:
                print(f"  ⚠️  Failed to extract screenshot {i+1}, will use generated thumbnail")
        
        return screenshots
    
    def extract_thumbnail_from_url(self, video_url: str, output_path: Path) -> bool:
        """
        Extract the video's default thumbnail
        
        Args:
            video_url: YouTube video URL
            output_path: Path to save the thumbnail
            
        Returns:
            True if thumbnail was extracted successfully
        """
        if not self.has_ytdlp:
            return False
        
        try:
            cmd = [
                'yt-dlp',
                '--write-thumbnail',
                '--skip-download',
                '--convert-thumbnails', 'jpg',
                '-o', str(output_path.with_suffix('')),
                '--quiet',
                '--no-warnings',
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            # Check if thumbnail was saved (yt-dlp adds .jpg extension)
            jpg_path = output_path.with_suffix('.jpg')
            if jpg_path.exists():
                if jpg_path != output_path:
                    shutil.move(str(jpg_path), str(output_path))
                return True
            
            return False
            
        except (subprocess.TimeoutExpired, Exception):
            return False