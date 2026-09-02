from PIL import Image, ImageDraw, ImageFilter
import os
import math

os.makedirs("assets", exist_ok=True)
os.makedirs("assets/icons", exist_ok=True)

width = 1500
height = 1000

# 1. Base dark background
base = Image.new('RGBA', (width, height), (10, 11, 15, 255))

# Subtle ambient glowing orbs in corners/center
ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
amb_draw = ImageDraw.Draw(ambient)
# Orange aura around avatar
amb_draw.ellipse((50, 80, 350, 380), fill=(255, 140, 0, 90))
# Top right subtle blue
amb_draw.ellipse((950, 20, 1450, 250), fill=(0, 120, 255, 40))
# Purple accent in middle
amb_draw.ellipse((400, 150, 850, 350), fill=(160, 40, 255, 45))
# Bottom neon accents
amb_draw.ellipse((30, 700, 380, 960), fill=(255, 140, 0, 50))     # Orange
amb_draw.ellipse((380, 700, 740, 960), fill=(220, 30, 180, 50))   # Pink
amb_draw.ellipse((740, 700, 1090, 960), fill=(0, 240, 160, 50))   # Green
amb_draw.ellipse((1090, 700, 1450, 960), fill=(255, 50, 80, 50))  # Red

ambient = ambient.filter(ImageFilter.GaussianBlur(110))
img = Image.alpha_composite(base, ambient)

# 2. Main Outer Card Frame
outer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
outer_draw = ImageDraw.Draw(outer)
outer_box = [(25, 25), (width - 25, height - 25)]
outer_draw.rounded_rectangle(outer_box, radius=32, fill=(13, 14, 18, 230), outline=(255, 255, 255, 30), width=2)

img = Image.alpha_composite(img, outer)

# 3. Pre-render Neon Glow Borders Layer
glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

def add_neon_box(box, color, radius=24, blur_radius=12):
    # Draw intense glowing line for blur
    glow_draw.rounded_rectangle(box, radius=radius, outline=color, width=4)

# A. Avatar Glowing Ring (Double pass for intense glow)
av_center = (200, 240)
av_r = 135
glow_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 170, 0, 255), width=8)
glow_draw.ellipse((av_center[0] - av_r - 4, av_center[1] - av_r - 4, av_center[0] + av_r + 4, av_center[1] + av_r + 4), outline=(255, 120, 0, 180), width=6)

# B. VIP Member Plaque (Top Center)
glow_draw.rounded_rectangle([(650, 65), (860, 155)], radius=18, outline=(255, 180, 20, 220), width=3)

# C. Rank Banner (Purple Neon)
glow_draw.rounded_rectangle([(360, 205), (860, 285)], radius=18, outline=(170, 70, 255, 240), width=4)

# D. Bottom 4 Neon Bento Cards
# Card 1: Orange/Gold
add_neon_box([(40, 725), (375, 945)], (255, 150, 0, 240))
# Card 2: Violet/Pink
add_neon_box([(395, 725), (730, 945)], (230, 40, 190, 240))
# Card 3: Green/Cyan
add_neon_box([(750, 725), (1085, 945)], (0, 240, 170, 240))
# Card 4: Crimson/Red
add_neon_box([(1105, 725), (1440, 945)], (255, 60, 90, 240))

# Blur the glow layer for the neon bloom effect
blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, blurred_glow)

# 4. Crisp Foreground Glass Panes Layer
fg_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
fg_draw = ImageDraw.Draw(fg_layer)

# Re-draw crisp sharp outlines over the glow
# Avatar inner ring
fg_draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), outline=(255, 220, 120, 255), width=3)
# Avatar placeholder background
fg_draw.ellipse((av_center[0] - (av_r-8), av_center[1] - (av_r-8), av_center[0] + (av_r-8), av_center[1] + (av_r-8)), fill=(18, 20, 26, 255))

# Crown badge beneath avatar
crown_box = [(175, 345), (225, 395)]
fg_draw.regular_polygon((200, 370, 26), 6, fill=(24, 20, 10, 255), outline=(255, 180, 30, 255))

# Top Right Server Card
fg_draw.rounded_rectangle([(920, 50), (1440, 180)], radius=24, fill=(16, 20, 28, 200), outline=(50, 80, 130, 180), width=2)

# Top Right Streak & Level Card
fg_draw.rounded_rectangle([(920, 205), (1440, 705)], radius=24, fill=(16, 18, 24, 200), outline=(255, 170, 0, 80), width=2)

