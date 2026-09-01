from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

width = 1200
users = [
    ("Noctaly", "10,000", "5,000", "2,000", "17,000"),
    ("Vibe", "0", "0", "0", "5,000"),
    ("Ghost", "100", "200", "0", "300"),
]
height = 250 + (len(users) * 110)

# Base dark modern background
base = Image.new('RGBA', (width, height), (15, 15, 18, 255))

# Draw glowing blobs with new colors (#fbec90,#ca675c)
# fbec90 = 251, 236, 144
# ca675c = 202, 103, 92
blobs = Image.new('RGBA', (width, height), (0, 0, 0, 0))
blob_draw = ImageDraw.Draw(blobs)
blob_draw.ellipse((-100, -100, 600, 600), fill=(251, 236, 144, 180)) # fbec90 top left
blob_draw.ellipse((width-600, height-600, width+100, height+100), fill=(202, 103, 92, 160)) # ca675c bottom right
blobs = blobs.filter(ImageFilter.GaussianBlur(120))
img = Image.alpha_composite(base, blobs)

# Draw Glass Card
glass = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glass_draw = ImageDraw.Draw(glass)
glass_draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=30, fill=(255, 255, 255, 15), outline=(255, 255, 255, 60), width=2)
img = Image.alpha_composite(img, glass)
draw = ImageDraw.Draw(img)

# Fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 60)
    font_header = ImageFont.truetype("arialbd.ttf", 30)
    font_main = ImageFont.truetype("arial.ttf", 40)
    font_bold = ImageFont.truetype("arialbd.ttf", 42)
except:
    font_title = font_header = font_main = font_bold = ImageFont.load_default()

# Bot Avatar (Placeholder)
draw.ellipse([40, 40, 130, 130], fill=(255, 255, 255, 200))

# Title
draw.text((150, 60), "ECONOMY LEADERBOARD", fill=(255, 255, 255), font=font_title)

# Columns spacing - tighter to fit larger text
cols = {
    "Rank": 40,
    "User": 200,
    "Channels": 520,
    "Categories": 750,
    "Games": 1000,
    "Total": 1160 # Right-aligned
}

y = 160
draw.text((cols["Rank"], y), "RNK", fill=(220, 220, 220), font=font_header)
draw.text((cols["User"], y), "NAME", fill=(220, 220, 220), font=font_header)
draw.text((cols["Channels"], y), "CHANNELS", fill=(220, 220, 220), font=font_header)
draw.text((cols["Categories"], y), "CATEGORIES", fill=(220, 220, 220), font=font_header)
draw.text((cols["Games"], y), "GAMES", fill=(220, 220, 220), font=font_header)

total_txt = "TOTAL"
bbox = draw.textbbox((0,0), total_txt, font=font_header)
draw.text((cols["Total"] - (bbox[2] - bbox[0]), y), total_txt, fill=(251, 236, 144), font=font_header)

draw.line([(40, y + 50), (width - 40, y + 50)], fill=(255, 255, 255, 100), width=2)

y_offset = y + 70

for i, (name, chat, posts, games, total) in enumerate(users):
    color = (251, 236, 144) if i == 0 else (255, 255, 255)
    
    draw.text((cols["Rank"], y_offset + 20), f"#{i+1}", fill=color, font=font_bold)
    
    # Fake user avatar
    draw.ellipse([110, y_offset + 10, 180, y_offset + 80], fill=(60, 60, 70))
    
    draw.text((cols["User"], y_offset + 20), name, fill=(255, 255, 255), font=font_bold)
    
    draw.text((cols["Channels"], y_offset + 20), chat, fill=(255, 255, 255), font=font_main)
    draw.text((cols["Categories"], y_offset + 20), posts, fill=(255, 255, 255), font=font_main)
    draw.text((cols["Games"], y_offset + 20), games, fill=(255, 255, 255), font=font_main)
    
    bbox = draw.textbbox((0,0), total, font=font_bold)
    draw.text((cols["Total"] - (bbox[2] - bbox[0]), y_offset + 20), total, fill=color, font=font_bold)
    
    if i < len(users) - 1:
        draw.line([(40, y_offset + 100), (width - 40, y_offset + 100)], fill=(255, 255, 255, 40), width=1)
        
    y_offset += 110

output_path = r"C:\Users\Vibe\.gemini\antigravity\brain\a461ef30-806c-4ab5-9139-1802c29f8708\scratch\leaderboard_preview5.png"
img.convert('RGB').save(output_path, format="PNG")
print("Preview 5 generated successfully!")
