import discord
from discord.ext import commands
import random

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Game commands will be provided and added here soon.
    pass

async def setup(bot):
    await bot.add_cog(Games(bot))
