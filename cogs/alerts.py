import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import json
import os
from config import ALERTS, ALERTS_FILE

class StreamAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_alerts = {}
        self.last_checked = {'youtube': {}, 'twitch': {}}
        self.session = None
        self.twitch_online_status = {}

        if not os.path.exists(ALERTS_FILE):
            os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
            with open(ALERTS_FILE, "w") as f:
                json.dump({"alerts": {}, "last_checked": {"youtube": {}, "twitch": {}}}, f, indent=2)

        self.load_alerts()

        if not ALERTS:
            print("Alerts are disabled in config.py. The alerts cog will not be loaded.")
            return

        self.youtube_check.start()
        self.twitch_check.start()

    async def create_session(self):
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(limit_per_host=10, ttl_dns_cache=300)
            timeout = aiohttp.ClientTimeout(total=15)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def load_alerts(self):
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r') as f:
                    data = json.load(f)
                    self.active_alerts = data.get('alerts', {})
                    self.last_checked = data.get('last_checked', {'youtube': {}, 'twitch': {}})
        except Exception as e:
            print(f"Error loading alerts: {e}")

    def save_alerts(self):
        try:
            data = {
                'alerts': self.active_alerts,
                'last_checked': self.last_checked
            }
            with open(ALERTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")

    async def check_youtube_channel(self, channel_id: str):
        await self.create_session()
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    root = ET.fromstring(xml_data)

                    entry = root.find("{http://www.w3.org/2005/Atom}entry")
                    if entry is None:
                        return None

                    video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
                    title = entry.find("{http://www.w3.org/2005/Atom}title").text
                    author = entry.find("{http://www.w3.org/2005/Atom}author").find("{http://www.w3.org/2005/Atom}name").text

                    return {
                        "id": {"videoId": video_id},
                        "snippet": {
                            "title": title,
                            "channelTitle": author
                        }
                    }
        except Exception as e:
            print(f"YouTube RSS error: {e}")

        return None

    async def check_twitch_channel(self, channel_name: str):
        await self.create_session()
        
        uptime_url = f"https://decapi.me/twitch/uptime/{channel_name.lower()}"
        
        try:
            async with self.session.get(uptime_url) as response:
                if response.status == 200:
                    text = await response.text()
                    if f"{channel_name} is offline" in text.lower():
                        return None
                    
                    title_url = f"https://decapi.me/twitch/title/{channel_name.lower()}"
                    async with self.session.get(title_url) as title_response:
                        if title_response.status == 200:
                            title = await title_response.text()
                            
                            game_url = f"https://decapi.me/twitch/game/{channel_name.lower()}"
                            async with self.session.get(game_url) as game_response:
                                if game_response.status == 200:
                                    text = await game_response.text()
                                
                                viewers_url = f"https://decapi.me/twitch/viewercount/{channel_name.lower()}"
                                async with self.session.get(viewers_url) as viewers_response:
                                    viewer_count = await viewers_response.text() if viewers_response.status == 200 else "Unknown"

                                    async with self.session.get(f"https://decapi.me/twitch/avatar/{channel_name.lower()}") as avatar_response:
                                        avatar = await avatar_response.text() if avatar_response.status == 200 else None
                                    
                                    return {
                                        "id": f"{channel_name}_{datetime.now().timestamp()}",
                                        "title": title.strip(),
                                        "game_name": text.strip(),
                                        "viewer_count": viewer_count.strip(),
                                        "channel_name": channel_name,
                                        "thumbnail_url": f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{channel_name.lower()}-1920x1080.jpg",
                                        "avatar_url": avatar
                                    }
        except Exception as e:
            print(f"Twitch decapi error: {e}")

        return None

    @tasks.loop(minutes=5)
    async def youtube_check(self):
        await self.bot.wait_until_ready()

        if not self.active_alerts:
            return

        for guild_id, config in list(self.active_alerts.items()):
            if not config.get('youtube'):
                continue

            channel = self.bot.get_channel(config['channel_id'])
            if not channel:
                continue

            for yt_channel in config['youtube']:
                try:
                    video = await self.check_youtube_channel(yt_channel)
                    if video:
                        video_id = video['id']['videoId']
                        last_video = self.last_checked['youtube'].get(yt_channel)

                        if last_video != video_id:
                            self.last_checked['youtube'][yt_channel] = video_id
                            self.save_alerts()

                            title = video['snippet']['title']
                            channel_name = video['snippet']['channelTitle']
                            url = f"https://www.youtube.com/watch?v={video_id}"

                            embed = discord.Embed(
                                title=title,
                                url=url,
                                description=f"New video uploaded by **{channel_name}**",
                                color=discord.Color.red(),
                                timestamp=datetime.now(timezone.utc)
                            )
                            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
                            embed.set_footer(text="YouTube", icon_url="https://img.icons8.com/?size=100&id=19318&format=png")

                            await channel.send(embed=embed)
                except Exception as e:
                    print(f"Error checking YouTube channel {yt_channel}: {e}")

    @tasks.loop(minutes=3)
    async def twitch_check(self):
        await self.bot.wait_until_ready()

        if not self.active_alerts:
            return

        for guild_id, config in list(self.active_alerts.items()):
            if not config.get('twitch'):
                continue

            channel = self.bot.get_channel(config['channel_id'])
            if not channel:
                continue

            for twitch_channel in config['twitch']:
                try:
                    stream = await self.check_twitch_channel(twitch_channel)
                    stream_key = f"{guild_id}_{twitch_channel}"
                    
                    if stream:
                        if not self.twitch_online_status.get(stream_key, False):
                            self.twitch_online_status[stream_key] = True
                            
                            url = f"https://www.twitch.tv/{twitch_channel}"

                            embed = discord.Embed(
                                title=f"{stream['channel_name']} is live now!",
                                url=url,
                                description=stream['title'],
                                color=0x9146ff,
                                timestamp=datetime.now(timezone.utc)
                            )
                            if stream['game_name'] != "":
                                embed.add_field(name="Game", value=stream['game_name'], inline=True)
                            if stream['viewer_count'] != "Unknown":
                                embed.add_field(name="Viewers", value=stream['viewer_count'], inline=True)
                            embed.set_image(url=stream['thumbnail_url'])
                            embed.set_footer(text="Twitch", icon_url="https://img.icons8.com/?size=100&id=18103&format=png")
                            embed.set_thumbnail(url=stream.get('avatar_url'))

                            await channel.send(embed=embed)
                    else:
                        self.twitch_online_status[stream_key] = False
                        
                except Exception as e:
                    print(f"Error checking Twitch channel {twitch_channel}: {e}")

    @youtube_check.before_loop
    @twitch_check.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()
        await self.create_session()

    def cog_unload(self):
        self.youtube_check.cancel()
        self.twitch_check.cancel()
        self.save_alerts()
        asyncio.create_task(self.close_session())

    alert_group = app_commands.Group(name="alert", description="Stream alert configuration")

    @alert_group.command(name="channel", description="Set the channel for stream alerts")
    async def alert_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.active_alerts:
            self.active_alerts[guild_id] = {"channel_id": interaction.channel.id, "youtube": [], "twitch": []}
        else:
            self.active_alerts[guild_id]["channel_id"] = interaction.channel.id
            
        self.save_alerts()
        await interaction.response.send_message(f"Alert channel set to {interaction.channel.mention}")

    @alert_group.command(name="youtube", description="Add or remove a YouTube channel")
    @app_commands.describe(action="Add or remove", channel_id="YouTube channel ID")
    async def alert_youtube(self, interaction: discord.Interaction, action: str, channel_id: str):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.active_alerts:
            await interaction.response.send_message("Please set an alert channel first with `/alert channel`")
            return

        config = self.active_alerts[guild_id]

        if action.lower() == "add":
            if channel_id not in config["youtube"]:
                config["youtube"].append(channel_id)
                self.save_alerts()
                await interaction.response.send_message(f"YouTube alert added for channel **{channel_id}**")
            else:
                await interaction.response.send_message("This channel is already in the list.")

        elif action.lower() == "remove":
            if channel_id in config["youtube"]:
                config["youtube"].remove(channel_id)
                self.save_alerts()
                await interaction.response.send_message(f"YouTube alert removed for channel **{channel_id}**")
            else:
                await interaction.response.send_message("This channel is not in the list.")
        else:
            await interaction.response.send_message("Invalid action. Use 'add' or 'remove'.")

    @alert_group.command(name="twitch", description="Add or remove a Twitch channel")
    @app_commands.describe(action="Add or remove", channel_name="Twitch channel name")
    async def alert_twitch(self, interaction: discord.Interaction, action: str, channel_name: str):
        guild_id = str(interaction.guild.id)

        if not ALERTS:
            await interaction.response.send_message("Twitch alerts are disabled in config.py.")
            return

        if guild_id not in self.active_alerts:
            await interaction.response.send_message("Please set an alert channel first with `/alert channel`")
            return

        config = self.active_alerts[guild_id]

        if action.lower() == "add":
            if channel_name.lower() not in [c.lower() for c in config["twitch"]]:
                config["twitch"].append(channel_name)
                self.save_alerts()
                await interaction.response.send_message(f"Twitch alert added for channel **{channel_name}**")
            else:
                await interaction.response.send_message("This channel is already in the list.")

        elif action.lower() == "remove":
            for channel in config["twitch"]:
                if channel.lower() == channel_name.lower():
                    config["twitch"].remove(channel)
                    self.save_alerts()
                    await interaction.response.send_message(f"Twitch alert removed for channel **{channel}**")
                    return
            await interaction.response.send_message("This channel is not in the list.")
        else:
            await interaction.response.send_message("Invalid action. Use 'add' or 'remove'.")

    @alert_group.command(name="list", description="List all configured alerts")
    async def alert_list(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.active_alerts or (
            not self.active_alerts[guild_id]["youtube"] and not self.active_alerts[guild_id]["twitch"]
        ):
            await interaction.response.send_message("No alerts configured for this server.")
            return

        config = self.active_alerts[guild_id]
        yt_list = "\n".join(config["youtube"]) if config["youtube"] else "None"
        tw_list = "\n".join(config["twitch"]) if config["twitch"] else "None"

        embed = discord.Embed(title="Configured Alerts", color=0x00ffcc)
        embed.add_field(name="YouTube", value=yt_list, inline=False)
        embed.add_field(name="Twitch", value=tw_list, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(StreamAlerts(bot))