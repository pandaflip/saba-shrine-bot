# cogs/pray.py
import discord
from discord.ext import commands
import random
import json
import os

PRAYER_MESSAGES_PATH = "data/prayer_messages.json"

RARITY_PROBABILITIES = {
    "super_rare": 5,
    "rare": 10,
    "strong": 25,
    "normal": 60
}

BLESSINGS_REWARDS = {
    "normal": 1,
    "strong": 3,
    "rare": 5,
    "super_rare": 10
}

BONUS_EMOJIS = {
    ":sabapray:": 1,
    ":tier6:": 1
}

class Pray(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = self.load_prayer_messages()

    def load_prayer_messages(self):
        with open(PRAYER_MESSAGES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_config_value(self, key):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT value FROM config WHERE key_name = %s", (key,))
        result = cursor.fetchone()
        return int(result[0]) if result else None

    def get_random_reward(self):
        rarity = random.choices(
            list(RARITY_PROBABILITIES.keys()),
            weights=RARITY_PROBABILITIES.values(),
            k=1
        )[0]
        message = random.choice(self.messages[rarity])
        base_blessings = BLESSINGS_REWARDS[rarity]
        return rarity, message, base_blessings

    def add_blessings(self, user_id: int, amount: int):
        cursor = self.bot.db.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, blessings) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE blessings = blessings + %s",
            (user_id, amount, amount)
        )
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        prayer_channel_id = self.get_config_value("prayer_channel_id")
        if message.channel.id != prayer_channel_id:
            return

        rarity, text, base = self.get_random_reward()
        bonus = sum(b for emoji, b in BONUS_EMOJIS.items() if emoji in message.content)
        total = base + bonus

        self.add_blessings(message.author.id, total)

        # Réponse dans le salon
        response = (
            f"{text}\n"
            f"**{message.author.mention}**, you received **{total} Blessings**!\n"
            f"*(Base: {base}, Bonus: +{bonus})* :sabapray:"
        )

        await message.reply(response)

async def setup(bot):
    await bot.add_cog(Pray(bot))
