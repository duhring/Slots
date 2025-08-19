#!/usr/bin/env python3
"""
Easy YouTube Highlights Generator
Interactive interface that handles everything for you
"""

import os
import sys
import subprocess
import re
from pathlib import Path
import shutil

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
        r'youtube\.com/watch\?.*?v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def check_dependencies():
    """Check if required tools are available"""
    missing = []
    
    # Check yt-dlp
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp")
    
    # Check Python packages
    try:
        import pytube, moviepy, transformers, torch, PIL, numpy
    except ImportError as e:
        missing.append(f"Python packages: {e}")
    
    if missing:
        print("❌ Missing dependencies:")
        for item in missing:
            print(f"  - {item}")
        
        if "yt-dlp" in str(missing):
            print("\nTo install yt-dlp:")
            print("  pip3 install --user yt-dlp")
        
        print("\nTo install Python packages:")
        print("  pip3 install --user pytube moviepy transformers torch pillow numpy")
        return False
    
    return True

def download_transcript(video_url, output_dir="./"):
    """Download transcript using yt-dlp"""
    print("📥 Downloading transcript...")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Transcript downloaded successfully!")
        
        # Find the downloaded vtt file
        for file in Path(output_dir).glob("*.en.vtt"):
            return str(file)
        
        # Fallback: look for any vtt file
        vtt_files = list(Path(output_dir).glob("*.vtt"))
        if vtt_files:
            return str(vtt_files[0])
            
        print("⚠️  No transcript file found. Trying auto-generated captions...")
        
        # Try with auto-generated captions
        cmd_auto = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "-o", f"{output_dir}/%(title)s.%(ext)s",
            video_url
        ]
        
        subprocess.run(cmd_auto, capture_output=True, text=True, check=True)
        
        # Look for auto-generated files
        for file in Path(output_dir).glob("*.en.vtt"):
            return str(file)
        
        vtt_files = list(Path(output_dir).glob("*.vtt"))
        if vtt_files:
            return str(vtt_files[0])
        
        print("❌ No captions available for this video.")
        print("🔄 Attempting AI transcription fallback...")
        
        # Try audio transcription as fallback
        try:
            import audio_transcriber
            success, vtt_file = audio_transcriber.transcribe_video(video_url, output_dir)
            if success:
                return vtt_file
        except Exception as e:
            print(f"⚠️  AI transcription failed: {e}")
        
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download transcript: {e}")
        if e.stderr:
            print("Error details:", e.stderr)
        
        # Try audio transcription as fallback
        print("🔄 Attempting AI transcription fallback...")
        try:
            import audio_transcriber
            success, vtt_file = audio_transcriber.transcribe_video(video_url, output_dir)
            if success:
                return vtt_file
        except Exception as e:
            print(f"⚠️  AI transcription failed: {e}")
        
        return None

def get_user_input():
    """Interactive input gathering with smart defaults"""
    print("🎬 Easy YouTube Highlights Generator")
    print("=" * 50)
    print("Create beautiful highlight pages in minutes!")
    print()
    
    # Get YouTube URL
    while True:
        url = input("📺 YouTube URL: ").strip()
        if not url:
            print("❌ Please enter a URL")
            continue
        if get_video_id(url):
            break
        print("❌ Invalid YouTube URL. Please try again.")
    
    print("✅ Valid YouTube URL detected!")
    
    # Get description (optional)
    description = input("📝 Page title (press Enter for auto-detect): ").strip()
    if not description:
        description = None  # Will be auto-detected from video
    
    # Get keywords with smart suggestions
    print("\n🔍 Keywords help find the most interesting parts of your video.")
    print("💡 Suggestions based on content type:")
    print("   📚 Educational: introduction, methodology, results, conclusion")
    print("   🛠️  Tutorial: setup, configuration, demo, testing")
    print("   🎤 Presentation: agenda, problem, solution, demo, questions")
    print("   🎮 Gaming: gameplay, strategy, tips, review")
    
    keywords_input = input("\nKeywords (space-separated, or press Enter for smart detection): ").strip()
    
    if keywords_input:
        keywords = keywords_input.split()
    else:
        # Smart keyword detection will be done by analyzing the transcript
        keywords = None
    
    # Get number of cards
    while True:
        try:
            cards_input = input("🃏 Number of highlight cards (1-10, default: 4): ").strip()
            if not cards_input:
                cards = 4
                break
            cards = int(cards_input)
            if 1 <= cards <= 10:
                break
            print("❌ Please enter a number between 1 and 10.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    # Get output directory
    output_input = input("📁 Output folder name (default: highlights): ").strip()
    output_dir = output_input if output_input else "highlights"
    
    # Add timestamp to avoid conflicts
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_dir}_{timestamp}"
    
    return {
        'url': url,
        'description': description,
        'keywords': keywords,
        'cards': cards,
        'output_dir': output_dir
    }

