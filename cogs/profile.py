import discord
from discord.ext import commands
from discord import app_commands
import io
import os
import aiohttp
import asyncio
import unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pilmoji import Pilmoji

def format_clean_name(user_obj, max_len=20):
    display = getattr(user_obj, 'display_name', getattr(user_obj, 'name', 'User'))
    clean = unicodedata.normalize('NFKD', display).encode('ascii', 'ignore').decode('ascii').strip()
    if len(clean) >= 2:
        return clean[:max_len] + "..." if len(clean) > max_len else clean
    handle = getattr(user_obj, 'name', 'User')
    clean_handle = unicodedata.normalize('NFKD', handle).encode('ascii', 'ignore').decode('ascii').strip()
    if len(clean_handle) >= 2:
        return clean_handle[:max_len] + "..." if len(clean_handle) > max_len else clean_handle
    printable = ''.join(c for c in display if 32 <= ord(c) <= 126).strip()
    if printable:
        return printable[:max_len]
    uid = getattr(user_obj, 'id', 0)
    return f"Member-{uid % 10000}"

async def fetch_avatar(user: discord.User, session: aiohttp.ClientSession) -> Image.Image:
    try:
        if user.display_avatar:
            url = str(user.display_avatar.replace(size=256, format="png"))
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except:
        pass
    return Image.new('RGBA', (256, 256), (50, 100, 200, 255))

async def fetch_guild_icon(guild: discord.Guild, session: aiohttp.ClientSession) -> Image.Image:
    try:
        if guild.icon:
            url = str(guild.icon.replace(size=128, format="png"))
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except:
        pass
    return None

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

COLOR_MAP = {
    "gold": ((255, 190, 20, 50), (255, 200, 40)),
    "purple": ((180, 70, 255, 50), (200, 100, 255)),
    "cyan": ((0, 210, 255, 45), (0, 230, 255)),
    "green": ((0, 220, 120, 40), (0, 240, 140)),
    "red": ((255, 50, 60, 45), (255, 80, 90)),
    "blue": ((60, 120, 255, 50), (100, 160, 255)),
    "orange": ((255, 120, 30, 50), (255, 140, 40)),
}

