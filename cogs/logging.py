import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, Style, init
from config import SERVER_OPTIONS, EMBED_COLOR
from datetime import datetime, timezone, timedelta
from typing import Optional
init(autoreset=True)

def truncate(text, limit):
        return text if len(text) <= limit else text[:limit-3] + "..."

class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def load_config(self):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, data):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id):
        data = self.load_config()
        return data.get(str(guild_id), {})

    def update_guild_config(self, guild_id, key, value):
        data = self.load_config()
        guild_id = str(guild_id)
        if guild_id not in data:
            data[guild_id] = {"server_name": "Unknown"}
        data[guild_id][key] = value
        self.save_config(data)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        guild_config = self.get_guild_config(message.guild.id)
        channel_id = guild_config.get("log_channel")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            content = truncate(message.content or "No content", 1024)
            attachments = truncate("\n".join(f"[{a.filename}]({a.url})" for a in message.attachments), 1024) if message.attachments else None
            embeds_text = truncate("\n".join(f"[Embed URL]({e.url})" if e.url else "No embed URL" for e in message.embeds), 1024) if message.embeds else None
            stickers_text = truncate("\n".join(f"[Sticker]({s.url})" if s.url else "No sticker URL" for s in message.stickers), 1024) if message.stickers else None

            embed = discord.Embed(title="Message Deleted", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Channel", value=message.channel.mention, inline=False)
            embed.add_field(name="Author", value=message.author.mention, inline=False)
            embed.add_field(name="Content", value=content, inline=False)
            if attachments:
                embed.add_field(name="Attachments", value=attachments, inline=False)
            if embeds_text:
                embed.add_field(name="Embeds", value=embeds_text, inline=False)
            if stickers_text:
                embed.add_field(name="Stickers", value=stickers_text, inline=False)
            embed.set_thumbnail(url=message.author.avatar.url)
            embed.set_footer(text="Deleted at", icon_url=self.bot.user.avatar.url)

            await channel.send(embed=embed)

        except discord.DiscordException as e:
            print(f"Failed to send log message: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        guild_config = self.get_guild_config(before.guild.id)
        channel_id = guild_config.get("log_channel")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            before_content = truncate(before.content or "No content", 1024)
            after_content = truncate(after.content or "No content", 1024)

            embed = discord.Embed(title="Message Edited", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Channel", value=before.channel.mention, inline=False)
            embed.add_field(name="Author", value=before.author.mention, inline=False)
            embed.add_field(name="Before", value=before_content, inline=False)
            embed.add_field(name="After", value=after_content, inline=False)
            embed.set_thumbnail(url=before.author.avatar.url)
            embed.set_footer(text="Edited at", icon_url=self.bot.user.avatar.url)

            await channel.send(embed=embed)

        except discord.DiscordException as e:
            print(f"Failed to send log message: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
                
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            print(f"Voice state updated for {Fore.YELLOW}{member}{Style.RESET_ALL}")
            guild_config = self.get_guild_config(member.guild.id)
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

    @app_commands.command(name="logchannel", description="Set or clear the log channel for this server. (Admin only)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="clear", value="clear")
    ])
    @app_commands.describe(
        channel="The channel where logs will be sent (only needed for 'set')"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def logchannel(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        channel: Optional[discord.TextChannel] = None
    ):
        guild_id = str(interaction.guild.id)
        data = self.load_config()

        if mode.value == "set":
            if channel is None:
                await interaction.response.send_message("You must specify a channel when using 'set'.", ephemeral=True)
                return

            self.update_guild_config(guild_id, "log_channel", int(channel.id))
            self.update_guild_config(guild_id, "server_name", interaction.guild.name)
            print(f"Log channel set to {Fore.BLUE}{channel.mention}{Style.RESET_ALL} for guild {Fore.BLUE}{interaction.guild.name}{Style.RESET_ALL}")
            await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

        elif mode.value == "clear":
            if guild_id in data and "log_channel" in data[guild_id]:
                del data[guild_id]["log_channel"]
                self.save_config(data)
                print(f"Log channel removed for guild {Fore.BLUE}{interaction.guild.name}{Style.RESET_ALL}")
                await interaction.response.send_message("Log channel removed.", ephemeral=True)
            else:
                await interaction.response.send_message("No log channel has been configured for this server.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ServerLogs(bot))
