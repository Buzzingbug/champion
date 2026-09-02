import discord
from discord.ext import commands
from discord import app_commands
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont

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
    return Image.new('RGBA', (256, 256), (0, 0, 0, 0))

async def generate_bento_profile(bot, user, guild):
    width, height = 1200, 800
    
    # 1. Base Background (reuse leaderboard bg)
    try:
        bg = Image.open("assets/leaderboard_bg.png").convert("RGBA")
        img = bg.crop((0, 0, width, height))
    except:
        img = Image.new('RGBA', (width, height), (15, 15, 18, 255))
        
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 2. Fonts
    try:
        font_huge = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 90)
        font_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 60)
        font_subtitle = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 40)
        font_stat_val = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 70)
        font_stat_lbl = ImageFont.truetype("assets/fonts/Roboto-Regular.ttf", 35)
    except:
        font_huge = font_title = font_subtitle = font_stat_val = font_stat_lbl = ImageFont.load_default()

    # 3. Fetch data
    messages = media = words = night = voice = current_streak = longest_streak = 0
    if bot.db_pool:
        async with bot.db_pool.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT * FROM user_activity WHERE user_id = $1 AND guild_id = $2",
                user.id, guild.id
            )
            if record:
                messages = record['messages_sent']
                media = record['media_shared']
                words = record['words_typed']
                night = record['night_owl_msgs']
                voice = record['voice_minutes']
                current_streak = record['current_streak']
                longest_streak = record['longest_streak']

    # 4. Calculate Persona
    persona = "The Newcomer"
    if voice > (messages * 2) and voice > 10:
        persona = "The Broadcaster"
    elif night > (messages * 0.3) and night > 50:
        persona = "The Night Owl"
    elif media > (messages * 0.2) and media > 20:
        persona = "The Media Mogul"
    elif messages > 100 and words > (messages * 15):
        persona = "The Novelist"
    elif messages > 10:
        persona = "The Regular"
        
    # Helper to draw glass box
    def draw_glass_box(box):
        draw.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 15), outline=(255, 255, 255, 40), width=2)
        
    # Box 1: User Profile (Top Left) (x: 40, y: 40, w: 740, h: 340)
    draw_glass_box([40, 40, 780, 380])
    
    # Avatar
    async with aiohttp.ClientSession() as session:
        avatar_img = await fetch_avatar(user, session)
    avatar_img = avatar_img.resize((240, 240))
    mask = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 240, 240), fill=255)
    img.paste(avatar_img, (80, 90), mask)
    
    # Name
    name = user.display_name[:12] + "..." if len(user.display_name) > 12 else user.display_name
    draw.text((360, 130), name, fill=(255, 255, 255), font=font_title)
    
    # Persona
    draw.text((360, 220), f"Persona: {persona}", fill=(251, 236, 144), font=font_subtitle)
    
    # Box 2: Streak (Top Right) (x: 820, y: 40, w: 340, h: 340)
    draw_glass_box([820, 40, 1160, 380])
    draw.text((860, 80), "Current Streak", fill=(200, 210, 220), font=font_stat_lbl)
    
    # Center streak value
    sv = f"{current_streak} Days"
    bbox = draw.textbbox((0,0), sv, font=font_huge)
    tw = bbox[2] - bbox[0]
    draw.text((820 + (340 - tw)//2, 180), sv, fill=(251, 100, 100) if current_streak > 3 else (255,255,255), font=font_huge)
    
    # Box 3: Messages (Bottom Left)
    draw_glass_box([40, 420, 386, 760])
    draw.text((80, 470), "Messages", fill=(200, 210, 220), font=font_stat_lbl)
    draw.text((80, 550), f"{messages:,}", fill=(255, 255, 255), font=font_stat_val)

    # Box 4: Media (Bottom Center)
    draw_glass_box([426, 420, 772, 760])
    draw.text((466, 470), "Media Shared", fill=(200, 210, 220), font=font_stat_lbl)
    draw.text((466, 550), f"{media:,}", fill=(255, 255, 255), font=font_stat_val)

    # Box 5: Voice Time (Bottom Right)
    draw_glass_box([812, 420, 1160, 760])
    draw.text((852, 470), "Voice (Mins)", fill=(200, 210, 220), font=font_stat_lbl)
    draw.text((852, 550), f"{voice:,}", fill=(255, 255, 255), font=font_stat_val)

    final_buffer = io.BytesIO()
    img.convert('RGB').save(final_buffer, format="PNG")
    final_buffer.seek(0)
    return discord.File(fp=final_buffer, filename="bento_profile.png")


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your stunning Activity Bento Box.")
    @app_commands.describe(user="The user to view the profile for.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        if not user:
            user = interaction.user
            
        await interaction.response.defer()
        
        try:
            file = await generate_bento_profile(self.bot, user, interaction.guild)
            await interaction.followup.send(file=file)
        except Exception as e:
            print(f"Profile error: {e}")
            await interaction.followup.send("Failed to generate profile.")

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
