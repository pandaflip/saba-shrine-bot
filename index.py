import discord
from discord.ext import commands
import os
import asyncio
from utils import config

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user.name}")
    await bot.tree.sync()

async def main():
    async with bot:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
        token = os.getenv("DISCORD_TOKEN")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())

# utils/config.py (utils/config.py)
import json
import os

CONFIG_PATH = "data/config.json"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def update_config(key, value):
    data = load_config()
    data[key] = value
    save_config(data)
    return data
