import discord
from discord import app_commands
from discord.ext import commands
import re

class SmashOrPassView(discord.ui.View):
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
                "SELECT 1 FROM smash_votes WHERE message_id = $1 AND user_id = $2",
                interaction.message.id, interaction.user.id
            )
            
            if record:
                await interaction.response.send_message("You have already voted on this post!", ephemeral=True)
                return

            # Insert vote
            await connection.execute(
                "INSERT INTO smash_votes (message_id, user_id, vote_choice) VALUES ($1, $2, $3)",
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

    @discord.ui.button(label="Smash", style=discord.ButtonStyle.success, emoji="🟢")
    async def smash_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "smash")

    @discord.ui.button(label="Pass", style=discord.ButtonStyle.danger, emoji="🔴")
    async def pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_vote(interaction, "pass")


class SmashOrPassCog(commands.GroupCog, group_name="smashorpass"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure the Smash or Pass feature for this server.")
    @app_commands.describe(
        channel="The channel where Smash or Pass will be active",
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
                INSERT INTO server_configs (guild_id, smash_channel_id, smash_role_id, smash_reward_amount, smash_custom_message)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id) DO UPDATE 
                SET smash_channel_id = $2, smash_role_id = $3, smash_reward_amount = $4, smash_custom_message = $5
                """,
                interaction.guild.id, channel.id, role.id, reward, message
            )
            
        await interaction.response.send_message(
            f"Successfully configured **Smash or Pass**!\n"
            f"Channel: {channel.mention}\n"
            f"Required Role: {role.mention}\n"
            f"Reward: **{reward} Supercoins**\n"
            f"Custom Message: `{message}`"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Fetch config for this guild
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM server_configs WHERE guild_id = $1",
                message.guild.id
            )

        if not config:
            return

        # Check if message is in the designated channel
        if message.channel.id != config['smash_channel_id']:
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
            color=discord.Color.purple()
        )
        
        # If there's an image, attach it to the embed for better display
        image_attached = False
        for f in files:
            if f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                embed.set_image(url=f"attachment://{f.filename}")
                image_attached = True
                break

        view = SmashOrPassView(
            db_pool=self.bot.db_pool,
            reward=config['smash_reward_amount'],
            custom_msg=config['smash_custom_message'],
            role_id=config['smash_role_id']
        )

        try:
            # Delete original message
            await message.delete()
            # Repost with embed, files, and buttons
            await message.channel.send(embed=embed, files=files, view=view)
        except discord.Forbidden:
            print("Bot lacks permissions to delete messages or send embeds/attachments in this channel.")
        except Exception as e:
            print(f"Error reposting smash or pass media: {e}")

async def setup(bot):
    await bot.add_cog(SmashOrPassCog(bot))
