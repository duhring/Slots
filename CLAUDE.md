# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Highlight Generator - Creates beautiful, shareable highlight pages from YouTube videos with AI summarization, video processing, and static website generation ready for deployment.

## Architecture

### Entry Points (Choose Based on Use Case)

1. **`easy_highlights.py`** - Interactive CLI for new users
   - Handles transcript download via yt-dlp
   - Smart keyword detection from content  
   - Dependency checking with helpful guidance

2. **`editorial_highlights.py` / `editorial_highlights_enhanced.py`** - Editorial workflow with GitHub Pages deployment
   - Interactive summary editing before publishing
   - Direct GitHub Pages deployment
   - Clean, minimal prompts

3. **`one_command_highlights.py`** - All-in-one orchestrator
   - Combines transcript input with advanced video processing
   - Real screenshot extraction using yt-dlp and ffmpeg
   - Most comprehensive feature set

4. **`generate_video_cards.py`** - Core engine for programmatic use
   - Full command-line control
   - Direct API-style usage

### Core Module Structure (`core/`)

- `processor.py` - Main transcript processing and segment finding
- `summarizer.py` - AI summarization with BART model
- `video_screenshot.py` - Video frame extraction utilities
- `enhanced_processor.py` - Advanced processing features
- `github_deploy.py` - GitHub Pages deployment functionality
- `config_manager.py` - Configuration management

### Supporting Utilities

- `improved_summarizer.py` - Enhanced BART with extractive fallback
- `transcript_converter.py` - Convert raw text to VTT with timing
- `create_distinct_thumbnails.py` - Generate visually distinct thumbnails
- `extract_timecode_screenshots.py` - Extract frames at specific timestamps
- `fix_visual_distinction.py` - Fix thumbnail visual similarity issues

## Common Commands

### Quick Start
```bash
python3 easy_highlights.py
```

### Editorial Workflow with GitHub Deployment
```bash
python3 editorial_highlights.py
```

### Advanced All-in-One Processing
```bash
python3 one_command_highlights.py
```

### Programmatic API Usage
```bash
python3 generate_video_cards.py \
    "https://youtu.be/VIDEO_ID" \
    transcript.vtt \
    --description "Video Title" \
    --keywords intro demo conclusion \
    --cards 4 \
    --output-dir highlights
```

### Testing Commands
```bash
# Test basic functionality
python3 test_quick.py

# Test editorial features  
python3 test_editorial.py

# Test specific components
python3 test_transcription.py
python3 test_smart_thumbnails.py
python3 test_video_click.py
```

### Utility Commands
```bash
# Manual transcript operations
yt-dlp --skip-download --write-subs --sub-lang en --sub-format vtt -o "%(title)s.%(ext)s" URL

# Convert raw text to VTT format
python3 transcript_converter.py

# Create distinct thumbnails
python3 create_distinct_thumbnails.py

# Extract screenshots at specific timestamps
python3 extract_timecode_screenshots.py

# Fix visual distinction issues
python3 fix_visual_distinction.py
```

### Local Preview
```bash
cd output_directory && python3 -m http.server 8000
```

## Dependencies Installation

```bash
pip3 install --user -r requirements.txt
```

### Known Compatibility Issues
- `openai-whisper` may not support Python 3.11+ - remove from requirements.txt if needed
- Core functionality works without openai-whisper dependency

Key packages:
- `yt-dlp` - YouTube transcript downloading
- `moviepy` - Video processing (use `from moviepy import VideoFileClip`)
- `transformers` & `torch` - AI models (BART summarization)
- `pytube` - YouTube video operations
- `pillow` - Image processing

## Technical Considerations

### MoviePy Import Pattern
Always use: `from moviepy import VideoFileClip`
NOT: `from moviepy.editor import VideoFileClip`

### Memory Management
- AI models require ~4GB RAM
- Implement extractive fallbacks for low memory
- Set `TOKENIZERS_PARALLELISM=false` to suppress fork warnings

### Error Handling Patterns
- All user-facing scripts provide helpful guidance for missing dependencies
- Graceful degradation when AI models or external tools unavailable
- Check transcript availability before processing

### File Organization
Output folders follow pattern: `{name}_{timestamp}/`
- `index.html` - Main highlight page
- `thumbnail_*.png` / `*.jpg` - Segment thumbnails
- `transcript.vtt` - Video transcript
- `screenshot_*.jpg` - Video screenshots (if extracted)

## Development Workflow

1. Test changes with `test_quick.py`
2. For new features, update appropriate entry point script
3. Core logic changes go in `core/` modules
4. Maintain backward compatibility in `generate_video_cards.py`

## Deployment Options

### Netlify
- Drag output folder to netlify.com dashboard
- Instant deployment

### GitHub Pages (via editorial_highlights.py)
- Automatic deployment to `https://[username].github.io/[repo]/[path]/`
- Default path structure: `YYYY-MM/descriptive-name/`

## Performance Expectations

- **Processing Time**: ~3-4 minutes for typical YouTube video
- **Memory Requirements**: ~4GB RAM for AI models (BART)
- **Output Quality**: Professional HTML with glass-morphism effects, responsive design
- **Thumbnail Quality**: High-quality frames extracted from video

## Known Issues & Limitations

### Common Issues
- **Title showing "None"**: Video title extraction may fail, affects display only
- **Video embedding failures**: Expected for some videos due to YouTube restrictions
- **Video download failures**: System continues with transcript-only processing

### Compatibility Notes
- Python 3.11+ may have issues with openai-whisper dependency
- All core functionality works without optional dependencies
- System provides graceful fallbacks for missing tools

## Key Architectural Patterns

- **Strategy Pattern**: Multiple summarization approaches (AI, extractive, simple)
- **Pipeline Pattern**: Scripts orchestrate core modules in sequence
- **Graceful Degradation**: Always provide fallbacks for external dependencies
- **Modular Design**: Core classes in `generate_video_cards.py` are reusable