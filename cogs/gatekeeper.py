import discord
from discord import app_commands
from discord.ext import commands

class GatekeeperCog(commands.GroupCog, group_name="gate"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Restrict a channel so users must have a minimum coin balance to speak.")
    @app_commands.describe(
        channel="The channel to restrict",
        amount="The minimum amount of coins required to speak",
        message="The message to send when someone's message is deleted",
        bypass_role="Optional role that ignores this restriction"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, amount: int, message: str, bypass_role: discord.Role = None):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        bypass_role_id = bypass_role.id if bypass_role else None

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO coin_gates (channel_id, guild_id, bypass_role_id, required_amount, custom_message)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (channel_id) DO UPDATE 
                SET bypass_role_id = $3, required_amount = $4, custom_message = $5
                """,
                channel.id, interaction.guild.id, bypass_role_id, amount, message
            )
            
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            
        role_text = f"\nBypass Role: {bypass_role.mention}" if bypass_role else ""
        
        await interaction.response.send_message(
            f"Successfully restricted {channel.mention}!\n"
            f"Users must now have at least **{amount} {coin_name}** to send messages here.{role_text}\n"
            f"Deletion Message: `{message}`"
        )

    @app_commands.command(name="remove", description="Remove the coin restriction from a channel.")
    @app_commands.describe(channel="The channel to un-restrict")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM coin_gates WHERE channel_id = $1",
                channel.id
            )
            
        if result == "DELETE 0":
            await interaction.response.send_message(f"{channel.mention} is not currently restricted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Successfully removed the restriction from {channel.mention}. Anyone can speak there now.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Short-circuit check to see if this channel is gated
        # To avoid querying DB on EVERY single message globally, we should ideally cache this.
        # But for now, we'll do a quick fetch. Asyncpg is very fast.
        async with self.bot.db_pool.acquire() as connection:
            gate = await connection.fetchrow(
                "SELECT bypass_role_id, required_amount, custom_message FROM coin_gates WHERE channel_id = $1",
                message.channel.id
            )

            if not gate:
                return

            # If user has the bypass role, let them speak
            if gate['bypass_role_id']:
                # Ensure the user object has roles (sometimes message.author is a User not Member, though rare in guilds)
                if isinstance(message.author, discord.Member):
                    if gate['bypass_role_id'] in [r.id for r in message.author.roles]:
                        return

            # Check their balance
            economy_record = await connection.fetchrow(
                "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                message.guild.id, message.author.id
            )
            
            balance = economy_record['supercoins'] if economy_record else 0

            if balance < gate['required_amount']:
                # Delete their message
                try:
                    await message.delete()
                except discord.Forbidden:
                    # Bot lacks permissions to delete messages
                    pass
                except discord.NotFound:
                    pass

                # Fetch custom coin name
                coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", message.guild.id)
                coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

                # Send response embed
                embed = discord.Embed(
                    title="Message Deleted",
                    description=f"{message.author.mention}, {gate['custom_message']}\n\n*You need at least **{gate['required_amount']} {coin_name}** to speak in this channel. You currently have **{balance}**.*",
                    color=discord.Color.red()
                )
                
                try:
                    await message.channel.send(content=message.author.mention, embed=embed, delete_after=5.0)
                except discord.Forbidden:
                    pass

async def setup(bot):
    await bot.add_cog(GatekeeperCog(bot))
