#!/usr/bin/env python3
"""
Test the transcription fallback functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio_transcriber

def test_transcription():
    """Test the audio transcription fallback"""
    video_url = "https://youtu.be/fH3_l0fUFZY?si=GP5p7AWHpPhC4EtR"
    output_dir = "test_transcription_output"
    
    print(f"Testing transcription for: {video_url}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    success, vtt_file = audio_transcriber.transcribe_video(video_url, output_dir)
    
    if success:
        print(f"\n✅ Transcription successful!")
        print(f"VTT file created: {vtt_file}")
        
        # Show first few lines of the transcript
        if Path(vtt_file).exists():
            with open(vtt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                print("\nFirst few lines of transcript:")
                print("-" * 30)
                for line in lines:
                    print(line.rstrip())
    else:
        print("\n❌ Transcription failed")
        
if __name__ == "__main__":
    test_transcription()