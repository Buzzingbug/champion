import os
import re

cogs_dir = "c:/Users/Vibe/.Github/champion/cogs"
files = [
    ("kfm.py", "kfm"),
    ("smashorpass.py", "smash"),
    ("leftorright.py", "lor"),
    ("gatekeeper.py", "gate"),
    ("games.py", "games"),
    ("puzzle.py", "jigsaw"),
    ("puzzle2.py", "slider"),
    ("weekly_winners.py", "weekly"),
]

for filename, prefix in files:
    path = os.path.join(cogs_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Change class inheritance
    content = re.sub(r'class \w+\(commands\.GroupCog, group_name="[^"]+"\):', lambda m: m.group(0).split('(commands.GroupCog')[0] + '(commands.Cog):', content)
    
    # Change command names
    def repl(m):
        cmd = m.group(1)
        return f'@app_commands.command(name="{prefix}_{cmd}"'
        
    content = re.sub(r'@app_commands\.command\(name="([^"]+)"', repl, content)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
# Special handling for category_rewards.py which has two GroupCogs
path = os.path.join(cogs_dir, "category_rewards.py")
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('class CategoryRewardsCog(commands.GroupCog, group_name="category"):', 'class CategoryRewardsCog(commands.Cog):')
content = content.replace('class ChannelRewardsCog(commands.GroupCog, group_name="channel_reward"):', 'class ChannelRewardsCog(commands.Cog):')

# Since commands are named "setup", "remove", "config" in both classes, we can just split and replace manually.
lines = content.split('\n')
in_channel_reward = False
for i, line in enumerate(lines):
    if "class ChannelRewardsCog" in line:
        in_channel_reward = True
        
    m = re.search(r'@app_commands\.command\(name="([^"]+)"', line)
    if m:
        cmd = m.group(1)
        prefix = "channel" if in_channel_reward else "category"
        lines[i] = line.replace(f'name="{cmd}"', f'name="{prefix}_{cmd}"')
        
with open(path, "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))
    
print("Refactoring completed.")
