# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
import json
import os

CONFIG_PATH = "data/config.json"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def save_config(self, data):
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return {}
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

    @app_commands.command(name="set-prayer-channel", description="Set the prayer channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prayer_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = self.load_config()
        config["prayer_channel_id"] = channel.id
        self.save_config(config)
        await interaction.response.send_message(f"✅ Prayer channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="set-reward-channel", description="Set the reward channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_reward_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = self.load_config()
        config["reward_channel_id"] = channel.id
        self.save_config(config)
        await interaction.response.send_message(f"✅ Reward channel set to {channel.mention}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
