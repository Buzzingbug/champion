from PIL import Image, ImageDraw, ImageFont
import os

width = 1000
users = [
    ("Noctaly", "10,000", "5,000", "2,000", "17,000 AURUM"),
    ("Vibe", "0", "0", "0", "5,000 AURUM"),
    ("Ghost", "100", "200", "0", "300 AURUM"),
]
height = 200 + (len(users) * 90)

img = Image.new('RGBA', (width, height), color=(20, 20, 24, 255))

# Glass overlay (just a slightly lighter box with gold border)
overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw_overlay = ImageDraw.Draw(overlay)
draw_overlay.rectangle([(15, 15), (width - 15, height - 15)], fill=(30, 30, 35, 255), outline=(241, 196, 15, 255), width=3)
img = Image.alpha_composite(img, overlay)
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("arial.ttf", 46)
    font_header = ImageFont.truetype("arial.ttf", 26)
    font_main = ImageFont.truetype("arial.ttf", 32)
    font_bold = ImageFont.truetype("arialbd.ttf", 34)
except:
    font_title = font_header = font_main = font_bold = ImageFont.load_default()

# Title
draw.text((40, 40), "🏆 ECONOMY LEADERBOARD", fill=(241, 196, 15), font=font_title)

# Columns
cols = {
    "Rank": 40,
    "User": 180,
    "Chat": 500,
    "Posts": 650,
    "Games": 800,
    "Total": 960 # Right-aligned
}

y = 120
draw.text((cols["Rank"], y), "RANK", fill=(150, 150, 150), font=font_header)
draw.text((cols["User"], y), "NAME", fill=(150, 150, 150), font=font_header)
draw.text((cols["Chat"], y), "CHAT", fill=(150, 150, 150), font=font_header)
draw.text((cols["Posts"], y), "MEDIA", fill=(150, 150, 150), font=font_header)
draw.text((cols["Games"], y), "GAMES", fill=(150, 150, 150), font=font_header)

total_txt = "TOTAL"
bbox = draw.textbbox((0,0), total_txt, font=font_header)
draw.text((cols["Total"] - (bbox[2] - bbox[0]), y), total_txt, fill=(241, 196, 15), font=font_header)

draw.line([(40, y + 45), (width - 40, y + 45)], fill=(241, 196, 15, 150), width=2)

y_offset = y + 70

for i, (name, chat, posts, games, total) in enumerate(users):
    color = (241, 196, 15) if i == 0 else (200, 200, 200)
    
    draw.text((cols["Rank"], y_offset + 15), f"#{i+1}", fill=color, font=font_bold)
    
    # Fake avatar
    draw.ellipse([100, y_offset, 160, y_offset + 60], fill=(60, 60, 70))
    
    draw.text((cols["User"], y_offset + 15), name, fill=(255, 255, 255), font=font_bold)
    
    draw.text((cols["Chat"], y_offset + 15), chat, fill=(200, 200, 200), font=font_main)
    draw.text((cols["Posts"], y_offset + 15), posts, fill=(200, 200, 200), font=font_main)
    draw.text((cols["Games"], y_offset + 15), games, fill=(200, 200, 200), font=font_main)
    
    bbox = draw.textbbox((0,0), total, font=font_bold)
    draw.text((cols["Total"] - (bbox[2] - bbox[0]), y_offset + 15), total, fill=color, font=font_bold)
    
    if i < len(users) - 1:
        draw.line([(40, y_offset + 80), (width - 40, y_offset + 80)], fill=(255, 255, 255, 40), width=1)
        
    y_offset += 90

output_path = r"C:\Users\Vibe\.gemini\antigravity\brain\a461ef30-806c-4ab5-9139-1802c29f8708\scratch\leaderboard_preview3.png"
img.convert('RGB').save(output_path, format="PNG")
print("Preview 3 generated successfully!")
