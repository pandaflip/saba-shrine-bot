import discord
from discord.ext import commands
from discord import app_commands
from data.db import get_connection

class ShrineSetupView(discord.ui.View):
    def __init__(self, channels):
        super().__init__(timeout=60)
        options = [discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels[:25]]

        self.add_item(ChannelSelect("Select Prayer Channel", "prayer_channel", options))
        self.add_item(ChannelSelect("Select Log Channel", "log_channel", options))
        self.add_item(ChannelSelect("Select Rewards Channel", "rewards_channel", options))
        self.add_item(SaveConfigButton())

class ChannelSelect(discord.ui.Select):
    def __init__(self, placeholder, key, options):
        self.key = key
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.__setattr__(self.key, int(self.values[0]))
        await interaction.response.send_message(f"✅ {self.placeholder} set.", ephemeral=True)

class SaveConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Save Shrine Config", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not all([view.prayer_channel, view.log_channel, view.rewards_channel]):
            await interaction.response.send_message("❌ Please select all channels before saving.", ephemeral=True)
            return

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    REPLACE INTO config (guild_id, key_name, value)
                    VALUES (%s, %s, %s), (%s, %s, %s), (%s, %s, %s)
                """, (
                    interaction.guild.id, "prayer_channel_id", view.prayer_channel,
                    interaction.guild.id, "log_channel_id", view.log_channel,
                    interaction.guild.id, "rewards_channel_id", view.rewards_channel
                ))
                conn.commit()
            await interaction.response.send_message("✅ Shrine configuration saved!", ephemeral=True)
        finally:
            conn.close()

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sabadmin_setupshop", description="Set up the shop embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_shop(self, interaction: discord.Interaction):
        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM shop_items")
                items = cursor.fetchall()

            embed = discord.Embed(title="Shrine Shop", color=discord.Color.purple())
            for item in items:
                embed.add_field(
                    name=f"{item['name']} [{item['price']} blessings]",
                    value=f"{item['description']}\nCategory: {item['category']}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)
        finally:
            conn.close()

    @app_commands.command(name="sabadmin_setup", description="Configure shrine channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_channels(self, interaction: discord.Interaction):
        view = ShrineSetupView(interaction.guild.text_channels)
        await interaction.response.send_message("🔐 Select shrine-related channels:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
