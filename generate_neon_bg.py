from PIL import Image, ImageDraw, ImageFilter
import os
import random

os.makedirs("assets", exist_ok=True)
os.makedirs("assets/icons", exist_ok=True)

width = 1500
height = 1000

# 1. Base Atmospheric Ambient Lighting - Synced with ring.png!
base = Image.new('RGBA', (width, height), (13, 15, 22, 255))
ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
amb_draw = ImageDraw.Draw(ambient)

# Avatar lighting (synced with ring.png)
amb_draw.ellipse((-80, -100, 480, 360), fill=(235, 25, 170, 180)) # Magenta top
amb_draw.ellipse((-60, 200, 440, 560), fill=(255, 175, 20, 170))  # Amber bottom
amb_draw.ellipse((380, 60, 950, 450), fill=(160, 45, 235, 120))   # Purple nebula
amb_draw.ellipse((880, -40, 1540, 380), fill=(0, 150, 255, 130))  # Electric Blue

# Bottom 4 Bento Floods
amb_draw.ellipse((0, 650, 420, 1000), fill=(255, 160, 10, 150))      # Gold
amb_draw.ellipse((360, 650, 760, 1000), fill=(245, 30, 200, 150))    # Pink
amb_draw.ellipse((710, 650, 1120, 1000), fill=(0, 255, 180, 150))    # Cyan
amb_draw.ellipse((1070, 650, 1500, 1000), fill=(255, 60, 90, 150))   # Red

ambient = ambient.filter(ImageFilter.GaussianBlur(95))
img = Image.alpha_composite(base, ambient)

# Starry stardust
random.seed(777)
stars = Image.new('RGBA', (width, height), (0, 0, 0, 0))
st_draw = ImageDraw.Draw(stars)
for _ in range(180):
    sx = random.randint(10, width - 10)
    sy = random.randint(10, height - 10)
    sr = random.choice([1, 1, 2])
    alpha = random.randint(90, 240)
    col = random.choice([(255, 255, 255, alpha), (255, 220, 160, alpha), (180, 220, 255, alpha)])
    st_draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=col)

img = Image.alpha_composite(img, stars)

# 2. Edge-to-Edge Glass Overlay
full_glass = Image.new('RGBA', (width, height), (0, 0, 0, 0))
ImageDraw.Draw(full_glass).rectangle([(0, 0), (width, height)], fill=(12, 14, 20, 45), outline=(255, 255, 255, 25), width=1)
img = Image.alpha_composite(img, full_glass)

# 3. Inner Glass Panes
glass_panes = Image.new('RGBA', (width, height), (0, 0, 0, 0))
gp_draw = ImageDraw.Draw(glass_panes)

def draw_glass(box, radius, fill_col=(255, 255, 255, 12), outline_col=(255, 255, 255, 36), width=1):
    gp_draw.rounded_rectangle(box, radius=radius, fill=fill_col, outline=outline_col, width=width)

# Top Right Server Card
draw_glass([(920, 45), (1460, 175)], 24, fill_col=(10, 20, 35, 90), outline_col=(60, 120, 190, 160), width=2)

# Top Right Master Streak & Level Card
draw_glass([(920, 195), (1460, 685)], 24, fill_col=(14, 18, 28, 175), outline_col=(60, 130, 210, 90), width=2)

# Rank Banner
draw_glass([(360, 165), (890, 245)], 18, fill_col=(45, 15, 75, 160), outline_col=(210, 110, 255, 240), width=2)

# 6 SYMMETRICAL TILES (415px x 80px)
# Row 1: VIP STATUS & AGE VERIFIED
draw_glass([(40, 395), (455, 475)], 16, fill_col=(35, 26, 10, 140), outline_col=(255, 200, 40, 220), width=2)
draw_glass([(485, 395), (900, 475)], 16, fill_col=(10, 32, 22, 140), outline_col=(0, 240, 140, 220), width=2)

