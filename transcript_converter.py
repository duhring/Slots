#!/usr/bin/env python3
"""
Convert raw YouTube transcript text to VTT format
"""

import re
from pathlib import Path

def convert_raw_transcript_to_vtt(raw_text, output_file):
    """
    Convert raw YouTube transcript text to VTT format
    Handles various formats of raw transcript text
    """
    
    # Clean up the text
    lines = raw_text.strip().split('\n')
    segments = []
    
    # Try to detect if text has timestamps already
    has_timestamps = any(re.search(r'\d+:\d+', line) for line in lines[:5])
    
    if has_timestamps:
        # Parse text that already has timestamps
        current_text = []
        current_time = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for timestamp patterns
            time_match = re.search(r'(\d+):(\d+)(?::(\d+))?', line)
            
            if time_match:
                # Save previous segment if we have one
                if current_time is not None and current_text:
                    segments.append({
                        'time': current_time,
                        'text': ' '.join(current_text).strip()
                    })
                
                # Start new segment
                minutes = int(time_match.group(1))
                seconds = int(time_match.group(2))
                subseconds = int(time_match.group(3)) if time_match.group(3) else 0
                current_time = minutes * 60 + seconds + (subseconds / 60.0)
                
                # Get text after timestamp
                text_after_time = re.sub(r'\d+:\d+(?::\d+)?\s*', '', line).strip()
                current_text = [text_after_time] if text_after_time else []
            else:
                # Add to current segment text
                if line and current_time is not None:
                    current_text.append(line)
        
        # Add final segment
        if current_time is not None and current_text:
            segments.append({
                'time': current_time,
                'text': ' '.join(current_text).strip()
            })
    
    else:
        # No timestamps - split into chunks and estimate timing
        # Assume average reading speed of 150 words per minute
        words_per_second = 2.5
        
        # Join all text and split into sentences
        full_text = ' '.join(lines)
        sentences = re.split(r'[.!?]+', full_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_time = 0
        for sentence in sentences:
            if not sentence:
                continue
                
            word_count = len(sentence.split())
            duration = max(2.0, word_count / words_per_second)  # Minimum 2 seconds
            
            segments.append({
                'time': current_time,
                'text': sentence.strip()
            })
            
            current_time += duration
    
    # Generate VTT content
    vtt_content = "WEBVTT\n\n"
    
    for i, segment in enumerate(segments):
        if not segment['text']:
            continue
            
        start_time = segment['time']
        
        # Calculate end time (start of next segment or +5 seconds)
        if i + 1 < len(segments):
            end_time = segments[i + 1]['time']
        else:
            end_time = start_time + 5.0
        
        # Format times as MM:SS.mmm
        start_formatted = format_vtt_time(start_time)
        end_formatted = format_vtt_time(end_time)
        
        vtt_content += f"{start_formatted} --> {end_formatted}\n"
        vtt_content += f"{segment['text']}\n\n"
    
    # Save VTT file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(vtt_content)
    
    print(f"✅ Converted transcript to VTT format: {output_file}")
    print(f"📊 Created {len(segments)} segments")
    
    return str(output_file)

def format_vtt_time(seconds):
    """Format seconds as MM:SS.mmm for VTT"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:06.3f}"

def interactive_converter():
    """Interactive transcript converter"""
    print("🎬 YouTube Transcript to VTT Converter")
    print("=" * 40)
    
    print("\nPaste your YouTube transcript below.")
    print("You can include timestamps (like '2:30 some text') or just raw text.")
    print("Press Enter twice when done:\n")
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:  # Two empty lines = done
                    break
            else:
                empty_count = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    if not lines:
        print("❌ No transcript text provided")
        return
    
    raw_text = '\n'.join(lines)
    
    # Ask for output filename
    default_name = "transcript.vtt"
    output_name = input(f"\nOutput filename (default: {default_name}): ").strip()
    if not output_name:
        output_name = default_name
    
    if not output_name.endswith('.vtt'):
        output_name += '.vtt'
    
    # Convert
    output_path = convert_raw_transcript_to_vtt(raw_text, output_name)
    
    print(f"\n🎉 Success!")
    print(f"📁 VTT file created: {output_path}")
    print(f"\nNow you can use this with the highlight generator:")
    print(f"python3 easy_highlights.py")

def main():
    import sys
    
    if len(sys.argv) > 1:
        # File mode
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "transcript.vtt"
        
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        convert_raw_transcript_to_vtt(raw_text, output_file)
    else:
        # Interactive mode
        interactive_converter()

if __name__ == "__main__":
    main()