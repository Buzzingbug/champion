import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import time
import re

class WeeklyWinnersCog(commands.GroupCog, group_name="weekly"):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_loop.start()

    def cog_unload(self):
        self.weekly_loop.cancel()

    @app_commands.command(name="channel", description="Set the dashboard channel for weekly winners.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO weekly_dashboards (guild_id, channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE 
                SET channel_id = $2
                """,
                interaction.guild.id, channel.id
            )
        await interaction.response.send_message(f"Weekly Winners dashboard channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="smash", description="Configure the weekly Smash or Pass winner message and prize.")
    @app_commands.describe(
        message="Custom message. Use {user} to mention the winner.",
        prize="Amount of coins awarded to the winner"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_smash(self, interaction: discord.Interaction, message: str, prize: int):
        if not self.bot.db_pool:
            return
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO weekly_dashboards (guild_id, smash_msg, smash_prize)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE 
                SET smash_msg = $2, smash_prize = $3
                """,
                interaction.guild.id, message, prize
            )
        await interaction.response.send_message(f"Smash or Pass weekly config saved! Prize: **{prize}**", ephemeral=True)

    @app_commands.command(name="kfm", description="Configure the weekly Kiss Fuck Marry winner message and prize.")
    @app_commands.describe(
        message="Custom message. Use {user} to mention the winner.",
        prize="Amount of coins awarded to the winner"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_kfm(self, interaction: discord.Interaction, message: str, prize: int):
        if not self.bot.db_pool:
            return
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO weekly_dashboards (guild_id, kfm_msg, kfm_prize)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE 
                SET kfm_msg = $2, kfm_prize = $3
                """,
                interaction.guild.id, message, prize
            )
        await interaction.response.send_message(f"KFM weekly config saved! Prize: **{prize}**", ephemeral=True)

    @app_commands.command(name="rol", description="Configure the weekly Left or Right winner message and prize.")
    @app_commands.describe(
        message="Custom message. Use {user} to mention the winner.",
        prize="Amount of coins awarded to the winner"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_rol(self, interaction: discord.Interaction, message: str, prize: int):
        if not self.bot.db_pool:
            return
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO weekly_dashboards (guild_id, rol_msg, rol_prize)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE 
                SET rol_msg = $2, rol_prize = $3
                """,
                interaction.guild.id, message, prize
            )
        await interaction.response.send_message(f"Left or Right weekly config saved! Prize: **{prize}**", ephemeral=True)

    @app_commands.command(name="trigger", description="[ADMIN] Manually trigger the weekly winners calculation.")
    @app_commands.checks.has_permissions(administrator=True)
    async def trigger(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.process_weekly_winners(manual_guild_id=interaction.guild.id)
        await interaction.followup.send("Weekly calculation triggered successfully.")

    @tasks.loop(minutes=60)
    async def weekly_loop(self):
        now = datetime.datetime.utcnow()
        # Sunday is 6, 12:00 PM UTC
        if now.weekday() == 6 and now.hour == 12:
            await self.process_weekly_winners()

    @weekly_loop.before_loop
    async def before_weekly_loop(self):
        await self.bot.wait_until_ready()

    async def process_weekly_winners(self, manual_guild_id=None):
        if not self.bot.db_pool:
            return
            
        now = datetime.datetime.utcnow()
        today = now.date()
        # Calculate snowflake from 7 days ago
        seven_days_ago_ms = int((time.time() - (7 * 24 * 60 * 60)) * 1000)
        min_snowflake = (seven_days_ago_ms - 1420070400000) << 22

        async with self.bot.db_pool.acquire() as connection:
            query = "SELECT * FROM weekly_dashboards"
            if manual_guild_id:
                query += f" WHERE guild_id = {manual_guild_id}"
            else:
                query += f" WHERE last_posted IS NULL OR last_posted < $1"
                
            dashboards = await connection.fetch(query, today) if not manual_guild_id else await connection.fetch(query)

            for dash in dashboards:
                guild_id = dash['guild_id']
                channel_id = dash['channel_id']
                if not channel_id:
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue

                # Process each game
                await self._process_game_winner(
                    connection, guild, channel, min_snowflake,
                    "smash_votes", dash['smash_msg'], dash['smash_prize'], "Smash or Pass", discord.Color.purple(), vote_filter="smash"
                )
                await self._process_game_winner(
                    connection, guild, channel, min_snowflake,
                    "kfm_votes", dash['kfm_msg'], dash['kfm_prize'], "Kiss Fuck Marry", discord.Color.brand_red()
                )
                await self._process_game_winner(
                    connection, guild, channel, min_snowflake,
                    "rol_votes", dash['rol_msg'], dash['rol_prize'], "Left or Right", discord.Color.blue()
                )

                if not manual_guild_id:
                    await connection.execute("UPDATE weekly_dashboards SET last_posted = $1 WHERE guild_id = $2", today, guild_id)

    async def _process_game_winner(self, connection, guild, channel, min_snowflake, table_name, custom_msg, prize, title, color, vote_filter=None):
        # Find the message with the highest votes in the last 7 days
        query = f"""
            SELECT message_id, COUNT(*) as vote_count 
            FROM {table_name} 
            WHERE message_id > $1 
        """
        if vote_filter:
            query += f" AND vote_choice = '{vote_filter}' "
            
        query += """
            GROUP BY message_id 
            ORDER BY vote_count DESC 
            LIMIT 1
        """
        
        winner = await connection.fetchrow(query, min_snowflake)

        if not winner:
            return

        message_id = winner['message_id']
        vote_count = winner['vote_count']

        # Determine which channel this message would be in based on cache
        channel_id = None
        if table_name == 'smash_votes' and guild.id in self.bot.cache.get('smash', {}):
            channel_id = self.bot.cache['smash'][guild.id].get('smash_channel_id')
        elif table_name == 'kfm_votes' and guild.id in self.bot.cache.get('kfm', {}):
            channel_id = self.bot.cache['kfm'][guild.id].get('channel_id')
        elif table_name == 'rol_votes' and guild.id in self.bot.cache.get('lor', {}):
            channel_id = self.bot.cache['lor'][guild.id].get('channel_id')

        if not channel_id:
            return

        game_channel = guild.get_channel(channel_id)
        if not game_channel:
            return

        try:
            msg = await game_channel.fetch_message(message_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return

        # Extract Original Author ID
        author_id = None
        if msg.embeds:
            desc = msg.embeds[0].description or ""
            match = re.search(r"<@!?(\d+)>", desc)
            if match:
                author_id = int(match.group(1))

        if not author_id:
            return

        author_member = guild.get_member(author_id)
        author_mention = f"<@{author_id}>"

        # Determine Image URL
        image_url = None
        if msg.embeds and msg.embeds[0].image:
            image_url = msg.embeds[0].image.url

        # Format Custom Message
        prize = prize or 0
        default_msg = f"🏆 Congratulations {{user}}! You won the {title} weekly prize of **{prize} coins** with {vote_count} votes!"
        display_msg = (custom_msg or default_msg).replace("{user}", author_mention)

        # Deposit Prize
        if prize > 0:
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3
                """,
                guild.id, author_id, prize
            )

        # Send Showcase Embed
        embed = discord.Embed(
            title=f"👑 {title} Weekly Winner!",
            description=display_msg,
            color=color
        )
        if image_url:
            embed.set_image(url=image_url)
        
        embed.set_footer(text=f"Total Votes: {vote_count}")

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to post winner to dashboard: {e}")

async def setup(bot):
    await bot.add_cog(WeeklyWinnersCog(bot))
