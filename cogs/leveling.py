import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from config import EMBED_COLOR, LEVELS_FILE

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = self.loadLevels()
        self.cooldowns = {}

    def loadLevels(self):
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("The JSON file is corrupted. Creating a new one...")
                return {}
        return {}

    def saveLevels(self):
        with open(LEVELS_FILE, 'w') as f:
            json.dump(self.levels, f, indent=4)

    def getRequiredXp(self, level):
        return 100 + (level - 1) * 50

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guildId = str(message.guild.id)
        memberId = str(message.author.id)
        guildName = message.guild.name

        if guildId not in self.levels:
            self.levels[guildId] = {"serverName": guildName, "members": {}}

        if memberId not in self.levels[guildId]["members"]:
            self.levels[guildId]["members"][memberId] = {"xp": 0, "level": 1}

        if memberId in self.cooldowns:
            if self.cooldowns[memberId] > asyncio.get_event_loop().time():
                return
        self.cooldowns[memberId] = asyncio.get_event_loop().time() + 5

        xpGain = random.randint(5, 15)
        self.levels[guildId]["members"][memberId]["xp"] += xpGain
        xp = self.levels[guildId]["members"][memberId]["xp"]
        level = self.levels[guildId]["members"][memberId]["level"]

        requiredXp = self.getRequiredXp(level)
        if xp >= requiredXp:
            excessXp = xp - requiredXp
            self.levels[guildId]["members"][memberId]["level"] += 1
            self.levels[guildId]["members"][memberId]["xp"] = excessXp

            newLevel = self.levels[guildId]["members"][memberId]["level"]
            await message.channel.send(f"{message.author.mention}, you leveled up to **{newLevel}**!")

        self.saveLevels()

    @app_commands.command(name="level", description="Shows the level and XP of a user.")
    @app_commands.describe(member="The user whose level you want to see.")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        guildId = str(interaction.guild.id)
        memberId = str(member.id)

        if guildId in self.levels and memberId in self.levels[guildId]["members"]:
            level = self.levels[guildId]["members"][memberId]["level"]
            xp = self.levels[guildId]["members"][memberId]["xp"]
            requiredXp = self.getRequiredXp(level)
            remainingXp = requiredXp - xp
            await interaction.response.send_message(
                f"{member.mention} is at level **{level}** with **{xp}** XP.\nNeeds **{remainingXp} XP** more to level up!"
            )
        else:
            await interaction.response.send_message(f"{member.mention} has no levels recorded yet.")

    @app_commands.command(name="leaderboard", description="Shows the ranking of users with the most levels.")
    async def leaderboard(self, interaction: discord.Interaction):
        guildId = str(interaction.guild.id)

        if guildId not in self.levels or "members" not in self.levels[guildId]:
            await interaction.response.send_message("There is no level data for this server yet.")
            return

        sortedLevels = sorted(
            self.levels[guildId]["members"].items(), key=lambda x: x[1]['level'], reverse=True  # Ordena por nível
        )

        leaderboard = []
        for i, (memberId, data) in enumerate(sortedLevels[:10], start=1):
            user = self.bot.get_user(int(memberId))
            if user:
                if i == 1:
                    emoji = "🥇"
                elif i == 2:
                    emoji = "🥈"
                elif i == 3:
                    emoji = "🥉"
                else:
                    emoji = "🏅"

                leaderboard.append(f"{emoji} **{i}. {user.name}** - Level: {data['level']} | XP: {data['xp']}")

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

    @level.error
    @leaderboard.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandError):
            await interaction.response.send_message("An error occurred.", ephemeral=True)



async def setup(bot):
    await bot.add_cog(Leveling(bot))
