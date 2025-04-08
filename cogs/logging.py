import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, Style
from config import SERVER_OPTIONS, EMBED_COLOR
from datetime import datetime, timezone, timedelta


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
        print(f"Updating config for guild {guild_id} with key {key} and value {value}")
        guild_id = str(guild_id)
        if guild_id not in data:
            data[guild_id] = {"server_name": "Unknown"}
        data[guild_id][key] = value
        self.saveConfig(data)


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        
        print(f"Message edited by {Fore.YELLOW}{before.author}{Style.RESET_ALL} in {Fore.YELLOW}{before.channel}{Style.RESET_ALL}")
        guild_config = self.getGuildConfig(before.guild.id)
        channel_id = guild_config.get("log_channel")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    print(f"Sending log to {Fore.YELLOW}{channel}{Style.RESET_ALL}")
                    embed = discord.Embed(title="Message Edited", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
                    embed.add_field(name="Channel", value=before.channel.mention, inline=False)
                    embed.add_field(name="Author", value=before.author.mention, inline=False)
                    embed.add_field(name="Before", value=before.content or "No content", inline=False)
                    embed.add_field(name="After", value=after.content or "No content", inline=False)
                    embed.set_thumbnail(url=before.author.avatar.url)
                    embed.set_footer(text="Edited at", icon_url=self.bot.user.avatar.url)
                    await channel.send(embed=embed)
                except discord.DiscordException as e:
                    print(f"Failed to send log message: {Fore.RED}{e}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"An unexpected error occurred: {Fore.RED}{e}{Style.RESET_ALL}")
        else:
            print(f"Log channel not found: {Fore.RED}{channel_id}{Style.RESET_ALL}")
            return

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        print(f"Message by {Fore.YELLOW}{message.author}{Style.RESET_ALL} was deleted in {Fore.YELLOW}{message.channel}{Style.RESET_ALL}")
        guild_config = self.getGuildConfig(message.guild.id)
        channel_id = guild_config.get("log_channel")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                    try:
                        embed = discord.Embed(title="Message Deleted", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
                        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                        embed.add_field(name="Author", value=message.author.mention, inline=False)
                        embed.add_field(name="Content", value=message.content or "No content", inline=False)

                        if message.attachments:
                            attachments = "\n".join([f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments])
                            embed.add_field(name="Attachments", value=attachments, inline=False)
                        
                        if message.embeds:
                            embeds = "\n".join([f"[Embed URL]({embed_data.url})" if embed_data.url else "No embed URL" for embed_data in message.embeds])
                            embed.add_field(name="Embeds", value=embeds, inline=False)
                        
                        if message.stickers:
                            stickers = "\n".join([f"[Sticker]({sticker.url})" if sticker.url else "No sticker URL" for sticker in message.stickers])
                            embed.add_field(name="Stickers", value=stickers, inline=False)
                        
                        embed.set_thumbnail(url=message.author.avatar.url)
                        embed.set_footer(text="Deleted at", icon_url=self.bot.user.avatar.url)
                        
                        await channel.send(embed=embed)

                    except discord.DiscordException as e:
                        print(f"Failed to send log message: {Fore.RED}{e}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {Fore.RED}{e}{Style.RESET_ALL}")                
            else:
                print(f"Log channel not found: {Fore.RED}{channel_id}{Style.RESET_ALL}")
                
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            print(f"Voice state updated for {Fore.YELLOW}{member}{Style.RESET_ALL}")
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

    @app_commands.command(name="setlogchannel", description="Set the log channel for this server.")
    @app_commands.describe(channel="The channel where logs will be sent.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.updateGuildConfig(interaction.guild.id, "log_channel", int(channel.id))
        self.updateGuildConfig(interaction.guild.id, "server_name", interaction.guild.name)
        print(f"Log channel set to {Fore.BLUE}{channel.mention}{Style.RESET_ALL} for guild {Fore.BLUE}{interaction.guild.name}{Style.RESET_ALL}")
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    @setlogchannel.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    
    @app_commands.command(name="clearlogchannel", description="Remove the log channel from this server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearlogchannel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        data = self.loadConfig()
        if guild_id in data and "log_channel" in data[guild_id]:
            del data[guild_id]["log_channel"]
            self.saveConfig(data)
            print(f"Log channel removed for guild {Fore.BLUE}{interaction.guild.name}{Style.RESET_ALL}")
            await interaction.response.send_message("Log channel removed.", ephemeral=True)
        else:
            await interaction.response.send_message("No log channel has been configured for this server.", ephemeral=True)

    @clearlogchannel.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ServerLogs(bot))
