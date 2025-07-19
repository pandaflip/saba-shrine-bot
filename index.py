# index.py
import discord
from discord.ext import commands
import os
import asyncio
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Important pour détecter les prières

class ShrineBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db = None

    async def setup_hook(self):
        # Connexion à la base de données
        self.db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            autocommit=True
        )

        # Chargement des cogs
        for cog in ["admin", "blessings", "pray", "shop", "shrine_setup"]:
            await self.load_extension(f"cogs.{cog}")

        # Synchroniser les commandes (slash)
        await self.tree.sync()
        print("[✅] Commandes slash synchronisées")

    async def close(self):
        if self.db:
            self.db.close()
        await super().close()

bot = ShrineBot()

@bot.event
async def on_ready():
    print(f"[🚀] Connecté en tant que {bot.user} (ID: {bot.user.id})")

# Lancement du bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN manquant dans le fichier .env")
    else:
        asyncio.run(bot.start(token))
