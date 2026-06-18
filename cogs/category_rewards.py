import discord
from discord import app_commands
from discord.ext import commands
import re
import datetime

class CategoryRewardsCog(commands.GroupCog, group_name="category"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Reward users with coins for posting media in a category.")
    @app_commands.describe(
        category="The category to enable rewards for",
        reward="Coins given per media post",
        daily_limit="Max coins a user can earn per day from this category",
        message="The message sent to the user when they hit their daily limit"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, category: discord.CategoryChannel, reward: int, daily_limit: int, message: str):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

            await connection.execute(
                """
                INSERT INTO category_configs (category_id, guild_id, reward_amount, daily_limit, custom_message)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (category_id) DO UPDATE 
                SET reward_amount = $3, daily_limit = $4, custom_message = $5
                """,
                category.id, interaction.guild.id, reward, daily_limit, message
            )
            
        # Update Cache
        self.bot.cache['categories'][category.id] = {
            'category_id': category.id,
            'guild_id': interaction.guild.id,
            'reward_amount': reward,
            'daily_limit': daily_limit,
            'custom_message': message
        }
            
        await interaction.response.send_message(
            f"Successfully configured Media Rewards for the **{category.name}** category!\n"
            f"Reward: **{reward} {coin_name} per post**\n"
            f"Daily Limit: **{daily_limit} {coin_name}**\n"
            f"Limit Message: `{message}`"
        )

    @app_commands.command(name="remove", description="Disable media rewards for a category.")
    @app_commands.describe(category="The category to remove rewards from")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM category_configs WHERE category_id = $1",
                category.id
            )
            
        if category.id in self.bot.cache['categories']:
            del self.bot.cache['categories'][category.id]
            
        if result == "DELETE 0":
            await interaction.response.send_message(f"The category **{category.name}** does not have rewards configured.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Successfully disabled media rewards for the **{category.name}** category.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.db_pool:
            return

        # Check if the channel is inside a category
        if not message.channel.category_id:
            return

        # Check cache (O(1))
        config = self.bot.cache['categories'].get(message.channel.category_id)
        if not config:
            return

        # Check for media (attachments or links)
        has_media = bool(message.attachments) or re.search(r"https?://\S+", message.content)
        if not has_media:
            return

        # Process the reward
        today = datetime.datetime.now(datetime.timezone.utc).date()
        reward = config['reward_amount']
        daily_limit = config['daily_limit']

        async with self.bot.db_pool.acquire() as connection:
            # Check today's earnings
            earnings_record = await connection.fetchrow(
                "SELECT earned_today FROM category_earnings WHERE user_id = $1 AND category_id = $2 AND date = $3",
                message.author.id, message.channel.category_id, today
            )

            earned_today = earnings_record['earned_today'] if earnings_record else 0

            # If they already hit the limit, send the message
            if earned_today >= daily_limit:
                try:
                    await message.channel.send(f"{message.author.mention} {config['custom_message']}", delete_after=5)
                except discord.Forbidden:
                    pass
                return

            # Calculate actual reward (don't exceed the limit)
            actual_reward = min(reward, daily_limit - earned_today)

            if actual_reward <= 0:
                return

            # Update earnings
            await connection.execute(
                """
                INSERT INTO category_earnings (user_id, category_id, date, earned_today)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, category_id, date)
                DO UPDATE SET earned_today = category_earnings.earned_today + $4
                """,
                message.author.id, message.channel.category_id, today, actual_reward
            )

            # Add to main economy
            await connection.execute(
                """
                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3
                """,
                message.guild.id, message.author.id, actual_reward
            )

async def setup(bot):
    await bot.add_cog(CategoryRewardsCog(bot))
