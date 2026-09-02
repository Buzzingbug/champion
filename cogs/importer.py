import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

class ImporterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="importmee6", description="Migrate and import all member levels and message stats from MEE6.")
    @app_commands.checks.has_permissions(administrator=True)
    async def import_mee6(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("❌ Database is not connected.", ephemeral=True)
            return

        await interaction.response.defer()

        guild_id = interaction.guild.id
        imported_count = 0
        page = 0
        today = discord.utils.utcnow().date()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            while page < 20: # Cap at 2000 users to be safe
                url = f"https://mee6.xyz/api/plugins/levels/leaderboard/{guild_id}?page={page}"
                
                try:
                    async with session.get(url, timeout=15) as resp:
                        if resp.status in (401, 403):
                            await interaction.followup.send(
                                f"❌ **MEE6 Leaderboard is Private.**\n"
                                f"To import your data, please make sure **'Make my server's leaderboard public'** is enabled in your MEE6 Dashboard (under Levels plugin), then run this command again.\n"
                                f"Check here: <https://mee6.xyz/dashboard/{guild_id}/levels>"
                            )
                            return
                        elif resp.status == 404:
                            await interaction.followup.send(
                                f"❌ **MEE6 Leaderboard not found.**\n"
                                f"Could not find any active MEE6 leveling data for server ID `{guild_id}`. Please verify MEE6 has the Levels plugin active."
                            )
                            return
                        elif resp.status != 200:
                            await interaction.followup.send(f"❌ MEE6 API returned an error (HTTP {resp.status}). Please try again in a few moments.")
                            return

                        data = await resp.json()
                        players = data.get("players", [])

                        if not players:
                            break # No more players

                        async with self.bot.db_pool.acquire() as connection:
                            async with connection.transaction():
                                for p in players:
                                    try:
                                        user_id = int(p["id"])
                                        messages = p.get("message_count", 0)
                                        xp = p.get("xp", 0)

                                        # If message count wasn't directly supplied, approximate from XP
                                        if messages <= 0 and xp > 0:
                                            messages = int(xp / 10)

                                        words = messages * 10

                                        await connection.execute("""
                                            INSERT INTO user_activity (
                                                user_id, guild_id, messages_sent, media_shared, words_typed, 
                                                night_owl_msgs, voice_minutes, current_streak, longest_streak, last_active_date
                                            )
                                            VALUES ($1, $2, $3, 0, $4, 0, 0, 1, 1, $5)
                                            ON CONFLICT (user_id, guild_id) DO UPDATE SET
                                                messages_sent = GREATEST(user_activity.messages_sent, EXCLUDED.messages_sent),
                                                words_typed = GREATEST(user_activity.words_typed, EXCLUDED.words_typed),
                                                last_active_date = COALESCE(user_activity.last_active_date, EXCLUDED.last_active_date)
                                        """, user_id, guild_id, messages, words, today)
                                        
                                        imported_count += 1
                                    except Exception as err:
                                        print(f"Error importing user {p.get('id')}: {err}")
                                        continue

                        page += 1
                        await asyncio.sleep(0.5) # Graceful delay between pages
                except Exception as e:
                    print(f"Importer request error: {e}")
                    await interaction.followup.send(f"❌ Error communicating with MEE6 API: `{e}`")
                    return

        if imported_count == 0:
            await interaction.followup.send(
                f"⚠️ **No members found.**\n"
                f"MEE6 returned 0 members for this server. Check if MEE6 has recorded any messages yet: <https://mee6.xyz/leaderboard/{guild_id}>"
            )
        else:
            embed = discord.Embed(
                title="✨ MEE6 Migration Completed!",
                description=(
                    f"Successfully imported **{imported_count} members** from MEE6 into Champion!\n\n"
                    f"• All existing message counts & XP have been merged.\n"
                    f"• Try running **`/profile`** to view your updated Bento Card.\n"
                    f"• Try running **`/activemembers`** to view the updated server ranks!"
                ),
                color=discord.Color.gold()
            )
            embed.set_footer(text="Champion Migration Assistant")
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ImporterCog(bot))
