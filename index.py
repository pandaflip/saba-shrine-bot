import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Charger les cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

# Lancer le bot
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    bot.run(os.getenv('DISCORD_TOKEN'))
