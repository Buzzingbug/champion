import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import io
import os
import gc
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Detect Linux glibc for instant memory reclamation on Railway
try:
    import ctypes
    libc = ctypes.CDLL("libc.so.6")
    HAS_MALLOC_TRIM = True
except Exception:
    HAS_MALLOC_TRIM = False

def release_memory():
    """Forces garbage collection and releases unmapped memory back to the OS."""
    gc.collect()
    if HAS_MALLOC_TRIM:
        try:
            libc.malloc_trim(0)
        except Exception:
            pass

TEMPLATE_PATH = "assets/bank_hud_template.png"
FONT_PATH = "assets/fonts/PlusJakartaSans.ttf"

_CACHED_TEMPLATE = None
_FONT_CACHE = {}
_ICON_CACHE = {}

def get_base_template() -> Image.Image:
    global _CACHED_TEMPLATE
    if _CACHED_TEMPLATE is None:
        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"{TEMPLATE_PATH} does not exist!")
        _CACHED_TEMPLATE = Image.open(TEMPLATE_PATH).convert("RGBA")
    return _CACHED_TEMPLATE.copy()

def get_font(size: int):
    if size not in _FONT_CACHE:
        if os.path.exists(FONT_PATH):
            _FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size)
        else:
            _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]

def get_cached_icon(path: str, size: int) -> Image.Image:
    key = (path, size)
    if key not in _ICON_CACHE:
        if os.path.exists(path):
            _ICON_CACHE[key] = Image.open(path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        else:
            _ICON_CACHE[key] = None
    return _ICON_CACHE[key]

def render_bank_hud_card(
    balance: int,
    coin_name: str,
    server_rank: int,
    games_won: int,
    channel_today: int,
    category_today: int,
    games_today: int,
    active_channels_today: int = 0,
    active_categories_today: int = 0,
    lifetime_channel: int = 0,
    lifetime_category: int = 0,
    lifetime_games: int = 0
) -> io.BytesIO:
    """Renders the glassmorphism digital banking HUD card with symmetric margins and high-DPI clarity."""
    img = get_base_template()

    # Dynamic Balance font sizing to prevent overflow
    bal_str = f"{balance:,}"
    bal_size = 82
    if len(bal_str) > 13:
        bal_size = 56
    elif len(bal_str) > 10:
        bal_size = 66
    elif len(bal_str) > 8:
        bal_size = 74

    f_balance_label = get_font(bal_size)
    f_balance_val = get_font(bal_size)
    f_h2 = get_font(28)
    f_header_amt = get_font(26)
    f_row_title = get_font(24)
    f_row_sub = get_font(15)
    f_row_amt = get_font(30)
    f_pill = get_font(20)
    f_caption = get_font(15)

    glass_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glass_draw = ImageDraw.Draw(glass_layer)

    def draw_text_glow(target_img, xy, text, font, fill=(255, 255, 255), glow_col=(255, 255, 255, 60), radius=6):
        gx, gy = xy
        glow_canvas = Image.new("RGBA", target_img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_canvas)
        gd.text((gx, gy), text, font=font, fill=glow_col)
        glow_canvas = glow_canvas.filter(ImageFilter.GaussianBlur(radius))
        target_img.alpha_composite(glow_canvas)
        
        d = ImageDraw.Draw(target_img)
        d.text((gx, gy), text, font=font, fill=fill)

    content_x = 75
    content_r = 648

    # 1. BALANCE & NUMBER (SAME MASSIVE SIZE)
    draw_text_glow(img, (content_x, 72), "BALANCE", f_balance_label, fill=(255, 255, 255), glow_col=(255, 255, 255, 70), radius=7)
    draw_text_glow(img, (content_x, 72 + bal_size + 15), bal_str, f_balance_val, fill=(255, 255, 255), glow_col=(255, 225, 170, 80), radius=9)

    # Subtitle
    draw = ImageDraw.Draw(img)
    draw.text((content_x + 3, 280), f"CURRENT LIQUIDITY • {coin_name.upper()} VAULT", font=f_caption, fill=(185, 200, 225, 210))

    # Divider Line
    draw.line([(content_x, 310), (content_r, 310)], fill=(255, 255, 255, 45), width=1)

    # 2. REWARD BREAKDOWN HEADER
    draw.text((content_x, 334), "REWARD BREAKDOWN", font=f_h2, fill=(255, 255, 255, 250))

    total_today = channel_today + category_today + games_today
    today_badge = f"+{total_today:,} TODAY" if total_today > 0 else "0 TODAY"
    badge_bbox = draw.textbbox((0, 0), today_badge, font=f_header_amt)
    badge_w = badge_bbox[2] - badge_bbox[0]
    draw_text_glow(img, (content_r - badge_w, 336), today_badge, f_header_amt, fill=(57, 255, 160), glow_col=(57, 255, 160, 110), radius=6)

    # Dynamic all-time & today subtitles linking category and channel coins!
    if channel_today > 0:
        sub_channel = f"{lifetime_channel:,} All-Time • (+{channel_today:,} today)"
    elif lifetime_channel > 0:
        sub_channel = f"{lifetime_channel:,} All-Time Channel Rewards"
    else:
        sub_channel = "No channel rewards earned yet"

    if category_today > 0:
        sub_category = f"{lifetime_category:,} All-Time • (+{category_today:,} today)"
    elif lifetime_category > 0:
        sub_category = f"{lifetime_category:,} All-Time Category Rewards"
    else:
        sub_category = "No category rewards earned yet"

    if games_today > 0:
        sub_games = f"{lifetime_games:,} All-Time • (+{games_today:,} today)"
    elif lifetime_games > 0:
        sub_games = f"{lifetime_games:,} All-Time Game Winnings"
    else:
        sub_games = "No minigame rewards won yet"

    # 3. ACTIVITY ROWS (TALL 90px, 36px ICONS, CRISP ACCENTS)
    rows = [
        ("assets/icons/chat.png", "Earned from Channels", sub_channel, f"{lifetime_channel:,}", (0, 225, 255)),
        ("assets/icons/media.png", "Earned from Categories", sub_category, f"{lifetime_category:,}", (220, 110, 255)),
        ("assets/icons/trophy.png", "Earned from Games", sub_games, f"{lifetime_games:,}", (255, 210, 70))
    ]

    row_y = 388
    row_h = 90
    row_gap = 16

    for ic_path, title, subtitle, amount, accent_col in rows:
        glass_draw.rounded_rectangle([(content_x, row_y), (content_r, row_y + row_h)], radius=16, fill=(14, 18, 32, 170), outline=(255, 255, 255, 55), width=1)
        glass_draw.rounded_rectangle([(content_x, row_y), (content_x + 5, row_y + row_h)], radius=3, fill=accent_col)
        row_y += row_h + row_gap

    # 4. BOTTOM PILL BUTTONS (64px TALL)
    btn_y = 750
    btn1_w = 265
    btn_h = 64

    # Button 1: Server Rank
    glass_draw.rounded_rectangle([(content_x, btn_y), (content_x + btn1_w, btn_y + btn_h)], radius=32, fill=(16, 20, 36, 180), outline=(255, 255, 255, 100), width=1)

    # Button 2: Games Won
    btn2_x = content_x + btn1_w + 16
    btn2_w = content_r - btn2_x
    glass_draw.rounded_rectangle([(btn2_x, btn_y), (btn2_x + btn2_w, btn_y + btn_h)], radius=32, fill=(16, 20, 36, 180), outline=(255, 255, 255, 100), width=1)

    img = Image.alpha_composite(img, glass_layer)
    draw = ImageDraw.Draw(img)

    row_y = 388
    for ic_path, title, subtitle, amount, accent_col in rows:
        ic = get_cached_icon(ic_path, 36)
        if ic:
            img.paste(ic, (content_x + 22, row_y + (row_h - 36) // 2), ic)
        
        draw.text((content_x + 72, row_y + 16), title, font=f_row_title, fill=(255, 255, 255))
        draw.text((content_x + 72, row_y + 50), subtitle, font=f_row_sub, fill=(170, 185, 215))
        
        amt_bbox = draw.textbbox((0, 0), amount, font=f_row_amt)
        amt_w = amt_bbox[2] - amt_bbox[0]
        draw_text_glow(img, (content_r - amt_w - 20, row_y + 24), amount, f_row_amt, fill=(57, 255, 160), glow_col=(57, 255, 160, 100), radius=5)
        
        row_y += row_h + row_gap

    # Bottom Buttons Content
    ic_crown = get_cached_icon("assets/icons/crown.png", 28)
    if ic_crown:
        img.paste(ic_crown, (content_x + 20, btn_y + (btn_h - 28) // 2), ic_crown)
    draw.text((content_x + 58, btn_y + (btn_h - 24) // 2), f"SERVER RANK #{server_rank}", font=f_pill, fill=(255, 255, 255))

    ic_trophy = get_cached_icon("assets/icons/trophy.png", 28)
    if ic_trophy:
        img.paste(ic_trophy, (btn2_x + 20, btn_y + (btn_h - 28) // 2), ic_trophy)
    draw.text((btn2_x + 58, btn_y + (btn_h - 24) // 2), f"GAMES WON: {games_won}", font=f_pill, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=92, method=4)
    buf.seek(0)
    return buf

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bank", description="View your digital bank account vault card.")
    @app_commands.describe(user="The member whose bank balance you want to view (defaults to yourself)")
    async def bank(self, interaction: discord.Interaction, user: discord.Member = None):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        target = user or interaction.user
        guild = interaction.guild

        if not guild:
            await interaction.followup.send("❌ This command can only be used inside a server.")
            return

        balance = 0
        server_rank = 1
        games_won = 0
        lifetime_games = 0
        lifetime_channel = 0
        lifetime_category = 0
        coin_name = "Supercoins"
        channel_today = 0
        category_today = 0
        games_today = 0
        messages_count = 0
        media_count = 0
        voice_hours = 0.0

        try:
            async with self.bot.db_pool.acquire() as connection:
                # 1. User economy stats
                econ = await connection.fetchrow(
                    "SELECT supercoins, lifetime_channel, lifetime_category, lifetime_games, games_won FROM economy WHERE guild_id = $1 AND user_id = $2",
                    guild.id, target.id
                )
                supercoins = int(econ['supercoins'] or 0) if econ else 0
                lifetime_channel = int(econ['lifetime_channel'] or 0) if econ else 0
                lifetime_category = int(econ['lifetime_category'] or 0) if econ else 0
                lifetime_games = int(econ['lifetime_games'] or 0) if econ else 0
                if econ and econ['games_won'] is not None:
                    games_won = int(econ['games_won'])
                else:
                    games_won = max(0, lifetime_games // 100)

                # Fetch historical totals from channel_earnings & category_earnings
                chan_hist_row = await connection.fetchrow(
                    "SELECT COALESCE(SUM(earned_today), 0) as total FROM channel_earnings WHERE user_id = $1",
                    target.id
                )
                chan_hist = int(chan_hist_row['total']) if chan_hist_row else 0

                cat_hist_row = await connection.fetchrow(
                    "SELECT COALESCE(SUM(earned_today), 0) as total FROM category_earnings WHERE user_id = $1",
                    target.id
                )
                cat_hist = int(cat_hist_row['total']) if cat_hist_row else 0

                # Ensure lifetime metrics reflect all recorded channel & category earnings
                lifetime_channel = max(lifetime_channel, chan_hist)
                lifetime_category = max(lifetime_category, cat_hist)

                # Link total balance to include all channel, category, and game earnings
                total_earned = lifetime_channel + lifetime_category + lifetime_games
                balance = max(supercoins, total_earned)

                # Auto-sync back to economy table if missing or behind
                if econ is None or supercoins < balance or int(econ['lifetime_channel'] or 0) < lifetime_channel or int(econ['lifetime_category'] or 0) < lifetime_category:
                    await connection.execute(
                        """
                        INSERT INTO economy (guild_id, user_id, supercoins, lifetime_channel, lifetime_category, lifetime_games, games_won)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (guild_id, user_id)
                        DO UPDATE SET 
                            supercoins = GREATEST(economy.supercoins, $3),
                            lifetime_channel = GREATEST(COALESCE(economy.lifetime_channel, 0), $4),
                            lifetime_category = GREATEST(COALESCE(economy.lifetime_category, 0), $5),
                            lifetime_games = GREATEST(COALESCE(economy.lifetime_games, 0), $6)
                        """,
                        guild.id, target.id, balance, lifetime_channel, lifetime_category, lifetime_games, games_won
                    )

                # 2. Server Rank
                rank_row = await connection.fetchrow(
                    "SELECT COUNT(*) + 1 AS rank FROM economy WHERE guild_id = $1 AND supercoins > $2",
                    guild.id, balance
                )
                if rank_row:
                    server_rank = int(rank_row['rank'])

                # 3. Currency name
                coin_record = await connection.fetchrow(
                    "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                    guild.id
                )
                if coin_record and coin_record['coin_name']:
                    coin_name = coin_record['coin_name']

                # 4. Today's Channel & Category Earnings with active counts
                active_channels_today = 0
                chan_row = await connection.fetchrow(
                    """
                    SELECT 
                        COUNT(DISTINCT channel_id) as active_count, 
                        COALESCE(SUM(earned_today), 0) as total 
                    FROM channel_earnings 
                    WHERE user_id = $1 AND date = CURRENT_DATE
                    """,
                    target.id
                )
                if chan_row:
                    channel_today = int(chan_row['total'])
                    active_channels_today = int(chan_row['active_count'] or 0)

                active_categories_today = 0
                cat_row = await connection.fetchrow(
                    """
                    SELECT 
                        COUNT(DISTINCT category_id) as active_count, 
                        COALESCE(SUM(earned_today), 0) as total 
                    FROM category_earnings 
                    WHERE user_id = $1 AND date = CURRENT_DATE
                    """,
                    target.id
                )
                if cat_row:
                    category_today = int(cat_row['total'])
                    active_categories_today = int(cat_row['active_count'] or 0)

            # Render card in worker thread to prevent event loop blocking
            buf = await asyncio.to_thread(
                render_bank_hud_card,
                balance=balance,
                coin_name=coin_name,
                server_rank=server_rank,
                games_won=games_won,
                channel_today=channel_today,
                category_today=category_today,
                games_today=games_today,
                active_channels_today=active_channels_today,
                active_categories_today=active_categories_today,
                lifetime_channel=lifetime_channel,
                lifetime_category=lifetime_category,
                lifetime_games=lifetime_games
            )

            file = discord.File(fp=buf, filename=f"bank_{target.id}.webp")
            await interaction.followup.send(file=file)

        except Exception as e:
            print(f"Error rendering bank card: {e}")
            await interaction.followup.send(f"❌ Bank error: Your balance is **{balance:,} {coin_name}**.", ephemeral=False)

        finally:
            release_memory()

    @app_commands.command(name="add_coins", description="Add coins to a user's bank account.")
    @app_commands.describe(user="The user to give coins to", amount="The amount of coins to give")
    @app_commands.checks.has_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3
                """,
                interaction.guild.id, user.id, amount
            )

            coin_record = await connection.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                interaction.guild.id
            )
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        await interaction.response.send_message(f"Successfully added **{amount:,} {coin_name}** to {user.mention}'s account!")

    @app_commands.command(name="set_currency_name", description="Set the custom name for your server's currency.")
    @app_commands.describe(name="The new name for the currency (e.g., VibeCoins)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setname(self, interaction: discord.Interaction, name: str):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO server_settings (guild_id, coin_name)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE 
                SET coin_name = $2
                """,
                interaction.guild.id, name
            )
            
        await interaction.response.send_message(
            f"Successfully updated the server's currency name to **{name}**!\nAll minigames will now use this name."
        )

    @app_commands.command(name="check_balance", description="[ADMIN] Check a user's bank account balance.")
    @app_commands.describe(user="The user to check the balance of")
    @app_commands.checks.has_permissions(administrator=True)
    async def check(self, interaction: discord.Interaction, user: discord.Member):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            economy_record = await connection.fetchrow(
                "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                interaction.guild.id, user.id
            )
            balance = economy_record['supercoins'] if economy_record else 0

            coin_record = await connection.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                interaction.guild.id
            )
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        await interaction.response.send_message(f"**{user.display_name}** currently has **{balance:,} {coin_name}** in their account.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
