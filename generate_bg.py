from PIL import Image, ImageDraw, ImageFilter
import os

os.makedirs("assets", exist_ok=True)

width = 1350
height = 1600 # Max height for ~10 users

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

img.save("assets/leaderboard_bg.png")
print("Saved assets/leaderboard_bg.png")
