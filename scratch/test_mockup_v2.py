from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
import random

os.makedirs("scratch", exist_ok=True)
os.makedirs("assets/icons", exist_ok=True)

width = 1500
height = 1000

# 1. Base Dark Carbon Background with Nebula Glows
base = Image.new('RGBA', (width, height), (9, 10, 14, 255))
ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
amb_draw = ImageDraw.Draw(ambient)

# Warm golden aura behind avatar
amb_draw.ellipse((40, 60, 360, 400), fill=(255, 140, 0, 110))
# Top right blue-cyan nebula
amb_draw.ellipse((920, 20, 1460, 260), fill=(0, 130, 255, 55))
# Center purple bloom
amb_draw.ellipse((380, 160, 880, 360), fill=(160, 40, 255, 60))
# Right streak card warm glow
amb_draw.ellipse((920, 200, 1440, 700), fill=(255, 140, 0, 45))
# Bottom 4 neon blooms
amb_draw.ellipse((30, 700, 380, 960), fill=(255, 140, 0, 70))     # Amber
amb_draw.ellipse((380, 700, 740, 960), fill=(220, 30, 180, 70))   # Pink
amb_draw.ellipse((740, 700, 1090, 960), fill=(0, 240, 160, 70))   # Cyan
amb_draw.ellipse((1090, 700, 1450, 960), fill=(255, 50, 80, 70))  # Crimson

ambient = ambient.filter(ImageFilter.GaussianBlur(110))
img = Image.alpha_composite(base, ambient)

# Starry / Stardust particle effect
random.seed(42)
stars = Image.new('RGBA', (width, height), (0, 0, 0, 0))
st_draw = ImageDraw.Draw(stars)
for _ in range(160):
    sx = random.randint(30, width - 30)
    sy = random.randint(30, height - 30)
    sr = random.choice([1, 1, 2])
    alpha = random.randint(60, 220)
    col = random.choice([(255, 255, 255, alpha), (255, 210, 140, alpha), (160, 210, 255, alpha)])
    st_draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=col)

img = Image.alpha_composite(img, stars)

# 2. Main Outer Card Frame
outer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
outer_draw = ImageDraw.Draw(outer)
outer_box = [(25, 25), (width - 25, height - 25)]
outer_draw.rounded_rectangle(outer_box, radius=32, fill=(13, 15, 20, 220), outline=(255, 255, 255, 35), width=2)
img = Image.alpha_composite(img, outer)

# 3. Neon Glow Layer
glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

def add_neon_box(box, color, radius=24):
    glow_draw.rounded_rectangle(box, radius=radius, outline=color, width=4)

# Avatar Halo
av_center = (200, 240)
av_r = 135
glow_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 170, 0, 255), width=8)
glow_draw.ellipse((av_center[0] - av_r - 4, av_center[1] - av_r - 4, av_center[0] + av_r + 4, av_center[1] + av_r + 4), outline=(255, 120, 0, 180), width=6)

# VIP Plaque
glow_draw.rounded_rectangle([(650, 65), (860, 155)], radius=18, outline=(255, 180, 20, 220), width=3)

# Purple Rank Banner
glow_draw.rounded_rectangle([(360, 205), (880, 285)], radius=18, outline=(170, 70, 255, 240), width=4)

# Bottom 4 Neon Bento Cards
add_neon_box([(40, 725), (375, 945)], (255, 150, 0, 240))
add_neon_box([(395, 725), (730, 945)], (230, 40, 190, 240))
add_neon_box([(750, 725), (1085, 945)], (0, 240, 170, 240))
add_neon_box([(1105, 725), (1440, 945)], (255, 60, 90, 240))

blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, blurred_glow)

# 4. Crisp Foreground Layer
fg_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
fg_draw = ImageDraw.Draw(fg_layer)

# Avatar inner ring
fg_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 220, 120, 255), width=3)
fg_draw.ellipse((av_center[0] - (av_r-8), av_center[1] - (av_r-8), av_center[0] + (av_r-8), av_center[1] + (av_r-8)), fill=(18, 20, 26, 255))

# Crown badge beneath avatar
fg_draw.regular_polygon((200, 370, 26), 6, fill=(24, 20, 10, 255), outline=(255, 180, 30, 255))

