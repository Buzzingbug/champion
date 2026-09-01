from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

width = 1600
users = [
    ("Noctaly", "10,000", "5,000", "2,000", "17,000 AURUM"),
    ("Vibe", "0", "0", "0", "5,000 AURUM"),
    ("Ghost", "100", "200", "0", "300 AURUM"),
]
height = 350 + (len(users) * 120)

# Base dark modern background
base = Image.new('RGBA', (width, height), (15, 20, 35, 255))

# Draw glowing blobs
blobs = Image.new('RGBA', (width, height), (0, 0, 0, 0))
blob_draw = ImageDraw.Draw(blobs)
# Cyan glow on top left
blob_draw.ellipse((-200, -200, 800, 800), fill=(0, 200, 255, 80))
# Purple glow on bottom right
blob_draw.ellipse((width-800, height-800, width+200, height+200), fill=(180, 0, 255, 60))

# Blur the blobs massively
blobs = blobs.filter(ImageFilter.GaussianBlur(150))
img = Image.alpha_composite(base, blobs)

# Draw Glass Card
glass = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glass_draw = ImageDraw.Draw(glass)
# Rounded rectangle for the glassmorphism
glass_draw.rounded_rectangle([(40, 40), (width - 40, height - 40)], radius=30, fill=(255, 255, 255, 12), outline=(255, 255, 255, 50), width=2)
img = Image.alpha_composite(img, glass)
draw = ImageDraw.Draw(img)

# Fonts
try:
    font_title = ImageFont.truetype("arial.ttf", 60)
    font_header = ImageFont.truetype("arial.ttf", 36)
    font_main = ImageFont.truetype("arial.ttf", 44)
    font_bold = ImageFont.truetype("arialbd.ttf", 46)
except:
    font_title = font_header = font_main = font_bold = ImageFont.load_default()

# Bot Avatar (Placeholder)
draw.ellipse([80, 70, 160, 150], fill=(255, 255, 255, 200))

# Title
draw.text((190, 80), "ECONOMY LEADERBOARD", fill=(255, 255, 255), font=font_title)

# Columns
cols = {
    "Rank": 80,
    "User": 280,
    "Channels": 750,
    "Categories": 1000,
    "Games": 1250,
    "Total": 1500 # Right-aligned
}

y = 200
draw.text((cols["Rank"], y), "RANK", fill=(180, 190, 210), font=font_header)
draw.text((cols["User"], y), "NAME", fill=(180, 190, 210), font=font_header)
draw.text((cols["Channels"], y), "CHANNELS", fill=(180, 190, 210), font=font_header)
draw.text((cols["Categories"], y), "CATEGORIES", fill=(180, 190, 210), font=font_header)
draw.text((cols["Games"], y), "GAMES", fill=(180, 190, 210), font=font_header)

total_txt = "TOTAL"
bbox = draw.textbbox((0,0), total_txt, font=font_header)
draw.text((cols["Total"] - (bbox[2] - bbox[0]), y), total_txt, fill=(241, 196, 15), font=font_header)

draw.line([(80, y + 60), (width - 80, y + 60)], fill=(255, 255, 255, 80), width=2)

y_offset = y + 90

for i, (name, chat, posts, games, total) in enumerate(users):
    color = (241, 196, 15) if i == 0 else (255, 255, 255)
    
    draw.text((cols["Rank"], y_offset + 25), f"#{i+1}", fill=color, font=font_bold)
    
    # Fake user avatar
    draw.ellipse([160, y_offset + 10, 240, y_offset + 90], fill=(60, 60, 70))
    
    draw.text((cols["User"], y_offset + 25), name, fill=(255, 255, 255), font=font_bold)
    
    draw.text((cols["Channels"], y_offset + 25), chat, fill=(220, 230, 255), font=font_main)
    draw.text((cols["Categories"], y_offset + 25), posts, fill=(220, 230, 255), font=font_main)
    draw.text((cols["Games"], y_offset + 25), games, fill=(220, 230, 255), font=font_main)
    
    bbox = draw.textbbox((0,0), total, font=font_bold)
    draw.text((cols["Total"] - (bbox[2] - bbox[0]), y_offset + 25), total, fill=color, font=font_bold)
    
    if i < len(users) - 1:
        draw.line([(80, y_offset + 120), (width - 80, y_offset + 120)], fill=(255, 255, 255, 20), width=1)
        
    y_offset += 130

output_path = r"C:\Users\Vibe\.gemini\antigravity\brain\a461ef30-806c-4ab5-9139-1802c29f8708\scratch\leaderboard_preview4.png"
img.convert('RGB').save(output_path, format="PNG")
print("Glassmorphism preview generated successfully!")
