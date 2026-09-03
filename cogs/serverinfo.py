import discord
from discord.ext import commands
from discord import app_commands
import io
import os
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from pilmoji import Pilmoji

TEMPLATE_PATH = "assets/serverinfo_hud_template.png"

def format_number(val: int) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{val:,}"

def generate_avatar_circle(icon_img: Image.Image, radius=91, initials="AH") -> Image.Image:
    """Takes any PIL Image (or None) and returns an antialiased circular avatar of exact radius."""
    diameter = radius * 2
    canvas = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    mask = Image.new("L", (diameter * 2, diameter * 2), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.ellipse([(0, 0), (diameter * 2, diameter * 2)], fill=255)
    mask = mask.resize((diameter, diameter), Image.Resampling.LANCZOS)

    if icon_img is not None:
        resized = icon_img.resize((diameter, diameter), Image.Resampling.LANCZOS)
        canvas.paste(resized, (0, 0), mask)
    else:
        d = ImageDraw.Draw(canvas)
        for r in range(radius, 0, -1):
            ratio = r / radius
            col = (
                int(14 + (28 - 14) * (1 - ratio)),
                int(18 + (38 - 18) * (1 - ratio)),
                int(34 + (70 - 34) * (1 - ratio)),
                255
            )
            d.ellipse([(radius - r, radius - r), (radius + r, radius + r)], fill=col)
        f_av = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 52)
        bbox = d.textbbox((0, 0), initials, font=f_av)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((radius - tw // 2, radius - th // 2 - 5), initials, fill=(255, 255, 255), font=f_av)

    border = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    ImageDraw.Draw(border).ellipse([(0, 0), (diameter - 1, diameter - 1)], outline=(0, 200, 255, 100), width=2)
    return Image.alpha_composite(canvas, border)

def render_serverinfo_hud_card(
    guild_name: str,
    guild_id: str,
    owner_name: str,
    created_str: str,
    vanity_str: str,
    boost_tier: int,
    boost_count: int,
    total_members: int,
    human_members: int,
    bot_members: int,
    text_channels: int,
    voice_channels: int,
    roles_count: int,
    top_role_name: str,
    verification_str: str,
    region_str: str,
    total_messages: int,
    total_media: int,
    voice_hours: int,
    coins_count: int,
    avatar_frames: list = None,
    avatar_durations: list = None,
    initials: str = "AH"
) -> io.BytesIO:
    """Renders the Server Info HUD. If avatar_frames is provided with multiple frames, outputs an animated GIF."""
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"{TEMPLATE_PATH} does not exist!")

    base_template = Image.open(TEMPLATE_PATH).convert("RGBA")
    card_base = base_template.copy()
    draw = ImageDraw.Draw(card_base, "RGBA")

    def paste_ic(img_dest, path, x, y, size=24):
        if os.path.exists(path):
            ic = Image.open(path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
            img_dest.paste(ic, (x, y), ic)

    # Dynamic Title Font sizing to avoid overlap
    title_size = 36
    if len(guild_name) > 28:
        title_size = 24
    elif len(guild_name) > 20:
        title_size = 28
    elif len(guild_name) > 15:
        title_size = 32

    f_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", title_size)
    f_h1 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 26)
    f_h2 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 16)
    f_h3 = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 15)
    f_body_b = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 13)
    f_body_reg = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 13)
    f_sm_b = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 12)
    f_sm_reg = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 11)
    f_micro_b = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 11)
    f_micro_reg = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 10)

    # 1. TOP-LEFT CONTAINER: OWNER CAPSULE
    paste_ic(card_base, "assets/icons/crown.png", 104, 281, 20)
    draw.text((130, 283), f"OWNER: {owner_name[:18]}", fill=(255, 215, 60), font=f_body_b)

    # 2. BOTTOM-LEFT CONTAINER: 5 METRIC PILLS
    def draw_bullet(cx, cy, col, ic_path):
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=col)
        if ic_path and os.path.exists(ic_path):
            ic = Image.open(ic_path).convert("RGBA").resize((12, 12), Image.Resampling.LANCZOS)
            card_base.paste(ic, (cx - 6, cy - 6), ic)

    # Pill 1: Total Members (y=394)
    draw_bullet(80, 394, (0, 210, 255), "assets/icons/heart.png")
    draw.text((104, 385), f"{total_members:,}", fill=(255, 255, 255), font=f_h3)
    draw.text((160, 387), "Total Members", fill=(175, 195, 225), font=f_body_reg)

    # Pill 2: Humans (y=438)
    draw_bullet(80, 438, (0, 230, 140), "assets/icons/badge_vip.png")
    pct_humans = (human_members / total_members * 100) if total_members > 0 else 100.0
    draw.text((104, 429), f"{human_members:,}", fill=(255, 255, 255), font=f_h3)
    draw.text((160, 431), f"Humans ({pct_humans:.1f}%)", fill=(160, 230, 200), font=f_body_reg)

    # Pill 3: Bots (y=482)
    draw_bullet(80, 482, (210, 90, 255), "assets/icons/boost.png")
    pct_bots = (bot_members / total_members * 100) if total_members > 0 else 0.0
    draw.text((104, 473), f"{bot_members:,}", fill=(255, 255, 255), font=f_h3)
    draw.text((142, 475), f"Integrated Bots ({pct_bots:.1f}%)", fill=(215, 185, 255), font=f_body_reg)

    # Pill 4: Channels (y=526)
    total_chans = text_channels + voice_channels
    draw_bullet(80, 526, (255, 195, 40), "assets/icons/chat.png")
    draw.text((104, 517), f"{total_chans} Channels", fill=(255, 255, 255), font=f_h3)
    draw.text((196, 519), f"• {text_channels} Text  {voice_channels} Voice", fill=(255, 210, 140), font=f_body_reg)

    # Pill 5: Roles (y=570)
    draw_bullet(80, 570, (255, 80, 140), "assets/icons/trophy.png")
    draw.text((104, 561), f"{roles_count} Roles", fill=(255, 255, 255), font=f_h3)
    clean_top = top_role_name[:16] if top_role_name else "None"
    draw.text((172, 563), f"• Top: @{clean_top}", fill=(255, 190, 215), font=f_body_reg)

    # 3. TOP-RIGHT CONTAINER: HEADER & IDENTITY
    with Pilmoji(card_base) as pilmoji:
        pilmoji.text((392, 64), guild_name, fill=(255, 255, 255), font=f_title)

    paste_ic(card_base, "assets/icons/calendar.png", 394, 114, 18)
    draw.text((418, 115), f"Est. {created_str}", fill=(185, 205, 235), font=f_body_reg)

    paste_ic(card_base, "assets/icons/chat.png", 615, 114, 18)
    draw.text((639, 115), vanity_str, fill=(0, 220, 255), font=f_body_b)

    def draw_glass_badge(x, y, w, h, border_col, ic_path, label, text_col):
        draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=7, fill=(16, 20, 36, 200), outline=border_col, width=1)
        if ic_path:
            paste_ic(card_base, ic_path, x + 8, y + (h - 14) // 2, 14)
            draw.text((x + 28, y + (h - 13) // 2), label, fill=text_col, font=f_sm_b)
        else:
            draw.text((x + 10, y + (h - 13) // 2), label, fill=text_col, font=f_sm_b)

    by = 148
    tier_label = f"TIER {boost_tier} BOOST" if boost_tier > 0 else "NO BOOST"
    draw_glass_badge(392, by, 126, 26, (210, 80, 255, 200), "assets/icons/boost.png", tier_label, (245, 215, 255))
    draw_glass_badge(528, by, 122, 26, (0, 240, 150, 200), "assets/icons/badge_staff.png", "COMMUNITY HUB", (210, 255, 235))
    draw_glass_badge(660, by, 106, 26, (255, 75, 120, 200), "assets/icons/heart.png", "18+ ADULT", (255, 210, 225))
    draw_glass_badge(776, by, 130, 26, (50, 150, 255, 200), "assets/icons/badge_vip.png", "HIGH SECURITY", (210, 235, 255))

    # Meta Capsule Row (Separated at y=190, NO overlap!)
    draw.rounded_rectangle([(392, 190), (950, 228)], radius=8, fill=(14, 18, 30, 160), outline=(0, 200, 255, 90), width=1)
    draw.text((406, 199), "GUILD ID:", fill=(130, 150, 185), font=f_sm_b)
    draw.text((466, 199), str(guild_id), fill=(240, 245, 255), font=f_body_b)

    draw.text((615, 199), "REGION:", fill=(130, 150, 185), font=f_sm_b)
    draw.text((670, 199), region_str[:22], fill=(0, 215, 255), font=f_body_b)

    draw.text((820, 199), "DEFENSE:", fill=(130, 150, 185), font=f_sm_b)
    draw.text((880, 199), verification_str[:12], fill=(0, 240, 140), font=f_body_b)

    # 4. MIDDLE-RIGHT LEFT CONTAINER: NITRO CITADEL
    paste_ic(card_base, "assets/icons/boost.png", 386, 292, 18)
    draw.text((410, 292), "NITRO BOOST CITADEL", fill=(255, 215, 60), font=f_h2)
    max_tag = "TIER 3 MAX" if boost_tier >= 3 else f"TIER {boost_tier} ACTIVE"
    draw.rounded_rectangle([(615, 290), (706, 310)], radius=6, fill=(0, 230, 140, 40), outline=(0, 240, 140, 180), width=1)
    draw.text((624, 293), max_tag, fill=(0, 240, 140), font=f_micro_b)

    draw.text((388, 320), str(boost_count), fill=(255, 255, 255), font=f_h1)
    draw.text((430, 326), "ACTIVE BOOSTERS", fill=(255, 205, 110), font=f_body_b)
    unlocked_str = "• 100% Unlocked" if boost_tier >= 3 else f"• Tier {boost_tier}"
    draw.text((570, 327), unlocked_str, fill=(175, 195, 225), font=f_sm_reg)

    perk_y = 368
    draw_glass_badge(388, perk_y, 74, 24, (160, 90, 240, 140), "assets/icons/media.png", "100MB", (225, 235, 255))
    draw_glass_badge(468, perk_y, 82, 24, (160, 90, 240, 140), "assets/icons/voice.png", "384kbps", (225, 235, 255))
    draw_glass_badge(556, perk_y, 80, 24, (160, 90, 240, 140), "assets/icons/crown.png", "250 Emo", (225, 235, 255))
    draw_glass_badge(642, perk_y, 74, 24, (160, 90, 240, 140), "assets/icons/chat.png", "Vanity", (225, 235, 255))

    # 5. MIDDLE-RIGHT RIGHT CONTAINER: DEFENSE MATRIX
    paste_ic(card_base, "assets/icons/badge_staff.png", 756, 292, 18)
    draw.text((780, 292), "DEFENSE MATRIX", fill=(0, 220, 255), font=f_h2)

    draw.text((756, 324), f"• Security: {verification_str}", fill=(240, 245, 255), font=f_sm_b)
    draw.text((756, 344), "• Phone Verification Req.", fill=(185, 210, 235), font=f_sm_reg)
    draw.text((756, 364), "• Explicit Media: Scan All", fill=(0, 240, 140), font=f_sm_b)
    draw.text((756, 384), "• 2FA Moderator Enforced", fill=(255, 205, 90), font=f_sm_reg)

    # 6. BOTTOM-RIGHT CONTAINER: SERVER PULSE & 4 CHIPS
    paste_ic(card_base, "assets/icons/fire.png", 388, 452, 20)
    draw.text((414, 452), "SERVER PULSE & ACTIVITY", fill=(255, 90, 150), font=f_h2)
    draw.text((818, 454), "TOP 1% ACTIVE", fill=(0, 240, 140), font=f_sm_b)

    draw.text((388, 480), f"{total_messages:,} Messages Logged", fill=(255, 255, 255), font=ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 22))
    draw.text((388, 512), f"{voice_hours:,} Voice Hours Logged  •  {total_media:,} Media Shared  •  {coins_count:,} Economy Coins", fill=(175, 195, 225), font=f_body_reg)

    # 4 Bottom pre-rendered chips
    # Chip 1: Messages
    paste_ic(card_base, "assets/icons/chat.png", 400, 592, 16)
    draw.text((428, 588), format_number(total_messages), fill=(255, 255, 255), font=f_sm_b)
    draw.text((428, 603), "Messages", fill=(190, 175, 225), font=f_micro_reg)

    # Chip 2: Media Shared
    paste_ic(card_base, "assets/icons/media.png", 536, 592, 16)
    draw.text((564, 588), format_number(total_media), fill=(255, 255, 255), font=f_sm_b)
    draw.text((564, 603), "Media Shared", fill=(175, 200, 235), font=f_micro_reg)

    # Chip 3: Voice Hours
    paste_ic(card_base, "assets/icons/voice.png", 678, 592, 16)
    draw.text((706, 588), f"{format_number(voice_hours)}h", fill=(255, 255, 255), font=f_sm_b)
    draw.text((706, 603), "Voice Hours", fill=(170, 225, 205), font=f_micro_reg)

    # Chip 4: Economy Coins
    paste_ic(card_base, "assets/icons/coin.png", 838, 592, 16)
    draw.text((868, 588), format_number(coins_count), fill=(255, 255, 255), font=f_sm_b)
    draw.text((868, 603), "Coins Logged", fill=(225, 205, 170), font=f_micro_reg)

    # =====================================================================
    # AVATAR COMPOSITING & HIGH-DPI SCALING (ELIMINATES BOUNDARY VOID)
    # =====================================================================
    av_cx, av_cy, av_r = 196, 171, 91
    av_x, av_y = av_cx - av_r, av_cy - av_r

    # Crop box tightly frames the glowing HUD chamfers with 10px breathing room
    CROP_BOX = (38, 32, 986, 642)
    TARGET_SCALE = 1.35  # Results in 1280 x 824 high-DPI output

    if avatar_frames and len(avatar_frames) > 1:
        gif_output_frames = []
        step = max(1, len(avatar_frames) // 16)
        sampled_frames = avatar_frames[::step][:16]
        sampled_durations = avatar_durations[::step][:16] if avatar_durations else [100] * len(sampled_frames)

        for frame_raw in sampled_frames:
            f_composite = card_base.copy()
            circ_av = generate_avatar_circle(frame_raw, radius=av_r, initials=initials)
            f_composite.paste(circ_av, (av_x, av_y), circ_av)
            f_cropped = f_composite.crop(CROP_BOX)
            cw, ch = int(f_cropped.width * TARGET_SCALE), int(f_cropped.height * TARGET_SCALE)
            f_scaled = f_cropped.resize((cw, ch), Image.Resampling.LANCZOS)
            p_frame = f_scaled.convert('RGB').quantize(colors=128, method=Image.Quantize.FASTOCTREE)
            gif_output_frames.append(p_frame)

        buf = io.BytesIO()
        gif_output_frames[0].save(
            buf,
            format='GIF',
            save_all=True,
            append_images=gif_output_frames[1:],
            duration=sampled_durations,
            loop=0,
            optimize=True
        )
        buf.seek(0)
        return buf
    else:
        single_frame = avatar_frames[0] if (avatar_frames and len(avatar_frames) > 0) else None
        circ_av = generate_avatar_circle(single_frame, radius=av_r, initials=initials)
        card_base.paste(circ_av, (av_x, av_y), circ_av)
        
        f_cropped = card_base.crop(CROP_BOX)
        cw, ch = int(f_cropped.width * TARGET_SCALE), int(f_cropped.height * TARGET_SCALE)
        final_card = f_cropped.resize((cw, ch), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        final_card.save(buf, format='PNG', optimize=True)
        buf.seek(0)
        return buf

async def fetch_guild_icon_frames(guild: discord.Guild, session: aiohttp.ClientSession):
    """Fetches guild icon. If animated, returns (frames, durations, True). Otherwise ([image], None, False)."""
    if not guild.icon:
        return None, None, False

    try:
        if guild.icon.is_animated():
            url = str(guild.icon.replace(format="gif", size=256))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    gif_im = Image.open(io.BytesIO(data))
                    frames = []
                    durations = []
                    for f in ImageSequence.Iterator(gif_im):
                        frames.append(f.convert("RGBA"))
                        durations.append(f.info.get("duration", 100))
                    if frames:
                        return frames, durations, True
        else:
            url = str(guild.icon.replace(format="png", size=256))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    im = Image.open(io.BytesIO(data)).convert("RGBA")
                    return [im], None, False
    except Exception as e:
        print(f"Error fetching guild icon: {e}")

    return None, None, False

class ServerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if not self.session.closed:
            await self.session.close()

    @app_commands.command(name="serverinfo", description="Display a futuristic cyberpunk Command Center overview of the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild

        if not guild:
            await interaction.followup.send("❌ This command can only be used inside a Discord server.")
            return

        # 1. Fetch Owner
        owner_name = "Unknown Owner"
        if guild.owner:
            owner_name = guild.owner.display_name
        else:
            try:
                owner_user = await self.bot.fetch_user(guild.owner_id)
                owner_name = owner_user.name
            except:
                owner_name = f"Owner-{guild.owner_id % 10000}"

        # 2. Created date & age
        created_at = guild.created_at
        days_old = max(0, (discord.utils.utcnow() - created_at).days)
        if days_old >= 365:
            age_str = f"{days_old / 365:.1f} Yrs"
        else:
            age_str = f"{days_old} Days"
        created_str = f"{created_at.strftime('%b %d, %Y')} ({age_str})"

        # 3. Vanity link
        vanity_str = f"discord.gg/{guild.vanity_url_code}" if guild.vanity_url_code else f"ID: {guild.id}"

        # 4. Members breakdown
        total_members = guild.member_count or len(guild.members)
        if guild.members and len(guild.members) > 1:
            human_members = sum(1 for m in guild.members if not m.bot)
            bot_members = sum(1 for m in guild.members if m.bot)
        else:
            # Fallback if unchunked
            human_members = total_members
            bot_members = 0

        # 5. Channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)

        # 6. Roles
        roles_count = len(guild.roles)
        top_role_name = guild.roles[-1].name if guild.roles else "None"

        # 7. Boosts
        boost_tier = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0

        # 8. Security & Region
        verification_str = str(guild.verification_level).capitalize()
        region_str = f"{guild.preferred_locale} • {verification_str}"

        # 9. Database Stats (Aggregated)
        total_messages = 0
        total_media = 0
        voice_hours = 0
        coins_count = 0

        if hasattr(self.bot, 'db_pool') and self.bot.db_pool:
            try:
                async with self.bot.db_pool.acquire() as conn:
                    # Sum activity
                    row_act = await conn.fetchrow(
                        """
                        SELECT 
                            COALESCE(SUM(messages_sent), 0) as msgs,
                            COALESCE(SUM(media_shared), 0) as media,
                            COALESCE(SUM(voice_minutes), 0) as voice
                        FROM user_activity
                        WHERE guild_id = $1
                        """,
                        guild.id
                    )
                    if row_act:
                        total_messages = int(row_act['msgs'])
                        total_media = int(row_act['media'])
                        voice_hours = int(row_act['voice']) // 60

                    # Sum coins
                    row_econ = await conn.fetchrow(
                        "SELECT COALESCE(SUM(supercoins), 0) as coins FROM economy WHERE guild_id = $1",
                        guild.id
                    )
                    if row_econ:
                        coins_count = int(row_econ['coins'])
            except Exception as e:
                print(f"Error querying server stats from database: {e}")

        # 10. Initials fallback
        words = guild.name.split()
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(guild.name) >= 2:
            initials = guild.name[:2].upper()
        else:
            initials = "SV"

        # 11. Fetch guild icon frames (static or animated GIF)
        avatar_frames, avatar_durations, is_animated = await fetch_guild_icon_frames(guild, self.session)

        # 12. Render card in worker thread to avoid blocking asyncio
        try:
            buf = await asyncio.to_thread(
                render_serverinfo_hud_card,
                guild_name=guild.name,
                guild_id=str(guild.id),
                owner_name=owner_name,
                created_str=created_str,
                vanity_str=vanity_str,
                boost_tier=boost_tier,
                boost_count=boost_count,
                total_members=total_members,
                human_members=human_members,
                bot_members=bot_members,
                text_channels=text_channels,
                voice_channels=voice_channels,
                roles_count=roles_count,
                top_role_name=top_role_name,
                verification_str=verification_str,
                region_str=region_str,
                total_messages=total_messages,
                total_media=total_media,
                voice_hours=voice_hours,
                coins_count=coins_count,
                avatar_frames=avatar_frames,
                avatar_durations=avatar_durations,
                initials=initials
            )

            file_ext = "gif" if is_animated else "png"
            filename = f"serverinfo_{guild.id}.{file_ext}"

            await interaction.followup.send(file=discord.File(fp=buf, filename=filename))

        except Exception as e:
            print(f"Error rendering serverinfo card: {e}")
            await interaction.followup.send("❌ Failed to render Server Info card. Please try again.")

async def setup(bot):
    await bot.add_cog(ServerInfoCog(bot))