# Row 2: Server Rank & Goon Coins
draw_glass([(40, 500), (455, 580)], 16, fill_col=(255, 255, 255, 12), outline_col=(255, 255, 255, 35))
draw_glass([(485, 500), (900, 580)], 16, fill_col=(255, 255, 255, 12), outline_col=(255, 255, 255, 35))

# Row 3: BOOST STATUS & TOP CHANNEL (Exact same 415x80 size!)
draw_glass([(40, 605), (455, 685)], 16, fill_col=(28, 16, 38, 140), outline_col=(210, 100, 255, 200), width=2)
draw_glass([(485, 605), (900, 685)], 16, fill_col=(10, 28, 42, 140), outline_col=(0, 210, 255, 200), width=2)

# Bottom 4 Bento Cards
draw_glass([(40, 725), (375, 945)], 24, fill_col=(255, 170, 0, 18), outline_col=(255, 180, 40, 100))
draw_glass([(395, 725), (730, 945)], 24, fill_col=(240, 50, 200, 18), outline_col=(240, 60, 200, 100))
draw_glass([(750, 725), (1085, 945)], 24, fill_col=(0, 250, 180, 18), outline_col=(0, 245, 180, 100))
draw_glass([(1105, 725), (1440, 945)], 24, fill_col=(255, 70, 100, 18), outline_col=(255, 80, 110, 100))

img = Image.alpha_composite(img, glass_panes)

# 4. Front Neon Glow
front_neon = Image.new('RGBA', (width, height), (0, 0, 0, 0))
fn_draw = ImageDraw.Draw(front_neon)
fn_draw.rounded_rectangle([(360, 165), (890, 245)], radius=18, outline=(190, 80, 255, 240), width=5)
fn_draw.rounded_rectangle([(40, 395), (455, 475)], radius=16, outline=(255, 190, 30, 220), width=4)
fn_draw.rounded_rectangle([(485, 395), (900, 475)], radius=16, outline=(0, 240, 140, 220), width=4)
fn_draw.rounded_rectangle([(40, 605), (455, 685)], radius=16, outline=(200, 80, 255, 200), width=4)
fn_draw.rounded_rectangle([(485, 605), (900, 685)], radius=16, outline=(0, 200, 255, 200), width=4)

fn_draw.rounded_rectangle([(40, 725), (375, 945)], radius=24, outline=(255, 160, 0, 255), width=5)
fn_draw.rounded_rectangle([(395, 725), (730, 945)], radius=24, outline=(245, 45, 210, 255), width=6)
fn_draw.rounded_rectangle([(750, 725), (1085, 945)], radius=24, outline=(0, 250, 185, 255), width=5)
fn_draw.rounded_rectangle([(1105, 725), (1440, 945)], radius=24, outline=(255, 70, 100, 255), width=5)

blurred_front_neon = front_neon.filter(ImageFilter.GaussianBlur(12))
img = Image.alpha_composite(img, blurred_front_neon)

# 5. Themed Illustrations
top_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
tl_draw = ImageDraw.Draw(top_layer)
tl_draw.rounded_rectangle([(40, 725), (375, 945)], radius=24, outline=(255, 200, 60, 255), width=2)
tl_draw.rounded_rectangle([(395, 725), (730, 945)], radius=24, outline=(255, 110, 235, 255), width=2)
tl_draw.rounded_rectangle([(750, 725), (1085, 945)], radius=24, outline=(80, 255, 210, 255), width=2)
tl_draw.rounded_rectangle([(1105, 725), (1440, 945)], radius=24, outline=(255, 120, 140, 255), width=2)

# Chat Bubbles
tl_draw.rounded_rectangle([(270, 795), (355, 855)], radius=14, fill=(255, 180, 30, 45), outline=(255, 200, 50, 240), width=2)
tl_draw.polygon([(285, 855), (275, 875), (305, 855)], fill=(255, 200, 50, 240))
tl_draw.line([(285, 815), (340, 815)], fill=(255, 230, 130, 220), width=3)
tl_draw.line([(285, 830), (325, 830)], fill=(255, 230, 130, 220), width=3)

