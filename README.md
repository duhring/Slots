# YouTube Highlight Generator 🎬

Create beautiful, shareable highlight pages from YouTube videos in minutes! This tool automatically downloads transcripts, finds interesting segments using AI, and generates stunning static websites ready for Netlify deployment.

## ✨ What's New - Easy Mode!

We've made it **super simple** to use. No more complex command lines!

### 🚀 Quick Start (Easy Mode)

```bash
python3 easy_highlights.py
```

That's it! The script will:
1. 📥 Ask for a YouTube URL
2. 🔍 Auto-download transcripts 
3. 🧠 Smart-detect keywords (or let you choose)
4. 🎨 Generate beautiful highlight cards
5. 🌐 Create a deployable website

### Example Output

![Highlight Cards Preview](https://via.placeholder.com/800x400/667eea/white?text=Beautiful+Highlight+Cards)

## 🎯 Features

- **Smart Transcript Download**: Automatically gets captions using yt-dlp
- **AI Keyword Detection**: Analyzes content to find interesting segments
- **Beautiful Design**: Modern glass-morphism cards with gradients
- **Mobile Responsive**: Looks great on all devices  
- **One-Click Deploy**: Ready for Netlify drag & drop
- **AI Summarization**: Uses BART model for concise summaries
- **Video Thumbnails**: Extracts frames from key moments

## 📋 Requirements

All handled automatically! The script checks and guides you through any missing dependencies:

- Python 3.9+
- yt-dlp (for transcript download)
- PyTorch & Transformers (for AI)
- MoviePy (for video processing)

## 🔧 Advanced Usage

### Command Line (Original)

```bash
python3 generate_video_cards.py \
    "https://youtu.be/YOUR_VIDEO_ID" \
    transcript.vtt \
    --description "Your Video Title" \
    --keywords introduction demo conclusion results \
    --cards 4 \
    --output-dir highlights
```

### Manual Transcript Download

```bash
yt-dlp --skip-download --write-subs --sub-lang en --sub-format vtt \
       -o "%(title)s.%(ext)s" \
       https://youtu.be/YOUR_VIDEO_ID
```

## 📁 Output Structure

```
highlights_20240805_143022/
├── index.html              # 🌐 Main highlight page
├── video.mp4              # 📹 Downloaded video
├── transcript.vtt         # 📄 Video transcript  
├── thumbnail_001.png      # 🖼️ Segment images
├── thumbnail_002.png
├── thumbnail_003.png
└── thumbnail_004.png
```

## 🌐 Deploy to Netlify

### Method 1: Drag & Drop (Easiest)
1. Go to [netlify.com](https://netlify.com)
2. Drag your output folder onto the dashboard
3. Your site is live! 🎉

### Method 2: Netlify CLI
```bash
npm install -g netlify-cli
netlify deploy --dir=your_highlights_folder
netlify deploy --prod --dir=your_highlights_folder
```

## 🎨 Customization Ideas

### Keyword Strategies
- **Educational**: `introduction methodology results conclusion`
- **Tutorial**: `setup configuration demo testing`  
- **Presentation**: `agenda problem solution demo questions`
- **Review**: `overview pros cons verdict recommendation`

### Output Variations
```bash
# Quick highlights (3 cards)
python3 easy_highlights.py
# Enter 3 when asked for number of cards

# Detailed breakdown (8 cards)  
python3 easy_highlights.py
# Enter 8 when asked for number of cards
```

## 🐛 Troubleshooting

### "No transcript found"
- Video may not have captions
- Try enabling auto-generated captions in YouTube settings
- Some private/restricted videos don't allow caption downloads

### "AI model failed to load"
- This is normal! Falls back to extractive summarization
- For full AI: ensure you have 8GB+ RAM available

### "Video download failed"
- Check if video is public and available
- Some regions/networks may block downloads
- Try a different video to test

## 🏆 Example Results

**Input**: Educational video about machine learning  
**Keywords**: `introduction algorithms training evaluation`  
**Output**: 4 beautiful cards showing key ML concepts with timestamps

**Deploy Time**: ~2 minutes from URL to live website!

## 🤝 Contributing

Found this useful? Here are ways to help:
- 🐛 Report bugs in issues
- 💡 Suggest new features  
- 🎨 Share your highlight pages
- ⭐ Star the repository

## 📝 License

MIT License - use freely for personal and commercial projects!

---

**Ready to create amazing video highlights?** 

```bash
python3 easy_highlights.py
```

Just run it and follow the prompts! 🚀