# VIP Plaque
fg_draw.rounded_rectangle([(650, 65), (860, 155)], radius=18, fill=(25, 22, 12, 230), outline=(255, 210, 80, 255), width=2)

# Rank Banner
fg_draw.rounded_rectangle([(360, 205), (860, 285)], radius=18, fill=(35, 15, 60, 240), outline=(200, 100, 255, 255), width=2)

# Mid Row Tiles:
# Row A:
fg_draw.rounded_rectangle([(40, 505), (340, 585)], radius=16, fill=(16, 18, 24, 200), outline=(255, 255, 255, 30), width=1) # Server Rank
fg_draw.rounded_rectangle([(360, 505), (550, 585)], radius=16, fill=(16, 18, 24, 200), outline=(255, 255, 255, 30), width=1) # Coins
fg_draw.rounded_rectangle([(570, 505), (880, 585)], radius=16, fill=(28, 22, 14, 210), outline=(255, 180, 40, 150), width=1) # VIP Role Banner

# Row B:
fg_draw.rounded_rectangle([(40, 605), (380, 685)], radius=16, fill=(16, 18, 24, 200), outline=(255, 255, 255, 30), width=1) # Member Since
fg_draw.rounded_rectangle([(400, 605), (880, 685)], radius=16, fill=(16, 18, 24, 200), outline=(255, 255, 255, 30), width=1) # Reactions

# Bottom 4 Bento Cards (Crisp Borders & dark glass fill)
fg_draw.rounded_rectangle([(40, 725), (375, 945)], radius=24, fill=(18, 16, 14, 210), outline=(255, 180, 40, 255), width=2)
fg_draw.rounded_rectangle([(395, 725), (730, 945)], radius=24, fill=(22, 14, 24, 210), outline=(240, 60, 200, 255), width=2)
fg_draw.rounded_rectangle([(750, 725), (1085, 945)], radius=24, fill=(14, 22, 20, 210), outline=(0, 245, 180, 255), width=2)
fg_draw.rounded_rectangle([(1105, 725), (1440, 945)], radius=24, fill=(24, 14, 16, 210), outline=(255, 80, 110, 255), width=2)

# 5. Draw decorative glowing charts inside the bottom cards
# A. Card 1: Glowing wave/sparkline (Orange)
wave_pts = [(160, 915), (200, 905), (230, 920), (260, 885), (290, 890), (320, 840), (350, 810), (370, 785)]
for i in range(len(wave_pts)-1):
    fg_draw.line([wave_pts[i], wave_pts[i+1]], fill=(255, 170, 0, 180), width=3)
    fg_draw.ellipse((wave_pts[i][0]-3, wave_pts[i][1]-3, wave_pts[i][0]+3, wave_pts[i][1]+3), fill=(255, 220, 100, 230))

# B. Card 2: Glowing bar chart (Pink)
bar_xs = [610, 635, 660, 685, 710]
bar_hs = [35, 60, 85, 110, 135]
for bx, bh in zip(bar_xs, bar_hs):
    fg_draw.rounded_rectangle([(bx, 930 - bh), (bx + 16, 930)], radius=4, fill=(230, 40, 190, 150), outline=(255, 120, 220, 220), width=1)

# C. Card 3: Glowing audio equalizer (Cyan/Green)
eq_xs = [940, 960, 980, 1000, 1020, 1040, 1060]
eq_hs = [50, 85, 40, 120, 75, 110, 65]
for ex, eh in zip(eq_xs, eq_hs):
    fg_draw.rounded_rectangle([(ex, 930 - eh), (ex + 12, 930)], radius=3, fill=(0, 240, 170, 150), outline=(100, 255, 210, 220), width=1)

# D. Card 4: Glowing heart / emoji circle (Red/Orange)
fg_draw.ellipse([(1345, 825), (1420, 900)], fill=(255, 80, 40, 160), outline=(255, 180, 80, 230), width=2)
# Glowing smile curve
fg_draw.arc([(1360, 845), (1405, 885)], start=30, end=150, fill=(20, 10, 12, 255), width=4)
fg_draw.ellipse([(1365, 848), (1375, 858)], fill=(20, 10, 12, 255))
fg_draw.ellipse([(1390, 848), (1400, 858)], fill=(20, 10, 12, 255))

img = Image.alpha_composite(img, fg_layer)

img.save("assets/neon_profile_bg.png")
print("Saved assets/neon_profile_bg.png successfully!")
