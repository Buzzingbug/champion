import os
import re

def update_file(filename, replacements):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: Could not find '{old}' in {filename}")
            
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. smashorpass.py
sop_replacements = [
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(""",
        """
        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute("""
    ),
    (
        """f"Reward: **{reward} Supercoins**\\n\"""",
        """f"Reward: **{reward} {coin_name}**\\n\""""
    )
]

# 2. kfm.py
kfm_replacements = [
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(""",
        """
        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute("""
    ),
    (
        """f"Reward: **{reward} Supercoins**\\n\"""",
        """f"Reward: **{reward} {coin_name}**\\n\""""
    )
]

# 3. leftorright.py
lor_replacements = [
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(""",
        """
        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute("""
    ),
    (
        """f"Reward: **{reward} Supercoins**\\n\"""",
        """f"Reward: **{reward} {coin_name}**\\n\""""
    )
]

# 4. puzzle.py
puzzle_replacements = [
    (
        """
                config = await connection.fetchrow(
                    "SELECT reward_amount FROM puzzle_configs WHERE guild_id = $1",
                    record['guild_id']
                )
                reward = config['reward_amount'] if config else 100""",
        """
                config = await connection.fetchrow(
                    "SELECT reward_amount FROM puzzle_configs WHERE guild_id = $1",
                    record['guild_id']
                )
                reward = config['reward_amount'] if config else 100
                
                coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", record['guild_id'])
                coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'"""
    ),
    (
        """await interaction.response.send_message(f"🎉 **Correct!** You've solved the puzzle and earned **{reward} Supercoins**!")""",
        """await interaction.response.send_message(f"🎉 **Correct!** You've solved the puzzle and earned **{reward} {coin_name}**!")"""
    ),
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(""",
        """
        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute("""
    ),
    (
        """f"Reward: **{reward} Supercoins**\"""",
        """f"Reward: **{reward} {coin_name}**\""""
    ),
    (
        """
        # Fetch config
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle_configs WHERE guild_id = $1",
                interaction.guild.id
            )""",
        """
        # Fetch config
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'"""
    ),
    (
        """to win **{config['reward_amount']} Supercoins**."
            )""",
        """to win **{config['reward_amount']} {coin_name}**."
            )"""
    )
]

# 5. puzzle2.py
puzzle2_replacements = [
    (
        """def __init__(self, db_pool, puzzle_message_id: int, original_author_id: int, original_msg_jump_url: str, pieces: list, board: list, empty_idx: int, reward: int, guild_id: int, channel_id: int):""",
        """def __init__(self, db_pool, puzzle_message_id: int, original_author_id: int, original_msg_jump_url: str, pieces: list, board: list, empty_idx: int, reward: int, guild_id: int, channel_id: int, coin_name: str):"""
    ),
    (
        """
        self.reward = reward
        self.guild_id = guild_id
        self.channel_id = channel_id""",
        """
        self.reward = reward
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.coin_name = coin_name"""
    ),
    (
        """embed.description = f"**Solved by {interaction.user.mention}!**\\nThey earned **{self.reward} Supercoins**." """,
        """embed.description = f"**Solved by {interaction.user.mention}!**\\nThey earned **{self.reward} {self.coin_name}**." """
    ),
    (
        """content=f"🎉 **Congratulations!** You solved the puzzle and earned {self.reward} Supercoins!\\n[View Original Message]({self.original_msg_jump_url})",""",
        """content=f"🎉 **Congratulations!** You solved the puzzle and earned {self.reward} {self.coin_name}!\\n[View Original Message]({self.original_msg_jump_url})","""
    ),
    (
        """
            config = await connection.fetchrow(
                "SELECT reward_amount FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            reward = config['reward_amount'] if config else 100""",
        """
            config = await connection.fetchrow(
                "SELECT reward_amount FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            reward = config['reward_amount'] if config else 100
            
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'"""
    ),
    (
        """
            reward=reward,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id
        )""",
        """
            reward=reward,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            coin_name=coin_name
        )"""
    ),
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            await connection.execute(""",
        """
        async with self.bot.db_pool.acquire() as connection:
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'
            await connection.execute("""
    ),
    (
        """f"Reward: **{reward} Supercoins**\"""",
        """f"Reward: **{reward} {coin_name}**\""""
    ),
    (
        """
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )""",
        """
        async with self.bot.db_pool.acquire() as connection:
            config = await connection.fetchrow(
                "SELECT * FROM puzzle2_configs WHERE guild_id = $1",
                interaction.guild.id
            )
            coin_record = await connection.fetchrow("SELECT coin_name FROM server_settings WHERE guild_id = $1", interaction.guild.id)
            coin_name = coin_record['coin_name'] if coin_record else 'Supercoins'"""
    ),
    (
        """to earn **{config['reward_amount']} Supercoins**."
            )""",
        """to earn **{config['reward_amount']} {coin_name}**."
            )"""
    )
]

update_file('cogs/smashorpass.py', sop_replacements)
update_file('cogs/kfm.py', kfm_replacements)
update_file('cogs/leftorright.py', lor_replacements)
update_file('cogs/puzzle.py', puzzle_replacements)
update_file('cogs/puzzle2.py', puzzle2_replacements)
