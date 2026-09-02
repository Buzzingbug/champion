from PIL import Image, ImageDraw, ImageFont
import os
import datetime

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

# Load template background
img = Image.open("assets/neon_profile_bg.png").convert("RGBA")
draw = ImageDraw.Draw(img, "RGBA")

# Fonts
font_name = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 62)
font_huge_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 68)
font_streak_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 74)
font_banner = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
font_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
font_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)
font_body = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 19)
font_body_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19)
font_badge = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 17)
font_small = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 16)

# Sample Data matching mockup
name = "`BuzzZ"
server_name = "Adult House"
join_date = "Jan 14, 2025"
server_rank = 142
total_members = 38000
supercoins = 2450
coin_name = "GOON COINS"
messages = 3
words = 0
media = 4
voice = 0
reactions_given = 1248
reactions_rcvd = 864
current_streak = 1
longest_streak = 1
boost_months = 8

total_xp = 130
level, cur_xp, next_xp, pct = get_level_data(total_xp)

# Helper to paste icon
def paste_icon(path, x, y, size=32):
    if os.path.exists(path):
        ic = Image.open(path).convert("RGBA").resize((size, size))
        img.paste(ic, (x, y), ic)

# 1. User Avatar Placeholder in Halo
av_center = (200, 240)
av_r = 126
draw.ellipse((av_center[0] - av_r, av_center[1] - av_r, av_center[0] + av_r, av_center[1] + av_r), fill=(80, 140, 230, 255))
paste_icon("assets/icons/crown.png", 184, 354, 32)

# 2. User Name & VIP Plaque
draw.text((360, 80), name, fill=(255, 255, 255), font=font_name)

# VIP Plaque (Top Center)
paste_icon("assets/icons/crown.png", 670, 88, 38)
draw.text((725, 84), "VIP", fill=(255, 215, 60), font=font_h2)
draw.text((725, 114), "MEMBER", fill=(255, 220, 120), font=font_h3)

# Sublabel: GOON RANK
draw.text((550, 178), "— GOON RANK —", fill=(190, 160, 220), font=font_h3)

# Purple Rank Banner
paste_icon("assets/icons/trophy.png", 390, 222, 42)
draw.text((455, 225), "GOON LEGEND", fill=(255, 255, 255), font=font_banner)
# Sharp vector arrow
draw.polygon([(820, 235), (835, 245), (820, 255)], fill=(220, 160, 255, 240))

# Badges Row (y: 325) - keep within 360 to 890
badges = [
    ("Booster", (180, 70, 255, 45), (200, 100, 255)),
    ("VIP", (255, 190, 20, 45), (255, 200, 40)),
    ("Age Verified", (0, 220, 120, 40), (0, 240, 140)),
    ("Content Creator", (255, 50, 60, 40), (255, 80, 90)),
    ("Staff", (60, 120, 255, 45), (100, 160, 255)),
    ("OG", (255, 120, 30, 45), (255, 140, 40)),
]

cur_x = 360
for b_label, bg_col, border_col in badges:
    tb = draw.textbbox((0, 0), b_label, font=font_badge)
    bw = (tb[2] - tb[0]) + 22
    if cur_x + bw > 895:
        break
    draw.rounded_rectangle([(cur_x, 325), (cur_x + bw, 360)], radius=12, fill=bg_col, outline=border_col, width=1)
    draw.text((cur_x + 11, 332), b_label, fill=(255, 255, 255), font=font_badge)
    cur_x += bw + 8

# 3. Top Right Server Card
# Server Icon placeholder (or house icon)
draw.rounded_rectangle([(945, 75), (1025, 155)], radius=18, fill=(30, 50, 80, 255), outline=(0, 180, 255, 180), width=2)
paste_icon("assets/icons/media.png", 965, 95, 40) # placeholder
draw.text((1045, 82), server_name, fill=(255, 255, 255), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36))
draw.text((1045, 130), "DISCORD SERVER", fill=(140, 170, 210), font=font_h3)

# 4. Streak & Leveling Card (Upper Right)
paste_icon("assets/icons/fire.png", 950, 230, 34)
draw.text((995, 236), "CURRENT STREAK", fill=(255, 180, 80), font=font_h3)

sv = f"{current_streak}"
draw.text((950, 275), sv, fill=(255, 140, 50), font=font_streak_num)
tb_s = draw.textbbox((0, 0), sv, font=font_streak_num)
draw.text((950 + (tb_s[2] - tb_s[0]) + 16, 302), "Day Active" if current_streak == 1 else "Days Active", fill=(255, 255, 255), font=font_h2)

draw.text((950, 375), f"Longest Streak: {longest_streak} Days", fill=(160, 175, 195), font=font_body)

# Level & XP
draw.text((950, 420), f"LEVEL {level}", fill=(255, 220, 100), font=font_h2)
draw.text((1110, 424), f"{cur_xp} / {next_xp} XP", fill=(180, 195, 215), font=font_body)
draw.text((1355, 420), f"{int(pct * 100)}%", fill=(255, 220, 100), font=font_h2)

