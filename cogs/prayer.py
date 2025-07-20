import discord
from discord.ext import commands
from discord import app_commands
from data.db import get_connection
import json
import random
import datetime
import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_PATH = os.path.join(BASE_DIR, "data", "prayer_messages.json")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    PRAYER_MESSAGES = json.load(f)

class Prayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                # Get shrine channel for this guild
                cursor.execute("SELECT value FROM config WHERE guild_id = %s AND key_name = 'prayer_channel_id'", (message.guild.id,))
                result = cursor.fetchone()

                if not result or message.channel.id != int(result["value"]):
                    return

                user_id = message.author.id

                # Skip cooldown check for administrators
                is_admin = message.author.guild_permissions.administrator

                if not is_admin:
                    cursor.execute("SELECT last_pray FROM users WHERE user_id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    now = datetime.datetime.utcnow()

                    if user_row and user_row["last_pray"]:
                        delta = (now - user_row["last_pray"]).total_seconds()
                        if delta < 7200:  # 2 hours
                            logging.debug(f"User {user_id} on cooldown ({delta:.0f}s left)")
                            return

                # Make sure user is in DB
                cursor.execute("INSERT IGNORE INTO users (user_id, blessings, prayers) VALUES (%s, 0, 0)", (user_id,))

                # Roll rarity
                roll = random.random() * 100
                if roll < 1:
                    rarity, reward = "Mythic", 25
                elif roll < 5:
                    rarity, reward = "Epic", 10
                elif roll < 15:
                    rarity, reward = "Rare", 5
                elif roll < 40:
                    rarity, reward = "Uncommon", 3
                else:
                    rarity, reward = "Common", 1

                # Emoji bonus
                if ":sabapray:" in message.content or ":tier6:" in message.content:
                    reward += 1

                now = datetime.datetime.utcnow()
                cursor.execute("""
                    UPDATE users SET
                        blessings = blessings + %s,
                        prayers = prayers + 1,
                        last_pray = %s
                    WHERE user_id = %s
                """, (reward, now, user_id))
                conn.commit()

                # Select message
                entry = random.choices(
                    PRAYER_MESSAGES[rarity],
                    weights=[m["weight"] for m in PRAYER_MESSAGES[rarity]],
                    k=1
                )[0]

                embed = discord.Embed(
                    title=f"{rarity} Prayer ✨",
                    description=entry["message"],
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"+{reward} blessings")
                await message.channel.send(embed=embed)

        finally:
            conn.close()

async def setup(bot):
    await bot.add_cog(Prayer(bot))
