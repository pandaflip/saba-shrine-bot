import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = int(os.getenv("APPLICATION_ID"))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, application_id=APPLICATION_ID)

@bot.event
async def on_ready():
    logging.info(f"✅ Bot logged in as {bot.user}")
    try:
        await bot.tree.sync()
    except Exception as e:
        logging.warning(f"⚠️ Slash command sync failed: {e}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                print(f"Trying to load: cogs.{filename[:-3]}")
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logging.info(f"✅ Loaded cog: cogs.{filename[:-3]}")
            except Exception as e:
                logging.error(f"❌ Failed to load cog cogs.{filename[:-3]}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.loop.create_task(load_cogs())
    bot.run(TOKEN)
