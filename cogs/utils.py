import discord
from discord import app_commands
from discord.ext import commands
import time

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's connection status and latency.")
    async def ping(self, interaction: discord.Interaction):
        start_time = time.time()
        
        # Defer the response to calculate Discord API round-trip latency
        await interaction.response.defer(ephemeral=True)
        
        end_time = time.time()
        api_latency = round((end_time - start_time) * 1000)
        websocket_latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="WebSocket Latency", value=f"`{websocket_latency}ms`", inline=True)
        embed.add_field(name="API Latency", value=f"`{api_latency}ms`", inline=True)
        
        # Check database latency if connected
        if self.bot.db_pool:
            db_start = time.time()
            try:
                async with self.bot.db_pool.acquire() as connection:
                    await connection.execute("SELECT 1")
                db_latency = round((time.time() - db_start) * 1000)
                embed.add_field(name="Database Latency", value=f"`{db_latency}ms`", inline=True)
            except Exception as e:
                embed.add_field(name="Database Latency", value="`Error`", inline=True)
        else:
            embed.add_field(name="Database Latency", value="`Disconnected`", inline=True)
            
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
