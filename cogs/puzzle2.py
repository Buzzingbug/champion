import discord
from discord import app_commands
from discord.ext import commands, tasks
import io
import random
from PIL import Image, ImageDraw
import time

class SlidingPuzzleView(discord.ui.View):
    def __init__(self, db_pool, puzzle_message_id: int, original_author_id: int, original_msg_jump_url: str, pieces: list, board: list, empty_idx: int, reward: int, guild_id: int, channel_id: int, coin_name: str):
        super().__init__(timeout=900) # 15 minutes timeout
        self.db_pool = db_pool
        self.puzzle_message_id = puzzle_message_id
        self.original_author_id = original_author_id
        self.original_msg_jump_url = original_msg_jump_url
        self.pieces = pieces
        self.board = board
        self.empty_idx = empty_idx
        self.reward = reward
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.coin_name = coin_name

    def generate_image(self):
        # Create a new blank 600x600 image
        img = Image.new("RGB", (600, 600), "black")
        for i in range(9):
            piece_id = self.board[i]
            if piece_id == 8: # Empty slot is black
                continue
            
            row = i // 3
            col = i % 3
            img.paste(self.pieces[piece_id], (col * 200, row * 200))
            
        # Draw grid lines
        draw = ImageDraw.Draw(img)
        for x in [200, 400]:
            draw.line([(x, 0), (x, 600)], fill="white", width=2)
        for y in [200, 400]:
            draw.line([(0, y), (600, y)], fill="white", width=2)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return discord.File(fp=buffer, filename="puzzle.jpg")

    async def move_empty(self, interaction: discord.Interaction, new_empty_idx: int):
        # Swap the piece at new_empty_idx with the empty_idx
        self.board[self.empty_idx], self.board[new_empty_idx] = self.board[new_empty_idx], self.board[self.empty_idx]
        self.empty_idx = new_empty_idx
        
        # Check if solved
        if self.board == [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            # Disable buttons
            for child in self.children:
                child.disabled = True
            
            # Award coins
            async with self.db_pool.acquire() as connection:
                # Check if it was already solved by someone else
                record = await connection.fetchrow(
                    "SELECT 1 FROM puzzle2_active WHERE message_id = $1",
                    self.puzzle_message_id
                )
                if not record:
                    await interaction.response.edit_message(content="Someone else already solved this puzzle!", attachments=[], view=None)
                    return
                
                await connection.execute(
                    """
                    INSERT INTO economy (guild_id, user_id, supercoins) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id, user_id) 
                    DO UPDATE SET supercoins = economy.supercoins + $3
                    """,
                    self.guild_id, interaction.user.id, self.reward
                )
                
                # Delete active puzzle
                await connection.execute(
                    "DELETE FROM puzzle2_active WHERE message_id = $1",
                    self.puzzle_message_id
                )
                
            # Edit original message
            try:
                bot = interaction.client
                channel = bot.get_channel(self.channel_id)
                if not channel:
                    channel = await bot.fetch_channel(self.channel_id)
                msg = await channel.fetch_message(self.puzzle_message_id)
                embed = msg.embeds[0]
                embed.color = discord.Color.green()
                embed.description = f"**Solved by {interaction.user.mention}!**\nThey earned **{self.reward} {self.coin_name}**."
                await msg.edit(embed=embed, view=None)
            except Exception as e:
                print(f"Failed to edit original msg: {e}")
                
            final_file = self.generate_image()
            await interaction.response.edit_message(
                content=f"🎉 **Congratulations!** You solved the puzzle and earned {self.reward} {self.coin_name}!\n[View Original Message]({self.original_msg_jump_url})",
                attachments=[final_file],
                view=self
            )
        else:
            # Not solved, just update image
            file = self.generate_image()
            await interaction.response.edit_message(attachments=[file], view=self)

    @discord.ui.button(emoji="⬆️", style=discord.ButtonStyle.primary, row=0)
    async def up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.empty_idx >= 3:
            await self.move_empty(interaction, self.empty_idx - 3)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⬇️", style=discord.ButtonStyle.primary, row=0)
    async def down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.empty_idx <= 5:
            await self.move_empty(interaction, self.empty_idx + 3)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary, row=1)
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.empty_idx % 3 != 0:
            await self.move_empty(interaction, self.empty_idx - 1)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary, row=1)
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.empty_idx % 3 != 2:
            await self.move_empty(interaction, self.empty_idx + 1)
        else:
            await interaction.response.defer()

