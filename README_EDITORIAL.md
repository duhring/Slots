# Editorial Highlights System

A minimal, interactive command-line tool for creating video highlights with GitHub Pages deployment.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive workflow
python editorial_highlights.py
```

## Features

- **Minimal Prompts**: Clean, efficient command-line interface
- **Summary Review**: Edit AI-generated summaries before publishing
- **GitHub Deployment**: Deploy directly to GitHub Pages
- **Smart Defaults**: Auto-detect keywords and suggest paths
- **Beautiful Output**: Clean, responsive HTML with embedded video

## Workflow

1. **Enter YouTube URL** - Paste the video link
2. **Keywords** - Enter keywords or let system auto-detect
3. **Process** - System extracts segments and generates summaries
4. **Review** - Edit summaries inline (Enter to keep)
5. **Preview** - Check the generated page locally
6. **Deploy** - Push to GitHub Pages with simple path

## Summary Editing

During review, you can:
- **Enter** - Keep the current summary
- **Type new text** - Replace completely
- **+text** - Append to existing summary
- **\*text** - Mark as key point with emphasis
- **Number** - Limit to N words (e.g., "25")

## Deployment

Files are deployed to GitHub Pages at:
```
https://[username].github.io/[repo]/[path]/
```

Default structure:
```
YYYY-MM/descriptive-name/
```

## First-Time Setup

On first run, you'll be prompted for:
- GitHub username
- Repository name (default: editorial-highlights)

The system will guide you through creating the GitHub repository if needed.

## Requirements

- Python 3.7+
- `yt-dlp` for transcript downloads (optional but recommended)
- Git configured on your system
- GitHub account for deployment

## File Structure

```
editorial_highlights.py   # Main interactive script
core/
  ├── processor.py       # Video/transcript processing
  ├── summarizer.py      # AI summarization
  ├── github_deploy.py   # GitHub deployment
  └── config_manager.py  # Settings management
```

## Tips

- For best results, ensure video has good captions/transcripts
- Keywords are optional - system can auto-detect themes
- Review summaries for accuracy before deploying
- Use descriptive paths for easy organization

## Troubleshooting

**Transcript download fails**: The system will prompt you to paste the transcript manually

**AI summarization unavailable**: System falls back to extractive summarization

**GitHub push fails**: 
1. Ensure repository exists on GitHub
2. Check your Git credentials
3. Manual push: `cd ~/Documents/GitHub/[repo] && git push -u origin main`