# Top Right Server Card
fg_draw.rounded_rectangle([(920, 50), (1440, 180)], radius=24, fill=(16, 20, 28, 210), outline=(50, 80, 130, 180), width=2)

# Top Right Streak & Level Card
fg_draw.rounded_rectangle([(920, 205), (1440, 705)], radius=24, fill=(16, 18, 24, 210), outline=(255, 170, 0, 90), width=2)

# VIP Plaque
fg_draw.rounded_rectangle([(650, 65), (860, 155)], radius=18, fill=(25, 22, 12, 230), outline=(255, 210, 80, 255), width=2)

# Rank Banner
fg_draw.rounded_rectangle([(360, 205), (880, 285)], radius=18, fill=(35, 15, 60, 240), outline=(200, 100, 255, 255), width=2)

# 4 Mid Row Tiles (Roomy & Perfectly Symmetrical!)
# Row A:
fg_draw.rounded_rectangle([(40, 505), (445, 585)], radius=16, fill=(16, 18, 24, 210), outline=(255, 255, 255, 30), width=1) # Rank
fg_draw.rounded_rectangle([(475, 505), (880, 585)], radius=16, fill=(16, 18, 24, 210), outline=(255, 255, 255, 30), width=1) # Coins
# Row B:
fg_draw.rounded_rectangle([(40, 605), (445, 685)], radius=16, fill=(16, 18, 24, 210), outline=(255, 255, 255, 30), width=1) # Joined
fg_draw.rounded_rectangle([(475, 605), (880, 685)], radius=16, fill=(16, 18, 24, 210), outline=(255, 255, 255, 30), width=1) # Reactions

# Bottom 4 Bento Cards
fg_draw.rounded_rectangle([(40, 725), (375, 945)], radius=24, fill=(18, 16, 14, 220), outline=(255, 180, 40, 255), width=2)
fg_draw.rounded_rectangle([(395, 725), (730, 945)], radius=24, fill=(22, 14, 24, 220), outline=(240, 60, 200, 255), width=2)
fg_draw.rounded_rectangle([(750, 725), (1085, 945)], radius=24, fill=(14, 22, 20, 220), outline=(0, 245, 180, 255), width=2)
fg_draw.rounded_rectangle([(1105, 725), (1440, 945)], radius=24, fill=(24, 14, 16, 220), outline=(255, 80, 110, 255), width=2)

# Decorative charts
# Wave
wave_pts = [(160, 915), (200, 905), (230, 920), (260, 885), (290, 890), (320, 840), (350, 810), (370, 785)]
for i in range(len(wave_pts)-1):
    fg_draw.line([wave_pts[i], wave_pts[i+1]], fill=(255, 170, 0, 180), width=3)
    fg_draw.ellipse((wave_pts[i][0]-3, wave_pts[i][1]-3, wave_pts[i][0]+3, wave_pts[i][1]+3), fill=(255, 220, 100, 230))

# Bars
bar_xs = [610, 635, 660, 685, 710]
bar_hs = [35, 60, 85, 110, 135]
for bx, bh in zip(bar_xs, bar_hs):
    fg_draw.rounded_rectangle([(bx, 930 - bh), (bx + 16, 930)], radius=4, fill=(230, 40, 190, 150), outline=(255, 120, 220, 220), width=1)

# Equalizer
eq_xs = [940, 960, 980, 1000, 1020, 1040, 1060]
eq_hs = [50, 85, 40, 120, 75, 110, 65]
for ex, eh in zip(eq_xs, eq_hs):
    fg_draw.rounded_rectangle([(ex, 930 - eh), (ex + 12, 930)], radius=3, fill=(0, 240, 170, 150), outline=(100, 255, 210, 220), width=1)

# Glowing smile circle
fg_draw.ellipse([(1345, 825), (1420, 900)], fill=(255, 80, 40, 160), outline=(255, 180, 80, 230), width=2)
fg_draw.arc([(1360, 845), (1405, 885)], start=30, end=150, fill=(20, 10, 12, 255), width=4)
fg_draw.ellipse([(1365, 848), (1375, 858)], fill=(20, 10, 12, 255))
fg_draw.ellipse([(1390, 848), (1400, 858)], fill=(20, 10, 12, 255))