class StartPuzzleView(discord.ui.View):
    def __init__(self, db_pool):
        super().__init__(timeout=None)
        self.db_pool = db_pool

    @discord.ui.button(label="Play in DMs", style=discord.ButtonStyle.success, emoji="🎮", custom_id="play_sliding_puzzle")
    async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        async with self.db_pool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT image_data FROM puzzle2_active WHERE message_id = $1",
                interaction.message.id
            )
            
            if not record:
                await interaction.followup.send("This puzzle has already been solved or does not exist!", ephemeral=True)
                return
                
            config = await connection.fetchrow(
                "SELECT reward_amount FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            reward = config['reward_amount'] if config else 100
            
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        image_data = record['image_data']
        img = Image.open(io.BytesIO(image_data))
        
        # Slice into 9 pieces
        pieces = []
        for row in range(3):
            for col in range(3):
                box = (col * 200, row * 200, (col + 1) * 200, (row + 1) * 200)
                pieces.append(img.crop(box))
                
        # Shuffle board starting from solved state to guarantee solvability
        board = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        empty_idx = 8
        
        # Make 60 random valid moves
        for _ in range(60):
            valid_moves = []
            if empty_idx >= 3: valid_moves.append(empty_idx - 3) # UP
            if empty_idx <= 5: valid_moves.append(empty_idx + 3) # DOWN
            if empty_idx % 3 != 0: valid_moves.append(empty_idx - 1) # LEFT
            if empty_idx % 3 != 2: valid_moves.append(empty_idx + 1) # RIGHT
            
            move = random.choice(valid_moves)
            board[empty_idx], board[move] = board[move], board[empty_idx]
            empty_idx = move

        view = SlidingPuzzleView(
            db_pool=self.db_pool,
            puzzle_message_id=interaction.message.id,
            original_author_id=interaction.message.author.id, # Bot's ID or whoever, actually doesn't matter much
            original_msg_jump_url=interaction.message.jump_url,
            pieces=pieces,
            board=board,
            empty_idx=empty_idx,
            reward=reward,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            coin_name=coin_name
        )
        
        file = view.generate_image()
        
        try:
            await interaction.user.send(
                content="**Sliding Puzzle**\nUse the arrows to slide the pieces into the empty black space. Put them back into the original picture to win!",
                file=file,
                view=view
            )
            await interaction.followup.send("I've sent the puzzle to your DMs! Check your messages to play.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I couldn't send you a DM. Please check your privacy settings to ensure you accept DMs from server members!", ephemeral=True)

class Puzzle2Cog(commands.GroupCog, group_name="puzzle2"):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_loop.start()
        self.bot.add_view(StartPuzzleView(self.bot.db_pool))

    def cog_unload(self):
        self.cleanup_loop.cancel()

    @tasks.loop(hours=12)
    async def cleanup_loop(self):
        if not self.bot.db_pool:
            return
            
        # 48 hours ago in milliseconds
        forty_eight_hours_ago_ms = int((time.time() - (48 * 60 * 60)) * 1000)
        max_snowflake = (forty_eight_hours_ago_ms - 1420070400000) << 22

        async with self.bot.db_pool.acquire() as connection:
            try:
                # Select stale puzzles to delete their Discord messages
                stale_puzzles = await connection.fetch(
                    "SELECT message_id, guild_id FROM puzzle2_active WHERE message_id < $1",
                    max_snowflake
                )
                
                for puzzle in stale_puzzles:
                    guild_id = puzzle['guild_id']
                    message_id = puzzle['message_id']
                    
                    # Fetch config to get channel_id
                    config = await connection.fetchrow(
                        "SELECT channel_id FROM puzzle2_configs WHERE guild_id = $1",
                        guild_id
                    )
                    if config:
                        channel = self.bot.get_channel(config['channel_id'])
                        if channel:
                            try:
                                msg = await channel.fetch_message(message_id)
                                await msg.delete()
                            except (discord.NotFound, discord.Forbidden):
                                pass

                # Delete from DB
                result = await connection.execute(
                    "DELETE FROM puzzle2_active WHERE message_id < $1",
                    max_snowflake
                )
                print(f"Auto-Cleanup: Removed stale puzzles ({result})")
            except Exception as e:
                print(f"Error during puzzle cleanup: {e}")

    @cleanup_loop.before_loop
    async def before_cleanup_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="setup", description="Configure the Sliding Puzzle feature.")
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
                INSERT INTO puzzle2_configs (guild_id, channel_id, reward_amount)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2, reward_amount = $3
                """,
                interaction.guild.id, channel.id, reward
            )
            
        await interaction.response.send_message(
            f"Successfully configured **Sliding Puzzles**!\nChannel: {channel.mention}\nReward: **{reward} {coin_name}**"
        )

    @app_commands.command(name="submit", description="Submit an image to become a sliding puzzle.")
    @app_commands.describe(image="The image to turn into a puzzle")
    async def submit(self, interaction: discord.Interaction, image: discord.Attachment):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        if not config:
            await interaction.response.send_message("Sliding puzzles are not configured here.", ephemeral=True)
            return

        if interaction.channel.id != config['channel_id']:
            await interaction.response.send_message(f"You can only submit puzzles in <#{config['channel_id']}>.", ephemeral=True)
            return
            
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("Attachment must be an image.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            image_bytes = await image.read()
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Crop to square and resize
            min_dim = min(img.width, img.height)
            left = (img.width - min_dim) / 2
            top = (img.height - min_dim) / 2
            right = (img.width + min_dim) / 2
            bottom = (img.height + min_dim) / 2
            
            img_square = img.crop((left, top, right, bottom))
            img_resized = img_square.resize((600, 600))
            
            # Save compressed JPEG to db
            compressed_buffer = io.BytesIO()
            img_resized.save(compressed_buffer, format="JPEG", quality=85)
            compressed_bytes = compressed_buffer.getvalue()
            
            # We want to show the full image in the embed, so we save it temporarily to post
            compressed_buffer.seek(0)
            file = discord.File(fp=compressed_buffer, filename="puzzle_full.jpg")
            
            embed = discord.Embed(
                title="🧩 Sliding Puzzle",
                description=f"**Submitted by {interaction.user.mention}**\n\nClick the button below to play privately! Slide the pieces to recreate this original image and earn **{config['reward_amount']} {coin_name}**.",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://puzzle_full.jpg")
            
            # We can't attach a view with dynamic state if it persists across restarts easily unless we pass message_id
            # Wait, `StartPuzzleView` takes message_id
            
            msg = await interaction.channel.send(embed=embed, file=file)
            
            # Save to db
            async with self.bot.db_pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO puzzle2_active (message_id, guild_id, image_data) VALUES ($1, $2, $3)",
                    msg.id, interaction.guild.id, compressed_bytes
                )
                
            # Add view
            view = StartPuzzleView(self.bot.db_pool)
            await msg.edit(view=view)
                
            await interaction.followup.send("Sliding puzzle created successfully!")
            
        except Exception as e:
            print(f"Error creating puzzle2: {e}")
            await interaction.followup.send("An error occurred while making the puzzle.")


async def setup(bot):
    await bot.add_cog(Puzzle2Cog(bot))
