import discord
from discord import app_commands
from discord.ext import commands

class EconomyCog(commands.GroupCog, group_name="economy"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bank", description="View your digital bank account balance.")
    async def bank(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db_pool.acquire() as connection:
            economy_record = await connection.fetchrow(
                "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                interaction.guild.id, interaction.user.id
            )
            balance = economy_record['supercoins'] if economy_record else 0

            coin_record = await connection.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                interaction.guild.id
            )
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        try:
            file = discord.File("assets/aurum_bank.jpg", filename="aurum_bank.jpg")
            
            embed = discord.Embed(
                title=f"🏦 AURUM Private Digital Banking",
                description=f"Welcome to your ultra-secure digital vault, {interaction.user.mention}.",
                color=discord.Color.gold()
            )
            embed.add_field(name="Current Balance", value=f"**{balance:,} {coin_name}**", inline=False)
            embed.set_image(url="attachment://aurum_bank.jpg")
            embed.set_footer(text="Secured by Botforge services")

            await interaction.followup.send(file=file, embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error sending bank embed: {e}")
            await interaction.followup.send(f"Bank error: Your balance is **{balance:,} {coin_name}**.", ephemeral=True)

    @app_commands.command(name="add", description="Add coins to a user's bank account.")
    @app_commands.describe(user="The user to give coins to", amount="The amount of coins to give")
    @app_commands.checks.has_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3
                """,
                interaction.guild.id, user.id, amount
            )

            coin_record = await connection.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                interaction.guild.id
            )
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        await interaction.response.send_message(f"Successfully added **{amount:,} {coin_name}** to {user.mention}'s account!")

    @app_commands.command(name="setname", description="Set the custom name for your server's currency.")
    @app_commands.describe(name="The new name for the currency (e.g., VibeCoins)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setname(self, interaction: discord.Interaction, name: str):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO server_settings (guild_id, coin_name)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE 
                SET coin_name = $2
                """,
                interaction.guild.id, name
            )
            
        await interaction.response.send_message(
            f"Successfully updated the server's currency name to **{name}**!\nAll minigames will now use this name."
        )

    @app_commands.command(name="check", description="[ADMIN] Check a user's bank account balance.")
    @app_commands.describe(user="The user to check the balance of")
    @app_commands.checks.has_permissions(administrator=True)
    async def check(self, interaction: discord.Interaction, user: discord.Member):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            economy_record = await connection.fetchrow(
                "SELECT supercoins FROM economy WHERE guild_id = $1 AND user_id = $2",
                interaction.guild.id, user.id
            )
            balance = economy_record['supercoins'] if economy_record else 0

            coin_record = await connection.fetchrow(
                "SELECT coin_name FROM server_settings WHERE guild_id = $1", 
                interaction.guild.id
            )
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

        await interaction.response.send_message(f"**{user.display_name}** currently has **{balance:,} {coin_name}** in their account.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
