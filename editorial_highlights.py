#!/usr/bin/env python3
"""
Editorial Highlights Generator
Minimal interactive system for creating video highlights with GitHub deployment
"""

import os
import sys
import json
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from core.processor import VideoProcessor
from core.summarizer import SummaryGenerator  
from core.github_deploy import GitHubDeployer
from core.config_manager import ConfigManager


class EditorialWorkflow:
    def __init__(self):
        self.processor = VideoProcessor()
        self.summarizer = SummaryGenerator()
        self.deployer = GitHubDeployer()
        self.config = ConfigManager()
        
    def run(self):
        """Main interactive workflow"""
        print("\n🎬 Editorial Video Highlights Generator")
        print("=" * 40)
        
        try:
            # Get inputs with minimal prompts
            video_url = self.get_url()
            keywords = self.get_keywords()
            num_cards = self.get_card_count()
            
            # Process video
            print("\nProcessing...")
            segments = self.process_video(video_url, keywords, num_cards)
            
            # Review and edit summaries
            segments = self.review_summaries(segments)
            
            # Generate output
            print("\n✓ Building page...")
            output_dir = self.generate_highlights(segments, video_url)
            
            # Preview
            preview_path = Path(output_dir) / "index.html"
            print(f"\nPreview: file://{preview_path.absolute()}")
            if self.prompt_yes("Open? (y)"):
                webbrowser.open(f"file://{preview_path.absolute()}")
            
            # Deploy to GitHub
            if self.prompt_yes("\nDeploy to GitHub? (y)"):
                self.deploy_to_github(output_dir)
            
            # Process another?
            if self.prompt_yes("\nProcess another? (y/n)", default='n'):
                self.run()
                
        except KeyboardInterrupt:
            print("\n\n✗ Cancelled")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Error: {e}")
            if self.prompt_yes("Try again? (y/n)", default='n'):
                self.run()
    
    def get_url(self) -> str:
        """Get YouTube URL with validation"""
        url = input("\nYouTube URL: ").strip()
        if not url:
            print("✗ URL required")
            return self.get_url()
        
        # Basic YouTube URL validation
        if "youtube.com/watch" not in url and "youtu.be/" not in url:
            print("✗ Invalid YouTube URL")
            return self.get_url()
            
        return url
    
    def get_keywords(self) -> List[str]:
        """Get keywords or auto-detect"""
        keywords_input = input("Keywords (or Enter for auto): ").strip()
        
        if not keywords_input:
            print("✓ Auto-detecting themes...")
            return []  # Processor will auto-detect
        
        # Parse comma-separated keywords
        keywords = [k.strip() for k in keywords_input.split(',')]
        return keywords
    
    def get_card_count(self) -> int:
        """Get number of highlight cards"""
        count_input = input("Cards (4): ").strip()
        
        if not count_input:
            return 4
            
        try:
            count = int(count_input)
            if count < 1 or count > 20:
                print("✗ Please choose 1-20 cards")
                return self.get_card_count()
            return count
        except ValueError:
            print("✗ Invalid number")
            return self.get_card_count()
    
    def process_video(self, url: str, keywords: List[str], num_cards: int) -> List[Dict]:
        """Process video and extract segments"""
        # Download transcript
        print("✓ Fetching transcript...")
        transcript = self.processor.get_transcript(url)
        
        # Parse video metadata
        video_title, video_id = self.processor.get_video_info(url)
        
        # Find segments
        if not keywords:
            # Auto-detect keywords from transcript
            keywords = self.processor.detect_keywords(transcript)
            print(f"✓ Using keywords: {', '.join(keywords[:5])}")
        
        print(f"✓ Finding segments...")
        segments = self.processor.find_segments(transcript, keywords, num_cards)
        
        # Generate summaries
        print(f"✓ Generating summaries...")
        for segment in segments:
            segment['summary'] = self.summarizer.summarize(segment['text'])
            
        print(f"✓ Found {len(segments)} segments")
        return segments
    
    def review_summaries(self, segments: List[Dict]) -> List[Dict]:
        """Allow user to review and edit summaries"""
        print("\n--- Review Summaries ---")
        
        for i, segment in enumerate(segments, 1):
            print(f"\n{i}. [{segment['timestamp']}] {segment.get('title', 'Segment ' + str(i))}")
            print(f"   Current: \"{segment['summary'][:80]}...\"")
            
            edit = input("   Edit (Enter to keep): ").strip()
            
            if edit:
                # Handle special edit commands
                if edit.startswith('+'):
                    # Append to existing
                    segment['summary'] = segment['summary'] + ' ' + edit[1:].strip()
                elif edit.startswith('*'):
                    # Make it emphasis/key point
                    segment['summary'] = edit[1:].strip()
                    segment['emphasis'] = True
                elif edit.isdigit():
                    # Limit to N words
                    words = segment['summary'].split()
                    segment['summary'] = ' '.join(words[:int(edit)])
                else:
                    # Full replacement
                    segment['summary'] = edit
        
        return segments
    
    def generate_highlights(self, segments: List[Dict], video_url: str) -> str:
        """Generate the highlights HTML page"""
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"editorial_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract video ID for embedding
        video_id = self.processor.extract_video_id(video_url)
        
        # Generate thumbnails
        print("✓ Creating thumbnails...")
        for i, segment in enumerate(segments, 1):
            thumbnail_path = Path(output_dir) / f"thumb_{i:02d}.jpg"
            self.processor.create_thumbnail(segment, thumbnail_path, i)
        
        # Generate HTML
        html_content = self.generate_html(segments, video_id, video_url)
        
        # Write HTML file
        html_path = Path(output_dir) / "index.html"
        html_path.write_text(html_content)
        
        return output_dir
    
    def generate_html(self, segments: List[Dict], video_id: str, video_url: str) -> str:
        """Generate clean editorial HTML"""
        cards_html = ""
        for i, segment in enumerate(segments, 1):
            # Calculate seconds for timestamp
            time_parts = segment['timestamp'].split(':')
            if len(time_parts) == 3:
                seconds = int(time_parts[0])*3600 + int(time_parts[1])*60 + int(time_parts[2])
            else:
                seconds = int(time_parts[0])*60 + int(time_parts[1])
            
            emphasis_class = "emphasis" if segment.get('emphasis') else ""
            
            cards_html += f"""
            <div class="card {emphasis_class}" onclick="seekToTime({seconds})">
                <img src="thumb_{i:02d}.jpg" alt="Segment {i}">
                <div class="card-content">
                    <div class="timestamp">{segment['timestamp']}</div>
                    <div class="summary">{segment['summary']}</div>
                </div>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Highlights</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .video-wrapper {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            margin-bottom: 40px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        
        .video-wrapper iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }}
        
        .card.emphasis {{
            border: 2px solid #667eea;
            background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
        }}
        
        .card img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
        }}
        
        .card-content {{
            padding: 20px;
        }}
        
        .timestamp {{
            font-size: 12px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .summary {{
            font-size: 14px;
            line-height: 1.6;
            color: #333;
        }}
        
        .youtube-link {{
            text-align: center;
            margin-top: 20px;
        }}
        
        .youtube-link a {{
            color: white;
            text-decoration: none;
            font-size: 14px;
            opacity: 0.8;
            transition: opacity 0.3s;
        }}
        
        .youtube-link a:hover {{
            opacity: 1;
        }}
        
        @media (max-width: 768px) {{
            .cards-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="video-wrapper">
            <iframe 
                id="youtube-player"
                src="https://www.youtube.com/embed/{video_id}?enablejsapi=1" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        
        <div class="cards-grid">
            {cards_html}
        </div>
        
        <div class="youtube-link">
            <a href="{video_url}" target="_blank">View on YouTube →</a>
        </div>
    </div>
    
    <script>
        let player;
        
        // Load YouTube IFrame API
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        
        function onYouTubeIframeAPIReady() {{
            player = new YT.Player('youtube-player', {{
                events: {{
                    'onReady': onPlayerReady
                }}
            }});
        }}
        
        function onPlayerReady(event) {{
            // Player is ready
        }}
        
        function seekToTime(seconds) {{
            if (player && player.seekTo) {{
                player.seekTo(seconds, true);
                player.playVideo();
                
                // Smooth scroll to video
                document.querySelector('.video-wrapper').scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }});
            }}
        }}
    </script>
</body>
</html>"""
    
    def deploy_to_github(self, output_dir: str):
        """Deploy to GitHub with minimal prompts"""
        # Ensure GitHub config exists
        if not self.config.has_github_config():
            self.setup_github_config()
        
        config = self.config.get_github_config()
        
        # Get deployment path
        default_path = datetime.now().strftime("%Y-%m") + "/" + Path(output_dir).name
        path = input(f"Path ({default_path}): ").strip() or default_path
        
        # Sanitize path
        path = path.strip('/').replace(' ', '-').lower()
        
        # Get commit message
        message = input("Message: ").strip() or "Add highlights"
        
        # Deploy
        try:
            print("\n✓ Deploying to GitHub...")
            deployed_url = self.deployer.deploy(
                output_dir, 
                config['repo'], 
                path, 
                message,
                config['username']
            )
            print(f"\n✓ Deployed: {deployed_url}")
            
        except Exception as e:
            print(f"\n✗ Deployment failed: {e}")
            print("Files remain in:", output_dir)
    
    def setup_github_config(self):
        """First-time GitHub setup"""
        print("\nFirst time setup:")
        username = input("GitHub username: ").strip()
        repo = input("Repo name (editorial-highlights): ").strip() or "editorial-highlights"
        
        self.config.save_github_config(username, repo)
        print("✓ Configuration saved")
    
    def prompt_yes(self, prompt: str, default='y') -> bool:
        """Simple yes/no prompt"""
        response = input(f"{prompt}: ").strip().lower()
        if not response:
            response = default
        return response in ['y', 'yes']


def main():
    """Entry point"""
    workflow = EditorialWorkflow()
    workflow.run()


if __name__ == "__main__":
    main()