img = Image.alpha_composite(img, fg_layer)

# Now render clean, perfectly measured text without any overflowing!
draw = ImageDraw.Draw(img, "RGBA")

font_name = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 60)
font_huge_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 68)
font_streak_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 74)
font_banner = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
font_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
font_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)
font_body = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 19)
font_body_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19)
font_badge = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 17)

def paste_icon(path, x, y, size=32):
    if os.path.exists(path):
        ic = Image.open(path).convert("RGBA").resize((size, size))
        img.paste(ic, (x, y), ic)

# Avatar
av_r = 126
draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), fill=(80, 140, 230, 255))
paste_icon("assets/icons/crown.png", 184, 354, 32)

# Username & VIP
draw.text((360, 80), "`BuzzZ", fill=(255, 255, 255), font=font_name)
paste_icon("assets/icons/crown.png", 670, 88, 38)
draw.text((725, 84), "VIP", fill=(255, 215, 60), font=font_h2)
draw.text((725, 114), "MEMBER", fill=(255, 220, 120), font=font_h3)

# Purple Rank Banner
paste_icon("assets/icons/trophy.png", 390, 222, 42)
draw.text((455, 225), "GOON LEGEND", fill=(255, 255, 255), font=font_banner)
draw.polygon([(840, 235), (855, 245), (840, 255)], fill=(220, 160, 255, 240))

# Badges (Configurable / Clean)
badges = [
    ("Booster", (180, 70, 255, 50), (200, 100, 255)),
    ("VIP", (255, 190, 20, 50), (255, 200, 40)),
    ("Age Verified", (0, 220, 120, 40), (0, 240, 140)),
    ("Content Creator", (255, 50, 60, 40), (255, 80, 90)),
    ("Staff", (60, 120, 255, 50), (100, 160, 255)),
    ("OG", (255, 120, 30, 50), (255, 140, 40)),
]
cur_x = 360
for b_label, bg_col, border_col in badges:
    tb = draw.textbbox((0, 0), b_label, font=font_badge)
    bw = (tb[2] - tb[0]) + 22
    if cur_x + bw > 880:
        break
    draw.rounded_rectangle([(cur_x, 325), (cur_x + bw, 360)], radius=12, fill=bg_col, outline=border_col, width=1)
    draw.text((cur_x + 11, 332), b_label, fill=(255, 255, 255), font=font_badge)
    cur_x += bw + 8

# Server Info (Top Right)
draw.rounded_rectangle([(945, 75), (1025, 155)], radius=18, fill=(30, 50, 80, 255), outline=(0, 180, 255, 180), width=2)
paste_icon("assets/icons/media.png", 965, 95, 40)
draw.text((1045, 82), "Adult House", fill=(255, 255, 255), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36))
draw.text((1045, 130), "DISCORD SERVER", fill=(140, 170, 210), font=font_h3)

# Streak & Level
paste_icon("assets/icons/fire.png", 950, 230, 34)
draw.text((995, 236), "CURRENT STREAK", fill=(255, 180, 80), font=font_h3)
draw.text((950, 275), "1", fill=(255, 140, 50), font=font_streak_num)
draw.text((1000, 302), "Day Active", fill=(255, 255, 255), font=font_h2)
draw.text((950, 375), "Longest Streak: 1 Days", fill=(160, 175, 195), font=font_body)

# Level & XP
draw.text((950, 420), "LEVEL 2", fill=(255, 220, 100), font=font_h2)
draw.text((1110, 424), "30 / 200 XP", fill=(180, 195, 215), font=font_body)
draw.text((1355, 420), "15%", fill=(255, 220, 100), font=font_h2)

# Candy Progress Bar
draw.rounded_rectangle([(950, 465), (1400, 493)], radius=14, fill=(35, 38, 48, 255), outline=(255, 255, 255, 20), width=1)
fill_w = int(450 * 0.15)
bar_fill = Image.new('RGBA', (fill_w, 28), (0, 0, 0, 0))
bf_draw = ImageDraw.Draw(bar_fill)
bf_draw.rounded_rectangle([(0, 0), (fill_w, 28)], radius=14, fill=(255, 170, 20, 240))
for sx in range(-20, fill_w + 30, 16):
    bf_draw.line([(sx, 0), (sx + 14, 28)], fill=(255, 220, 90, 180), width=5)
