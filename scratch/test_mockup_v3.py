from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
import random
import math

os.makedirs("scratch", exist_ok=True)
os.makedirs("assets/icons", exist_ok=True)

width = 1500
height = 1000

# 1. Base Rich Luminous Gradient (Not dull black!)
# Create top-to-bottom and left-to-right color wash
base = Image.new('RGBA', (width, height), (16, 17, 24, 255))
ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
amb_draw = ImageDraw.Draw(ambient)

# Rich Amber/Gold flood on the left (matches mockup's left side warmth)
amb_draw.ellipse((-80, -60, 520, 520), fill=(255, 155, 10, 150))
amb_draw.ellipse((-40, 20, 420, 480), fill=(255, 190, 40, 110))

# Rich Deep Purple in center-top
amb_draw.ellipse((340, 100, 920, 420), fill=(170, 45, 255, 80))

# Deep Blue/Cyan on top right
amb_draw.ellipse((880, -20, 1520, 320), fill=(0, 140, 255, 75))

# Warm Amber under the right streak card
amb_draw.ellipse((900, 220, 1460, 680), fill=(255, 140, 0, 55))

# Bottom Neon Glow Floods (Much richer and brighter)
amb_draw.ellipse((20, 680, 390, 980), fill=(255, 150, 0, 95))      # Card 1: Warm Gold
amb_draw.ellipse((380, 680, 740, 980), fill=(235, 30, 190, 95))    # Card 2: Magenta Pink
amb_draw.ellipse((730, 680, 1100, 980), fill=(0, 245, 170, 95))    # Card 3: Cyan Green
amb_draw.ellipse((1090, 680, 1460, 980), fill=(255, 55, 85, 95))   # Card 4: Crimson Red

# Heavy blur for smooth seamless atmospheric lighting
ambient = ambient.filter(ImageFilter.GaussianBlur(100))
img = Image.alpha_composite(base, ambient)

# Starry / Stardust particle effect
random.seed(1337)
stars = Image.new('RGBA', (width, height), (0, 0, 0, 0))
st_draw = ImageDraw.Draw(stars)
for _ in range(180):
    sx = random.randint(25, width - 25)
    sy = random.randint(25, height - 25)
    sr = random.choice([1, 1, 1, 2])
    alpha = random.randint(80, 240)
    col = random.choice([(255, 255, 255, alpha), (255, 220, 160, alpha), (180, 220, 255, alpha), (255, 170, 220, alpha)])
    st_draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=col)

img = Image.alpha_composite(img, stars)

# 2. Main Outer Card Frame with Subtle Glass Tint
outer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
outer_draw = ImageDraw.Draw(outer)
outer_box = [(25, 25), (width - 25, height - 25)]
# Glass fill with slight top highlight
outer_draw.rounded_rectangle(outer_box, radius=32, fill=(15, 16, 22, 210), outline=(255, 255, 255, 45), width=2)
img = Image.alpha_composite(img, outer)

# 3. Neon Bloom Pass
glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

def add_neon_glow(box, color, radius=24, width=5):
    glow_draw.rounded_rectangle(box, radius=radius, outline=color, width=width)

# Avatar Halo Glow
av_center = (200, 240)
av_r = 135
glow_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 170, 0, 255), width=10)
glow_draw.ellipse((av_center[0] - av_r - 6, av_center[1] - av_r - 6, av_center[0] + av_r + 6, av_center[1] + av_r + 6), outline=(255, 120, 0, 200), width=8)

# VIP Plaque Glow
glow_draw.rounded_rectangle([(650, 65), (860, 155)], radius=18, outline=(255, 190, 30, 230), width=4)

# Purple Rank Banner Glow
glow_draw.rounded_rectangle([(360, 205), (880, 285)], radius=18, outline=(180, 75, 255, 255), width=5)

# Bottom 4 Neon Bento Cards Glow
add_neon_glow([(40, 725), (375, 945)], (255, 155, 0, 255), radius=24, width=5)
add_neon_glow([(395, 725), (730, 945)], (235, 45, 195, 255), radius=24, width=5)
add_neon_glow([(750, 725), (1085, 945)], (0, 245, 175, 255), radius=24, width=5)
add_neon_glow([(1105, 725), (1440, 945)], (255, 65, 95, 255), radius=24, width=5)

blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(15))
img = Image.alpha_composite(img, blurred_glow)

# 4. Crisp Foreground Glass Layer & Illustrations
fg_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
fg_draw = ImageDraw.Draw(fg_layer)

# Helper for glossy glass tiles
def draw_glossy_tile(box, radius, fill_col, border_col, border_width=1):
    fg_draw.rounded_rectangle(box, radius=radius, fill=fill_col, outline=border_col, width=border_width)