# Candy-Bar Progress Bar
bar_box = [(950, 465), (1400, 493)]
draw.rounded_rectangle(bar_box, radius=14, fill=(35, 38, 48, 255), outline=(255, 255, 255, 20), width=1)
fill_w = max(int(450 * pct), 18)
# Draw striped candy bar
bar_fill = Image.new('RGBA', (fill_w, 28), (0, 0, 0, 0))
bf_draw = ImageDraw.Draw(bar_fill)
bf_draw.rounded_rectangle([(0, 0), (fill_w, 28)], radius=14, fill=(255, 170, 20, 240))
# Add candy stripes
for sx in range(-20, fill_w + 30, 16):
    bf_draw.line([(sx, 0), (sx + 14, 28)], fill=(255, 220, 90, 180), width=5)
img.paste(bar_fill, (950, 465), bar_fill)

draw.text((950, 515), f"Total Server XP: {total_xp:,}", fill=(160, 175, 195), font=font_body)

draw.line([(950, 555), (1400, 555)], fill=(255, 255, 255, 40), width=1)

# Boost Status
paste_icon("assets/icons/boost.png", 950, 580, 36)
draw.text((1000, 580), "BOOST STATUS", fill=(210, 100, 255), font=font_h3)
draw.text((1000, 608), f"Server Booster • {boost_months} Months", fill=(220, 225, 235), font=font_body)

# Favorite Channel
paste_icon("assets/icons/chat.png", 950, 645, 34)
draw.text((1000, 645), "FAVORITE CHANNEL", fill=(140, 180, 255), font=font_h3)
draw.text((1000, 672), "#general-chat • Active Chatter", fill=(220, 225, 235), font=font_body)


# 5. Middle Stats Row
# Tile 1: Server Rank
paste_icon("assets/icons/trophy.png", 55, 522, 38)
draw.text((105, 518), "SERVER RANK", fill=(255, 200, 50), font=font_h3)
draw.text((105, 548), f"#{server_rank} / {total_members:,} Members", fill=(255, 255, 255), font=font_body_bold)

# Tile 2: Goon Coins
paste_icon("assets/icons/coin.png", 375, 522, 38)
draw.text((425, 518), coin_name, fill=(255, 200, 50), font=font_h3)
draw.text((425, 548), f"{supercoins:,} Coins", fill=(255, 255, 255), font=font_body_bold)

# Tile 3: VIP Exclusive Banner
paste_icon("assets/icons/crown.png", 585, 522, 38)
draw.text((635, 518), "VIP  •  Exclusive Access", fill=(255, 210, 60), font=font_h3)
draw.text((635, 548), f"Thank you for supporting {server_name}!", fill=(180, 195, 215), font=font_small)

# Tile 4: Member Since
paste_icon("assets/icons/calendar.png", 55, 622, 38)
draw.text((105, 618), "MEMBER SINCE", fill=(180, 140, 255), font=font_h3)
draw.text((105, 648), f"Joined {server_name} • {join_date}", fill=(255, 255, 255), font=font_body_bold)

# Tile 5: Reactions
paste_icon("assets/icons/heart.png", 415, 622, 38)
draw.text((465, 618), "REACTIONS", fill=(255, 80, 110), font=font_h3)
draw.text((465, 648), f"{reactions_given:,} Given  •  {reactions_rcvd:,} Received", fill=(255, 255, 255), font=font_body_bold)


# 6. Bottom 4 Neon Bento Cards
# Card 1: Messages
paste_icon("assets/icons/chat.png", 65, 750, 36)
draw.text((112, 755), "MESSAGES", fill=(255, 190, 60), font=font_h3)
draw.text((65, 810), f"{messages:,}", fill=(255, 255, 255), font=font_huge_num)
draw.text((65, 905), f"{words:,} words typed", fill=(170, 185, 205), font=font_body)

# Card 2: Media
paste_icon("assets/icons/media.png", 420, 750, 36)
draw.text((467, 755), "MEDIA SHARED", fill=(255, 100, 220), font=font_h3)
draw.text((420, 810), f"{media:,}", fill=(255, 255, 255), font=font_huge_num)
draw.text((420, 905), "Photos, clips & files", fill=(170, 185, 205), font=font_body)

# Card 3: Voice
paste_icon("assets/icons/voice.png", 775, 750, 36)
draw.text((822, 755), "VOICE TIME", fill=(0, 240, 180), font=font_h3)
v_str = f"{voice // 60}h {voice % 60}m" if voice >= 60 else f"{voice} mins"
draw.text((775, 810), v_str, fill=(255, 255, 255), font=font_huge_num)
draw.text((775, 905), f"{voice:,} total minutes", fill=(170, 185, 205), font=font_body)

# Card 4: Reactions Given
paste_icon("assets/icons/heart.png", 1130, 750, 36)
draw.text((1177, 755), "REACTIONS", fill=(255, 90, 120), font=font_h3)
draw.text((1130, 810), f"{reactions_given:,}", fill=(255, 255, 255), font=font_huge_num)
draw.text((1130, 905), "Given", fill=(170, 185, 205), font=font_body)

img.convert("RGB").save("scratch/neon_profile_preview.png")
print("Saved scratch/neon_profile_preview.png successfully!")