tl_draw.rounded_rectangle([(225, 860), (290, 910)], radius=10, fill=(255, 150, 20, 40), outline=(255, 180, 40, 200), width=2)
tl_draw.polygon([(270, 910), (280, 925), (285, 910)], fill=(255, 180, 40, 200))
tl_draw.line([(238, 882), (277, 882)], fill=(255, 210, 110, 200), width=2)

# Photos
tl_draw.rounded_rectangle([(615, 785), (690, 865)], radius=8, fill=(230, 45, 190, 45), outline=(255, 100, 225, 200), width=2)
tl_draw.rounded_rectangle([(640, 825), (715, 915)], radius=8, fill=(240, 55, 205, 65), outline=(255, 130, 240, 255), width=2)
tl_draw.rectangle([(648, 833), (707, 885)], fill=(25, 10, 30, 255))
tl_draw.ellipse([(655, 840), (665, 850)], fill=(255, 190, 240, 255))
tl_draw.polygon([(652, 880), (672, 855), (688, 880)], fill=(240, 70, 210, 240))
tl_draw.polygon([(675, 880), (692, 862), (704, 880)], fill=(210, 50, 180, 240))

# Audio Waves
vx, vy = 1010, 855
tl_draw.ellipse([(vx - 14, vy - 14), (vx + 14, vy + 14)], fill=(0, 250, 185, 255))
tl_draw.ellipse([(vx - 6, vy - 6), (vx + 6, vy + 6)], fill=(12, 28, 24, 255))
tl_draw.arc([(vx - 32, vy - 32), (vx + 32, vy + 32)], start=-70, end=70, fill=(80, 255, 210, 240), width=3)
tl_draw.arc([(vx - 32, vy - 32), (vx + 32, vy + 32)], start=110, end=250, fill=(80, 255, 210, 240), width=3)
tl_draw.arc([(vx - 50, vy - 50), (vx + 50, vy + 50)], start=-60, end=60, fill=(80, 255, 210, 180), width=3)
tl_draw.arc([(vx - 50, vy - 50), (vx + 50, vy + 50)], start=120, end=240, fill=(80, 255, 210, 180), width=3)

# Heart Emoji
ex, ey = 1380, 860
tl_draw.ellipse([(ex - 42, ey - 42), (ex + 42, ey + 42)], fill=(255, 75, 60, 240), outline=(255, 200, 130, 255), width=3)
tl_draw.arc([(ex - 24, ey - 16), (ex - 8, ey)], start=180, end=0, fill=(35, 10, 15, 255), width=4)
tl_draw.arc([(ex + 8, ey - 16), (ex + 24, ey)], start=180, end=0, fill=(35, 10, 15, 255), width=4)
tl_draw.chord([(ex - 22, ey - 4), (ex + 22, ey + 24)], start=0, end=180, fill=(40, 12, 18, 255))
tl_draw.chord([(ex - 12, ey + 10), (ex + 12, ey + 24)], start=0, end=180, fill=(255, 120, 130, 255))

img = Image.alpha_composite(img, top_layer)

# Halo behind ring
halo = Image.new('RGBA', (width, height), (0, 0, 0, 0))
h_draw = ImageDraw.Draw(halo)
h_draw.ellipse((200 - 150, 230 - 165, 200 + 150, 230 + 135), fill=(240, 30, 180, 100))
h_draw.ellipse((200 - 150, 230 - 135, 200 + 150, 230 + 165), fill=(255, 200, 30, 100))
halo = halo.filter(ImageFilter.GaussianBlur(35))
img = Image.alpha_composite(img, halo)

img.save("assets/neon_profile_bg.png")
print("Saved assets/neon_profile_bg.png with V17 layout successfully!")
