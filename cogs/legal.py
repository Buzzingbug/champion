import discord
from discord import app_commands
from discord.ext import commands

class LegalCog(commands.GroupCog, group_name="legal"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="about", description="Display information about the bot and its compliance.")
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ℹ️ About This Bot",
            description=(
                "This bot is a custom Economy and Gaming bot designed to provide interactive "
                "media games, puzzles, and a virtual currency system."
            ),
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Data & Privacy", 
            value=(
                "We take your privacy seriously. This bot processes your Discord User ID "
                "to maintain your economy balance and track your game scores. We comply with "
                "all GDPR and Discord Developer Terms of Service requirements.\n\n"
                "Use `/legal privacy` or `/legal terms` for more details."
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="privacy", description="View the bot's Privacy Policy.")
    async def privacy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔒 Privacy Policy",
            description=(
                "**What we collect:**\n"
                "• Your Discord User ID (to track your balance)\n"
                "• Server and Channel IDs\n"
                "• Temporary media uploads for puzzles (deleted within 48 hours)\n\n"
                "**Data Retention:**\n"
                "We use automated data retention to purge stale tracking and earning logs regularly.\n\n"
                "**Right to Erasure:**\n"
                "To exercise your right to have your data deleted, please join our Support Server "
                "and open a ticket. We process these manually to prevent bad actors from evading bans."
            ),
            color=discord.Color.green()
        )
        
        # In a real production environment, you would link to the hosted URL here
        embed.add_field(
            name="Full Privacy Policy",
            value="[Click here to view our complete Privacy Policy](https://example.com/privacy)"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="terms", description="View the bot's Terms of Service.")
    async def terms(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 Terms of Service",
            description=(
                "By using this bot, you agree to abide by Discord's Terms of Service and Community Guidelines.\n\n"
                "**Rules:**\n"
                "• No exploiting or bug abuse for virtual currency.\n"
                "• No submitting illegal or highly explicit media to the games.\n"
                "• Virtual currency (Supercoins) holds no real-world value.\n\n"
                "We reserve the right to blacklist users for violating these rules."
            ),
            color=discord.Color.gold()
        )
        
        # In a real production environment, you would link to the hosted URL here
        embed.add_field(
            name="Full Terms of Service",
            value="[Click here to view our complete Terms of Service](https://example.com/terms)"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LegalCog(bot))
