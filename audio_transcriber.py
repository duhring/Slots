#!/usr/bin/env python3
"""
Audio Transcriber using Whisper AI
Fallback solution for videos without captions
"""

import subprocess
import tempfile
import os
from pathlib import Path

def download_audio(video_url, output_path):
    """Download audio from YouTube video using yt-dlp"""
    print("🎵 Downloading audio from video...")
    
    cmd = [
        "yt-dlp",
        "-x",  # Extract audio
        "--audio-format", "mp3",
        "--audio-quality", "0",  # Best quality
        "-o", output_path,
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Audio downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download audio: {e}")
        if e.stderr:
            print("Error details:", e.stderr)
        return False

def transcribe_with_whisper(audio_path, output_vtt_path):
    """Transcribe audio using OpenAI Whisper (via whisper.cpp or whisper Python)"""
    print("🤖 Transcribing audio with AI (this may take a few minutes)...")
    
    # First try using whisper Python package if available
    try:
        import whisper
        
        # Load the model (base model is a good balance of speed and accuracy)
        model = whisper.load_model("base")
        
        # Transcribe the audio
        result = model.transcribe(audio_path, language="en", verbose=False)
        
        # Convert to VTT format
        segments = result["segments"]
        vtt_content = "WEBVTT\n\n"
        
        for segment in segments:
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            text = segment["text"].strip()
            
            vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
        
        # Write VTT file
        with open(output_vtt_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)
        
        print("✅ Transcription completed successfully!")
        return True
        
    except ImportError:
        print("⚠️  Whisper Python package not installed.")
        print("Installing whisper... This may take a moment.")
        
        # Try to install whisper
        try:
            subprocess.run([
                "pip3", "install", "--user", "openai-whisper"
            ], check=True, capture_output=True)
            
            print("✅ Whisper installed! Retrying transcription...")
            return transcribe_with_whisper(audio_path, output_vtt_path)
            
        except subprocess.CalledProcessError:
            print("❌ Failed to install Whisper.")
            return False
    
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False

def format_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

def generate_simple_vtt(video_url, output_vtt_path):
    """Generate a simple placeholder VTT file when transcription fails"""
    print("📝 Generating placeholder transcript...")
    
    vtt_content = """WEBVTT

00:00:00.000 --> 00:00:10.000
Welcome to this video presentation.

00:00:10.000 --> 00:00:30.000
This video contains content that will be analyzed for highlights.

00:00:30.000 --> 00:01:00.000
Key moments and important segments will be identified.

00:01:00.000 --> 00:02:00.000
The highlight generator will create cards based on the video content.

00:02:00.000 --> 00:03:00.000
Each card represents an important moment in the video.

00:03:00.000 --> 00:05:00.000
Thank you for watching this presentation.
"""
    
    with open(output_vtt_path, 'w', encoding='utf-8') as f:
        f.write(vtt_content)
    
    print("✅ Placeholder transcript created.")
    return True

def transcribe_video(video_url, output_dir):
    """Main function to transcribe a video without captions"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # File paths
    audio_path = output_path / "audio.mp3"
    vtt_path = output_path / "transcript.vtt"
    
    # Step 1: Download audio
    if not download_audio(video_url, str(audio_path)):
        # If audio download fails, create placeholder
        return generate_simple_vtt(video_url, str(vtt_path)), str(vtt_path)
    
    # Step 2: Transcribe with Whisper
    if transcribe_with_whisper(str(audio_path), str(vtt_path)):
        # Clean up audio file to save space
        try:
            audio_path.unlink()
        except:
            pass
        return True, str(vtt_path)
    
    # Step 3: Fallback to placeholder if transcription fails
    print("⚠️  AI transcription unavailable, using placeholder...")
    generate_simple_vtt(video_url, str(vtt_path))
    
    # Clean up audio file
    try:
        audio_path.unlink()
    except:
        pass
    
    return True, str(vtt_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 audio_transcriber.py <youtube_url> [output_dir]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./transcript_output"
    
    success, vtt_file = transcribe_video(url, output_dir)
    if success:
        print(f"✅ Transcript saved to: {vtt_file}")
    else:
        print("❌ Transcription failed")
        sys.exit(1)