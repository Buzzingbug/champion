import discord
from discord import app_commands
from discord.ext import commands
import io
import random
from PIL import Image, ImageDraw, ImageFont
import re

class PuzzleModal(discord.ui.Modal, title='Solve Puzzle'):
    solution_input = discord.ui.TextInput(
        label='Enter the 9 numbers in order',
        style=discord.TextStyle.short,
        placeholder='e.g. 529147368',
        required=True,
        max_length=20
    )

    def __init__(self, db_pool, message_id: int):
        super().__init__()
        self.db_pool = db_pool
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction):
        user_input = self.solution_input.value.strip().replace(" ", "").replace(",", "")
        
        async with self.db_pool.acquire() as connection:
            # Fetch the puzzle
            record = await connection.fetchrow(
                "SELECT guild_id, correct_order FROM active_puzzles WHERE message_id = $1",
                self.message_id
            )

            if not record:
                await interaction.response.send_message("This puzzle has already been solved or no longer exists!", ephemeral=True)
                return

            correct_order = record['correct_order'].replace(" ", "")

            if user_input == correct_order:
                # Solved!
                # Fetch reward
                config = await connection.fetchrow(
                    "SELECT reward_amount FROM puzzle_configs WHERE guild_id = $1",
                    record['guild_id']
                )
                reward = config['reward_amount'] if config else 100
                
                coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", record['guild_id'])
                coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

                # Award coins
                await connection.execute(
                    """
                    INSERT INTO economy (guild_id, user_id, supercoins) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id, user_id) 
                    DO UPDATE SET supercoins = economy.supercoins + $3
                    """,
                    interaction.guild.id, interaction.user.id, reward
                )

                # Delete puzzle
                await connection.execute(
                    "DELETE FROM active_puzzles WHERE message_id = $1",
                    self.message_id
                )

                await interaction.response.send_message(f"🎉 **Correct!** You've solved the puzzle and earned **{reward} {coin_name}**!")
                
                # Update original message
                try:
                    msg = await interaction.channel.fetch_message(self.message_id)
                    embed = msg.embeds[0]
                    embed.color = discord.Color.green()
                    embed.description = f"**Solved by {interaction.user.mention}!**\n\nThe correct sequence was: `{correct_order}`"
                    await msg.edit(embed=embed, view=None)
                except Exception:
                    pass

            else:
                await interaction.response.send_message("Incorrect order! Try again.", ephemeral=True)

class PuzzleView(discord.ui.View):
    def __init__(self, db_pool):
        super().__init__(timeout=None) # Persists forever
        self.db_pool = db_pool

    @discord.ui.button(label="Solve Puzzle", style=discord.ButtonStyle.success, emoji="🧩", custom_id="puzzle_solve_btn")
    async def solve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PuzzleModal(self.db_pool, interaction.message.id))

class PuzzleCog(commands.GroupCog, group_name="puzzle"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure the Jigsaw Puzzle feature for this server.")
    @app_commands.describe(
        channel="The channel where puzzles will be posted",
        reward="Amount of Supercoins given to the solver"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, reward: int):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute(
                """
                INSERT INTO puzzle_configs (guild_id, channel_id, reward_amount)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2, reward_amount = $3
                """,
                interaction.guild.id, channel.id, reward
            )
            
        await interaction.response.send_message(
            f"Successfully configured **Jigsaw Puzzles**!\n"
            f"Channel: {channel.mention}\n"
            f"Reward: **{reward} {coin_name}**"
        )

    @app_commands.command(name="submit", description="Submit an image to be scrambled into a puzzle.")
    @app_commands.describe(
        image="The image to scramble",
        title="Optional title for the puzzle"
    )
    async def submit(self, interaction: discord.Interaction, image: discord.Attachment, title: str = "Jigsaw Puzzle!"):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        # Fetch config
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        if not config:
            await interaction.response.send_message("Puzzles are not configured here. Admin needs to run `/puzzle setup`.", ephemeral=True)
            return

        if interaction.channel.id != config['channel_id']:
            await interaction.response.send_message(f"You can only submit puzzles in <#{config['channel_id']}>.", ephemeral=True)
            return
            
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("Attachment must be a valid image.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            image_bytes = await image.read()
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Crop to square
            min_dim = min(img.width, img.height)
            left = (img.width - min_dim) / 2
            top = (img.height - min_dim) / 2
            right = (img.width + min_dim) / 2
            bottom = (img.height + min_dim) / 2
            
            img_square = img.crop((left, top, right, bottom))
            
            # Resize to 600x600 so each tile is 200x200
            img_resized = img_square.resize((600, 600))
            
            # Slice into 9 pieces
            pieces = []
            for row in range(3):
                for col in range(3):
                    box = (col * 200, row * 200, (col + 1) * 200, (row + 1) * 200)
                    pieces.append(img_resized.crop(box))
            
            # Shuffle indices
            indices = list(range(9))
            random.shuffle(indices)
            
            # correct_order represents which slot (1-9) holds piece 0, piece 1, etc.
            correct_sequence = []
            for orig_idx in range(9):
                slot_idx = indices.index(orig_idx)
                correct_sequence.append(str(slot_idx + 1))
            
            # Try to load a large font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except IOError:
                try:
                    font = ImageFont.load_default(size=60)
                except TypeError:
                    font = ImageFont.load_default()

            # Create the scrambled image
            scrambled = Image.new("RGB", (600, 600))
            for i in range(9):
                row = i // 3
                col = i % 3
                piece = pieces[indices[i]].copy()
                
                # Draw number on the piece
                draw = ImageDraw.Draw(piece)
                # Black rectangle for visibility
                draw.rectangle([(5, 5), (45, 45)], fill="black")
                draw.text((15, 10), str(i + 1), fill="white", font=font)
                
                scrambled.paste(piece, (col * 200, row * 200))
                
            # Draw grid lines
            draw_scrambled = ImageDraw.Draw(scrambled)
            for x in [200, 400]:
                draw_scrambled.line([(x, 0), (x, 600)], fill="black", width=3)
            for y in [200, 400]:
                draw_scrambled.line([(0, y), (600, y)], fill="black", width=3)
                
            final_buffer = io.BytesIO()
            scrambled.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            
            file = discord.File(fp=final_buffer, filename="scrambled.png")
            
            embed = discord.Embed(
                title=title,
                description=f"**Submitted by {interaction.user.mention}**\n\nClick the button below to solve! You need to enter the 9 numbers in the correct order to win **{config['reward_amount']} {coin_name}**.",
                color=discord.Color.gold()
            )
            embed.set_image(url="attachment://scrambled.png")
            
            view = PuzzleView(self.bot.db_pool)
            
            msg = await interaction.channel.send(embed=embed, file=file, view=view)
            
            # Save active puzzle
            async with self.bot.db_pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO active_puzzles (message_id, guild_id, correct_order) VALUES ($1, $2, $3)",
                    msg.id, interaction.guild.id, "".join(correct_sequence)
                )
                
            await interaction.followup.send("Puzzle created successfully!")
            
        except Exception as e:
            print(f"Error creating puzzle: {e}")
            await interaction.followup.send("An error occurred while making the puzzle.")


async def setup(bot):
    await bot.add_cog(PuzzleCog(bot))