# Avatar rings
fg_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 230, 130, 255), width=3)
fg_draw.ellipse((av_center[0] - (av_r-8), av_center[1] - (av_r-8), av_center[0] + (av_r-8), av_center[1] + (av_r-8)), fill=(18, 20, 26, 255))
# Crown badge beneath avatar
fg_draw.regular_polygon((200, 370, 26), 6, fill=(26, 22, 12, 255), outline=(255, 190, 30, 255))

# Top Right Server Card
draw_glossy_tile([(920, 50), (1440, 180)], 24, (16, 20, 30, 220), (60, 90, 140, 190), 2)

# Top Right Streak & Level Card
draw_glossy_tile([(920, 205), (1440, 705)], 24, (18, 19, 26, 220), (255, 170, 0, 100), 2)

# VIP Plaque
draw_glossy_tile([(650, 65), (860, 155)], 18, (28, 24, 14, 240), (255, 215, 80, 255), 2)

# Rank Banner
draw_glossy_tile([(360, 205), (880, 285)], 18, (38, 16, 66, 245), (210, 110, 255, 255), 2)

# 4 Mid Row Tiles (Roomy 400px tiles!)
draw_glossy_tile([(40, 505), (445, 585)], 16, (18, 20, 27, 215), (255, 255, 255, 35))
draw_glossy_tile([(475, 505), (880, 585)], 16, (18, 20, 27, 215), (255, 255, 255, 35))
draw_glossy_tile([(40, 605), (445, 685)], 16, (18, 20, 27, 215), (255, 255, 255, 35))
draw_glossy_tile([(475, 605), (880, 685)], 16, (18, 20, 27, 215), (255, 255, 255, 35))

# Bottom 4 Bento Cards (Glossy glass fill + intense neon borders)
draw_glossy_tile([(40, 725), (375, 945)], 24, (20, 17, 14, 225), (255, 185, 45, 255), 2)
draw_glossy_tile([(395, 725), (730, 945)], 24, (24, 15, 26, 225), (245, 65, 205, 255), 2)
draw_glossy_tile([(750, 725), (1085, 945)], 24, (14, 24, 22, 225), (0, 250, 185, 255), 2)
draw_glossy_tile([(1105, 725), (1440, 945)], 24, (26, 14, 18, 225), (255, 85, 115, 255), 2)

# --- 5. THEMED ILLUSTRATIONS INSIDE BOTTOM CARDS (No boring graphs!) ---

# A. Card 1 (Messages): Glowing Chat Bubbles Cluster
# Large chat bubble
fg_draw.rounded_rectangle([(270, 795), (355, 855)], radius=14, fill=(255, 180, 30, 45), outline=(255, 190, 40, 220), width=2)
fg_draw.polygon([(285, 855), (275, 875), (305, 855)], fill=(255, 190, 40, 220))
# Inner message lines
fg_draw.line([(285, 815), (340, 815)], fill=(255, 220, 120, 200), width=3)
fg_draw.line([(285, 830), (325, 830)], fill=(255, 220, 120, 200), width=3)
# Small overlapping secondary bubble
fg_draw.rounded_rectangle([(225, 860), (290, 910)], radius=10, fill=(255, 150, 20, 40), outline=(255, 170, 30, 180), width=2)
fg_draw.polygon([(270, 910), (280, 925), (285, 910)], fill=(255, 170, 30, 180))
fg_draw.line([(238, 882), (277, 882)], fill=(255, 200, 100, 180), width=2)

# B. Card 2 (Media Shared): Glowing Overlapping Photo/Polaroid Frames
# Back frame (tilted slightly)
fg_draw.rounded_rectangle([(615, 785), (690, 865)], radius=8, fill=(230, 45, 190, 35), outline=(240, 80, 210, 180), width=2)
# Front frame
fg_draw.rounded_rectangle([(640, 825), (715, 915)], radius=8, fill=(240, 55, 205, 55), outline=(255, 110, 225, 240), width=2)
# Photo picture area inside front frame
fg_draw.rectangle([(648, 833), (707, 885)], fill=(30, 12, 35, 255))
# Mountain & sun inside photo
fg_draw.ellipse([(655, 840), (665, 850)], fill=(255, 180, 230, 255))
fg_draw.polygon([(652, 880), (672, 855), (688, 880)], fill=(230, 60, 195, 240))
fg_draw.polygon([(675, 880), (692, 862), (704, 880)], fill=(200, 40, 170, 240))

