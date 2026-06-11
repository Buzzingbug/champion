import discord
from discord import app_commands
from discord.ext import commands

class EconomyCog(commands.GroupCog, group_name="economy"):
    def __init__(self, bot):
        self.bot = bot

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