def smart_keyword_detection(transcript_text):
    """Detect likely keywords from transcript content"""
    # Common patterns that indicate interesting segments
    patterns = {
        'introduction': ['introduction', 'intro', 'welcome', 'today we', 'going to', 'start'],
        'conclusion': ['conclusion', 'summary', 'recap', 'in summary', 'to wrap up', 'finally'],
        'demo': ['demo', 'demonstration', 'show you', 'example', 'let me show', 'here is'],
        'important': ['important', 'key', 'main', 'crucial', 'essential', 'remember'],
        'results': ['results', 'outcome', 'findings', 'data', 'numbers', 'statistics'],
        'tips': ['tip', 'trick', 'advice', 'suggestion', 'recommend', 'best practice']
    }
    
    text_lower = transcript_text.lower()
    detected_keywords = []
    
    for keyword, indicators in patterns.items():
        for indicator in indicators:
            if indicator in text_lower:
                detected_keywords.append(keyword)
                break
    
    # Default fallback
    if not detected_keywords:
        detected_keywords = ['introduction', 'conclusion', 'important']
    
    return detected_keywords[:4]  # Limit to 4 keywords

def run_generator(config, transcript_file):
    """Run the highlight generator with the given config"""
    print(f"\n🚀 Generating {config['cards']} highlight cards...")
    
    # If no keywords provided, analyze transcript for smart detection
    keywords = config['keywords']
    if not keywords:
        print("🧠 Analyzing transcript for smart keyword detection...")
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            keywords = smart_keyword_detection(transcript_content)
            print(f"✅ Detected keywords: {', '.join(keywords)}")
        except:
            keywords = ['introduction', 'conclusion', 'important']
            print(f"⚠️  Using default keywords: {', '.join(keywords)}")
    
    try:
        # Import and use generate_video_cards directly instead of subprocess
        print("⚙️  Running generator...")
        
        # Import the necessary components
        try:
            import generate_video_cards
            import argparse
        except ImportError as e:
            print(f"❌ Failed to import generator modules: {e}")
            return False
        
        # Build arguments similar to command line
        args = argparse.Namespace()
        args.youtube_url = config['url']
        args.transcript_file = transcript_file
        args.description = config.get('description', '')
        args.keywords = keywords
        args.cards = config['cards']
        args.output_dir = config['output_dir']
        
        # Temporarily modify sys.argv to simulate command line arguments
        original_argv = sys.argv
        try:
            sys.argv = [
                'generate_video_cards.py',
                args.youtube_url,
                args.transcript_file,
                '--description', args.description,
                '--keywords'] + args.keywords + [
                '--cards', str(args.cards),
                '--output-dir', args.output_dir
            ]
            
            # Call the main function directly
            generate_video_cards.main()
            print(f"✅ Highlights generated successfully!")
            return True
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Failed to generate highlights: {e}")
        return False

def show_results(output_dir):
    """Show the results and next steps"""
    output_path = Path(output_dir)
    
    print("\n" + "🎉" * 20)
    print("SUCCESS! Your video highlights are ready!")
    print("🎉" * 20)
    
    print(f"\n📁 Files created in '{output_dir}':")
    for file in sorted(output_path.glob("*")):
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   📄 {file.name} ({size_mb:.1f}MB)")
    
    html_file = output_path / "index.html"
    if html_file.exists():
        print(f"\n🌐 View your highlights: file://{html_file.absolute()}")
    
    print(f"\n🚀 Deploy to Netlify:")
    print(f"   1. Go to https://netlify.com")
    print(f"   2. Drag the '{output_dir}' folder onto the Netlify dashboard")
    print(f"   3. Your site will be live in seconds!")
    
    print(f"\n📱 Or serve locally:")
    print(f"   cd {output_dir}")
    print(f"   python3 -m http.server 8000")
    print(f"   Open http://localhost:8000")

def main():
    try:
        print("🔍 Checking dependencies...")
        if not check_dependencies():
            sys.exit(1)
        print("✅ All dependencies available!")
        
        # Get user configuration
        config = get_user_input()
        
        print(f"\n📋 Configuration:")
        print(f"   URL: {config['url']}")
        print(f"   Cards: {config['cards']}")
        print(f"   Keywords: {config['keywords'] or 'Auto-detect'}")
        print(f"   Output: {config['output_dir']}")
        
        # Download transcript
        transcript_file = download_transcript(config['url'], config['output_dir'])
        
        if not transcript_file:
            print("\n❌ Cannot proceed without transcript.")
            print("This video may not have captions available.")
            sys.exit(1)
        
        print(f"✅ Transcript saved: {transcript_file}")
        
        # Generate highlights
        success = run_generator(config, transcript_file)
        
        if success:
            show_results(config['output_dir'])
        else:
            print("\n❌ Generation failed. Please check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()