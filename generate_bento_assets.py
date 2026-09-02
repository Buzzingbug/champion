from PIL import Image, ImageDraw, ImageFilter
import os
import math

os.makedirs("assets/icons", exist_ok=True)

# 1. Generate dedicated bento background (1200x800) WITHOUT pre-baked outer border
width = 1200
height = 800

base = Image.new('RGBA', (width, height), (15, 15, 18, 255))
blobs = Image.new('RGBA', (width, height), (0, 0, 0, 0))
blob_draw = ImageDraw.Draw(blobs)

# Top-left golden glow
blob_draw.ellipse((-80, -80, 500, 500), fill=(251, 236, 144, 170))
# Bottom-right reddish-orange glow
blob_draw.ellipse((width-500, height-500, width+80, height+80), fill=(202, 103, 92, 150))
# Subtle mid accent
blob_draw.ellipse((width//2 - 200, height//2 - 150, width//2 + 200, height//2 + 150), fill=(210, 140, 100, 30))

blobs = blobs.filter(ImageFilter.GaussianBlur(100))
img = Image.alpha_composite(base, blobs)
img.save("assets/bento_bg.png")
print("Saved assets/bento_bg.png")


# 2. Helper to generate crisp minimalist monochrome icons (64x64)
def create_icon_canvas():
    return Image.new('RGBA', (64, 64), (0, 0, 0, 0))

# A. Chat / Message Icon
icon_msg = create_icon_canvas()
d = ImageDraw.Draw(icon_msg)
# Rounded speech bubble
d.rounded_rectangle([(8, 10), (56, 44)], radius=10, outline=(251, 236, 144, 230), width=3)
# Tail
d.polygon([(18, 44), (28, 44), (16, 54)], fill=(251, 236, 144, 230))
# Lines inside
d.line([(18, 22), (46, 22)], fill=(251, 236, 144, 200), width=3)
d.line([(18, 32), (38, 32)], fill=(251, 236, 144, 200), width=3)
icon_msg.save("assets/icons/chat.png")

# B. Media / Camera Icon
icon_media = create_icon_canvas()
d = ImageDraw.Draw(icon_media)
# Camera body
d.rounded_rectangle([(8, 18), (56, 52)], radius=8, outline=(200, 215, 255, 230), width=3)
# Lens ring
d.ellipse([(22, 25), (42, 45)], outline=(200, 215, 255, 230), width=3)
# Small flash/shutter
d.rounded_rectangle([(22, 11), (34, 18)], radius=3, fill=(200, 215, 255, 230))
d.ellipse([(45, 24), (49, 28)], fill=(200, 215, 255, 230))
icon_media.save("assets/icons/media.png")

# C. Voice / Headset/Mic Icon
icon_voice = create_icon_canvas()
d = ImageDraw.Draw(icon_voice)
# Headset band
d.arc([(10, 10), (54, 52)], start=180, end=0, fill=(180, 235, 200, 230), width=3)
# Left ear cup
d.rounded_rectangle([(8, 28), (18, 46)], radius=4, fill=(180, 235, 200, 230))
# Right ear cup
d.rounded_rectangle([(46, 28), (56, 46)], radius=4, fill=(180, 235, 200, 230))
# Mic boom
d.arc([(18, 30), (46, 56)], start=30, end=130, fill=(180, 235, 200, 230), width=3)
d.ellipse([(38, 51), (44, 57)], fill=(180, 235, 200, 230))
icon_voice.save("assets/icons/voice.png")

# D. Flame / Streak Icon
icon_fire = create_icon_canvas()
d = ImageDraw.Draw(icon_fire)
# Draw flame path
flame_pts = [
    (32, 8), (40, 22), (48, 28), (52, 40), (46, 54),
    (32, 58), (18, 54), (12, 40), (16, 28), (24, 28),
    (22, 36), (28, 40), (32, 32), (30, 20)
]
d.polygon(flame_pts, fill=(255, 120, 80, 230))
# Inner bright core
core_pts = [
    (32, 28), (38, 38), (40, 46), (32, 52), (24, 46), (26, 38)
]
d.polygon(core_pts, fill=(255, 220, 120, 255))
icon_fire.save("assets/icons/fire.png")

# E. Star / Trophy Icon
icon_trophy = create_icon_canvas()
d = ImageDraw.Draw(icon_trophy)
# Cup body
d.polygon([(18, 14), (46, 14), (42, 36), (32, 42), (22, 36)], fill=(251, 236, 144, 230))
# Handles
d.arc([(10, 16), (24, 32)], start=90, end=270, fill=(251, 236, 144, 230), width=3)
d.arc([(40, 16), (54, 32)], start=-90, end=90, fill=(251, 236, 144, 230), width=3)
# Stem & base
d.rectangle([(29, 42), (35, 48)], fill=(251, 236, 144, 230))
d.rounded_rectangle([(20, 48), (44, 54)], radius=2, fill=(251, 236, 144, 230))
icon_trophy.save("assets/icons/trophy.png")

print("All icons successfully generated in assets/icons/")
