#!/usr/bin/env python3
"""
Fix the HTML to add visual distinction via CSS instead of thumbnail generation
"""

def add_visual_distinction_to_html(html_file_path):
    """Add CSS-based visual distinction to existing HTML"""
    
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    
    # Color schemes for each segment
    color_schemes = [
        {"name": "orange", "color": "#ff5733", "bg": "linear-gradient(45deg, #ff5733, #ff8c42)"},
        {"name": "blue", "color": "#4a90e2", "bg": "linear-gradient(45deg, #4a90e2, #50c8ff)"},
        {"name": "purple", "color": "#9c27b0", "bg": "linear-gradient(45deg, #9c27b0, #e91e63)"},
        {"name": "green", "color": "#4caf50", "bg": "linear-gradient(45deg, #4caf50, #8bc34a)"}
    ]
    
    # Add CSS for visual distinction
    css_additions = """
        
        /* Color-coded segment cards */
        .highlight-card.segment-1 {
            border: 4px solid #ff5733;
            background: linear-gradient(135deg, rgba(255, 87, 51, 0.1), rgba(255, 255, 255, 0.1));
        }
        
        .highlight-card.segment-1::before {
            content: "SEGMENT 1 • ORANGE";
            position: absolute;
            top: -15px;
            left: 15px;
            background: linear-gradient(45deg, #ff5733, #ff8c42);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            z-index: 10;
        }
        
        .highlight-card.segment-2 {
            border: 4px solid #4a90e2;
            background: linear-gradient(135deg, rgba(74, 144, 226, 0.1), rgba(255, 255, 255, 0.1));
        }
        
        .highlight-card.segment-2::before {
            content: "SEGMENT 2 • BLUE";
            position: absolute;
            top: -15px;
            left: 15px;
            background: linear-gradient(45deg, #4a90e2, #50c8ff);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            z-index: 10;
        }
        
        .highlight-card.segment-3 {
            border: 4px solid #9c27b0;
            background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(255, 255, 255, 0.1));
        }
        
        .highlight-card.segment-3::before {
            content: "SEGMENT 3 • PURPLE";
            position: absolute;
            top: -15px;
            left: 15px;
            background: linear-gradient(45deg, #9c27b0, #e91e63);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            z-index: 10;
        }
        
        .highlight-card.segment-4 {
            border: 4px solid #4caf50;
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(255, 255, 255, 0.1));
        }
        
        .highlight-card.segment-4::before {
            content: "SEGMENT 4 • GREEN";
            position: absolute;
            top: -15px;
            left: 15px;
            background: linear-gradient(45deg, #4caf50, #8bc34a);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            z-index: 10;
        }
        
        .highlight-card {
            position: relative;
            margin-top: 20px;
        }
        
        .watch-btn.segment-1 {
            background: linear-gradient(45deg, #ff5733, #ff8c42);
        }
        
        .watch-btn.segment-2 {
            background: linear-gradient(45deg, #4a90e2, #50c8ff);
        }
        
        .watch-btn.segment-3 {
            background: linear-gradient(45deg, #9c27b0, #e91e63);
        }
        
        .watch-btn.segment-4 {
            background: linear-gradient(45deg, #4caf50, #8bc34a);
        }
        
    </style>"""
    
    # Insert the CSS before closing </style>
    html_content = html_content.replace("</style>", css_additions)
    
    # Add segment classes to the cards
    for i in range(1, 5):
        # Find and replace highlight-card divs with segment classes
        old_card = f'<div class="highlight-card">'
        new_card = f'<div class="highlight-card segment-{i}">'
        html_content = html_content.replace(old_card, new_card, 1)
        
        # Add segment classes to watch buttons
        old_button_pattern = r'<button onclick="seekToTime\(\d+\)" class="watch-btn">'
        new_button = f'<button onclick="seekToTime(\\1)" class="watch-btn segment-{i}">'
        
        # This is a bit tricky, let's do it step by step
        if f'segment-{i}' in html_content:  # Only if we successfully added card class
            # Find the watch button in this card and add the class
            card_start = html_content.find(f'<div class="highlight-card segment-{i}">')
            if card_start != -1:
                card_end = html_content.find('<div class="highlight-card', card_start + 1)
                if card_end == -1:
                    card_end = html_content.find('</div>', card_start)
                    # Find the closing div of this card
                    div_count = 1
                    pos = card_start + len(f'<div class="highlight-card segment-{i}">')
                    while div_count > 0 and pos < len(html_content):
                        if html_content[pos:pos+5] == '<div ':
                            div_count += 1
                        elif html_content[pos:pos+6] == '</div>':
                            div_count -= 1
                        pos += 1
                    card_end = pos
                
                # Replace watch button within this card
                card_section = html_content[card_start:card_end]
                card_section = card_section.replace('class="watch-btn"', f'class="watch-btn segment-{i}"')
                html_content = html_content[:card_start] + card_section + html_content[card_end:]
    
    # Save the updated HTML
    with open(html_file_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Added visual distinction to {html_file_path}")

if __name__ == "__main__":
    # Test with the most recent HTML file
    import sys
    import glob
    
    # Find the most recent highlights directory
    html_files = glob.glob("genie3_highlights*/index.html")
    if html_files:
        # Sort by modification time, get the newest
        html_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        latest_html = html_files[0]
        print(f"Processing: {latest_html}")
        add_visual_distinction_to_html(latest_html)
    else:
        print("No HTML files found")