img.paste(bar_fill, (950, 465), bar_fill)

draw.text((950, 515), "Total Server XP: 130", fill=(160, 175, 195), font=font_body)
draw.line([(950, 555), (1400, 555)], fill=(255, 255, 255, 40), width=1)

# Boost & Activity
paste_icon("assets/icons/boost.png", 950, 580, 36)
draw.text((1000, 580), "BOOST STATUS", fill=(210, 100, 255), font=font_h3)
draw.text((1000, 608), "Server Booster • 8 Months", fill=(220, 225, 235), font=font_body)

paste_icon("assets/icons/chat.png", 950, 645, 34)
draw.text((1000, 645), "FAVORITE CHANNEL", fill=(140, 180, 255), font=font_h3)
draw.text((1000, 672), "#general-chat • 428 messages", fill=(220, 225, 235), font=font_body)

# 4 ROOMY MID TILES (Clean, unclipped, plenty of room!)
# Tile 1: Server Rank
paste_icon("assets/icons/trophy.png", 55, 522, 38)
draw.text((108, 518), "SERVER RANK", fill=(255, 200, 50), font=font_h3)
draw.text((108, 548), "#142 / 38,000 Members", fill=(255, 255, 255), font=font_body_bold)

# Tile 2: Goon Coins
paste_icon("assets/icons/coin.png", 490, 522, 38)
draw.text((545, 518), "GOON COINS", fill=(255, 200, 50), font=font_h3)
draw.text((545, 548), "2,450 Coins", fill=(255, 255, 255), font=font_body_bold)

# Tile 3: Member Since
paste_icon("assets/icons/calendar.png", 55, 622, 38)
draw.text((108, 618), "MEMBER SINCE", fill=(180, 140, 255), font=font_h3)
draw.text((108, 648), "Joined • Jan 14, 2025", fill=(255, 255, 255), font=font_body_bold)

# Tile 4: Reactions
paste_icon("assets/icons/heart.png", 490, 622, 38)
draw.text((545, 618), "REACTIONS", fill=(255, 80, 110), font=font_h3)
draw.text((545, 648), "1,248 Given  •  864 Recv", fill=(255, 255, 255), font=font_body_bold)

# 4 Bottom Cards
# Card 1: Messages
paste_icon("assets/icons/chat.png", 65, 750, 36)
draw.text((112, 755), "MESSAGES", fill=(255, 190, 60), font=font_h3)
draw.text((65, 810), "3", fill=(255, 255, 255), font=font_huge_num)
draw.text((65, 905), "0 words typed", fill=(170, 185, 205), font=font_body)

# Card 2: Media
paste_icon("assets/icons/media.png", 420, 750, 36)
draw.text((467, 755), "MEDIA SHARED", fill=(255, 100, 220), font=font_h3)
draw.text((420, 810), "4", fill=(255, 255, 255), font=font_huge_num)
draw.text((420, 905), "Photos, clips & files", fill=(170, 185, 205), font=font_body)

# Card 3: Voice
paste_icon("assets/icons/voice.png", 775, 750, 36)
draw.text((822, 755), "VOICE TIME", fill=(0, 240, 180), font=font_h3)
draw.text((775, 810), "0 mins", fill=(255, 255, 255), font=font_huge_num)
draw.text((775, 905), "0 total minutes", fill=(170, 185, 205), font=font_body)

# Card 4: Reactions Given
paste_icon("assets/icons/heart.png", 1130, 750, 36)
draw.text((1177, 755), "REACTIONS", fill=(255, 90, 120), font=font_h3)
draw.text((1130, 810), "1,248", fill=(255, 255, 255), font=font_huge_num)
draw.text((1130, 905), "Given", fill=(170, 185, 205), font=font_body)

img.convert("RGB").save("scratch/neon_mockup_v2.png")
print("Saved scratch/neon_mockup_v2.png successfully!")
