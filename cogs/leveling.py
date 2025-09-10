import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from colorama import Fore, Style
from config import EMBED_COLOR, LEVELS_FILE

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = self.load_levels()
        self.cooldowns = {}

    def load_levels(self):
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("The JSON file is corrupted. Creating a new one...")
                return {}
        return {}

    def save_levels(self):
        with open(LEVELS_FILE, 'w') as f:
            json.dump(self.levels, f, indent=4)

    def get_required_xp(self, level):
        return 100 + (level - 1) * 50
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild_id = str(after.id)
        guild_name = after.name

        if guild_id in self.levels:
            if self.levels[guild_id]["server_name"] != guild_name:
                self.levels[guild_id]["server_name"] = guild_name
                self.save_levels()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        member_id = str(message.author.id)
        guild_name = message.guild.name

        if guild_id not in self.levels:
            self.levels[guild_id] = {"server_name": guild_name, "members": {}}
        else:
            self.levels[guild_id]["server_name"] = guild_name

        if member_id not in self.levels[guild_id]["members"]:
            self.levels[guild_id]["members"][member_id] = {"xp": 0, "level": 1}

        if member_id in self.cooldowns:
            if self.cooldowns[member_id] > asyncio.get_event_loop().time():
                return
        self.cooldowns[member_id] = asyncio.get_event_loop().time() + 5

        xp_gain = random.randint(5, 15)
        self.levels[guild_id]["members"][member_id]["xp"] += xp_gain
        xp = self.levels[guild_id]["members"][member_id]["xp"]
        level = self.levels[guild_id]["members"][member_id]["level"]

        required_xp = self.get_required_xp(level)
        if xp >= required_xp:
            excess_xp = xp - required_xp
            self.levels[guild_id]["members"][member_id]["level"] += 1
            self.levels[guild_id]["members"][member_id]["xp"] = excess_xp

            new_level = self.levels[guild_id]["members"][member_id]["level"]
            await message.channel.send(f"{message.author.mention}, you leveled up to **{new_level}**!")

        self.save_levels()

    @app_commands.command(name="level", description="Shows the level and XP of a user.")
    @app_commands.describe(member="The user whose level you want to see.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        guild_id = str(interaction.guild.id)
        member_id = str(member.id)

        if guild_id in self.levels and member_id in self.levels[guild_id]["members"]:
            level = self.levels[guild_id]["members"][member_id]["level"]
            xp = self.levels[guild_id]["members"][member_id]["xp"]
            required_xp = self.get_required_xp(level)
            remaining_xp = required_xp - xp
            await interaction.response.send_message(
                f"{member.mention} is at level **{level}** with **{xp}** XP.\nNeeds **{remaining_xp} XP** more to level up!"
            )
        else:
            await interaction.response.send_message(f"{member.mention} has no levels recorded yet.")

    @app_commands.command(name="leaderboard", description="Shows the ranking of users with the most levels.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.levels or "members" not in self.levels[guild_id]:
            await interaction.response.send_message("There is no level data for this server yet.")
            return

        sorted_levels = sorted(
            self.levels[guild_id]["members"].items(),
            key=lambda x: (x[1]['level'], x[1]['xp']),
            reverse=True
        )

        leaderboard = []
        for i, (member_id, data) in enumerate(sorted_levels[:10], start=1):
            user = await self.bot.fetch_user(int(member_id))
            if user:
                if i == 1:
                    emoji = "🥇"
                    leaderboard.append(f"{emoji} **{user.name}** - Level: {data['level']} | XP: {data['xp']}")
                elif i == 2:
                    emoji = "🥈"
                    leaderboard.append(f"{emoji} **{user.name}** - Level: {data['level']} | XP: {data['xp']}")
                elif i == 3:
                    emoji = "🥉"
                    leaderboard.append(f"{emoji} **{user.name}** - Level: {data['level']} | XP: {data['xp']}")
                else:
                    leaderboard.append(f"▫️ **{i}. {user.name}** - Level: {data['level']} | XP: {data['xp']}")

        if leaderboard:
            embed = discord.Embed(
                title="Level Leaderboard",
                description="\n".join(leaderboard),
                color=EMBED_COLOR
            )
            embed.set_footer(text="Keep chatting to level up!")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No one is on the leaderboard yet.")


async def setup(bot):
    await bot.add_cog(Leveling(bot))
