import discord
from discord.ext import commands, tasks
import datetime
import time

class DataRetentionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.retention_loop.start()

    def cog_unload(self):
        self.retention_loop.cancel()

    @tasks.loop(hours=24)
    async def retention_loop(self):
        if not self.bot.db_pool:
            return
            
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # 1. Purge Voting Data older than 30 days
        # We can extract the timestamp from the message_id snowflake
        thirty_days_ago_ms = int((time.time() - (30 * 24 * 60 * 60)) * 1000)
        max_snowflake_30_days = (thirty_days_ago_ms - 1420070400000) << 22

        # 2. Purge Daily Earning Limits older than 7 days
        seven_days_ago = (now - datetime.timedelta(days=7)).date()

        async with self.bot.db_pool.acquire() as connection:
            try:
                # Cleanup Votes
                smash_del = await connection.execute("DELETE FROM smash_votes WHERE message_id < $1", max_snowflake_30_days)
                kfm_del = await connection.execute("DELETE FROM kfm_votes WHERE message_id < $1", max_snowflake_30_days)
                rol_del = await connection.execute("DELETE FROM rol_votes WHERE message_id < $1", max_snowflake_30_days)
                
                # Cleanup Earnings
                cat_del = await connection.execute("DELETE FROM category_earnings WHERE date < $1", seven_days_ago)
                chan_del = await connection.execute("DELETE FROM channel_earnings WHERE date < $1", seven_days_ago)

                print(f"Data Retention Audit Complete:")
                print(f"Purged Votes - Smash: {smash_del}, KFM: {kfm_del}, ROL: {rol_del}")
                print(f"Purged Earnings - Category: {cat_del}, Channel: {chan_del}")

            except Exception as e:
                print(f"Error during automated data retention sweep: {e}")

    @retention_loop.before_loop
    async def before_retention_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DataRetentionCog(bot))
