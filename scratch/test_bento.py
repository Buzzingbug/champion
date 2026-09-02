import os
from PIL import Image, ImageDraw, ImageFont

def get_level_data(xp):
    level = 1
    while True:
        req = int(50 * level * (level + 1))
        if xp < req:
            prev_req = int(50 * (level - 1) * level) if level > 1 else 0
            current_level_xp = xp - prev_req
            xp_to_next = req - prev_req
            pct = min(max(current_level_xp / xp_to_next, 0.0), 1.0)
            return level, current_level_xp, xp_to_next, pct
        level += 1
        if level >= 100:
            return 100, 1, 1, 1.0

width, height = 1200, 800

# 1. Base clean background
img = Image.open("assets/bento_bg.png").convert("RGBA")

# 2. Fonts
font_huge = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 85)
font_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 52)
font_stat_val = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 64)
font_subtitle = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
font_stat_lbl = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 22)
font_small = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 22)
font_pill = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)

# Sample data
messages = 142
media = 18
words = 2150
voice = 85
current_streak = 5
longest_streak = 12
name = "Buzz"

total_xp = (messages * 10) + (media * 25) + (voice * 5)
level, cur_xp, next_xp, pct = get_level_data(total_xp)

# Persona
if voice > (messages * 2) and voice > 10:
    persona = "BROADCASTER"
elif media > (messages * 0.2) and media > 15:
    persona = "MEDIA MOGUL"
elif messages > 100 and words > (messages * 15):
    persona = "NOVELIST"
elif messages > 50:
    persona = "ACTIVE REGULAR"
else:
    persona = "NEWCOMER"

# 3. Create glass layer
glass_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glass_draw = ImageDraw.Draw(glass_layer)

def draw_glass_box(box):
    glass_draw.rounded_rectangle(box, radius=28, fill=(255, 255, 255, 14), outline=(255, 255, 255, 45), width=2)

# Grid definitions:
# Top row (y: 40 to 385)
draw_glass_box([40, 40, 780, 385])     # Box 1: User Profile & XP
draw_glass_box([800, 40, 1160, 385])   # Box 2: Streak

# Bottom row (y: 415 to 760)
draw_glass_box([40, 415, 400, 760])    # Box 3: Messages
draw_glass_box([420, 415, 780, 760])   # Box 4: Media
draw_glass_box([800, 415, 1160, 760])  # Box 5: Voice

# Composite glass layer
img = Image.alpha_composite(img, glass_layer)
draw = ImageDraw.Draw(img, "RGBA")

# Helper to paste icon
def paste_icon(path, x, y, size=32):
    if os.path.exists(path):
        ic = Image.open(path).convert("RGBA").resize((size, size))
        img.paste(ic, (x, y), ic)

# --- Box 1: Profile & Leveling ---
# Sample avatar circle placeholder
draw.ellipse([(70, 75), (250, 255)], fill=(100, 150, 240, 255), outline=(255, 255, 255, 100), width=3)

# Name
draw.text((280, 75), name, fill=(255, 255, 255), font=font_title)

# Persona Pill Badge
badge_text = persona.upper()
tb = draw.textbbox((0, 0), badge_text, font=font_pill)
bw = (tb[2] - tb[0]) + 24
badge_h = 32
draw.rounded_rectangle([(280, 144), (280 + bw, 144 + badge_h)], radius=8, fill=(35, 33, 22, 255), outline=(251, 236, 144, 180), width=1)
draw.text((292, 150), badge_text, fill=(251, 236, 144), font=font_pill)

# Level & XP text
draw.text((280, 205), f"LEVEL {level}", fill=(255, 255, 255), font=font_subtitle)
xp_str = f"{cur_xp:,} / {next_xp:,} XP"
draw.text((410, 208), xp_str, fill=(180, 195, 215), font=font_small)

pct_str = f"{int(pct * 100)}%"
tb_pct = draw.textbbox((0, 0), pct_str, font=font_subtitle)
draw.text((740 - (tb_pct[2] - tb_pct[0]), 205), pct_str, fill=(251, 236, 144), font=font_subtitle)

# Progress Bar
bar_x0, bar_y0, bar_x1, bar_y1 = 280, 250, 740, 272
draw.rounded_rectangle([(bar_x0, bar_y0), (bar_x1, bar_y1)], radius=11, fill=(255, 255, 255, 25))
fill_w = int((bar_x1 - bar_x0) * pct)
if fill_w > 12:
    draw.rounded_rectangle([(bar_x0, bar_y0), (bar_x0 + fill_w, bar_y1)], radius=11, fill=(251, 236, 144, 220))

# Total XP footer
draw.text((280, 315), f"Total Server XP: {total_xp:,}", fill=(160, 175, 195), font=font_small)


# --- Box 2: Streak ---
paste_icon("assets/icons/fire.png", 835, 75, 34)
draw.text((880, 80), "CURRENT STREAK", fill=(200, 210, 220), font=font_stat_lbl)

# Large streak number
sv = f"{current_streak}"
draw.text((835, 140), sv, fill=(255, 120, 80) if current_streak > 0 else (255, 255, 255), font=font_huge)
tb_s = draw.textbbox((0, 0), sv, font=font_huge)
nw = tb_s[2] - tb_s[0]
label_streak = "Day Active" if current_streak == 1 else "Days Active"
draw.text((835 + nw + 16, 185), label_streak, fill=(220, 220, 220), font=font_subtitle)

draw.text((835, 315), f"Longest Streak: {longest_streak} Days", fill=(160, 175, 195), font=font_small)


# --- Box 3: Messages ---
paste_icon("assets/icons/chat.png", 75, 450, 34)
draw.text((120, 455), "MESSAGES", fill=(200, 210, 220), font=font_stat_lbl)
draw.text((75, 520), f"{messages:,}", fill=(255, 255, 255), font=font_stat_val)
draw.text((75, 680), f"{words:,} words typed", fill=(160, 175, 195), font=font_small)


# --- Box 4: Media Shared ---
paste_icon("assets/icons/media.png", 455, 450, 34)
draw.text((500, 455), "MEDIA SHARED", fill=(200, 210, 220), font=font_stat_lbl)
draw.text((455, 520), f"{media:,}", fill=(255, 255, 255), font=font_stat_val)
draw.text((455, 680), "Photos, clips & files", fill=(160, 175, 195), font=font_small)


# --- Box 5: Voice Time ---
paste_icon("assets/icons/voice.png", 835, 450, 34)
draw.text((880, 455), "VOICE TIME", fill=(200, 210, 220), font=font_stat_lbl)
if voice >= 60:
    v_str = f"{voice // 60}h {voice % 60}m"
else:
    v_str = f"{voice} mins"
draw.text((835, 520), v_str, fill=(255, 255, 255), font=font_stat_val)
draw.text((835, 680), f"{voice:,} total minutes", fill=(160, 175, 195), font=font_small)

os.makedirs("scratch", exist_ok=True)
img.convert("RGB").save("scratch/preview_bento.png")
print("Saved scratch/preview_bento.png")
