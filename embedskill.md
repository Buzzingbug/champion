# Glassmorphic Image Leaderboard Playbook (Embed Skill)

This document outlines the architecture, settings, and code patterns required to replace standard Discord text embeds with stunning, high-resolution, glassmorphic image-based leaderboards using Python's Pillow (`PIL`).

## 1. The Core Philosophy
Discord text embeds are limited and often break formatting on mobile. By rendering a complete image in-memory and sending it as an attachment, you gain 100% control over typography, gradients, spacing, and avatar masking.

### Key Learnings from Production
* **The Font Scaling Trick:** If you generate an image that perfectly fits Discord's chat width (~400px), standard fonts will look tiny. Instead, generate a **massive canvas (e.g., 1350px wide)** and use absolutely gigantic fonts (60pt - 85pt). When Discord automatically scales the 1350px image down to fit the chat, the gigantic text scales down to look incredibly crisp and highly legible on both Desktop and Mobile.
* **Linux Font Fallbacks:** Cloud hosts (Railway, Heroku, Ubuntu) **do not** have Windows fonts like `arial.ttf`. If you use them, Pillow will silently fail and load a microscopic, unscalable default bitmap font. Always bundle a `.ttf` file (e.g., `Roboto-Bold.ttf`) in your repo's `assets/` folder and load it using absolute/relative paths.
* **CPU Assassination (The Blur Problem):** Drawing gradients and applying `ImageFilter.GaussianBlur(120)` on a 1350px image is extremely CPU-intensive. Doing this dynamically on every command run will max out a 1vCPU cloud server instantly.
  * **Solution:** Generate the blurred background layer ONCE via a script, save it as `bg.png`, and load that static image in the command. 
* **Network Latency (The Loop Problem):** Fetching 10 user avatars in a standard `for` loop takes ~3-5 seconds because you await each HTTP request sequentially.
  * **Solution:** Always use `asyncio.gather(*tasks)` to fetch all 10 avatars from Discord's CDN simultaneously in parallel.

## 2. Design Settings

* **Canvas Width:** `1350px`
* **Canvas Height:** Dynamic based on rows `250 + (len(users) * 110)`
* **Base Background:** Dark modern blue/grey `#0f0f12` `(15, 15, 18, 255)`
* **Glowing Blobs:** 
  * Top Left (Gold): `(251, 236, 144, 180)`
  * Bottom Right (Crimson/Red): `(202, 103, 92, 160)`
* **Glass Card:** White with 15 opacity `(255, 255, 255, 15)`, corner radius `30`.
* **Typography:**
  * Title: `Roboto-Bold.ttf`, Size `85`, Color: Pure White (Contrast against gold)
  * Headers: `Roboto-Bold.ttf`, Size `28`, Color: Muted Grey
  * Data Names: `Roboto-Bold.ttf`, Size `42`, Color: Pure White
  * Data Stats: `Roboto-Regular.ttf`, Size `40`, Color: Soft Blue/Grey `(200, 210, 220)` (Allows names to pop)

## 3. Implementation Boilerplate

### A. Pre-generating the Background (Run Once)
```python
from PIL import Image, ImageDraw, ImageFilter

width, height = 1350, 1600
base = Image.new('RGBA', (width, height), (15, 15, 18, 255))

# Draw glowing blobs
blobs = Image.new('RGBA', (width, height), (0, 0, 0, 0))
blob_draw = ImageDraw.Draw(blobs)
blob_draw.ellipse((-100, -100, 600, 600), fill=(251, 236, 144, 180)) 
blob_draw.ellipse((width-600, height-600, width+100, height+100), fill=(202, 103, 92, 160)) 
blobs = blobs.filter(ImageFilter.GaussianBlur(120))
img = Image.alpha_composite(base, blobs)

# Draw Glass Card
glass = Image.new('RGBA', (width, height), (0, 0, 0, 0))
glass_draw = ImageDraw.Draw(glass)
glass_draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=30, fill=(255, 255, 255, 15), outline=(255, 255, 255, 60), width=2)
img = Image.alpha_composite(img, glass)

img.save("assets/leaderboard_bg.png")
```

### B. Dynamic Rendering Command (Production Code)
```python
import discord, io, aiohttp, asyncio
from PIL import Image, ImageDraw, ImageFont

async def fetch_avatar(user, session):
    # Use size=128 to save network ingress bandwidth!
    url = str(user.display_avatar.replace(size=128, format="png"))
    async with session.get(url) as resp:
        if resp.status == 200:
            return Image.open(io.BytesIO(await resp.read())).convert("RGBA")
    # Fallback transparent image
    return Image.new("RGBA", (128, 128), (0,0,0,0))

async def generate_leaderboard(bot, users):
    width = 1350
    height = 250 + (len(users) * 110)
    
    # 1. Load Static Cached Background (Zero CPU cost)
    bg = Image.open("assets/leaderboard_bg.png").convert("RGBA")
    img = bg.crop((0, 0, width, height))
    draw = ImageDraw.Draw(img)

    # 2. Load Bundled Fonts (Failsafe for Linux)
    font_title = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 85)
    font_bold = ImageFont.truetype("assets/fonts/Roboto-Bold.ttf", 42)

    # 3. Parallel Avatar Fetching (Zero Network lag)
    async with aiohttp.ClientSession() as session:
        async def get_av(u):
            user_obj = bot.get_user(u['id']) or await bot.fetch_user(u['id'])
            return await fetch_avatar(user_obj, session)
        
        avatars = await asyncio.gather(*[get_av(u) for u in users])

    # 4. Render Rows
    y_offset = 230
    for i, (user, avatar_img) in enumerate(zip(users, avatars)):
        # Circular Mask Avatar
        avatar_img = avatar_img.resize((70, 70))
        mask = Image.new("L", (70, 70), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 70, 70), fill=255)
        img.paste(avatar_img, (110, y_offset + 10), mask)
        
        # Draw Text
        draw.text((200, y_offset + 20), user['name'], fill=(255,255,255), font=font_bold)
        
        y_offset += 110

    # 5. Output to Discord File
    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="leaderboard.png")
```
