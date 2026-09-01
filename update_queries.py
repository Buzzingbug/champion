import os
import glob

replacements = [
    {
        "pattern": """                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3""",
        "files": ["cogs/kfm.py", "cogs/leftorright.py", "cogs/smashorpass.py", "cogs/weekly_winners.py"],
        "replacement": """                INSERT INTO economy (guild_id, user_id, supercoins, lifetime_games) 
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3, lifetime_games = economy.lifetime_games + $3"""
    },
    {
        "pattern": """                    INSERT INTO economy (guild_id, user_id, supercoins) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id, user_id) 
                    DO UPDATE SET supercoins = economy.supercoins + $3""",
        "files": ["cogs/puzzle.py", "cogs/puzzle2.py"],
        "replacement": """                    INSERT INTO economy (guild_id, user_id, supercoins, lifetime_games) 
                    VALUES ($1, $2, $3, $3)
                    ON CONFLICT (guild_id, user_id) 
                    DO UPDATE SET supercoins = economy.supercoins + $3, lifetime_games = economy.lifetime_games + $3"""
    },
    {
        "pattern": """                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3""",
        "files": ["cogs/category_rewards.py"],
        "replacement": """                INSERT INTO economy (guild_id, user_id, supercoins, lifetime_category) 
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3, lifetime_category = economy.lifetime_category + $3"""
    },
    {
        "pattern": """                INSERT INTO economy (guild_id, user_id, supercoins) 
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3""",
        "files": ["cogs/channel_rewards.py"],
        "replacement": """                INSERT INTO economy (guild_id, user_id, supercoins, lifetime_channel) 
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET supercoins = economy.supercoins + $3, lifetime_channel = economy.lifetime_channel + $3"""
    }
]

for item in replacements:
    for filename in item["files"]:
        path = os.path.join(r"c:\Users\Vibe\.Github\champion", filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if item["pattern"] in content:
                content = content.replace(item["pattern"], item["replacement"])
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {filename}")
            else:
                print(f"Pattern not found in {filename}")
        else:
            print(f"File not found: {filename}")
