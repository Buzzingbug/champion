from collections import defaultdict
import datetime
import discord
from discord.ext import commands, tasks

class ActivityTrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # cache structure: { (user_id, guild_id): {'messages_sent': 0, 'media_shared': 0, 'words_typed': 0, 'night_owl_msgs': 0, 'voice_minutes': 0} }
        self.activity_cache = defaultdict(lambda: {'messages_sent': 0, 'media_shared': 0, 'words_typed': 0, 'night_owl_msgs': 0, 'voice_minutes': 0})
        self.voice_states = {} # user_id -> join_time
        
        self.flush_cache.start()

    def cog_unload(self):
        self.flush_cache.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        key = (message.author.id, message.guild.id)
        
        self.activity_cache[key]['messages_sent'] += 1
        
        words = len(message.content.split())
        self.activity_cache[key]['words_typed'] += words
        
        if message.attachments:
            self.activity_cache[key]['media_shared'] += len(message.attachments)
            
        # Check if night owl (1 AM - 5 AM UTC)
        hour = message.created_at.hour
        if 1 <= hour <= 5:
            self.activity_cache[key]['night_owl_msgs'] += 1
            
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
            
        # Joined voice
        if before.channel is None and after.channel is not None:
            self.voice_states[member.id] = discord.utils.utcnow()
            
        # Left voice
        elif before.channel is not None and after.channel is None:
            join_time = self.voice_states.pop(member.id, None)
            if join_time:
                duration = discord.utils.utcnow() - join_time
                minutes = int(duration.total_seconds() / 60)
                if minutes > 0:
                    key = (member.id, member.guild.id)
                    self.activity_cache[key]['voice_minutes'] += minutes

    @tasks.loop(minutes=1)
    async def flush_cache(self):
        if not self.bot.db_pool or not self.activity_cache:
            return
            
        # Copy and clear cache safely
        cache_copy = dict(self.activity_cache)
        self.activity_cache.clear()
        
        # Calculate streak logic per user
        today = discord.utils.utcnow().date()
        
        async with self.bot.db_pool.acquire() as connection:
            async with connection.transaction():
                for (user_id, guild_id), stats in cache_copy.items():
                    # Check streak
                    record = await connection.fetchrow(
                        "SELECT current_streak, longest_streak, last_active_date FROM user_activity WHERE user_id = $1 AND guild_id = $2",
                        user_id, guild_id
                    )
                    
                    if record:
                        last_date = record['last_active_date']
                        current_streak = record['current_streak']
                        longest_streak = record['longest_streak']
                        
                        if last_date == today:
                            # Already active today, streak is same
                            pass
                        elif last_date == today - datetime.timedelta(days=1):
                            # Active yesterday, streak continues
                            current_streak += 1
                            longest_streak = max(current_streak, longest_streak)
                        else:
                            # Streak broken
                            current_streak = 1
                            longest_streak = max(current_streak, longest_streak)
                    else:
                        current_streak = 1
                        longest_streak = 1
                    
                    await connection.execute("""
                        INSERT INTO user_activity (user_id, guild_id, messages_sent, media_shared, words_typed, night_owl_msgs, voice_minutes, current_streak, longest_streak, last_active_date)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (user_id, guild_id) DO UPDATE SET
                            messages_sent = user_activity.messages_sent + EXCLUDED.messages_sent,
                            media_shared = user_activity.media_shared + EXCLUDED.media_shared,
                            words_typed = user_activity.words_typed + EXCLUDED.words_typed,
                            night_owl_msgs = user_activity.night_owl_msgs + EXCLUDED.night_owl_msgs,
                            voice_minutes = user_activity.voice_minutes + EXCLUDED.voice_minutes,
                            current_streak = EXCLUDED.current_streak,
                            longest_streak = EXCLUDED.longest_streak,
                            last_active_date = EXCLUDED.last_active_date
                    """, user_id, guild_id, stats['messages_sent'], stats['media_shared'], stats['words_typed'], stats['night_owl_msgs'], stats['voice_minutes'], current_streak, longest_streak, today)

    @flush_cache.before_loop
    async def before_flush(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ActivityTrackerCog(bot))
