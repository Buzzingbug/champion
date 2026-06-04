import discord
from discord import app_commands
from discord.ext import commands
import re

class KFMView(discord.ui.View):
    def __init__(self, db_pool, reward: int, custom_msg: str, role_id: int):
        super().__init__(timeout=None) # Persists forever
        self.db_pool = db_pool
        self.reward = reward
        self.custom_msg = custom_msg
        self.role_id = role_id

    async def process_vote(self, interaction: discord.Interaction, choice: str):
        # Check role
        if self.role_id not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("You do not have the required role to vote on this!", ephemeral=True)
            return

        async with self.db_pool.acquire() as connection:
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
                interaction.guild.id, interaction.user.id, self.reward
            )

        # Send custom success message
        await interaction.response.send_message(self.custom_msg, ephemeral=True)

    @discord.ui.button(label="Kiss", style=discord.ButtonStyle.primary, emoji="💋")
    async def kiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "kiss")

    @discord.ui.button(label="Fuck", style=discord.ButtonStyle.danger, emoji="😈")
    async def fuck_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "fuck")

    @discord.ui.button(label="Marry", style=discord.ButtonStyle.success, emoji="💍")
    async def marry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "marry")


class KFMCog(commands.GroupCog, group_name="kfm"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure the Kiss, Fuck, Marry feature for this server.")
    @app_commands.describe(
        channel="The channel where KFM will be active",
        role="The role required to vote",
        reward="Amount of Supercoins given per vote",
        message="The ephemeral message shown to users after they vote"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, reward: int, message: str):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO kfm_configs (guild_id, channel_id, role_id, reward_amount, custom_message)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2, role_id = $3, reward_amount = $4, custom_message = $5
                """,
                interaction.guild.id, channel.id, role.id, reward, message
            )
            
        await interaction.response.send_message(
            f"Successfully configured **Kiss, Fuck, Marry**!\n"
            f"Channel: {channel.mention}\n"
            f"Required Role: {role.mention}\n"
            f"Reward: **{reward} Supercoins**\n"
            f"Custom Message: `{message}`"
        )

    @app_commands.command(name="reset", description="Reset and disable the Kiss, Fuck, Marry feature for this server.")
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
            
        if result == "DELETE 0":
            await interaction.response.send_message("The feature is not currently configured for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("Successfully reset and disabled **Kiss, Fuck, Marry** for this server.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Fetch config for this guild
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM kfm_configs WHERE guild_id = $1",
                message.guild.id
            )

        if not config:
            return

        # Check if message is in the designated channel
        if message.channel.id != config['channel_id']:
            return

        # Check if the message contains media (attachments or links)
        has_media = bool(message.attachments) or re.search(r"https?://\S+", message.content)
        if not has_media:
            return

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

        view = KFMView(
            db_pool=self.bot.db_pool,
            reward=config['reward_amount'],
            custom_msg=config['custom_message'],
            role_id=config['role_id']
        )

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
