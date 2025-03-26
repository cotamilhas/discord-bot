import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, Style
from config import SERVER_OPTIONS, EMBED_COLOR
from datetime import datetime, timezone


class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def loadConfig(self):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def saveConfig(self, data):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def getGuildConfig(self, guild_id):
        data = self.loadConfig()
        return data.get(str(guild_id), {})

    def updateGuildConfig(self, guild_id, key, value):
        data = self.loadConfig()
        guild_id = str(guild_id)
        if guild_id not in data:
            data[guild_id] = {"server_name": "Unknown"}
        data[guild_id][key] = value
        self.saveConfig(data)

    def add_log(self, message):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        if len(self.log_messages) > 100:  # Limita o número de logs para não crescer indefinidamente
            self.log_messages.pop(0)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        print(f"Message edited by {before.author} in {before.channel}")
        guild_config = self.getGuildConfig(before.guild.id)
        channel_id = guild_config.get("log_channel")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(title="Message Edited", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Channel", value=before.channel.mention, inline=False)
                embed.add_field(name="Author", value=before.author.mention, inline=False)
                embed.add_field(name="Before", value=before.content or "No content", inline=False)
                embed.add_field(name="After", value=after.content or "No content", inline=False)
                embed.set_thumbnail(url=before.author.avatar.url)
                embed.set_footer(text="Edited at", icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)
                self.add_log(f"Message edited in {before.channel.name} by {before.author.name}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            print(f"Voice state updated for {member}")
            guild_config = self.getGuildConfig(member.guild.id)
            channel_id = guild_config.get("log_channel")
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    if before.channel is None:
                        title = "Joined Voice Channel"
                    elif after.channel is None:
                        title = "Left Voice Channel"
                    else:
                        title = "Switched Voice Channels"
                    
                    embed = discord.Embed(title=title, color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
                    embed.add_field(name="Member", value=member.mention, inline=False)
                    if before.channel is None:
                        embed.add_field(name="Action", value="Joined voice channel", inline=False)
                        embed.add_field(name="Channel", value=after.channel.mention, inline=False)
                    elif after.channel is None:
                        embed.add_field(name="Action", value="Left voice channel", inline=False)
                        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
                    else:
                        embed.add_field(name="Action", value="Switched voice channels", inline=False)
                        embed.add_field(name="Before", value=before.channel.mention, inline=False)
                        embed.add_field(name="After", value=after.channel.mention, inline=False)
                    embed.set_thumbnail(url=member.avatar.url)
                    embed.set_footer(text="Updated at", icon_url=self.bot.user.avatar.url)
                    await channel.send(embed=embed)
                    self.add_log(f"Voice state updated for {member.name}")

    # Comando para pegar os logs do servidor
    @app_commands.command(name="getlogs", description="Get recent logs.")
    async def getlogs(self, interaction: discord.Interaction):
        if self.log_messages:
            logs = "\n".join(self.log_messages[-10:])  # Retorna os 10 logs mais recentes
            await interaction.response.send_message(f"Recent logs:\n{logs}")
        else:
            await interaction.response.send_message("No logs available.")

# Comando para limpar logs
    @app_commands.command(name="clearlogs", description="Clear the logs.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearlogs(self, interaction: discord.Interaction):
        self.log_messages.clear()  # Limpa a lista de logs
        await interaction.response.send_message("Logs cleared.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerLogs(bot))