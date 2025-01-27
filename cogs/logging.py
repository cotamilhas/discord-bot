import discord
from discord.ext import commands
import json
from colorama import Fore, Style
from config import SERVER_OPTIONS, EMBED_COLOR
from datetime import datetime


class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        print(f"Message edited by {Fore.YELLOW}{before.author}{Style.RESET_ALL} in {Fore.YELLOW}{before.channel}{Style.RESET_ALL}")
        channel_id = self.getLogChannel(before.guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Message Edited", color=EMBED_COLOR, timestamp=datetime.utcnow())
                embed.add_field(
                    name="Channel", value=before.channel.mention, inline=False)
                embed.add_field(
                    name="Author", value=before.author.mention, inline=False)
                embed.add_field(
                    name="Before", value=before.content or "No content", inline=False)
                embed.add_field(
                    name="After", value=after.content or "No content", inline=False)
                embed.set_thumbnail(url=before.author.avatar.url)
                embed.set_footer(text=f"Edited at",
                                 icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        print(f"Message deleted by {Fore.RED}{message.author}{Style.RESET_ALL} in {Fore.RED}{message.channel}{Style.RESET_ALL}")
        channel_id = self.getLogChannel(message.guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Message Deleted", color=EMBED_COLOR, timestamp=datetime.utcnow())
                embed.add_field(
                    name="Channel", value=message.channel.mention, inline=False)
                embed.add_field(
                    name="Author", value=message.author.mention, inline=False)
                embed.add_field(
                    name="Content", value=message.content or "No content", inline=False)
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.set_footer(text=f"Deleted at",
                                 icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"{Fore.GREEN}{member}{Style.RESET_ALL} joined the server.")
        channel_id = self.getLogChannel(member.guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Member Joined", color=EMBED_COLOR, timestamp=datetime.utcnow())
                embed.add_field(
                    name="Member", value=member.mention, inline=False)
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_footer(text=f"Joined at",
                                 icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f"{Fore.MAGENTA}{member}{Style.RESET_ALL} left the server.")
        channel_id = self.getLogChannel(member.guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Member Left", color=EMBED_COLOR, timestamp=datetime.utcnow())
                embed.add_field(
                    name="Member", value=member.mention, inline=False)
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_footer(
                    text=f"Left at", icon_url=self.bot.user.avatar.url)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            channel_id = self.getLogChannel(member.guild.id)
            if channel_id:
                log_channel = self.bot.get_channel(channel_id)
                if log_channel:
                    if before.channel is None:
                        print(f"Member {Fore.CYAN}{member}{Style.RESET_ALL} joined {Fore.CYAN}{after.channel}{Style.RESET_ALL}")
                        embed = discord.Embed(
                            title="Voice Channel Join", color=EMBED_COLOR, timestamp=datetime.utcnow())
                        embed.add_field(
                            name="Member", value=member.mention, inline=False)
                        embed.add_field(
                            name="Channel", value=after.channel.mention, inline=False)
                    elif after.channel is None:
                        print(f"Member {Fore.CYAN}{member}{Style.RESET_ALL} left {Fore.CYAN}{before.channel}{Style.RESET_ALL}")
                        embed = discord.Embed(
                            title="Voice Channel Leave", color=EMBED_COLOR, timestamp=datetime.utcnow())
                        embed.add_field(
                            name="Member", value=member.mention, inline=False)
                        embed.add_field(
                            name="Channel", value=before.channel.mention, inline=False)
                    else:
                        print(f"Member {Fore.CYAN}{member}{Style.RESET_ALL} switched from {Fore.CYAN}{before.channel}{Style.RESET_ALL} to {Fore.CYAN}{after.channel}{Style.RESET_ALL}")
                        embed = discord.Embed(
                            title="Voice Channel Switch", color=EMBED_COLOR, timestamp=datetime.utcnow())
                        embed.add_field(
                            name="Member", value=member.mention, inline=False)
                        embed.add_field(
                            name="From", value=before.channel.mention, inline=True)
                        embed.add_field(
                            name="To", value=after.channel.mention, inline=True)

                    embed.set_thumbnail(url=member.avatar.url)
                    embed.set_footer(text=f"Updated at",
                                     icon_url=self.bot.user.avatar.url)
                    await log_channel.send(embed=embed)

    @commands.command(help="Set the log channel for this server.")
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        try:
            if channel.guild.id == ctx.guild.id:
                self.saveLogChannel(ctx.guild.id, channel.id)
                print(f"Log channel set to {Fore.BLUE}{channel.mention}{Style.RESET_ALL} for guild {Fore.BLUE}{ctx.guild.id}{Style.RESET_ALL}")
                await ctx.send(f"Log channel set to {channel.mention}.")
            else:
                await ctx.send("Invalid channel or channel does not belong to this server.")
        except Exception as e:
            print(f"An error occurred: {Fore.RED}{e}{Style.RESET_ALL}")
            await ctx.send(f"An error occurred: {e}")

    def saveLogChannel(self, guild_id, channel_id):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if str(guild_id) not in data:
            data[str(guild_id)] = {}

        data[str(guild_id)]["log_channel"] = channel_id

        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def getLogChannel(self, guild_id):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(str(guild_id), {}).get("log_channel")
        except (FileNotFoundError, json.JSONDecodeError):
            return None


async def setup(bot):
    await bot.add_cog(ServerLogs(bot))
