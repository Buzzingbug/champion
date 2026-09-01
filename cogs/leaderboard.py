import discord
from discord import app_commands
from discord.ext import commands
import io
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter

async def fetch_avatar(user: discord.User, session: aiohttp.ClientSession) -> Image.Image:
    try:
        if user.display_avatar:
            async with session.get(str(user.display_avatar.replace(size=256, format="png"))) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except:
        pass
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 256, 256), fill=(100, 100, 100, 255))
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
        
    width = 1200
    height = 250 + (len(users) * 110) if users else 450
    
    # Base dark modern background
    base = Image.new('RGBA', (width, height), (15, 15, 18, 255))

    # Draw glowing blobs
    blobs = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    blob_draw = ImageDraw.Draw(blobs)
    blob_draw.ellipse((-100, -100, 600, 600), fill=(251, 236, 144, 180)) # fbec90 top left
    blob_draw.ellipse((width-600, height-600, width+100, height+100), fill=(202, 103, 92, 160)) # ca675c bottom right
    blobs = blobs.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(base, blobs)

    # Draw Glass Card
    glass = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    glass_draw = ImageDraw.Draw(glass)
    glass_draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=30, fill=(255, 255, 255, 15), outline=(255, 255, 255, 60), width=2)
    img = Image.alpha_composite(img, glass)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 60)
        font_header = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 30)
        font_main = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 40)
        font_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 42)
    except Exception as e:
        print(f"Failed to load fonts: {e}")
        font_title = font_header = font_main = font_bold = ImageFont.load_default()

    # Bot Avatar
    async with aiohttp.ClientSession() as session:
        bot_av = await fetch_avatar(bot.user, session)
    bot_av = bot_av.resize((90, 90))
    mask = Image.new("L", (90, 90), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 90, 90), fill=255)
    img.paste(bot_av, (40, 40), mask)

    # Title
    draw.text((150, 60), "ECONOMY LEADERBOARD", fill=(255, 255, 255), font=font_title)
    
    # Draw Columns
    cols = {
        "Rank": 40,
        "User": 200,
        "Channels": 520,
        "Categories": 750,
        "Games": 1000,
        f"Total {coin_name}": 1160 # right aligned
    }
    
    y = 160
    draw.text((cols["Rank"], y), "RNK", fill=(220, 220, 220), font=font_header)
    draw.text((cols["User"], y), "NAME", fill=(220, 220, 220), font=font_header)
    draw.text((cols["Channels"], y), "CHANNELS", fill=(220, 220, 220), font=font_header)
    draw.text((cols["Categories"], y), "CATEGORIES", fill=(220, 220, 220), font=font_header)
    draw.text((cols["Games"], y), "GAMES", fill=(220, 220, 220), font=font_header)
    
    total_txt = f"TOTAL {coin_name}"
    bbox = draw.textbbox((0,0), total_txt, font=font_header)
    draw.text((cols[f"Total {coin_name}"] - (bbox[2] - bbox[0]), y), total_txt, fill=(251, 236, 144), font=font_header)
    
    draw.line([(40, y + 50), (width - 40, y + 50)], fill=(255, 255, 255, 100), width=2)
    
    y_offset = y + 70
    
    if not users:
        draw.text((40, y_offset + 30), "No users found in the economy yet.", fill=(255, 255, 255), font=font_main)
    else:
        async with aiohttp.ClientSession() as session:
            for i, u in enumerate(users, start=offset + 1):
                # Colors
                if i == 1: color = (251, 236, 144) # Gold
                elif i == 2: color = (189, 195, 199) # Silver
                elif i == 3: color = (205, 127, 50) # Bronze
                else: color = (255, 255, 255)

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
                draw.text((cols["Rank"], y_offset + 20), f"#{i}", fill=color, font=font_bold)
                
                # Avatar
                avatar_img = avatar_img.resize((70, 70))
                # Circular mask
                mask = Image.new("L", (70, 70), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 70, 70), fill=255)
                img.paste(avatar_img, (110, y_offset + 10), mask)
                
                # Name
                name_disp = name[:10] + "..." if len(name) > 10 else name
                draw.text((cols["User"], y_offset + 20), name_disp, fill=(255, 255, 255), font=font_bold)
                
                # Stats
                draw.text((cols["Channels"], y_offset + 20), f"{u['lifetime_channel'] or 0:,}", fill=(255, 255, 255), font=font_main)
                draw.text((cols["Categories"], y_offset + 20), f"{u['lifetime_category'] or 0:,}", fill=(255, 255, 255), font=font_main)
                draw.text((cols["Games"], y_offset + 20), f"{u['lifetime_games'] or 0:,}", fill=(255, 255, 255), font=font_main)
                
                # Total
                total_val = f"{u['supercoins']:,}"
                bbox = draw.textbbox((0,0), total_val, font=font_bold)
                draw.text((cols[f"Total {coin_name}"] - (bbox[2] - bbox[0]), y_offset + 20), total_val, fill=color, font=font_bold)
                
                # Line
                if i < offset + len(users):
                    draw.line([(40, y_offset + 100), (width - 40, y_offset + 100)], fill=(255, 255, 255, 40), width=1)
                
                y_offset += 110

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
