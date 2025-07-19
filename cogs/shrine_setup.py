# cogs/shrine_setup.py
import discord
from discord.ext import commands
from discord import app_commands
from data.db import update_config

class ShrineSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.prayer_channel = None
        self.reward_channel = None

    @discord.ui.channel_select(
        placeholder="Select the prayer channel (typically, the #paper-boat)",
        channel_types=[discord.ChannelType.text]
    )
    async def select_prayer_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.prayer_channel = select.values[0]
        await interaction.response.send_message(
            f"📿 Prayer channel set to: {self.prayer_channel.mention}",
            ephemeral=True
        )

    @discord.ui.channel_select(
        placeholder="Select the reward channel (the channel where the comm will be sent)",
        channel_types=[discord.ChannelType.text]
    )
    async def select_reward_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.reward_channel = select.values[0]
        await interaction.response.send_message(
            f"🎁 Reward channel set to: {self.reward_channel.mention}",
            ephemeral=True
        )

    @discord.ui.button(label="✅ Confirm Setup", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.prayer_channel or not self.reward_channel:
            await interaction.response.send_message(
                "⚠️ Please select both channels before confirming.",
                ephemeral=True
            )
            return

        # Update the config table
        update_config("prayer_channel_id", str(self.prayer_channel.id))
        update_config("reward_channel_id", str(self.reward_channel.id))

        await interaction.response.send_message(
            f"✅ Shrine setup complete!\n"
            f"- Prayer Channel: {self.prayer_channel.mention}\n"
            f"- Reward Channel: {self.reward_channel.mention}",
            ephemeral=False
        )
        self.stop()


class ShrineSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shrinesetup", description="Setup the shrine: prayer and reward channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def shrine_setup(self, interaction: discord.Interaction):
        """Admin-only setup for defining prayer and reward channels."""
        view = ShrineSetupView()
        await interaction.response.send_message(
            "🛠️ Shrine Setup:\nPlease select the channels below to configure your shrine system.",
            view=view,
            ephemeral=True
        )

  @app_commands.command(name="viewconfig", description="View the current shrine configuration.")
    @app_commands.checks.has_permissions(administrator=True)
    async def view_config(self, interaction: discord.Interaction):
        """Admin-only command to check current config (prayer/reward channels)."""
        from data.db import get_config

        prayer_id = get_config("prayer_channel_id")
        reward_id = get_config("reward_channel_id")

        guild = interaction.guild
        prayer_channel = guild.get_channel(int(prayer_id)) if prayer_id else None
        reward_channel = guild.get_channel(int(reward_id)) if reward_id else None

        if not prayer_channel and not reward_channel:
            await interaction.response.send_message(
                "⚠️ No shrine configuration found. Use `/shrinesetup` to initialize it.",
                ephemeral=True
            )
            return

        message = "**🔧 Current Shrine Configuration:**\n"
        message += f"📿 Prayer Channel: {prayer_channel.mention if prayer_channel else '*Not Set*'}\n"
        message += f"🎁 Reward Channel: {reward_channel.mention if reward_channel else '*Not Set*'}"

        await interaction.response.send_message(message, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShrineSetup(bot))
