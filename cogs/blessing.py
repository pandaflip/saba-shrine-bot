import discord
from discord import app_commands
from discord.ext import commands
from data.db import get_connection
import json
import os

# Load ranks.json
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RANKS_PATH = os.path.join(BASE_DIR, "data", "ranks.json")
with open(RANKS_PATH, "r", encoding="utf-8") as f:
    RANKS = json.load(f)

def get_rank(prayers):
    current = RANKS[0]
    next_rank = None

    for i, rank in enumerate(RANKS):
        if prayers >= rank["min"]:
            current = rank
            if i + 1 < len(RANKS):
                next_rank = RANKS[i + 1]
        else:
            break
    return current, next_rank

def make_progress_bar(current, total, length=10):
    filled = int((current / total) * length)
    return "▰" * filled + "▱" * (length - filled)

class Blessing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="blessing_gift", description="Gift blessings to another user.")
    @app_commands.describe(user="Recipient of the blessings", amount="Number of blessings to gift")
    async def blessing_gift(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        giver_id = interaction.user.id
        receiver_id = user.id

        if giver_id == receiver_id:
            await interaction.response.send_message("❌ You cannot gift blessings to yourself.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("❌ The amount must be greater than 0.", ephemeral=True)
            return

        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT blessings FROM users WHERE user_id = %s", (giver_id,))
                row = cursor.fetchone()
                if not row or row["blessings"] < amount:
                    await interaction.response.send_message("😔 You don't have enough blessings.", ephemeral=True)
                    return

                cursor.execute("UPDATE users SET blessings = blessings - %s WHERE user_id = %s", (amount, giver_id))
                cursor.execute("""
                    INSERT INTO users (user_id, blessings, prayers)
                    VALUES (%s, %s, 0)
                    ON DUPLICATE KEY UPDATE blessings = blessings + %s
                """, (receiver_id, amount, amount))
                conn.commit()

            await interaction.response.send_message(
                f"💖 {interaction.user.mention} has gifted **{amount} blessings** to {user.mention}!"
            )
        finally:
            conn.close()

    @app_commands.command(name="blessing_profile", description="View your or another user's shrine profile.")
    @app_commands.describe(user="The user to view (leave blank for yourself)")
    async def blessing_profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        user_id = target.id

        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT blessings, prayers FROM users WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()

                if not row:
                    msg = f"{target.mention} hasn't prayed yet! 🙏" if user else "You haven't prayed yet! 🙏"
                    await interaction.response.send_message(msg, ephemeral=True)
                    return

                blessings = row["blessings"]
                prayers = row["prayers"]

                current_rank, next_rank = get_rank(prayers)

                if next_rank:
                    current_threshold = current_rank["min"]
                    next_threshold = next_rank["min"]
                    progress = prayers - current_threshold
                    needed = next_threshold - current_threshold
                    progress_bar = make_progress_bar(progress, needed)
                    progress_text = f"{progress} / {needed} → **{next_rank['name']}**"
                else:
                    progress_bar = "▰" * 10
                    progress_text = "🌟 You've reached the highest rank!"

                embed = discord.Embed(
                    title=f"{target.display_name}'s Shrine Profile",
                    color=discord.Color.purple()
                )
                embed.set_thumbnail(url=target.display_avatar.url)
                embed.add_field(name="💰 Blessings", value=f"{blessings}", inline=True)
                embed.add_field(name="🙏 Prayers", value=f"{prayers}", inline=True)
                embed.add_field(name="🏅 Rank", value=current_rank["name"], inline=False)
                embed.add_field(name="📈 Progress", value=f"{progress_bar}\n{progress_text}", inline=False)

                await interaction.response.send_message(embed=embed)
        finally:
            conn.close()

    @app_commands.command(name="blessing_leaderboard", description="Display the top users with most prayers.")
    async def blessing_leaderboard(self, interaction: discord.Interaction):
        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT user_id, blessings, prayers
                    FROM users
                    ORDER BY prayers DESC
                    LIMIT 10
                """)
                results = cursor.fetchall()

            if not results:
                await interaction.response.send_message("No one has prayed yet!", ephemeral=True)
                return

            leaderboard = ""
            for i, row in enumerate(results, start=1):
                member = interaction.guild.get_member(row["user_id"])
                name = member.display_name if member else f"<@{row['user_id']}>"
                leaderboard += f"**{i}.** {name} — {row['prayers']} prayers, {row['blessings']} blessings\n"

            embed = discord.Embed(title="🏆 Top Worshippers", description=leaderboard, color=discord.Color.gold())
            await interaction.response.send_message(embed=embed)
        finally:
            conn.close()

async def setup(bot):
    await bot.add_cog(Blessing(bot))