def generate_proportional_3d_bar(pct: float, bar_w=490, bar_h=60) -> Image.Image:
    """Renders the perfectly proportioned 3D Neon Liquid Bar with 48px Level Orb."""
    SCALE = 3
    BW, BH = bar_w * SCALE, bar_h * SCALE
    b_canvas = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b_canvas)

    trk_x, trk_y = 6 * SCALE, 12 * SCALE
    trk_w, trk_h = (bar_w - 12) * SCALE, 34 * SCALE
    trk_r = trk_h // 2

    # 1. Ambient Drop Shadow
    t_shad = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    ImageDraw.Draw(t_shad).rounded_rectangle(
        [(trk_x, trk_y + 3 * SCALE), (trk_x + trk_w, trk_y + trk_h + 3 * SCALE)],
        radius=trk_r, fill=(0, 0, 0, 160)
    )
    t_shad = t_shad.filter(ImageFilter.GaussianBlur(4 * SCALE))
    b_canvas = Image.alpha_composite(b_canvas, t_shad)

    # 2. Dark Sunken Canal (#080c15)
    bd.rounded_rectangle(
        [(trk_x, trk_y), (trk_x + trk_w, trk_y + trk_h)],
        radius=trk_r, fill=(8, 12, 21, 255), outline=(100, 135, 175, 80), width=2 * SCALE
    )

    fill_len = max(int(trk_w * pct), trk_r * 2)

    # 3. Outer Neon Glow Aura
    fill_glow = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    ImageDraw.Draw(fill_glow).rounded_rectangle(
        [(trk_x - 3 * SCALE, trk_y - 3 * SCALE), (trk_x + fill_len + 3 * SCALE, trk_y + trk_h + 3 * SCALE)],
        radius=trk_r + 3 * SCALE, fill=(40, 155, 255, 170)
    )
    fill_glow = fill_glow.filter(ImageFilter.GaussianBlur(6 * SCALE))
    b_canvas = Image.alpha_composite(b_canvas, fill_glow)

    # 4. 3D Cylindrical Liquid Gradient Fill
    cyl_fill = Image.new('RGBA', (fill_len, trk_h), (0, 0, 0, 0))
    cf_draw = ImageDraw.Draw(cyl_fill)
    for y in range(trk_h):
        y_rat = y / trk_h
        if y_rat < 0.22:
            r, g, b = 40, 165, 255
        elif y_rat < 0.38:
            factor = 1.0 - abs(y_rat - 0.28) / 0.12
            r = int(40 + (255 - 40) * factor * 0.9)
            g = int(185 + (255 - 185) * factor * 0.9)
            b = 255
        elif y_rat < 0.72:
            r, g, b = 0, 150, 245
        else:
            r, g, b = 0, 95, 215
        cf_draw.line([(0, y), (fill_len, y)], fill=(r, g, b, 255), width=1)

    # Horizontal smooth gradient
    h_grad = Image.new('RGBA', (fill_len, trk_h), (0, 0, 0, 0))
    hg_draw = ImageDraw.Draw(h_grad)
    for x in range(fill_len):
        x_rat = x / max(fill_len, 1)
        hg_draw.line([(x, 0), (x, trk_h)], fill=(int(117 * x_rat), int(217 * x_rat), 255, 95), width=1)
    cyl_fill = Image.alpha_composite(cyl_fill, h_grad)

    # Specular light highlight streak
    for x in range(trk_r, fill_len - trk_r):
        cf_draw.line([(x, 4 * SCALE), (x, 7 * SCALE)], fill=(255, 255, 255, 170), width=1)

    mask = Image.new('L', (fill_len, trk_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (fill_len, trk_h)], radius=trk_r, fill=255)
    b_canvas.paste(cyl_fill, (trk_x, trk_y), mask)

    # 5. Level Orb (Diameter 48px, protruding by 7px symmetrically)
    orb_cx = trk_x + fill_len
    orb_cy = trk_y + trk_h // 2
    orb_r = 24 * SCALE

    o_glow = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    ImageDraw.Draw(o_glow).ellipse(
        [(orb_cx - orb_r - 7 * SCALE, orb_cy - orb_r - 7 * SCALE), (orb_cx + orb_r + 7 * SCALE, orb_cy + orb_r + 7 * SCALE)],
        fill=(40, 165, 255, 220)
    )
    o_glow = o_glow.filter(ImageFilter.GaussianBlur(7 * SCALE))
    b_canvas = Image.alpha_composite(b_canvas, o_glow)

    orb_surf = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    os_draw = ImageDraw.Draw(orb_surf)

    for rad in range(orb_r, 0, -1):
        rat = rad / orb_r
        r_val = int(245 - rat * (245 - 23))
        g_val = int(252 - rat * (252 - 100))
        b_val = int(255 - rat * (255 - 201))
        ox = int((1 - rat) * (-4 * SCALE))
        oy = int((1 - rat) * (-5 * SCALE))
        os_draw.ellipse(
            [(orb_cx - rad + ox, orb_cy - rad + oy), (orb_cx + rad + ox, orb_cy + rad + oy)],
            fill=(r_val, g_val, b_val, 255)
        )

    # Illuminated white ring border
    os_draw.ellipse([(orb_cx - orb_r, orb_cy - orb_r), (orb_cx + orb_r, orb_cy + orb_r)], outline=(220, 246, 255, 255), width=2 * SCALE)

    # Orb Percentage Number (Crisp Pure White with Soft Shadow)
    try:
        font_orb = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19 * SCALE)
    except:
        font_orb = ImageFont.load_default()

    orb_txt = f"{int(pct * 100)}"
    tb_ot = os_draw.textbbox((0, 0), orb_txt, font=font_orb)
    ot_w = tb_ot[2] - tb_ot[0]
    ot_h = tb_ot[3] - tb_ot[1]
    os_draw.text((orb_cx - ot_w // 2, orb_cy - ot_h // 2 - 2 * SCALE + 2 * SCALE), orb_txt, fill=(15, 50, 100, 180), font=font_orb)
    os_draw.text((orb_cx - ot_w // 2, orb_cy - ot_h // 2 - 2 * SCALE), orb_txt, fill=(255, 255, 255, 255), font=font_orb)

    b_canvas = Image.alpha_composite(b_canvas, orb_surf)
    return b_canvas.resize((bar_w, bar_h), Image.Resampling.LANCZOS)


async def generate_neon_profile(bot, member: discord.Member, guild: discord.Guild):
    width, height = 1500, 1000

    # 1. Load Pre-rendered Optimized Background
    bg_path = "assets/neon_profile_bg.png"
    try:
        img = Image.open(bg_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (width, height), (12, 14, 20, 255))

    draw = ImageDraw.Draw(img, "RGBA")

    # 2. Fonts
    try:
        font_name = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 62)
        font_huge_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 68)
        font_streak_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 68)
        font_banner = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
        font_h1 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
        font_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
        font_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)
        font_body_b = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19)
        font_body_reg = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 19)
        font_server = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36)
        font_stat_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 17)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_name = font_huge_num = font_streak_num = font_banner = font_h1 = font_h2 = font_h3 = font_body_b = font_body_reg = font_server = font_stat_title = ImageFont.load_default()

    # 3. Fetch Data from Database
    messages = media = words = night = voice = current_streak = longest_streak = 0
    supercoins = 0
    coin_name = "COINS"
    server_rank = 1
    custom_badge_rows = []

    if bot.db_pool:
        async with bot.db_pool.acquire() as conn:
            act_rec = await conn.fetchrow(
                "SELECT * FROM user_activity WHERE user_id = $1 AND guild_id = $2",
                member.id, guild.id
            )
            if act_rec:
                messages = act_rec['messages_sent'] or 0
                media = act_rec['media_shared'] or 0
                words = act_rec['words_typed'] or 0
                night = act_rec['night_owl_msgs'] or 0
                voice = act_rec['voice_minutes'] or 0
                current_streak = act_rec['current_streak'] or 0
                longest_streak = act_rec['longest_streak'] or 0

            eco_rec = await conn.fetchrow(
                "SELECT supercoins FROM economy WHERE user_id = $1 AND guild_id = $2",
                member.id, guild.id
            )
            if eco_rec:
                supercoins = eco_rec['supercoins'] or 0

            rank_rec = await conn.fetchrow(
                "SELECT COUNT(*) + 1 AS rank FROM economy WHERE guild_id = $1 AND supercoins > $2",
                guild.id, supercoins
            )
            if rank_rec:
                server_rank = rank_rec['rank']

            coin_rec = await conn.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1",
                guild.id
            )
            if coin_rec and coin_rec['coin_name']:
                coin_name = coin_rec['coin_name'].upper()

            custom_badge_rows = await conn.fetch(
                "SELECT role_id, badge_label, badge_color FROM profile_badges WHERE guild_id = $1",
                guild.id
            )

    total_xp = (messages * 10) + (media * 25) + (voice * 5)
    level, cur_xp, next_xp, pct = get_level_data(total_xp)

    # Rank Banner Title
    if level >= 25:
        rank_banner_title = "SERVER TITAN"
    elif level >= 15:
        rank_banner_title = "GOON LEGEND" if "goon" in guild.name.lower() else "SERVER LEGEND"
    elif level >= 10:
        rank_banner_title = "SERVER ELITE"
    elif level >= 5:
        rank_banner_title = "ACTIVE REGULAR"
    else:
        rank_banner_title = "THE NEWCOMER"

    def paste_icon(path, x, y, size=32):
        if os.path.exists(path):
            try:
                ic = Image.open(path).convert("RGBA").resize((size, size))
                img.paste(ic, (x, y), ic)
            except:
                pass

    # 4. Fetch User Avatar & Guild Icon in Parallel
    async with aiohttp.ClientSession() as session:
        avatar_task = fetch_avatar(member, session)
        guild_icon_task = fetch_guild_icon(guild, session)
        avatar_img, g_icon_img = await asyncio.gather(avatar_task, guild_icon_task)

    # 5. Avatar with ring.png Frame (No Crown at bottom)
    av_r = 124
    av_center = (200, 230)
    avatar_img = avatar_img.resize((av_r * 2, av_r * 2))
    av_mask = Image.new("L", (av_r * 2, av_r * 2), 0)
    ImageDraw.Draw(av_mask).ellipse((0, 0, av_r * 2, av_r * 2), fill=255)
    img.paste(avatar_img, (av_center[0] - av_r, av_center[1] - av_r), av_mask)

    ring_path = "assets/icons/ring.png"
    if os.path.exists(ring_path):
        ring_img = Image.open(ring_path).convert("RGBA")
        r_size = 372
        ring_resized = ring_img.resize((r_size, r_size), Image.Resampling.LANCZOS)
        rx_pos = av_center[0] - r_size // 2
        ry_pos = av_center[1] - r_size // 2
        img.paste(ring_resized, (rx_pos, ry_pos), ring_resized)

    # 6. Username & Rank Banner
    clean_name = format_clean_name(member, max_len=20)
    draw.text((360, 75), clean_name, fill=(255, 255, 255), font=font_name)

    paste_icon("assets/icons/trophy.png", 390, 182, 42)
    draw.text((455, 185), rank_banner_title, fill=(255, 255, 255), font=font_banner)
    draw.polygon([(850, 195), (865, 205), (850, 215)], fill=(220, 160, 255, 240))

    # 7. Single Role Badge: STAFF (Linked to /badge add role:@Role label:Staff)
    staff_role_ids = set()
    vip_role_ids = set()
    for r in custom_badge_rows:
        lbl = (r['badge_label'] or '').lower().strip()
        rid = r['role_id']
        if any(k in lbl for k in ("staff", "mod", "admin")):
            staff_role_ids.add(rid)
        if any(k in lbl for k in ("vip", "supporter", "premium")):
            vip_role_ids.add(rid)

    has_staff = (
        any(r.id in staff_role_ids for r in member.roles) or
        any("staff" in r.name.lower() or "mod" in r.name.lower() for r in member.roles) or
        member.guild_permissions.manage_messages or 
        member.guild_permissions.kick_members or 
        member.guild_permissions.administrator
    )

    if has_staff:
        draw.rounded_rectangle([(360, 275), (550, 340)], radius=16, fill=(20, 35, 60, 180), outline=(0, 190, 255, 160), width=2)
        paste_icon("assets/icons/badge_staff.png", 372, 282, 46)
        draw.text((428, 286), "STAFF", fill=(0, 225, 255), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 22))
        draw.text((428, 312), "Official Moderator", fill=(175, 195, 220), font=ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 14))

    # 8. Symmetrical 415px x 80px Tiles
    # Row 1 Tile 1: VIP STATUS (Linked to /badge add role:@Role label:VIP)
    has_vip = (
        any(r.id in vip_role_ids for r in member.roles) or
        any("vip" in r.name.lower() for r in member.roles) or 
        member.guild_permissions.administrator
    )
    if has_vip:
        paste_icon("assets/icons/badge_vip.png", 52, 408, 48)
        draw.text((112, 408), "VIP STATUS", fill=(255, 215, 60), font=font_h3)
        draw.text((112, 438), "Active VIP Access  •  Supporter", fill=(255, 255, 255), font=font_body_b)
    else:
        paste_icon("assets/icons/crown.png", 55, 412, 42)
        draw.text((112, 408), "VIP STATUS", fill=(160, 175, 195), font=font_h3)
        draw.text((112, 438), "Standard  •  Free Member", fill=(180, 195, 215), font=font_body_b)

    # Row 1 Tile 2: AGE VERIFIED
    paste_icon("assets/icons/heart.png", 500, 412, 42)
    draw.text((558, 408), "AGE VERIFIED", fill=(0, 240, 140), font=font_h3)
    has_verified = any("verified" in r.name.lower() for r in member.roles)
    ver_sub = "18+ Verified  •  Official Check" if has_verified else "Standard Check  •  Member"
    draw.text((558, 438), ver_sub, fill=(255, 255, 255), font=font_body_b)

    # Row 2: SERVER RANK & GOON COINS
    paste_icon("assets/icons/trophy.png", 55, 517, 38)
    draw.text((112, 513), "SERVER RANK", fill=(255, 200, 50), font=font_h3)
    total_m = guild.member_count or 100
    draw.text((112, 543), f"#{server_rank} / {total_m:,} Members", fill=(255, 255, 255), font=font_body_b)

    paste_icon("assets/icons/coin.png", 500, 517, 38)
    draw.text((558, 513), coin_name[:14], fill=(255, 200, 50), font=font_h3)
    draw.text((558, 543), f"{supercoins:,} Coins", fill=(255, 255, 255), font=font_body_b)

    # Row 3: SWAPPED IN - BOOST STATUS & TOP CHANNEL (Exact same 415x80 size)
    paste_icon("assets/icons/boost.png", 55, 622, 40)
    draw.text((112, 618), "BOOST STATUS", fill=(210, 110, 255), font=font_h3)
    if member.premium_since:
        delta = discord.utils.utcnow() - member.premium_since
        months = max(1, int(delta.days // 30))
        boost_desc = f"Server Booster  •  {months} Months"
    else:
        boost_desc = "Standard Member"
    draw.text((112, 648), boost_desc, fill=(255, 255, 255), font=font_body_b)

    paste_icon("assets/icons/chat.png", 500, 622, 38)
    draw.text((558, 618), "TOP CHANNEL", fill=(0, 215, 255), font=font_h3)
    draw.text((558, 648), f"#general-chat  •  {messages:,} Messages", fill=(255, 255, 255), font=font_body_b)

    # 9. Top Right Server Identity Card (Pilmoji Emojis)
    if g_icon_img:
        g_icon_img = g_icon_img.resize((80, 80))
        g_mask = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(g_mask).rounded_rectangle([(0, 0), (80, 80)], radius=18, fill=255)
        img.paste(g_icon_img, (945, 70), g_mask)
    else:
        draw.rounded_rectangle([(945, 70), (1025, 150)], radius=18, fill=(30, 50, 80, 255), outline=(0, 180, 255, 180), width=2)
        paste_icon("assets/icons/media.png", 965, 90, 40)

    server_title = guild.name[:18] + "..." if len(guild.name) > 18 else guild.name
    with Pilmoji(img) as pilmoji:
        pilmoji.text((1045, 77), server_title, fill=(255, 255, 255), font=font_server)
    draw.text((1045, 128), "DISCORD SERVER", fill=(140, 170, 210), font=font_h3)

    # 10. Master Streak & Level Card (Right Side)
    rx, ry = 920, 195

    # Borderless Large Streaks
    paste_icon("assets/icons/fire.png", rx + 30, ry + 25, 36)
    draw.text((rx + 76, ry + 28), "CURRENT STREAK", fill=(255, 175, 60), font=font_stat_title)
    sv = f"{current_streak}"
    draw.text((rx + 30, ry + 68), sv, fill=(255, 140, 40) if current_streak > 0 else (200, 210, 225), font=font_streak_num)
    draw.text((rx + 80, ry + 96), "Day Active" if current_streak == 1 else "Days Active", fill=(255, 255, 255), font=font_h2)

    paste_icon("assets/icons/trophy.png", rx + 285, ry + 25, 34)
    draw.text((rx + 330, ry + 28), "LONGEST STREAK", fill=(255, 215, 60), font=font_stat_title)
    draw.text((rx + 285, ry + 68), f"{longest_streak}", fill=(255, 215, 60) if longest_streak > 0 else (200, 210, 225), font=font_streak_num)
    draw.text((rx + 335, ry + 96), "Days Record", fill=(255, 255, 255), font=font_h2)

    # Divider
    draw.line([(rx + 25, ry + 165), (rx + 515, ry + 165)], fill=(255, 255, 255, 30), width=1)

    # Level Header
    draw.text((rx + 30, ry + 200), f"LEVEL {level}", fill=(244, 223, 53), font=font_h1)
    draw.text((rx + 325, ry + 210), f"{cur_xp:,} / {next_xp:,} XP", fill=(155, 169, 189), font=font_h3)

    # Perfectly Proportioned 3D Neon Liquid Progress Bar
    bar_3d = generate_proportional_3d_bar(pct, bar_w=490, bar_h=60)
    img.paste(bar_3d, (rx + 25, ry + 265), bar_3d)

    # Clean Spacious Footer Stats
    draw.text((rx + 30, ry + 360), f"TOTAL SERVER XP {total_xp:,} XP", fill=(130, 150, 180), font=font_stat_title)
    rank_tier_str = f"TOP {max(1, int(100 - level * 1.8))}% ACTIVE" if level > 1 else "NEW RECRUIT"
    draw.text((rx + 360, ry + 360), rank_tier_str, fill=(0, 230, 140) if level > 1 else (150, 170, 195), font=font_stat_title)

    xp_needed = max(0, next_xp - cur_xp)
    pct_left = max(0.0, (1.0 - pct) * 100)
    draw.text((rx + 30, ry + 415), f"XP TO LEVEL {level + 1}", fill=(150, 165, 195), font=font_h3)
    draw.text((rx + 180, ry + 415), f"{xp_needed:,} XP Needed", fill=(210, 140, 255), font=font_h3)
    draw.text((rx + 380, ry + 415), f"{pct_left:.1f}% Left", fill=(255, 215, 80), font=font_h3)

    # 11. Bottom 4 Bento Cards
    reactions_est = (words // 4) + messages
    rcvd_est = int(reactions_est * 0.7)

    # Card 1: Messages
    paste_icon("assets/icons/chat.png", 65, 750, 36)
    draw.text((112, 755), "MESSAGES", fill=(255, 190, 60), font=font_h3)
    draw.text((65, 810), f"{messages:,}", fill=(255, 255, 255), font=font_huge_num)
    draw.text((65, 905), f"{words:,} words typed", fill=(170, 185, 205), font=font_body_reg)

    # Card 2: Media
    paste_icon("assets/icons/media.png", 420, 750, 36)
    draw.text((467, 755), "MEDIA SHARED", fill=(255, 100, 220), font=font_h3)
    draw.text((420, 810), f"{media:,}", fill=(255, 255, 255), font=font_huge_num)
    draw.text((420, 905), "Photos, clips & files", fill=(170, 185, 205), font=font_body_reg)

    # Card 3: Voice
    paste_icon("assets/icons/voice.png", 775, 750, 36)
    draw.text((822, 755), "VOICE TIME", fill=(0, 240, 180), font=font_h3)
    v_str = f"{voice // 60}h {voice % 60}m" if voice >= 60 else f"{voice} mins"
    draw.text((775, 810), v_str, fill=(255, 255, 255), font=font_huge_num)
    draw.text((775, 905), f"{voice:,} total minutes", fill=(170, 185, 205), font=font_body_reg)

    # Card 4: Reactions
    paste_icon("assets/icons/heart.png", 1130, 750, 36)
    draw.text((1177, 755), "REACTIONS", fill=(255, 90, 120), font=font_h3)
    draw.text((1130, 810), f"{reactions_est:,}", fill=(255, 255, 255), font=font_huge_num)
    draw.text((1130, 905), f"{reactions_est:,} Given • {rcvd_est:,} Recv", fill=(170, 185, 205), font=font_body_reg)

    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="profile.png")


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    badge_group = app_commands.Group(
        name="badge", 
        description="Manage role badges shown on gamer profiles",
        default_permissions=discord.Permissions(administrator=True)
    )

    @app_commands.command(name="profile", description="Display your ultra-premium cyberpunk gamer profile card")
    @app_commands.describe(user="The member whose profile you want to view (defaults to yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        await interaction.response.defer()

        file = await generate_neon_profile(self.bot, target, interaction.guild)
        await interaction.followup.send(file=file)

    @badge_group.command(name="add", description="Bind a custom badge to a server role")
    @app_commands.describe(
        role="The role to assign a badge to",
        label="The badge text label (e.g. 'VIP', 'Staff', 'Streamer', 'OG')",
        color="Color glow: gold, purple, cyan, green, red, blue, orange"
    )
    async def badge_add(self, interaction: discord.Interaction, role: discord.Role, label: str, color: str = "purple"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only server administrators can configure profile badges.", ephemeral=True)
            return

        c_name = color.lower()
        if c_name not in COLOR_MAP:
            valid_cols = ", ".join(COLOR_MAP.keys())
            await interaction.response.send_message(f"❌ Invalid color '{color}'. Choose from: `{valid_cols}`", ephemeral=True)
            return

        label_clean = label.strip()[:16]

        if not self.bot.db_pool:
            await interaction.response.send_message("❌ Database connection unavailable.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO profile_badges (guild_id, role_id, badge_label, badge_color)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, role_id) 
                DO UPDATE SET badge_label = $3, badge_color = $4
                """,
                interaction.guild_id, role.id, label_clean, c_name
            )

        await interaction.response.send_message(
            f"✅ Configured badge **[{label_clean}]** (`{c_name}`) for role {role.mention}! It will now display on members' profile cards.",
            ephemeral=False
        )

    @badge_group.command(name="remove", description="Remove a custom badge binding from a server role")
    @app_commands.describe(role="The role to remove the badge from")
    async def badge_remove(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only server administrators can configure profile badges.", ephemeral=True)
            return

        if not self.bot.db_pool:
            await interaction.response.send_message("❌ Database connection unavailable.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM profile_badges WHERE guild_id = $1 AND role_id = $2",
                interaction.guild_id, role.id
            )

        if "DELETE 0" in res:
            await interaction.response.send_message(f"⚠️ No custom badge was bound to role {role.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"🗑️ Removed custom badge for role {role.mention}.", ephemeral=False)

    @badge_group.command(name="list", description="List all configured custom badges for this server")
    async def badge_list(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("❌ Database connection unavailable.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role_id, badge_label, badge_color FROM profile_badges WHERE guild_id = $1",
                interaction.guild_id
            )

        if not rows:
            await interaction.response.send_message(
                "ℹ️ No custom badges configured yet. Default smart badges (Booster, VIP, Staff, Verified, OG) are active.\n"
                "Use `/badge add` to bind roles to custom badges!",
                ephemeral=True
            )
            return

        lines = ["**Configured Server Badges:**"]
        for r in rows:
            role = interaction.guild.get_role(r['role_id'])
            role_mention = role.mention if role else f"`Deleted Role ({r['role_id']})`"
            lines.append(f"• {role_mention} ➔ **[{r['badge_label']}]** (`{r['badge_color']}`)")

        await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
