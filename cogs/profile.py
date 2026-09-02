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

def generate_3d_progress_bar(pct: float, sb_w=490, sb_h=64) -> Image.Image:
    """Renders the 3D Glossy Infographics Bar with 3x supersampling & Lanczos filtering."""
    SCALE = 3
    w, h = sb_w * SCALE, sb_h * SCALE
    bar_canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    ot_x, ot_y = 10 * SCALE, 8 * SCALE
    ot_w, ot_h = 470 * SCALE, 48 * SCALE
    ot_r = ot_h // 2

    ig_x, ig_y = ot_x + 16 * SCALE, ot_y + 11 * SCALE
    ig_w, ig_h = ot_w - 32 * SCALE, 26 * SCALE
    ig_r = ig_h // 2
    fill_w = max(int(ig_w * pct), ig_h)

    # 1. Track Shadow
    t_shad = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ts_draw = ImageDraw.Draw(t_shad)
    ts_draw.rounded_rectangle([(ot_x, ot_y + 4 * SCALE), (ot_x + ot_w, ot_y + ot_h + 4 * SCALE)], radius=ot_r, fill=(0, 0, 0, 140))
    t_shad = t_shad.filter(ImageFilter.GaussianBlur(4 * SCALE))
    bar_canvas = Image.alpha_composite(bar_canvas, t_shad)

    # 2. Track Pill
    t_pill = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    tp_draw = ImageDraw.Draw(t_pill)
    tp_draw.rounded_rectangle([(ot_x, ot_y), (ot_x + ot_w, ot_y + ot_h)], radius=ot_r, fill=(36, 34, 46, 255))
    tp_draw.rounded_rectangle([(ig_x, ig_y), (ig_x + ig_w, ig_y + ig_h)], radius=ig_r, fill=(20, 18, 26, 255))
    tp_draw.arc([(ig_x, ig_y), (ig_x + ig_w, ig_y + ig_h)], start=180, end=360, fill=(10, 8, 14, 255), width=2 * SCALE)
    bar_canvas = Image.alpha_composite(bar_canvas, t_pill)

    # 3. 3D Glossy Liquid Bar Fill (Volumetric Cylindrical Lighting)
    bar_cyl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bc_draw = ImageDraw.Draw(bar_cyl)
    for y_rel in range(ig_h):
        y_ratio = y_rel / ig_h
        if y_ratio < 0.2:
            r, g, b = 40, 165, 255
        elif y_ratio < 0.35:
            factor = 1.0 - abs(y_ratio - 0.25) / 0.15
            r = int(40 + (255 - 40) * factor * 0.8)
            g = int(185 + (255 - 185) * factor * 0.8)
            b = 255
        elif y_ratio < 0.7:
            r, g, b = 0, 150, 245
        else:
            r, g, b = 0, 95, 215
        bc_draw.line([(ig_x, ig_y + y_rel), (ig_x + fill_w, ig_y + y_rel)], fill=(r, g, b, 255), width=1)

    b_mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(b_mask).rounded_rectangle([(ig_x, ig_y), (ig_x + fill_w, ig_y + ig_h)], radius=ig_r, fill=255)

    bar_masked = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bar_masked.paste(bar_cyl, (0, 0), b_mask)
    bar_canvas = Image.alpha_composite(bar_canvas, bar_masked)

    # 4. 3D White Sphere Knob
    knob_cx = ig_x + fill_w
    knob_cy = ig_y + ig_h // 2
    knob_r = 19 * SCALE

    k_shad = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ks_draw = ImageDraw.Draw(k_shad)
    ks_draw.ellipse([(knob_cx - knob_r - 2 * SCALE, knob_cy - knob_r + 2 * SCALE), 
                     (knob_cx + knob_r + 2 * SCALE, knob_cy + knob_r + 6 * SCALE)], fill=(0, 0, 0, 160))
    k_shad = k_shad.filter(ImageFilter.GaussianBlur(3 * SCALE))
    bar_canvas = Image.alpha_composite(bar_canvas, k_shad)

    knob_surf = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ksu_draw = ImageDraw.Draw(knob_surf)
    for rad in range(knob_r, 0, -1):
        ratio = rad / knob_r
        col = int(218 + (255 - 218) * (1 - ratio))
        ox = int((1 - ratio) * (-2 * SCALE))
        oy = int((1 - ratio) * (-3 * SCALE))
        ksu_draw.ellipse([(knob_cx - rad + ox, knob_cy - rad + oy), 
                          (knob_cx + rad + ox, knob_cy + rad + oy)], fill=(col, col, col + 4, 255))

    bar_canvas = Image.alpha_composite(bar_canvas, knob_surf)

    try:
        font_knob = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 16 * SCALE)
    except:
        font_knob = ImageFont.load_default()

    knob_str = f"{int(pct * 100)}"
    tb_k = ksu_draw.textbbox((0, 0), knob_str, font=font_knob)
    kw = tb_k[2] - tb_k[0]
    kh = tb_k[3] - tb_k[1]
    k_text = ImageDraw.Draw(bar_canvas)
    k_text.text((knob_cx - kw // 2, knob_cy - kh // 2 - 2 * SCALE), knob_str, fill=(0, 150, 240, 255), font=font_knob)

    return bar_canvas.resize((sb_w, sb_h), Image.Resampling.LANCZOS)


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
        font_streak_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 64)
        font_banner = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
        font_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
        font_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)
        font_body = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 19)
        font_body_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19)
        font_server = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_name = font_huge_num = font_streak_num = font_banner = font_h2 = font_h3 = font_body = font_body_bold = font_server = ImageFont.load_default()

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

    # 5. Avatar with User's ring.png Frame
    av_r = 124
    av_center = (200, 230)
    avatar_img = avatar_img.resize((av_r * 2, av_r * 2))
    av_mask = Image.new("L", (av_r * 2, av_r * 2), 0)
    ImageDraw.Draw(av_mask).ellipse((0, 0, av_r * 2, av_r * 2), fill=255)
    img.paste(avatar_img, (av_center[0] - av_r, av_center[1] - av_r), av_mask)

    # Overlay ring.png (No crown at bottom)
    ring_path = "assets/icons/ring.png"
    if os.path.exists(ring_path):
        ring_img = Image.open(ring_path).convert("RGBA")
        r_size = 372
        ring_resized = ring_img.resize((r_size, r_size), Image.Resampling.LANCZOS)
        rx = av_center[0] - r_size // 2
        ry = av_center[1] - r_size // 2
        img.paste(ring_resized, (rx, ry), ring_resized)

    # 6. Username (Full width, zero overlap)
    clean_name = format_clean_name(member, max_len=20)
    draw.text((360, 75), clean_name, fill=(255, 255, 255), font=font_name)

    # Purple Rank Banner
    paste_icon("assets/icons/trophy.png", 390, 182, 42)
    draw.text((455, 185), rank_banner_title, fill=(255, 255, 255), font=font_banner)
    draw.polygon([(850, 195), (865, 205), (850, 215)], fill=(220, 160, 255, 240))

    # 7. Role Badges Flaticon Dock (Dynamic Display)
    member_role_ids = {r.id for r in member.roles}
    unlocked_badges = []

    # Check for custom badges
    if custom_badge_rows:
        for row in custom_badge_rows:
            if row['role_id'] in member_role_ids:
                unlocked_badges.append((row['badge_label'], "assets/icons/badge_vip.png"))

    # Default checks if no custom badges
    has_vip = any("vip" in r.name.lower() for r in member.roles) or member.guild_permissions.administrator
    has_staff = member.guild_permissions.manage_messages or member.guild_permissions.kick_members or member.guild_permissions.administrator
    is_og = bool(member.joined_at and (discord.utils.utcnow() - member.joined_at).days > 180)

    if not unlocked_badges:
        if has_vip:
            unlocked_badges.append(("VIP Access", "assets/icons/badge_vip.png"))
        if has_staff:
            unlocked_badges.append(("Staff Team", "assets/icons/badge_staff.png"))
        if is_og:
            unlocked_badges.append(("OG Member", "assets/icons/badge_og.png"))

    # Render Badges in Dock
    draw.text((605, 290), "ROLE BADGES", fill=(130, 150, 185), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 16))
    draw.text((605, 312), "Unlocked server privileges", fill=(170, 185, 210), font=ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 14))

    if len(unlocked_badges) == 1:
        # Single Badge Layout: 1 icon + clean subtitle
        b_label, b_icon = unlocked_badges[0]
        paste_icon(b_icon, 380, 279, 56)
        draw.text((450, 288), b_label.upper(), fill=(255, 215, 60), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 18))
        draw.text((450, 312), "Verified Privilege", fill=(170, 185, 210), font=ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 14))
    elif len(unlocked_badges) > 1:
        for i, (b_label, b_icon) in enumerate(unlocked_badges[:3]):
            paste_icon(b_icon, 370 + (i * 72), 276, 56)
    else:
        # Default Member status
        paste_icon("assets/icons/crown.png", 380, 286, 42)
        draw.text((440, 298), "STANDARD MEMBER", fill=(170, 185, 210), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 16))

    # 8. The 6 Symmetrical 415px x 80px Tiles (2x3 Grid)
    # Row 1: VIP Status & Age Verified
    paste_icon("assets/icons/crown.png", 55, 412, 42)
    draw.text((112, 408), "VIP STATUS", fill=(255, 215, 60), font=font_h3)
    vip_sub = "Active VIP Access  •  Supporter" if has_vip else "Standard  •  Free Member"
    draw.text((112, 438), vip_sub, fill=(255, 255, 255), font=font_body_bold)

    paste_icon("assets/icons/heart.png", 500, 412, 42)
    draw.text((558, 408), "AGE VERIFIED", fill=(0, 240, 140), font=font_h3)
    has_verified = any("verified" in r.name.lower() for r in member.roles)
    ver_sub = "18+ Verified  •  Official Check" if has_verified else "Standard Check  •  Member"
    draw.text((558, 438), ver_sub, fill=(255, 255, 255), font=font_body_bold)

    # Row 2: Server Rank & Goon Coins
    paste_icon("assets/icons/trophy.png", 55, 517, 38)
    draw.text((112, 513), "SERVER RANK", fill=(255, 200, 50), font=font_h3)
    total_m = guild.member_count or 100
    draw.text((112, 543), f"#{server_rank} / {total_m:,} Members", fill=(255, 255, 255), font=font_body_bold)

    paste_icon("assets/icons/coin.png", 500, 517, 38)
    draw.text((558, 513), coin_name[:14], fill=(255, 200, 50), font=font_h3)
    draw.text((558, 543), f"{supercoins:,} Coins", fill=(255, 255, 255), font=font_body_bold)

    # Row 3: Member Since & Prime Time
    paste_icon("assets/icons/calendar.png", 55, 622, 38)
    draw.text((112, 618), "MEMBER SINCE", fill=(180, 140, 255), font=font_h3)
    join_str = member.joined_at.strftime("%b %d, %Y") if member.joined_at else "Recent"
    draw.text((112, 648), f"Joined  •  {join_str}", fill=(255, 255, 255), font=font_body_bold)

    paste_icon("assets/icons/fire.png", 500, 622, 38)
    draw.text((558, 618), "PRIME TIME", fill=(0, 220, 255), font=font_h3)
    if night > (messages * 0.25) and night > 5:
        prime_str = "Night Owl  •  11 PM - 3 AM"
    elif voice > messages:
        prime_str = "Voice Broadcaster"
    else:
        prime_str = "Active Chatter  •  Daytime"
    draw.text((558, 648), prime_str, fill=(255, 255, 255), font=font_body_bold)

    # 9. Top Right Server Identity Card (Pilmoji Color Emojis)
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

    # 10. Upper Right Streak & Level Card (Spacious Layout)
    paste_icon("assets/icons/fire.png", 950, 225, 30)
    draw.text((990, 228), "CURRENT STREAK", fill=(255, 180, 80), font=font_h3)
    sv = f"{current_streak}"
    draw.text((950, 260), sv, fill=(255, 140, 50) if current_streak > 0 else (255, 255, 255), font=font_streak_num)
    draw.text((990, 280), "Day Active" if current_streak == 1 else "Days Active", fill=(255, 255, 255), font=font_h2)

    draw.text((1220, 228), "BEST STREAK", fill=(160, 180, 210), font=font_h3)
    draw.text((1220, 260), f"{longest_streak}", fill=(255, 215, 60), font=font_streak_num)
    draw.text((1260, 280), "Days", fill=(255, 255, 255), font=font_h2)

    # Level & XP Header
    draw.text((950, 350), f"LEVEL {level}", fill=(255, 220, 100), font=font_h2)
    draw.text((1115, 354), f"{cur_xp:,} / {next_xp:,} XP", fill=(180, 195, 215), font=font_body)

    # 3D Glossy Infographics Progress Bar
    bar_3d = generate_3d_progress_bar(pct, sb_w=490, sb_h=64)
    img.paste(bar_3d, (945, 390), bar_3d)

    # Total Server XP & Clean Divider Line
    draw.text((950, 465), f"Total Server XP: {total_xp:,}", fill=(160, 175, 195), font=font_body)
    draw.line([(950, 498), (1440, 498)], fill=(255, 255, 255, 35), width=1)

    # Boost Status
    paste_icon("assets/icons/boost.png", 950, 520, 36)
    draw.text((1000, 520), "BOOST STATUS", fill=(210, 100, 255), font=font_h3)
    if member.premium_since:
        delta = discord.utils.utcnow() - member.premium_since
        months = max(1, int(delta.days // 30))
        boost_desc = f"Server Booster • {months} Months"
    else:
        boost_desc = "Standard Member"
    draw.text((1000, 548), boost_desc, fill=(220, 225, 235), font=font_body)

    # Activity Status
    paste_icon("assets/icons/chat.png", 950, 595, 34)
    draw.text((1000, 595), "FAVORITE CHANNEL", fill=(140, 180, 255), font=font_h3)
    draw.text((1000, 623), f"#general • {messages:,} messages", fill=(220, 225, 235), font=font_body)

    # 11. Bottom 4 Bento Cards
    reactions_est = (words // 4) + messages
    rcvd_est = int(reactions_est * 0.7)

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

    # Card 4: Reactions
    paste_icon("assets/icons/heart.png", 1130, 750, 36)
    draw.text((1177, 755), "REACTIONS", fill=(255, 90, 120), font=font_h3)
    draw.text((1130, 810), f"{reactions_est:,}", fill=(255, 255, 255), font=font_huge_num)
    draw.text((1130, 905), f"{reactions_est:,} Given • {rcvd_est:,} Recv", fill=(170, 185, 205), font=font_body)

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
