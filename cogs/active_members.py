import discord
from discord import app_commands
from discord.ext import commands
import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont

async def fetch_avatar(user: discord.User, session: aiohttp.ClientSession) -> Image.Image:
    try:
        if user.display_avatar:
            async with session.get(str(user.display_avatar.replace(size=128, format="png"))) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except:
        pass
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 128, 128), fill=(100, 100, 100, 255))
    return img

def calculate_level(xp):
    level = 1
    while True:
        req = int(50 * level * (level + 1))
        if xp < req:
            return level
        level += 1
        if level >= 100:
            return 100

async def generate_active_members_image(bot, guild, page):
    limit = 10
    offset = (page - 1) * limit
    
    async with bot.db_pool.acquire() as connection:
        users = await connection.fetch("""
            SELECT user_id, messages_sent, media_shared, voice_minutes, current_streak,
                   (COALESCE(messages_sent, 0) * 10 + COALESCE(media_shared, 0) * 25 + COALESCE(voice_minutes, 0) * 5) AS total_xp
            FROM user_activity
            WHERE guild_id = $1
            ORDER BY (COALESCE(messages_sent, 0) * 10 + COALESCE(media_shared, 0) * 25 + COALESCE(voice_minutes, 0) * 5) DESC
            LIMIT $2 OFFSET $3
        """, guild.id, limit + 1, offset)
        
        has_more = len(users) > limit
        users = users[:limit]
        
    width = 1350
    height = 250 + (len(users) * 110) if users else 450
    
    try:
        bg = Image.open("assets/leaderboard_bg.png").convert("RGBA")
        img = bg.crop((0, 0, width, height))
    except:
        img = Image.new('RGBA', (width, height), (15, 15, 18, 255))

    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 80)
        font_header = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 28)
        font_main = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 40)
        font_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 42)
        font_lvl = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 36)
    except Exception as e:
        print(f"Failed to load fonts: {e}")
        font_title = font_header = font_main = font_bold = font_lvl = ImageFont.load_default()

    # Center Title
    title_text = "ACTIVITY LEADERBOARD"
    bbox = draw.textbbox((0,0), title_text, font=font_title)
    title_w = bbox[2] - bbox[0]
    start_x = (width - title_w) // 2
    draw.text((start_x, 40), title_text, fill=(255, 255, 255), font=font_title)
    
    # Column mapping
    cols = {
        "Rank": 40,
        "User": 200,
        "Level": 560,
        "Messages": 740,
        "Voice": 960,
        "XP": 1300
    }
    
    # Headers
    y_offset = 150
    draw.text((cols["Rank"], y_offset), "RANK", fill=(180, 180, 180), font=font_header)
    draw.text((cols["User"], y_offset), "MEMBER", fill=(180, 180, 180), font=font_header)
    draw.text((cols["Level"], y_offset), "LEVEL", fill=(180, 180, 180), font=font_header)
    draw.text((cols["Messages"], y_offset), "MESSAGES", fill=(180, 180, 180), font=font_header)
    draw.text((cols["Voice"], y_offset), "VOICE TIME", fill=(180, 180, 180), font=font_header)
    
    bbox = draw.textbbox((0,0), "TOTAL XP", font=font_header)
    draw.text((cols["XP"] - (bbox[2] - bbox[0]), y_offset), "TOTAL XP", fill=(251, 236, 144), font=font_header)
    
    # Line
    draw.line([(40, y_offset + 50), (width - 40, y_offset + 50)], fill=(255, 255, 255, 60), width=2)
    y_offset += 70

    if not users:
        draw.text((40, y_offset + 30), "No active members recorded yet.", fill=(255, 255, 255), font=font_main)
    else:
        async with aiohttp.ClientSession() as session:
            async def get_user_data(u):
                member = guild.get_member(u['user_id'])
                if member:
                    name = member.display_name
                    av = await fetch_avatar(member, session)
                else:
                    try:
                        user_obj = await bot.fetch_user(u['user_id'])
                        name = user_obj.name
                        av = await fetch_avatar(user_obj, session)
                    except:
                        name = f"Unknown ({u['user_id']})"
                        av = await fetch_avatar(bot.user, session)
                return name, av

            tasks = [get_user_data(u) for u in users]
            user_results = await asyncio.gather(*tasks)

            for i, (u, (name, avatar_img)) in enumerate(zip(users, user_results), start=offset + 1):
                # Colors
                if i == 1: color = (251, 236, 144) # Gold
                elif i == 2: color = (189, 195, 199) # Silver
                elif i == 3: color = (205, 127, 50) # Bronze
                else: color = (220, 220, 220)
                
                # Rank
                draw.text((cols["Rank"] + 10, y_offset + 20), f"{i}", fill=color, font=font_bold)
                
                # Avatar
                avatar_img = avatar_img.resize((70, 70))
                mask = Image.new("L", (70, 70), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 70, 70), fill=255)
                img.paste(avatar_img, (110, y_offset + 10), mask)
                
                # Name
                name_disp = name[:10] + "..." if len(name) > 10 else name
                draw.text((cols["User"], y_offset + 20), name_disp, fill=(255, 255, 255), font=font_bold)
                
                # Level
                user_xp = u['total_xp'] or 0
                lvl = calculate_level(user_xp)
                draw.text((cols["Level"], y_offset + 22), f"LVL {lvl}", fill=(251, 236, 144), font=font_lvl)
                
                # Messages
                stat_color = (200, 210, 220)
                draw.text((cols["Messages"], y_offset + 20), f"{u['messages_sent'] or 0:,}", fill=stat_color, font=font_main)
                
                # Voice
                v_mins = u['voice_minutes'] or 0
                if v_mins >= 60:
                    v_txt = f"{v_mins // 60}h {v_mins % 60}m"
                else:
                    v_txt = f"{v_mins}m"
                draw.text((cols["Voice"], y_offset + 20), v_txt, fill=stat_color, font=font_main)
                
                # Total XP
                xp_val = f"{user_xp:,} XP"
                bbox = draw.textbbox((0,0), xp_val, font=font_bold)
                draw.text((cols["XP"] - (bbox[2] - bbox[0]), y_offset + 20), xp_val, fill=color, font=font_bold)
                
                # Row separator
                if i < offset + len(users):
                    draw.line([(40, y_offset + 100), (width - 40, y_offset + 100)], fill=(255, 255, 255, 40), width=1)
                
                y_offset += 110

    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="active_members.png"), has_more

class ActiveMembersView(discord.ui.View):
    def __init__(self, bot, guild, page=1):
        super().__init__(timeout=600)
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
        file, has_more = await generate_active_members_image(self.bot, self.guild, self.page)
        
        self.children[0].disabled = (self.page == 1)
        self.children[1].disabled = not has_more
        
        await interaction.edit_original_response(attachments=[file], view=self)

class ActiveMembersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activemembers", description="View the most active members and top leveling ranks.")
    async def activemembers(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            file, has_more = await generate_active_members_image(self.bot, interaction.guild, 1)
            
            view = ActiveMembersView(self.bot, interaction.guild)
            view.children[0].disabled = True
            view.children[1].disabled = not has_more
            
            await interaction.followup.send(file=file, view=view)
        except Exception as e:
            print(f"Active members error: {e}")
            await interaction.followup.send("Failed to generate active members leaderboard.")

async def setup(bot):
    await bot.add_cog(ActiveMembersCog(bot))
