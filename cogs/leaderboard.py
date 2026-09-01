import discord
from discord import app_commands
from discord.ext import commands
import io
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

async def fetch_avatar(user: discord.User, session: aiohttp.ClientSession) -> Image.Image:
    try:
        if user.display_avatar:
            async with session.get(str(user.display_avatar.replace(size=128, format="png"))) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except:
        pass
    # Fallback to gray circle
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 128, 128), fill=(100, 100, 100, 255))
    return img

async def generate_global_leaderboard_image(bot, guild, page):
    limit = 10
    offset = (page - 1) * limit
    
    async with bot.db_pool.acquire() as connection:
        coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", guild.id)
        coin_name = coin_record['coin_name'].upper() if coin_record else 'SUPERCOINS'
        
        users = await connection.fetch(
            "SELECT user_id, supercoins, lifetime_channel, lifetime_category, lifetime_games FROM economy WHERE guild_id = $1 ORDER BY supercoins DESC LIMIT $2 OFFSET $3",
            guild.id, limit + 1, offset
        )
        has_more = len(users) > limit
        users = users[:limit]
        
    width, height = 1200, 200 + (len(users) * 80) if users else 400
    
    # Try to load the Aurum bank image as background
    bg_path = "assets/aurum_bank.jpg"
    if os.path.exists(bg_path):
        img = Image.open(bg_path).convert('RGBA')
        # Resize and crop
        aspect = img.width / img.height
        target_aspect = width / height
        if aspect > target_aspect:
            new_width = int(target_aspect * img.height)
            off = (img.width - new_width) / 2
            img = img.crop((off, 0, img.width - off, img.height))
        else:
            new_height = int(img.width / target_aspect)
            off = (img.height - new_height) / 2
            img = img.crop((0, off, img.width, img.height - off))
        img = img.resize((width, height))
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.4)
    else:
        img = Image.new('RGBA', (width, height), color=(20, 20, 24))

    # Glass overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.rectangle([(20, 20), (width - 20, height - 20)], fill=(0, 0, 0, 180), outline=(241, 196, 15, 120), width=2)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_main = ImageFont.truetype("arial.ttf", 24)
        font_bold = ImageFont.truetype("arial.ttf", 26)
    except:
        font_title = font_header = font_main = font_bold = ImageFont.load_default()

    # Draw Title
    draw.text((40, 40), "🏆 ECONOMY LEADERBOARD", fill=(241, 196, 15), font=font_title)
    
    # Draw Columns
    cols = {
        "Rank": 40,
        "User": 180,
        "Channel Earned": 500,
        "Category Earned": 700,
        "Game Earned": 900,
        f"Total {coin_name}": 1180 # right aligned
    }
    
    y = 110
    draw.text((cols["Rank"], y), "RANK", fill=(150, 150, 150), font=font_header)
    draw.text((cols["User"], y), "NAME", fill=(150, 150, 150), font=font_header)
    draw.text((cols["Channel Earned"], y), "CHANNELS", fill=(150, 150, 150), font=font_header)
    draw.text((cols["Category Earned"], y), "CATEGORIES", fill=(150, 150, 150), font=font_header)
    draw.text((cols["Game Earned"], y), "GAMES", fill=(150, 150, 150), font=font_header)
    
    total_txt = f"TOTAL {coin_name}"
    bbox = draw.textbbox((0,0), total_txt, font=font_header)
    draw.text((cols[f"Total {coin_name}"] - (bbox[2] - bbox[0]), y), total_txt, fill=(241, 196, 15), font=font_header)
    
    draw.line([(40, y + 40), (width - 40, y + 40)], fill=(241, 196, 15, 100), width=2)
    
    y_offset = y + 70
    
    if not users:
        draw.text((40, y_offset), "No users found in the economy yet.", fill=(200, 200, 200), font=font_main)
    else:
        async with aiohttp.ClientSession() as session:
            for i, u in enumerate(users, start=offset + 1):
                # Colors
                if i == 1: color = (241, 196, 15) # Gold
                elif i == 2: color = (189, 195, 199) # Silver
                elif i == 3: color = (205, 127, 50) # Bronze
                else: color = (200, 200, 200)

                # Fetch user
                member = guild.get_member(u['user_id'])
                if member:
                    name = member.display_name
                    avatar_img = await fetch_avatar(member, session)
                else:
                    try:
                        user_obj = await bot.fetch_user(u['user_id'])
                        name = user_obj.name
                        avatar_img = await fetch_avatar(user_obj, session)
                    except:
                        name = f"Unknown ({u['user_id']})"
                        avatar_img = await fetch_avatar(bot.user, session) # fallback
                
                # Rank
                draw.text((cols["Rank"], y_offset + 10), f"#{i}", fill=color, font=font_bold)
                
                # Avatar
                avatar_img = avatar_img.resize((50, 50))
                # Circular mask
                mask = Image.new("L", (50, 50), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 50, 50), fill=255)
                img.paste(avatar_img, (100, y_offset), mask)
                
                # Name
                name_disp = name[:15] + "..." if len(name) > 15 else name
                draw.text((cols["User"], y_offset + 10), name_disp, fill=(255, 255, 255), font=font_bold)
                
                # Stats
                draw.text((cols["Channel Earned"], y_offset + 10), f"{u['lifetime_channel'] or 0:,}", fill=(200, 200, 200), font=font_main)
                draw.text((cols["Category Earned"], y_offset + 10), f"{u['lifetime_category'] or 0:,}", fill=(200, 200, 200), font=font_main)
                draw.text((cols["Game Earned"], y_offset + 10), f"{u['lifetime_games'] or 0:,}", fill=(200, 200, 200), font=font_main)
                
                # Total
                total_val = f"{u['supercoins']:,}"
                bbox = draw.textbbox((0,0), total_val, font=font_bold)
                draw.text((cols[f"Total {coin_name}"] - (bbox[2] - bbox[0]), y_offset + 10), total_val, fill=color, font=font_bold)
                
                # Line
                if i < offset + len(users):
                    draw.line([(40, y_offset + 70), (width - 40, y_offset + 70)], fill=(255, 255, 255, 30), width=1)
                
                y_offset += 80

    final_buffer = io.BytesIO()
    img.convert('RGB').save(final_buffer, format="PNG")
    final_buffer.seek(0)
    return discord.File(fp=final_buffer, filename="leaderboard.png"), has_more

class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild, page=1):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild = guild
        self.page = page
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.update_leaderboard(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_leaderboard(interaction)
        
    async def update_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        file, has_more = await generate_global_leaderboard_image(self.bot, self.guild, self.page)
        
        self.children[0].disabled = (self.page == 1)
        self.children[1].disabled = not has_more
        
        # We must edit the message to replace the attachment
        await interaction.edit_original_response(attachments=[file], view=self)

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the detailed Economy Leaderboard.")
    @app_commands.checks.has_permissions(administrator=True)
    async def leaderboard(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            file, has_more = await generate_global_leaderboard_image(self.bot, interaction.guild, 1)
            
            view = LeaderboardView(self.bot, interaction.guild)
            view.children[0].disabled = True
            view.children[1].disabled = not has_more
            
            await interaction.followup.send(file=file, view=view)
        except Exception as e:
            print(f"Leaderboard error: {e}")
            await interaction.followup.send("Failed to generate leaderboard.")

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
