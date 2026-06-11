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
            
        await interaction.response.defer()

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
            file = discord.File("assets/bank_banner.png", filename="bank_banner.png")
            
            embed = discord.Embed(
                title=f"🏦 Central Bank of {interaction.guild.name}",
                description=f"Welcome to your private vault, {interaction.user.mention}.",
                color=discord.Color.gold()
            )
            embed.add_field(name="Current Balance", value=f"**{balance:,} {coin_name}**", inline=False)
            embed.set_image(url="attachment://bank_banner.png")
            embed.set_footer(text="Secured by Champion Bot Servers")

            await interaction.followup.send(file=file, embed=embed)
        except Exception as e:
            print(f"Error sending bank embed: {e}")
            await interaction.followup.send(f"Bank error: Your balance is **{balance:,} {coin_name}**.")

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

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
