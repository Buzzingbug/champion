import discord
from discord.ext import commands
from discord import app_commands
import io
import os
import aiohttp
import asyncio
import unicodedata
import datetime
from PIL import Image, ImageDraw, ImageFont

def format_clean_name(user_obj, max_len=12):
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
    img = Image.new('RGBA', (256, 256), (50, 100, 200, 255))
    return img

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

async def generate_neon_profile(bot, member: discord.Member, guild: discord.Guild):
    width, height = 1500, 1000

    # 1. Base Pre-rendered Neon Background
    try:
        img = Image.open("assets/neon_profile_bg.png").convert("RGBA")
    except:
        img = Image.new('RGBA', (width, height), (10, 11, 15, 255))

    draw = ImageDraw.Draw(img, "RGBA")

    # 2. Fonts
    try:
        font_name = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 60)
        font_huge_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 68)
        font_streak_num = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 74)
        font_banner = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 34)
        font_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
        font_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 20)
        font_body = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 19)
        font_body_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 19)
        font_badge = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 17)
        font_small = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 16)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_name = font_huge_num = font_streak_num = font_banner = font_h2 = font_h3 = font_body = font_body_bold = font_badge = font_small = ImageFont.load_default()

    # 3. Fetch Data from DB
    messages = media = words = night = voice = current_streak = longest_streak = 0
    supercoins = 0
    coin_name = "COINS"
    server_rank = 1

    if bot.db_pool:
        async with bot.db_pool.acquire() as conn:
            # Activity Record
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

            # Economy Record
            eco_rec = await conn.fetchrow(
                "SELECT supercoins FROM economy WHERE user_id = $1 AND guild_id = $2",
                member.id, guild.id
            )
            if eco_rec:
                supercoins = eco_rec['supercoins'] or 0

            # Server Rank
            rank_rec = await conn.fetchrow(
                "SELECT COUNT(*) + 1 AS rank FROM economy WHERE guild_id = $1 AND supercoins > $2",
                guild.id, supercoins
            )
            if rank_rec:
                server_rank = rank_rec['rank']

            # Coin Name
            coin_rec = await conn.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1",
                guild.id
            )
            if coin_rec and coin_rec['coin_name']:
                coin_name = coin_rec['coin_name'].upper()

    total_xp = (messages * 10) + (media * 25) + (voice * 5)
    level, cur_xp, next_xp, pct = get_level_data(total_xp)

    # Calculate Title / Rank Banner
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

    # Helper to paste icon
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

    # Paste Avatar into the glowing neon halo
    av_r = 126
    av_center = (200, 240)
    avatar_img = avatar_img.resize((av_r * 2, av_r * 2))
    av_mask = Image.new("L", (av_r * 2, av_r * 2), 0)
    ImageDraw.Draw(av_mask).ellipse((0, 0, av_r * 2, av_r * 2), fill=255)
    img.paste(avatar_img, (av_center[0] - av_r, av_center[1] - av_r), av_mask)

    paste_icon("assets/icons/crown.png", 184, 354, 32)

    # 5. User Name & VIP Plaque
    clean_name = format_clean_name(member, max_len=12)
    draw.text((360, 80), clean_name, fill=(255, 255, 255), font=font_name)

    # VIP Member Plaque (Top Center)
    paste_icon("assets/icons/crown.png", 670, 88, 38)
    draw.text((725, 84), "VIP", fill=(255, 215, 60), font=font_h2)
    draw.text((725, 114), "MEMBER", fill=(255, 220, 120), font=font_h3)

    # Sublabel: Server Rank
    sub_rank_label = f"— {coin_name} RANK —" if len(coin_name) < 14 else "— SERVER RANK —"
    draw.text((530, 178), sub_rank_label, fill=(190, 160, 220), font=font_h3)

    # Purple Rank Banner
    paste_icon("assets/icons/trophy.png", 390, 222, 42)
    draw.text((455, 225), rank_banner_title, fill=(255, 255, 255), font=font_banner)
    # Vector arrow
    draw.polygon([(820, 235), (835, 245), (820, 255)], fill=(220, 160, 255, 240))

    # Badges Bar (Dynamic detection)
    badges = []
    # Check Booster
    if member.premium_since:
        badges.append(("Booster", (180, 70, 255, 45), (200, 100, 255)))
    # Check VIP
    has_vip = any("vip" in r.name.lower() for r in member.roles) or member.guild_permissions.administrator
    if has_vip:
        badges.append(("VIP", (255, 190, 20, 45), (255, 200, 40)))
    # Check Staff
    if member.guild_permissions.manage_messages or member.guild_permissions.kick_members or member.guild_permissions.administrator:
        badges.append(("Staff", (60, 120, 255, 45), (100, 160, 255)))
    # Check Verified
    if any("verified" in r.name.lower() for r in member.roles):
        badges.append(("Verified", (0, 220, 120, 40), (0, 240, 140)))
    # Check Content Creator / Creator
    if any("creator" in r.name.lower() or "artist" in r.name.lower() for r in member.roles):
        badges.append(("Creator", (255, 50, 60, 40), (255, 80, 90)))
    # Check OG
    if member.joined_at and (discord.utils.utcnow() - member.joined_at).days > 180:
        badges.append(("OG", (255, 120, 30, 45), (255, 140, 40)))
    
    if not badges:
        badges.append(("Member", (100, 140, 200, 45), (140, 180, 240)))

    cur_x = 360
    for b_label, bg_col, border_col in badges:
        tb = draw.textbbox((0, 0), b_label, font=font_badge)
        bw = (tb[2] - tb[0]) + 22
        if cur_x + bw > 895:
            break
        draw.rounded_rectangle([(cur_x, 325), (cur_x + bw, 360)], radius=12, fill=bg_col, outline=border_col, width=1)
        draw.text((cur_x + 11, 332), b_label, fill=(255, 255, 255), font=font_badge)
        cur_x += bw + 8

    # 6. Top Right Server Identity Card
    if g_icon_img:
        g_icon_img = g_icon_img.resize((80, 80))
        g_mask = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(g_mask).rounded_rectangle([(0, 0), (80, 80)], radius=18, fill=255)
        img.paste(g_icon_img, (945, 75), g_mask)
    else:
        draw.rounded_rectangle([(945, 75), (1025, 155)], radius=18, fill=(30, 50, 80, 255), outline=(0, 180, 255, 180), width=2)
        paste_icon("assets/icons/media.png", 965, 95, 40)

    server_title = guild.name[:16] + "..." if len(guild.name) > 16 else guild.name
    draw.text((1045, 82), server_title, fill=(255, 255, 255), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36))
    draw.text((1045, 130), "DISCORD SERVER", fill=(140, 170, 210), font=font_h3)

    # 7. Streak & Leveling Card (Upper Right)
    paste_icon("assets/icons/fire.png", 950, 230, 34)
    draw.text((995, 236), "CURRENT STREAK", fill=(255, 180, 80), font=font_h3)

    sv = f"{current_streak}"
    draw.text((950, 275), sv, fill=(255, 140, 50) if current_streak > 0 else (255, 255, 255), font=font_streak_num)
    tb_s = draw.textbbox((0, 0), sv, font=font_streak_num)
    draw.text((950 + (tb_s[2] - tb_s[0]) + 16, 302), "Day Active" if current_streak == 1 else "Days Active", fill=(255, 255, 255), font=font_h2)

    draw.text((950, 375), f"Longest Streak: {longest_streak} Days", fill=(160, 175, 195), font=font_body)

    # Level & XP
    draw.text((950, 420), f"LEVEL {level}", fill=(255, 220, 100), font=font_h2)
    draw.text((1110, 424), f"{cur_xp:,} / {next_xp:,} XP", fill=(180, 195, 215), font=font_body)
    draw.text((1355, 420), f"{int(pct * 100)}%", fill=(255, 220, 100), font=font_h2)

    # Candy-Bar Progress Bar
    bar_box = [(950, 465), (1400, 493)]
    draw.rounded_rectangle(bar_box, radius=14, fill=(35, 38, 48, 255), outline=(255, 255, 255, 20), width=1)
    fill_w = max(int(450 * pct), 18)
    bar_fill = Image.new('RGBA', (fill_w, 28), (0, 0, 0, 0))
    bf_draw = ImageDraw.Draw(bar_fill)
    bf_draw.rounded_rectangle([(0, 0), (fill_w, 28)], radius=14, fill=(255, 170, 20, 240))
    # Candy stripes
    for sx in range(-20, fill_w + 30, 16):
        bf_draw.line([(sx, 0), (sx + 14, 28)], fill=(255, 220, 90, 180), width=5)
    img.paste(bar_fill, (950, 465), bar_fill)

    draw.text((950, 515), f"Total Server XP: {total_xp:,}", fill=(160, 175, 195), font=font_body)

    draw.line([(950, 555), (1400, 555)], fill=(255, 255, 255, 40), width=1)

    # Boost Status
    paste_icon("assets/icons/boost.png", 950, 580, 36)
    draw.text((1000, 580), "BOOST STATUS", fill=(210, 100, 255), font=font_h3)
    if member.premium_since:
        delta = discord.utils.utcnow() - member.premium_since
        months = max(1, int(delta.days // 30))
        boost_desc = f"Server Booster • {months} Months"
    else:
        boost_desc = "Standard Member"
    draw.text((1000, 608), boost_desc, fill=(220, 225, 235), font=font_body)

    # Favorite Channel
    paste_icon("assets/icons/chat.png", 950, 645, 34)
    draw.text((1000, 645), "ACTIVITY STATUS", fill=(140, 180, 255), font=font_h3)
    draw.text((1000, 672), f"Active Member • {messages:,} msgs", fill=(220, 225, 235), font=font_body)

    # 8. Middle Stats Row
    # Tile 1: Server Rank
    paste_icon("assets/icons/trophy.png", 55, 522, 38)
    draw.text((105, 518), "SERVER RANK", fill=(255, 200, 50), font=font_h3)
    total_m = guild.member_count or 100
    draw.text((105, 548), f"#{server_rank} / {total_m:,} Members", fill=(255, 255, 255), font=font_body_bold)

    # Tile 2: Server Coins
    paste_icon("assets/icons/coin.png", 375, 522, 38)
    draw.text((425, 518), coin_name[:12], fill=(255, 200, 50), font=font_h3)
    draw.text((425, 548), f"{supercoins:,} Coins", fill=(255, 255, 255), font=font_body_bold)

    # Tile 3: VIP Exclusive Banner
    paste_icon("assets/icons/crown.png", 585, 522, 38)
    draw.text((635, 518), "VIP  •  Exclusive Access", fill=(255, 210, 60), font=font_h3)
    draw.text((635, 548), f"Thank you for supporting {guild.name[:12]}!", fill=(180, 195, 215), font=font_small)

    # Tile 4: Member Since
    paste_icon("assets/icons/calendar.png", 55, 622, 38)
    draw.text((105, 618), "MEMBER SINCE", fill=(180, 140, 255), font=font_h3)
    join_str = member.joined_at.strftime("%b %d, %Y") if member.joined_at else "Recent"
    draw.text((105, 648), f"Joined {guild.name[:10]} • {join_str}", fill=(255, 255, 255), font=font_body_bold)

    # Tile 5: Reactions / Engagement
    paste_icon("assets/icons/heart.png", 415, 622, 38)
    draw.text((465, 618), "REACTIONS & ENGAGEMENT", fill=(255, 80, 110), font=font_h3)
    reactions_est = (words // 4) + messages
    draw.text((465, 648), f"{reactions_est:,} Total Interactions Recorded", fill=(255, 255, 255), font=font_body_bold)

    # 9. Bottom 4 Neon Bento Cards
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
    draw.text((1130, 810), f"{reactions_est:,}", fill=(255, 255, 255), font=font_huge_num)
    draw.text((1130, 905), "Given across channels", fill=(170, 185, 205), font=font_body)

    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="profile.png")


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your ultra-premium Cyberpunk Gamer Profile Card.")
    @app_commands.describe(user="The member to view the profile for.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target_member = user if user else interaction.user
        
        # Ensure we have member object with guild attributes
        if not isinstance(target_member, discord.Member):
            target_member = interaction.guild.get_member(target_member.id) or target_member

        await interaction.response.defer()

        try:
            file = await generate_neon_profile(self.bot, target_member, interaction.guild)
            await interaction.followup.send(file=file)
        except Exception as e:
            print(f"Neon profile generation error: {e}")
            await interaction.followup.send("❌ Failed to generate profile.")

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
