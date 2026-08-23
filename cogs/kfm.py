import discord
from discord import app_commands
from discord.ext import commands
import re

class KFMView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None) # Persists forever
        self.bot = bot

    async def process_vote(self, interaction: discord.Interaction, choice: str):
        config = self.bot.cache['kfm'].get(interaction.guild.id)
        if not config:
            await interaction.response.send_message("KFM is not configured for this server.", ephemeral=True)
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
                "SELECT 1 FROM kfm_votes WHERE message_id = $1 AND user_id = $2",
                interaction.message.id, interaction.user.id
            )
            
            if record:
                await interaction.response.send_message("You have already voted on this post!", ephemeral=True)
                return

            # Insert vote
            await connection.execute(
                "INSERT INTO kfm_votes (message_id, user_id, vote_choice) VALUES ($1, $2, $3)",
                interaction.message.id, interaction.user.id, choice
            )

            # Give Supercoins
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3
                """,
                interaction.guild.id, interaction.user.id, reward
            )

        # Send custom success message
        await interaction.response.send_message(custom_msg, ephemeral=True)

    @discord.ui.button(label="Kiss", style=discord.ButtonStyle.primary, emoji="💋", custom_id="kfm_kiss")
    async def kiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "kiss")

    @discord.ui.button(label="Fuck", style=discord.ButtonStyle.danger, emoji="😈", custom_id="kfm_fuck")
    async def fuck_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "fuck")

    @discord.ui.button(label="Marry", style=discord.ButtonStyle.success, emoji="💍", custom_id="kfm_marry")
    async def marry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "marry")


class KFMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(KFMView(self.bot))

    @app_commands.command(name="kfm_setup", description="Configure the Kiss, Fuck, Marry feature for this server.")
    @app_commands.describe(
        channel="The channel where KFM will be active",
        role="The role required to vote",
        reward="Amount of Supercoins given per vote",
        message="The ephemeral message shown to users after they vote",
        post_cost="Amount of Supercoins it costs to post an image (default 0)"
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
                INSERT INTO kfm_configs (guild_id, channel_id, role_id, reward_amount, custom_message, post_cost)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2, role_id = $3, reward_amount = $4, custom_message = $5, post_cost = $6
                """,
                interaction.guild.id, channel.id, role.id, reward, message, post_cost
            )
            
        self.bot.cache['kfm'][interaction.guild.id] = {
            'guild_id': interaction.guild.id,
            'channel_id': channel.id,
            'role_id': role.id,
            'reward_amount': reward,
            'custom_message': message,
            'post_cost': post_cost
        }
            
        await interaction.response.send_message(
            f"Successfully configured **Kiss, Fuck, Marry**!\n"
            f"Channel: {channel.mention}\n"
            f"Required Role: {role.mention}\n"
            f"Reward: **{reward} {coin_name}**\n"
            f"Custom Message: `{message}`"
        )

    @app_commands.command(name="kfm_reset", description="Reset and disable the Kiss, Fuck, Marry feature for this server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM kfm_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            
        if interaction.guild.id in self.bot.cache['kfm']:
            del self.bot.cache['kfm'][interaction.guild.id]
            
        if result == "DELETE 0":
            await interaction.response.send_message("The feature is not currently configured for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("Successfully reset and disabled **Kiss, Fuck, Marry** for this server.", ephemeral=True)

    @app_commands.command(name="kfm_submit", description="Submit an image to Kiss, Fuck, Marry.")
    @app_commands.describe(image="The image to submit")
    async def submit(self, interaction: discord.Interaction, image: discord.Attachment):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        config = self.bot.cache['kfm'].get(interaction.guild.id)
        if not config:
            await interaction.response.send_message("KFM is not configured for this server.", ephemeral=True)
            return

        if interaction.channel.id != config['channel_id']:
            await interaction.response.send_message(f"You can only submit images in <#{config['channel_id']}>.", ephemeral=True)
            return

        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("Attachment must be an image.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with self.bot.db_pool.acquire() as connection:
            if config.get('post_cost', 0) > 0:
                user_bal = await connection.fetchrow(
                    "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                    interaction.guild.id, interaction.user.id
                )
                if not user_bal or user_bal['supercoins'] < config['post_cost']:
                    await interaction.followup.send(f"You don't have enough coins to post here! It costs **{config['post_cost']}** coins to enter.", ephemeral=True)
                    return
                
                # Deduct cost
                await connection.execute(
                    "UPDATE economy SET supercoins = supercoins - $3 WHERE guild_id = $1 AND user_id = $2",
                    interaction.guild.id, interaction.user.id, config['post_cost']
                )

        file = await image.to_file()
        embed = discord.Embed(
            description=f"**Submitted by {interaction.user.mention}**",
            color=discord.Color.brand_red()
        )
        embed.set_image(url=f"attachment://{file.filename}")

        view = KFMView(self.bot)

        try:
            await interaction.channel.send(embed=embed, file=file, view=view)
            await interaction.followup.send("Successfully submitted!")
        except Exception as e:
            await interaction.followup.send(f"Failed to submit: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Cache check: O(1) latency
        config = self.bot.cache['kfm'].get(message.guild.id)
        if not config or message.channel.id != config['channel_id']:
            return

        # Check if the message contains media (attachments or links)
        has_media = bool(message.attachments) or re.search(r"https?://\S+", message.content)
        if not has_media:
            return

        async with self.bot.db_pool.acquire() as connection:
            if config.get('post_cost', 0) > 0:
                user_bal = await connection.fetchrow(
                    "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                    message.guild.id, message.author.id
                )
                if not user_bal or user_bal['supercoins'] < config['post_cost']:
                    try:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} You don't have enough coins to post here! It costs **{config['post_cost']}** coins to enter.", delete_after=5)
                    except discord.Forbidden:
                        pass
                    return
                
                # Deduct cost
                await connection.execute(
                    "UPDATE economy SET supercoins = supercoins - $3 WHERE guild_id = $1 AND user_id = $2",
                    message.guild.id, message.author.id, config['post_cost']
                )

        # Prepare to repost
        files = []
        for att in message.attachments:
            files.append(await att.to_file())

        embed = discord.Embed(
            description=f"**Submitted by {message.author.mention}**\n\n{message.content}",
            color=discord.Color.brand_red()
        )
        
        # If there's an image, attach it to the embed for better display
        image_attached = False
        for f in files:
            if f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                embed.set_image(url=f"attachment://{f.filename}")
                image_attached = True
                break

        view = KFMView(self.bot)

        try:
            # Delete original message
            await message.delete()
            # Repost with embed, files, and buttons
            await message.channel.send(embed=embed, files=files, view=view)
        except discord.Forbidden:
            print("Bot lacks permissions to delete messages or send embeds/attachments in this channel.")
        except Exception as e:
            print(f"Error reposting kfm media: {e}")

async def setup(bot):
    await bot.add_cog(KFMCog(bot))
