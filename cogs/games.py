import discord
from discord import app_commands
from discord.ext import commands

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="games_config", description="View the configuration of all minigames.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database not connected.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎮 Minigames Configuration",
            description="Here is the current setup for all server minigames.",
            color=discord.Color.blurple()
        )

        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'

            # Smash or Pass
            smash = self.bot.cache.get('smash', {}).get(interaction.guild.id)
            if smash:
                embed.add_field(
                    name="🟢 Smash or Pass",
                    value=(f"**Channel:** <#{smash['smash_channel_id']}>\n"
                           f"**Required Role:** <@&{smash['smash_role_id']}>\n"
                           f"**Reward:** {smash['smash_reward_amount']} {coin_name}\n"
                           f"**Post Cost:** {smash.get('post_cost', 0)} {coin_name}"),
                    inline=False
                )
            else:
                embed.add_field(name="🟢 Smash or Pass", value="*Not configured.*", inline=False)

            # KFM
            kfm = self.bot.cache.get('kfm', {}).get(interaction.guild.id)
            if kfm:
                embed.add_field(
                    name="💋 Kiss, Fuck, Marry",
                    value=(f"**Channel:** <#{kfm['channel_id']}>\n"
                           f"**Required Role:** <@&{kfm['role_id']}>\n"
                           f"**Reward:** {kfm['reward_amount']} {coin_name}\n"
                           f"**Post Cost:** {kfm.get('post_cost', 0)} {coin_name}"),
                    inline=False
                )
            else:
                embed.add_field(name="💋 Kiss, Fuck, Marry", value="*Not configured.*", inline=False)

            # Left or Right
            lor = self.bot.cache.get('lor', {}).get(interaction.guild.id)
            if lor:
                embed.add_field(
                    name="⚖️ Left or Right",
                    value=(f"**Channel:** <#{lor['channel_id']}>\n"
                           f"**Required Role:** <@&{lor['role_id']}>\n"
                           f"**Reward:** {lor['reward_amount']} {coin_name}\n"
                           f"**Post Cost:** {lor.get('post_cost', 0)} {coin_name}"),
                    inline=False
                )
            else:
                embed.add_field(name="⚖️ Left or Right", value="*Not configured.*", inline=False)

            # Puzzle
            puzzle = await connection.fetchrow("SELECT * FROM puzzle2_configs WHERE guild_id = $1", interaction.guild.id)
            if puzzle:
                embed.add_field(
                    name="🧩 Sliding Puzzle",
                    value=(f"**Channel:** <#{puzzle['channel_id']}>\n"
                           f"**Reward:** {puzzle['reward_amount']} {coin_name}"),
                    inline=False
                )
            else:
                embed.add_field(name="🧩 Sliding Puzzle", value="*Not configured.*", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
