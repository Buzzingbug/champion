import discord
from discord import app_commands
from discord.ext import commands
import time

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_uptime(self):
        if not hasattr(self.bot, 'start_time'):
            return "Just started"
            
        uptime_seconds = int(time.time() - self.bot.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)

    @app_commands.command(name="ping", description="Check the bot's system status.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        latency = round(self.bot.latency * 1000)
        uptime_str = self.get_uptime()
        
        # Check Redis connection
        redis_status = "❌ Disconnected"
        if hasattr(self.bot, 'redis_pool') and self.bot.redis_pool:
            try:
                await self.bot.redis_pool.ping()
                redis_status = "✅ Connected"
            except Exception:
                redis_status = "❌ Error"
                
        shard_id = interaction.guild.shard_id if interaction.guild else 0
        
        embed = discord.Embed(
            title="🏓 System Status",
            color=0x2b2d31 # Discord dark theme color
        )
        
        embed.add_field(name="Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Redis Cache", value=f"`{redis_status}`", inline=True)
        
        embed.add_field(name="Shard ID", value=f"`{shard_id}`", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="clear_dms", description="Deletes all messages the bot has sent you in DMs.")
    async def clear_dms(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.user.dm_channel
            if not channel:
                channel = await interaction.user.create_dm()
                
            deleted = 0
            # Discord limits bots to deleting their own messages
            async for msg in channel.history(limit=100):
                if msg.author.id == self.bot.user.id:
                    try:
                        await msg.delete()
                        deleted += 1
                    except discord.HTTPException:
                        pass
                        
            await interaction.followup.send(f"✅ Successfully cleaned up {deleted} messages from your DMs!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to message you in DMs.", ephemeral=True)
        except Exception as e:
            print(f"Error clearing DMs: {e}")
            await interaction.followup.send("An error occurred while trying to clear DMs.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
