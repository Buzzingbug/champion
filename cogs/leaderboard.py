import discord
from discord import app_commands
from discord.ext import commands

async def generate_leaderboard_embed(bot, guild, mode, page):
    limit = 10
    offset = (page - 1) * limit
    
    async with bot.db_pool.acquire() as connection:
        coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", guild.id)
        coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
        
        embed = discord.Embed(title="🏆 Economy Leaderboard", color=discord.Color.gold())
        
        if mode == "global":
            # Global
            total_circ = await connection.fetchval("SELECT SUM(supercoins) FROM economy WHERE guild_id = $1", guild.id)
            total_circ = total_circ if total_circ else 0
            embed.description = f"**Total Circulation:** {total_circ:,} {coin_name}\n\n"
            
            users = await connection.fetch(
                "SELECT user_id, supercoins FROM economy WHERE guild_id = $1 ORDER BY supercoins DESC LIMIT $2 OFFSET $3",
                guild.id, limit + 1, offset
            )
            has_more = len(users) > limit
            users = users[:limit]
            
            if not users:
                embed.description += "No users have any coins yet!"
                
            for i, u in enumerate(users, start=offset + 1):
                embed.add_field(name=f"#{i}", value=f"<@{u['user_id']}> — **{u['supercoins']:,} {coin_name}**", inline=False)
                
        elif mode.startswith("cat_"):
            cat_id = int(mode.split("_")[1])
            cat = guild.get_channel(cat_id)
            embed.title = f"📂 Top Earners: {cat.name if cat else 'Category'}"
            
            users = await connection.fetch(
                "SELECT user_id, SUM(earned_today) as total FROM category_earnings WHERE category_id = $1 GROUP BY user_id ORDER BY total DESC LIMIT $2 OFFSET $3",
                cat_id, limit + 1, offset
            )
            has_more = len(users) > limit
            users = users[:limit]
            
            if not users:
                embed.description = "No one has earned coins from this category yet!"
                
            for i, u in enumerate(users, start=offset + 1):
                embed.add_field(name=f"#{i}", value=f"<@{u['user_id']}> — **{u['total']:,} {coin_name}**", inline=False)
                
        elif mode.startswith("chan_"):
            chan_id = int(mode.split("_")[1])
            chan = guild.get_channel(chan_id)
            embed.title = f"💬 Top Earners: {chan.name if chan else 'Channel'}"
            
            users = await connection.fetch(
                "SELECT user_id, SUM(earned_today) as total FROM channel_earnings WHERE channel_id = $1 GROUP BY user_id ORDER BY total DESC LIMIT $2 OFFSET $3",
                chan_id, limit + 1, offset
            )
            has_more = len(users) > limit
            users = users[:limit]
            
            if not users:
                embed.description = "No one has earned coins from this channel yet!"
                
            for i, u in enumerate(users, start=offset + 1):
                embed.add_field(name=f"#{i}", value=f"<@{u['user_id']}> — **{u['total']:,} {coin_name}**", inline=False)
                
    embed.set_footer(text=f"Page {page}")
    return embed, has_more


class LeaderboardSelect(discord.ui.Select):
    def __init__(self, bot, guild, current_mode="global"):
        self.bot = bot
        options = [
            discord.SelectOption(label="🌍 Global Richest", value="global", description="Top richest users overall", default=(current_mode=="global"))
        ]
        
        guild_cats = [c for c in bot.cache['categories'].values() if c['guild_id'] == guild.id]
        for c in guild_cats[:12]:
            cat = guild.get_channel(c['category_id'])
            if cat:
                options.append(discord.SelectOption(label=f"📂 Category: {cat.name}", value=f"cat_{c['category_id']}", default=(current_mode==f"cat_{c['category_id']}")))
                
        guild_chans = [c for c in bot.cache['channel_rewards'].values() if c['guild_id'] == guild.id]
        for c in guild_chans[:12]:
            chan = guild.get_channel(c['channel_id'])
            if chan:
                options.append(discord.SelectOption(label=f"💬 Channel: {chan.name}", value=f"chan_{c['channel_id']}", default=(current_mode==f"chan_{c['channel_id']}")))
                
        super().__init__(placeholder="Select a Leaderboard...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.mode = self.values[0]
        self.view.page = 1
        
        for opt in self.options:
            opt.default = (opt.value == self.view.mode)
            
        await self.view.update_leaderboard(interaction)


class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild, page=1, mode="global"):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild = guild
        self.page = page
        self.mode = mode
        
        self.add_item(LeaderboardSelect(bot, guild, current_mode=mode))
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True, row=1)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.update_leaderboard(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_leaderboard(interaction)
        
    async def update_leaderboard(self, interaction: discord.Interaction):
        # Update buttons
        self.children[1].disabled = (self.page == 1) # Prev
        
        embed, has_more = await generate_leaderboard_embed(self.bot, self.guild, self.mode, self.page)
        self.children[2].disabled = not has_more # Next
        
        await interaction.response.edit_message(embed=embed, view=self)


class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the server's economy leaderboard.")
    @app_commands.checks.has_permissions(administrator=True)
    async def leaderboard(self, interaction: discord.Interaction):
        if not self.bot.db_pool:
            await interaction.response.send_message("Database is not connected. Please try again later.", ephemeral=True)
            return

        await interaction.response.defer()
        
        embed, has_more = await generate_leaderboard_embed(self.bot, interaction.guild, "global", 1)
        
        view = LeaderboardView(self.bot, interaction.guild)
        view.children[1].disabled = True
        view.children[2].disabled = not has_more
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
