import discord
from discord import app_commands
from discord.ext import commands
import io
from PIL import Image

class LORView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None) # Persists forever
        self.bot = bot

    async def process_vote(self, interaction: discord.Interaction, choice: str):
        config = self.bot.cache['lor'].get(interaction.guild.id)
        if not config:
            await interaction.response.send_message("Left or Right is not configured for this server.", ephemeral=True)
            return

        role_id = config['role_id']
        reward = config['reward_amount']
        custom_msg = config['custom_message']

        # Check role
        if role_id not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("You do not have the required role to vote on this!", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            # Check if already voted
            record = await connection.fetchrow(
                "SELECT 1 FROM rol_votes WHERE message_id = $1 AND user_id = $2",
                interaction.message.id, interaction.user.id
            )
            
            if record:
                await interaction.response.send_message("You have already voted on this post!", ephemeral=True)
                return

            # Insert vote
            await connection.execute(
                "INSERT INTO rol_votes (message_id, user_id, vote_choice) VALUES ($1, $2, $3)",
                interaction.message.id, interaction.user.id, choice
            )

            # Give Supercoins
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins, lifetime_games) 
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3, lifetime_games = economy.lifetime_games + $3
                """,
                interaction.guild.id, interaction.user.id, reward
            )

        # Send custom success message
        await interaction.response.send_message(custom_msg, ephemeral=True)

    @discord.ui.button(label="Left", style=discord.ButtonStyle.danger, emoji="⬅️", custom_id="lor_left")
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "left")

    @discord.ui.button(label="Right", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="lor_right")
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "right")


class LORCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(LORView(self.bot))

    @app_commands.command(name="lor_setup", description="Configure the Left or Right feature for this server.")
    @app_commands.describe(
        channel="The channel where Left or Right will be active",
        role="The role required to vote",
        reward="Amount of Supercoins given per vote",
        message="The ephemeral message shown to users after they vote",
        post_cost="Amount of Supercoins it costs to post images (default 0)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, reward: int, message: str, post_cost: int = 0):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute(
                """
                INSERT INTO rol_configs (guild_id, channel_id, role_id, reward_amount, custom_message, post_cost)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2, role_id = $3, reward_amount = $4, custom_message = $5, post_cost = $6
                """,
                interaction.guild.id, channel.id, role.id, reward, message, post_cost
            )
            
        self.bot.cache['lor'][interaction.guild.id] = {
            'guild_id': interaction.guild.id,
            'channel_id': channel.id,
            'role_id': role.id,
            'reward_amount': reward,
            'custom_message': message,
            'post_cost': post_cost
        }
            
        await interaction.response.send_message(
            f"Successfully configured **Left or Right**!\n"
            f"Channel: {channel.mention}\n"
            f"Required Role: {role.mention}\n"
            f"Reward: **{reward} {coin_name}**\n"
            f"Custom Message: `{message}`"
        )

    @app_commands.command(name="lor_reset", description="Reset and disable the Left or Right feature for this server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM rol_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            
        if result == "DELETE 0":
            await interaction.response.send_message("The feature is not currently configured for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("Successfully reset and disabled **Left or Right** for this server.", ephemeral=True)

    @app_commands.command(name="lor_submit", description="Submit two images for Left or Right.")
    @app_commands.describe(
        image_left="The image that will appear on the left",
        image_right="The image that will appear on the right",
        title="Optional title for the post"
    )
    async def submit(self, interaction: discord.Interaction, image_left: discord.Attachment, image_right: discord.Attachment, title: str = "Left or Right?"):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        # Fetch config for this guild from cache
        config = self.bot.cache['lor'].get(interaction.guild.id)

        if not config:
            await interaction.response.send_message("Left or Right has not been configured in this server. An admin needs to run `/leftorright setup` first.", ephemeral=True)
            return

        # Check if they are in the configured channel
        if interaction.channel.id != config['channel_id']:
            await interaction.response.send_message(f"You can only submit images in <#{config['channel_id']}>.", ephemeral=True)
            return

        # Verify attachments are images
        if not image_left.content_type or not image_left.content_type.startswith('image/') or \
           not image_right.content_type or not image_right.content_type.startswith('image/'):
            await interaction.response.send_message("Both attachments must be valid images.", ephemeral=True)
            return

        # Check economy and deduct post cost BEFORE downloading images
        async with self.bot.db_pool.acquire() as connection:
            if config.get('post_cost', 0) > 0:
                user_bal = await connection.fetchrow(
                    "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                    interaction.guild.id, interaction.user.id
                )
                if not user_bal or user_bal['supercoins'] < config['post_cost']:
                    await interaction.response.send_message(f"You don't have enough coins to submit! It costs **{config['post_cost']}** coins to play.", ephemeral=True)
                    return
                
                # Deduct cost
                await connection.execute(
                    "UPDATE economy SET supercoins = supercoins - $3 WHERE guild_id = $1 AND user_id = $2",
                    interaction.guild.id, interaction.user.id, config['post_cost']
                )

        # Defer response since image downloading and processing takes time
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Download images
            left_bytes = await image_left.read()
            right_bytes = await image_right.read()
            
            # Open with Pillow
            img1 = Image.open(io.BytesIO(left_bytes)).convert("RGBA")
            img2 = Image.open(io.BytesIO(right_bytes)).convert("RGBA")
            
            # Scale them to the same height (e.g. 500px)
            target_height = 500
            
            aspect1 = img1.width / img1.height
            img1_resized = img1.resize((int(target_height * aspect1), target_height))
            
            aspect2 = img2.width / img2.height
            img2_resized = img2.resize((int(target_height * aspect2), target_height))
            
            # Create a blank image to hold both
            spacing = 20
            total_width = img1_resized.width + img2_resized.width + spacing
            
            new_img = Image.new("RGBA", (total_width, target_height), (0, 0, 0, 0))
            new_img.paste(img1_resized, (0, 0))
            new_img.paste(img2_resized, (img1_resized.width + spacing, 0))
            
            # Save stitched image to buffer
            final_buffer = io.BytesIO()
            new_img.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            
            file = discord.File(fp=final_buffer, filename="leftorright.png")
            
            # Prepare embed and view
            embed = discord.Embed(
                title=title,
                description=f"**Submitted by {interaction.user.mention}**",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://leftorright.png")
            
            view = LORView(self.bot)
            
            # Send the result to the channel
            await interaction.channel.send(embed=embed, file=file, view=view)
            
            # Notify user
            await interaction.followup.send("Successfully submitted!")
            
        except Exception as e:
            print(f"Error processing images: {e}")
            await interaction.followup.send("An error occurred while processing the images. Please ensure they are valid images and try again.")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Check cache (O(1))
        config = self.bot.cache['lor'].get(message.guild.id)
        if not config:
            return
            
        if message.channel.id != config['channel_id']:
            return

        # Check if they are trying to post images
        has_media = bool(message.attachments)
        if not has_media:
            return

        valid_images = [att for att in message.attachments if att.content_type and att.content_type.startswith('image/')]
        
        if len(valid_images) != 2:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Please post exactly two images at once or together for Left or Right!", delete_after=5)
            except discord.Forbidden:
                pass
            return
            
        # Deduct post cost
        async with self.bot.db_pool.acquire() as connection:
            if config.get('post_cost', 0) > 0:
                user_bal = await connection.fetchrow(
                    "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                    message.guild.id, message.author.id
                )
                if not user_bal or user_bal['supercoins'] < config['post_cost']:
                    try:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} You don't have enough coins to post! It costs **{config['post_cost']}** coins.", delete_after=5)
                    except discord.Forbidden:
                        pass
                    return
                
                # Deduct cost
                await connection.execute(
                    "UPDATE economy SET supercoins = supercoins - $3 WHERE guild_id = $1 AND user_id = $2",
                    message.guild.id, message.author.id, config['post_cost']
                )

        temp_msg = None
        try:
            temp_msg = await message.channel.send(f"Processing your images, {message.author.mention}...")
            
            # Download images
            left_bytes = await valid_images[0].read()
            right_bytes = await valid_images[1].read()
            
            # Open with Pillow
            img1 = Image.open(io.BytesIO(left_bytes)).convert("RGBA")
            img2 = Image.open(io.BytesIO(right_bytes)).convert("RGBA")
            
            # Scale them to the same height (e.g. 500px)
            target_height = 500
            
            aspect1 = img1.width / img1.height
            img1_resized = img1.resize((int(target_height * aspect1), target_height))
            
            aspect2 = img2.width / img2.height
            img2_resized = img2.resize((int(target_height * aspect2), target_height))
            
            # Create a blank image to hold both
            spacing = 20
            total_width = img1_resized.width + img2_resized.width + spacing
            
            new_img = Image.new("RGBA", (total_width, target_height), (0, 0, 0, 0))
            new_img.paste(img1_resized, (0, 0))
            new_img.paste(img2_resized, (img1_resized.width + spacing, 0))
            
            # Save stitched image to buffer
            final_buffer = io.BytesIO()
            new_img.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            
            file = discord.File(fp=final_buffer, filename="leftorright.png")
            
            title = message.content if message.content else "Left or Right?"
            
            # Prepare embed and view
            embed = discord.Embed(
                title=title,
                description=f"**Submitted by {message.author.mention}**",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://leftorright.png")
            
            view = LORView(self.bot)
            
            # Delete original user message & temp message
            try:
                await message.delete()
            except:
                pass
                
            if temp_msg:
                try:
                    await temp_msg.delete()
                except:
                    pass
                
            # Send the result to the channel
            await message.channel.send(embed=embed, file=file, view=view)
            
        except Exception as e:
            print(f"Error processing images in LOR drop: {e}")
            if temp_msg:
                try:
                    await temp_msg.edit(content=f"{message.author.mention} An error occurred while processing the images. Please ensure they are valid images and try again.")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(LORCog(bot))
