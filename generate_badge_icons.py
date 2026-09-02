from PIL import Image, ImageDraw, ImageFilter
import os
import math

os.makedirs("assets/icons", exist_ok=True)

size = 128

def create_badge(filename, glow_color, rim_color, inner_bg, emblem_fn):
    # 1. Base transparent image
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # 2. Glow layer
    glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse([(10, 10), (size - 10, size - 10)], fill=glow_color)
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas, glow)
    
    # 3. Badge Disc layer
    disc = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(disc)
    # Dark metallic background
    d_draw.ellipse([(12, 12), (size - 12, size - 12)], fill=inner_bg, outline=rim_color, width=5)
    # Inner subtle rim
    d_draw.ellipse([(20, 20), (size - 20, size - 20)], outline=(255, 255, 255, 70), width=2)
    canvas = Image.alpha_composite(canvas, disc)
    
    # 4. Emblem layer
    emblem = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    e_draw = ImageDraw.Draw(emblem)
    emblem_fn(e_draw, size // 2, size // 2)
    canvas = Image.alpha_composite(canvas, emblem)
    
    # 5. Glossy glass shine on top
    shine = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shine)
    s_draw.chord([(20, 20), (size - 20, size // 2 + 10)], start=180, end=0, fill=(255, 255, 255, 50))
    canvas = Image.alpha_composite(canvas, shine)
    
    canvas.save(filename)
    print(f"Saved {filename}")

# VIP Badge: Glowing 3D Gold Crown
def draw_vip(draw, cx, cy):
    pts = [
        (cx - 30, cy - 12),
        (cx - 18, cy + 4),
        (cx, cy - 22),
        (cx + 18, cy + 4),
        (cx + 30, cy - 12),
        (cx + 24, cy + 20),
        (cx - 24, cy + 20)
    ]
    draw.polygon(pts, fill=(255, 210, 40, 255), outline=(255, 245, 180, 255))
    # Crown jewels
    draw.ellipse([(cx - 30 - 3, cy - 12 - 3), (cx - 30 + 3, cy - 12 + 3)], fill=(255, 255, 255, 255))
    draw.ellipse([(cx - 4, cy - 22 - 4), (cx + 4, cy - 22 + 4)], fill=(255, 255, 255, 255))
    draw.ellipse([(cx + 30 - 3, cy - 12 - 3), (cx + 30 + 3, cy - 12 + 3)], fill=(255, 255, 255, 255))
    # Bottom jewel band
    draw.rounded_rectangle([(cx - 22, cy + 14), (cx + 22, cy + 20)], radius=3, fill=(230, 150, 10, 255))
    draw.ellipse([(cx - 12, cy + 15), (cx - 8, cy + 19)], fill=(255, 60, 60, 255))
    draw.ellipse([(cx - 2, cy + 15), (cx + 2, cy + 19)], fill=(60, 220, 255, 255))
    draw.ellipse([(cx + 8, cy + 15), (cx + 12, cy + 19)], fill=(255, 60, 60, 255))

# Staff Badge: Cyan/Blue Shield & Star
def draw_staff(draw, cx, cy):
    # Outer shield
    pts = [
        (cx - 26, cy - 22),
        (cx + 26, cy - 22),
        (cx + 26, cy + 4),
        (cx, cy + 26),
        (cx - 26, cy + 4)
    ]
    draw.polygon(pts, fill=(35, 110, 240, 255), outline=(140, 220, 255, 255))
    # Inner star
    star_pts = []
    for i in range(10):
        r = 14 if i % 2 == 0 else 6
        angle = i * math.pi / 5 - math.pi / 2
        star_pts.append((cx + r * math.cos(angle), cy - 2 + r * math.sin(angle)))
    draw.polygon(star_pts, fill=(255, 255, 255, 255))

# OG Badge: Golden/Amber Vintage Star & Laurel Ring
def draw_og(draw, cx, cy):
    # Laurel ring
    draw.arc([(cx - 30, cy - 30), (cx + 30, cy + 30)], start=40, end=320, fill=(255, 180, 50, 255), width=4)
    # Big star
    star_pts = []
    for i in range(10):
        r = 20 if i % 2 == 0 else 9
        angle = i * math.pi / 5 - math.pi / 2
        star_pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(star_pts, fill=(255, 140, 30, 255), outline=(255, 235, 160, 255))
    # Center text "OG"
    draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=(255, 255, 255, 255))

create_badge(
    "assets/icons/badge_vip.png",
    glow_color=(255, 190, 30, 220),
    rim_color=(255, 215, 60, 255),
    inner_bg=(28, 20, 8, 255),
    emblem_fn=draw_vip
)

create_badge(
    "assets/icons/badge_staff.png",
    glow_color=(0, 160, 255, 220),
    rim_color=(90, 200, 255, 255),
    inner_bg=(8, 18, 38, 255),
    emblem_fn=draw_staff
)

create_badge(
    "assets/icons/badge_og.png",
    glow_color=(255, 130, 20, 220),
    rim_color=(255, 160, 40, 255),
    inner_bg=(32, 16, 8, 255),
    emblem_fn=draw_og
)