# C. Card 3 (Voice Time): Streaming Live Radio Audio Waves / Sound Broadcast
# Center mic/speaker transmitter icon
vx, vy = 1010, 855
fg_draw.ellipse([(vx - 14, vy - 14), (vx + 14, vy + 14)], fill=(0, 245, 175, 240))
fg_draw.ellipse([(vx - 6, vy - 6), (vx + 6, vy + 6)], fill=(12, 28, 24, 255))
# Expanding glowing sound broadcast rings
fg_draw.arc([(vx - 32, vy - 32), (vx + 32, vy + 32)], start=-70, end=70, fill=(0, 245, 175, 220), width=3)
fg_draw.arc([(vx - 32, vy - 32), (vx + 32, vy + 32)], start=110, end=250, fill=(0, 245, 175, 220), width=3)
fg_draw.arc([(vx - 50, vy - 50), (vx + 50, vy + 50)], start=-60, end=60, fill=(0, 245, 175, 160), width=3)
fg_draw.arc([(vx - 50, vy - 50), (vx + 50, vy + 50)], start=120, end=240, fill=(0, 245, 175, 160), width=3)
fg_draw.arc([(vx - 68, vy - 68), (vx + 68, vy + 68)], start=-50, end=50, fill=(0, 245, 175, 90), width=2)
fg_draw.arc([(vx - 68, vy - 68), (vx + 68, vy + 68)], start=130, end=230, fill=(0, 245, 175, 90), width=2)

# D. Card 4 (Reactions): 3D Style Smiling Heart Emoji with Sparkles
ex, ey = 1380, 860
fg_draw.ellipse([(ex - 42, ey - 42), (ex + 42, ey + 42)], fill=(255, 75, 55, 230), outline=(255, 190, 120, 255), width=3)
# Eyes (smiling closed curves)
fg_draw.arc([(ex - 24, ey - 16), (ex - 8, ey)], start=180, end=0, fill=(35, 10, 15, 255), width=4)
fg_draw.arc([(ex + 8, ey - 16), (ex + 24, ey)], start=180, end=0, fill=(35, 10, 15, 255), width=4)
# Big glowing open smile
fg_draw.chord([(ex - 22, ey - 4), (ex + 22, ey + 24)], start=0, end=180, fill=(40, 12, 18, 255))
fg_draw.chord([(ex - 12, ey + 10), (ex + 12, ey + 24)], start=0, end=180, fill=(255, 120, 130, 255)) # Tongue
# Sparkles around emoji
fg_draw.line([(ex + 48, ey - 25), (ex + 48, ey - 15)], fill=(255, 220, 140, 255), width=2)
fg_draw.line([(ex + 43, ey - 20), (ex + 53, ey - 20)], fill=(255, 220, 140, 255), width=2)
fg_draw.line([(ex - 48, ey + 20), (ex - 48, ey + 30)], fill=(255, 220, 140, 255), width=2)
fg_draw.line([(ex - 53, ey + 25), (ex - 43, ey + 25)], fill=(255, 220, 140, 255), width=2)

img = Image.alpha_composite(img, fg_layer)

# 5. Render Clean Typography Layer
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

# Username & VIP Plaque
draw.text((360, 80), "`BuzzZ", fill=(255, 255, 255), font=font_name)
paste_icon("assets/icons/crown.png", 670, 88, 38)
draw.text((725, 84), "VIP", fill=(255, 215, 60), font=font_h2)
draw.text((725, 114), "MEMBER", fill=(255, 220, 120), font=font_h3)

# Purple Rank Banner
paste_icon("assets/icons/trophy.png", 390, 222, 42)
draw.text((455, 225), "GOON LEGEND", fill=(255, 255, 255), font=font_banner)
draw.polygon([(840, 235), (855, 245), (840, 255)], fill=(220, 160, 255, 240))

# Badges Row (Clean and contained)
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

# --- 4 MID TILES (Non-duplicate, useful data!) ---
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

# Tile 4: PRIME TIME / PEAK ACTIVE WINDOW (Replaced duplicate reactions!)
paste_icon("assets/icons/crown.png", 490, 622, 38)
draw.text((545, 618), "PRIME TIME", fill=(0, 220, 255), font=font_h3)
draw.text((545, 648), "Night Owl  •  11 PM - 3 AM", fill=(255, 255, 255), font=font_body_bold)

# --- 4 BOTTOM CARDS (Clean numbers & labels, illustrations are in background) ---
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

# Card 4: Reactions (Single home for full reaction stats!)
paste_icon("assets/icons/heart.png", 1130, 750, 36)
draw.text((1177, 755), "REACTIONS", fill=(255, 90, 120), font=font_h3)
draw.text((1130, 810), "1,248", fill=(255, 255, 255), font=font_huge_num)
draw.text((1130, 905), "1,248 Given • 864 Recv", fill=(170, 185, 205), font=font_body)

img.convert("RGB").save("scratch/neon_mockup_v3.png")
print("Saved scratch/neon_mockup_v3.png successfully!")
