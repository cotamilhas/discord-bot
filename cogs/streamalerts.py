import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import json
import os
import logging
import ssl
import io
from config import ALERTS, ALERTS_FILE, EMBED_COLOR
from config import YOUTUBE_CHANNEL_LIMIT, TWITCH_CHANNEL_LIMIT, DEBUG_MODE

if DEBUG_MODE:
    logger = logging.getLogger("streamalerts")
    logging.basicConfig(level=logging.INFO)
else:
    logger = logging.getLogger("streamalerts")
    logging.basicConfig(level=logging.WARNING)

class StreamAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_alerts = {}
        self.last_checked = {}
        self.session = None
        self.twitch_online_status = {}
        self.retry_count = 0
        self.max_retries = 3

        if DEBUG_MODE:
            logger.setLevel(logging.DEBUG)
            logging.basicConfig(level=logging.DEBUG)

        if not os.path.exists(ALERTS_FILE):
            os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
            with open(ALERTS_FILE, "w") as f:
                json.dump({"alerts": {}, "last_checked": {}}, f, indent=2)
            if DEBUG_MODE:
                logger.debug(f"[DEBUG_MODE] Created new alerts file: {ALERTS_FILE}")

        self.load_alerts()

        if not ALERTS:
            print("Alerts are disabled in config.py. The alerts cog will not be loaded.")
            if DEBUG_MODE:
                logger.debug("[DEBUG_MODE] Alerts disabled in config, cog not loaded")
            return

        if DEBUG_MODE:
            logger.debug("[DEBUG_MODE] Starting YouTube and Twitch check tasks")
            
        self.youtube_check.start()
        self.twitch_check.start()

    async def create_session(self):
        try:
            if not self.session or self.session.closed:
                connector = aiohttp.TCPConnector(limit_per_host=10, ttl_dns_cache=300, limit=0)
                timeout = aiohttp.ClientTimeout(total=30, sock_connect=15, sock_read=15)
                self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                if DEBUG_MODE:
                    logger.debug("[DEBUG_MODE] Created new aiohttp session")
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            await asyncio.sleep(5)
            await self.create_session()

    async def close_session(self):
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                if DEBUG_MODE:
                    logger.debug("[DEBUG_MODE] Closed aiohttp session")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def load_alerts(self):
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r') as f:
                    data = json.load(f)
                    self.active_alerts = data.get('alerts', {})
                    self.last_checked = data.get('last_checked', {})
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Loaded alerts: {len(self.active_alerts)} guilds")
                    logger.debug(f"[DEBUG_MODE] Last checked data for {len(self.last_checked)} guilds")
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")

    def save_alerts(self):
        try:
            data = {
                'alerts': self.active_alerts,
                'last_checked': self.last_checked
            }
            with open(ALERTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            if DEBUG_MODE:
                logger.debug("[DEBUG_MODE] Saved alerts to file")
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")

    async def safe_request(self, url, max_retries=3):
        if DEBUG_MODE:
            logger.debug(f"[DEBUG_MODE] Making request to: {url}")
            
        for attempt in range(max_retries):
            try:
                await self.create_session()
                async with self.session.get(url) as response:
                    if response.status == 200:
                        if DEBUG_MODE:
                            logger.debug(f"[DEBUG_MODE] Request successful: {url}")
                        return await response.text()
                    elif response.status == 429:
                        wait_time = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"[STREAMALERTS] Rate limited. Waiting {wait_time} seconds...")
                        if DEBUG_MODE:
                            logger.debug(f"[DEBUG_MODE] Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"[STREAMALERTS] Request failed with status {response.status}")
                        if DEBUG_MODE:
                            logger.debug(f"[DEBUG_MODE] Request failed with status {response.status} (attempt {attempt + 1})")
                        await asyncio.sleep(5)
            except (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError, 
                   aiohttp.ClientResponseError, asyncio.TimeoutError, ssl.SSLError) as e:
                logger.info(f"[STREAMALERTS] Suppressed connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Connection error (attempt {attempt + 1}): {type(e).__name__}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.info(f"[STREAMALERTS] Max retries reached for {url}. Suppressing exception.")
                    return None
            except Exception as e:
                logger.error(f"[STREAMALERTS] Unexpected error in request: {e}")
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"[STREAMALERTS] Max retries reached for {url}. Suppressing exception.")
                    return None
        return None

    async def check_youtube_channel(self, channel_id: str):
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        if DEBUG_MODE:
            logger.debug(f"[DEBUG_MODE] Checking YouTube channel: {channel_id}")

        try:
            xml_data = await self.safe_request(url)
            if not xml_data:
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] No XML data for YouTube channel: {channel_id}")
                return None

            root = ET.fromstring(xml_data)
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            if entry is None:
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] No entries found for YouTube channel: {channel_id}")
                return None

            video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            author = entry.find("{http://www.w3.org/2005/Atom}author").find("{http://www.w3.org/2005/Atom}name").text

            if DEBUG_MODE:
                logger.debug(f"[DEBUG_MODE] YouTube channel {channel_id}: Found video '{title}' by {author}")

            return {
                "id": {"videoId": video_id},
                "snippet": {
                    "title": title,
                    "channelTitle": author
                }
            }
        except ET.ParseError as e:
            logger.error(f"[STREAMALERTS][YouTube] XML parse error for channel {channel_id}: {e}")
        except Exception as e:
            logger.error(f"[STREAMALERTS][YouTube] Unexpected error for channel {channel_id}: {e}")

        return None
    
    async def get_best_thumbnail(self, video_id: str) -> str:
        if DEBUG_MODE:
            logger.debug(f"[DEBUG_MODE] Getting thumbnail for video: {video_id}")
            
        base_url = f"https://img.youtube.com/vi/{video_id}/"
        thumbs = ["maxresdefault.jpg", "hqdefault.jpg", "mqdefault.jpg", "default.jpg"]

        async with aiohttp.ClientSession() as session:
            for thumb in thumbs:
                url = base_url + thumb
                try:
                    async with session.head(url) as resp:
                        if resp.status == 200:
                            if DEBUG_MODE:
                                logger.debug(f"[DEBUG_MODE] Found thumbnail: {url}")
                            return url
                except Exception as e:
                    logger.warning(f"[STREAMALERTS] Thumbnail check failed: {url} - {e}")
                    
        if DEBUG_MODE:
            logger.debug(f"[DEBUG_MODE] No thumbnail found for video: {video_id}")
        return None
    
    async def download_image(self, url):
        await self.create_session()
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            logger.warning(f"Failed to download image: {e}")
        return None

    async def check_twitch_channel(self, channel_name: str):
        if DEBUG_MODE:
            logger.debug(f"[DEBUG_MODE] Checking Twitch channel: {channel_name}")

        endpoints = [
            f"https://decapi.me/twitch/uptime/{channel_name.lower()}",
            f"https://decapi.me/twitch/title/{channel_name.lower()}",
            f"https://decapi.me/twitch/game/{channel_name.lower()}",
            f"https://decapi.me/twitch/viewercount/{channel_name.lower()}",
            f"https://decapi.me/twitch/avatar/{channel_name.lower()}"
        ]

        try:
            results = []
            for url in endpoints:
                try:
                    result = await self.safe_request(url)
                    results.append(result.strip() if result else "Unknown")
                    if DEBUG_MODE:
                        logger.debug(f"[DEBUG_MODE] Twitch API result for {url}: {result}")
                except (aiohttp.ClientConnectionError, ssl.SSLError) as e:
                    logger.info(f"[STREAMALERTS] Suppressed error for {url}: {e}")
                    results.append("Unknown")
                except Exception as e:
                    logger.error(f"[STREAMALERTS] Unexpected error for {url}: {e}")
                    results.append("Unknown")
            
            uptime, title, game, viewers, avatar = results

            if f"{channel_name} is offline" in uptime.lower() or "offline" in uptime.lower():
                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Twitch channel {channel_name} is offline")
                return None

            if DEBUG_MODE:
                logger.debug(f"[DEBUG_MODE] Twitch channel {channel_name} is online: {title}")

            return {
                "id": f"{channel_name}_{datetime.now().timestamp()}",
                "title": title if title != "Unknown" else "No title",
                "game_name": game if game != "Unknown" else "",
                "viewer_count": viewers if viewers != "Unknown" else "Unknown",
                "channel_name": channel_name,
                "thumbnail_url": f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{channel_name.lower()}-1920x1080.jpg",
                "avatar_url": avatar if avatar != "Unknown" else None
            }
        except Exception as e:
            logger.error(f"Twitch decapi error for {channel_name}: {e}")
            return None

    @tasks.loop(minutes=5)
    async def youtube_check(self):
        if DEBUG_MODE:
            logger.debug("[DEBUG_MODE] Starting YouTube check cycle")
            
        try:
            await self.bot.wait_until_ready()

            if not self.active_alerts:
                if DEBUG_MODE:
                    logger.debug("[DEBUG_MODE] No active alerts, skipping YouTube check")
                return

            if DEBUG_MODE:
                logger.debug(f"[DEBUG_MODE] Checking YouTube for {len(self.active_alerts)} guilds")

            for guild_id, config in list(self.active_alerts.items()):
                if not config.get('youtube'):
                    if DEBUG_MODE:
                        logger.debug(f"[DEBUG_MODE] Guild {guild_id}: No YouTube channels")
                    continue

                channel = self.bot.get_channel(config['channel_id'])
                if not channel:
                    if DEBUG_MODE:
                        logger.debug(f"[DEBUG_MODE] Guild {guild_id}: Channel not found")
                    continue

                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Guild {guild_id}: Checking {len(config['youtube'])} YouTube channels")

                if guild_id not in self.last_checked:
                    self.last_checked[guild_id] = {'youtube': {}, 'twitch': {}}
                elif 'youtube' not in self.last_checked[guild_id]:
                    self.last_checked[guild_id]['youtube'] = {}

                for yt_channel in config['youtube']:
                    try:
                        if DEBUG_MODE:
                            logger.debug(f"[DEBUG_MODE] Checking YouTube channel: {yt_channel}")
                            
                        video = await self.check_youtube_channel(yt_channel)
                        if video:
                            video_id = video['id']['videoId']
                            last_video = self.last_checked[guild_id]['youtube'].get(yt_channel)

                            if DEBUG_MODE:
                                logger.debug(f"[DEBUG_MODE] Guild {guild_id} - YouTube channel {yt_channel}: Last video: {last_video}, Current video: {video_id}")

                            if last_video != video_id:
                                self.last_checked[guild_id]['youtube'][yt_channel] = video_id
                                self.save_alerts()

                                title = video['snippet']['title']
                                channel_name = video['snippet']['channelTitle']
                                url = f"https://www.youtube.com/watch?v={video_id}"

                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Sending YouTube alert to guild {guild_id} for {channel_name}: {title}")

                                embed = discord.Embed(
                                    title=title,
                                    url=url,
                                    description=f"New video uploaded by **{channel_name}**",
                                    color=discord.Color.red(),
                                    timestamp=datetime.now(timezone.utc)
                                )
                                thumbnail_url = await self.get_best_thumbnail(video_id)
                                if thumbnail_url:
                                    embed.set_image(url=thumbnail_url)
                                embed.set_footer(text="YouTube", icon_url="https://img.icons8.com/?size=100&id=19318&format=png")

                                await channel.send(embed=embed)
                            else:
                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Guild {guild_id} - YouTube channel {yt_channel}: No new video")
                        else:
                            if DEBUG_MODE:
                                logger.debug(f"[DEBUG_MODE] Guild {guild_id} - YouTube channel {yt_channel}: No video found")
                    except Exception as e:
                        logger.error(f"[STREAMALERTS] Error checking YouTube channel {yt_channel} in guild {guild_id}: {e}")
                        continue
        except Exception as e:
            logger.critical(f"[STREAMALERTS] Critical error in youtube_check: {e}")
            await asyncio.sleep(60)
            self.youtube_check.restart()

    @tasks.loop(minutes=3)
    async def twitch_check(self):
        if DEBUG_MODE:
            logger.debug("[DEBUG_MODE] Starting Twitch check cycle")
            
        try:
            await self.bot.wait_until_ready()

            if not self.active_alerts:
                if DEBUG_MODE:
                    logger.debug("[DEBUG_MODE] No active alerts, skipping Twitch check")
                return

            if DEBUG_MODE:
                logger.debug(f"[DEBUG_MODE] Checking Twitch for {len(self.active_alerts)} guilds")

            for guild_id, config in list(self.active_alerts.items()):
                if not config.get('twitch'):
                    if DEBUG_MODE:
                        logger.debug(f"[DEBUG_MODE] Guild {guild_id}: No Twitch channels")
                    continue

                channel = self.bot.get_channel(config['channel_id'])
                if not channel:
                    if DEBUG_MODE:
                        logger.debug(f"[DEBUG_MODE] Guild {guild_id}: Channel not found")
                    continue

                if DEBUG_MODE:
                    logger.debug(f"[DEBUG_MODE] Guild {guild_id}: Checking {len(config['twitch'])} Twitch channels")

                for twitch_channel in config['twitch']:
                    try:
                        if DEBUG_MODE:
                            logger.debug(f"[DEBUG_MODE] Checking Twitch channel: {twitch_channel}")
                            
                        stream = await self.check_twitch_channel(twitch_channel)
                        stream_key = f"{guild_id}_{twitch_channel}"
                        
                        if stream:
                            if not self.twitch_online_status.get(stream_key, False):
                                self.twitch_online_status[stream_key] = True
                                url = f"https://www.twitch.tv/{twitch_channel}"

                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Sending Twitch alert to guild {guild_id} for {twitch_channel}: {stream['title']}")

                                embed = discord.Embed(
                                    title=f"{stream['channel_name']} is live now!",
                                    url=url,
                                    description=stream['title'],
                                    color=discord.Color.purple(),
                                    timestamp=datetime.now(timezone.utc)
                                )
                                
                                if stream['game_name'] != "":
                                    embed.add_field(name="Game", value=stream['game_name'], inline=True)
                                    
                                if stream['viewer_count'] != "Unknown":
                                    embed.add_field(name="Viewers", value=stream['viewer_count'], inline=True)

                                embed.set_footer(text="Twitch", icon_url="https://img.icons8.com/?size=100&id=18103&format=png")
                                
                                if stream.get('avatar_url'):
                                    embed.set_thumbnail(url=stream.get('avatar_url'))

                                thumbnail_bytes = await self.download_image(stream['thumbnail_url'])
                                if thumbnail_bytes:
                                    file = discord.File(io.BytesIO(thumbnail_bytes), filename="twitch_thumb.jpg")
                                    embed.set_image(url="attachment://twitch_thumb.jpg")
                                    await channel.send(embed=embed, file=file)
                                else:
                                    embed.set_image(url=stream['thumbnail_url'])
                                    await channel.send(embed=embed)
                            else:
                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Guild {guild_id} - Twitch channel {twitch_channel}: Already online, no new alert")
                        else:
                            if self.twitch_online_status.get(stream_key, False):
                                self.twitch_online_status[stream_key] = False
                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Guild {guild_id} - Twitch channel {twitch_channel}: Went offline")
                            else:
                                if DEBUG_MODE:
                                    logger.debug(f"[DEBUG_MODE] Guild {guild_id} - Twitch channel {twitch_channel}: Still offline")
                                
                    except Exception as e:
                        logger.error(f"[STREAMALERTS] Error checking Twitch channel {twitch_channel} in guild {guild_id}: {e}")
                        continue

        except Exception as e:
            logger.critical(f"[STREAMALERTS] Critical error in twitch_check: {e}")
            await asyncio.sleep(60)
            self.twitch_check.restart()

    @youtube_check.before_loop
    @twitch_check.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()
        await self.create_session()

    def cog_unload(self):
        try:
            if DEBUG_MODE:
                logger.debug("[DEBUG_MODE] Unloading StreamAlerts cog")
                
            self.youtube_check.cancel()
            self.twitch_check.cancel()
            self.save_alerts()
            asyncio.create_task(self.close_session())
        except Exception as e:
            logger.error(f"Error in cog_unload: {e}")

    alerts = app_commands.Group(name="alerts", description="Manage stream alerts")

    @alerts.command(name="channel", description="Set the channel for stream alerts")
    async def alerts_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)

        if channel is None:
            channel = interaction.channel

        if guild_id not in self.active_alerts:
            self.active_alerts[guild_id] = {"channel_id": channel.id, "youtube": [], "twitch": []}
            if guild_id not in self.last_checked:
                self.last_checked[guild_id] = {'youtube': {}, 'twitch': {}}
        else:
            self.active_alerts[guild_id]["channel_id"] = channel.id

        self.save_alerts()
        await interaction.response.send_message(f"Alerts will be sent to {channel.mention}")

    @alerts.command(name="youtube", description="Add or remove a YouTube channel")
    @app_commands.describe(action="Choose add or remove", channel_id="YouTube channel ID")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def alerts_youtube(self, interaction: discord.Interaction, action: app_commands.Choice[str], channel_id: str):   
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)

        if guild_id not in self.active_alerts:
            await interaction.response.send_message("Set an alert channel first with `/alerts channel`", ephemeral=True)
            return

        config = self.active_alerts[guild_id]

        if action.value == "add":
            if len(config["youtube"]) >= YOUTUBE_CHANNEL_LIMIT:
                await interaction.response.send_message(f"You can only have up to {YOUTUBE_CHANNEL_LIMIT} YouTube channels.", ephemeral=True)
                return
            if channel_id not in config["youtube"]:
                config["youtube"].append(channel_id)
                if guild_id not in self.last_checked:
                    self.last_checked[guild_id] = {'youtube': {}, 'twitch': {}}
                self.save_alerts()
                await interaction.response.send_message(f"YouTube alert added for **{channel_id}**", ephemeral=True)
            else:
                await interaction.response.send_message("This channel is already in the list.", ephemeral=True)

        elif action.value == "remove":
            if channel_id in config["youtube"]:
                config["youtube"].remove(channel_id)
                if guild_id in self.last_checked and channel_id in self.last_checked[guild_id]['youtube']:
                    del self.last_checked[guild_id]['youtube'][channel_id]
                self.save_alerts()
                await interaction.response.send_message(f"YouTube alert removed for **{channel_id}**", ephemeral=True)
            else:
                await interaction.response.send_message("This channel is not in the list.", ephemeral=True)

    @alerts.command(name="twitch", description="Add or remove a Twitch channel")
    @app_commands.describe(action="Choose add or remove", channel_name="Twitch channel name")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def alerts_twitch(self, interaction: discord.Interaction, action: app_commands.Choice[str], channel_name: str):            
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)

        if guild_id not in self.active_alerts:
            await interaction.response.send_message("Set an alert channel first with `/alerts channel`", ephemeral=True)
            return

        config = self.active_alerts[guild_id]

        if action.value == "add":
            if len(config["twitch"]) >= TWITCH_CHANNEL_LIMIT:
                await interaction.response.send_message(f"You can only have up to {TWITCH_CHANNEL_LIMIT} Twitch channels.", ephemeral=True)
                return
            if channel_name.lower() not in [c.lower() for c in config["twitch"]]:
                config["twitch"].append(channel_name)
                self.save_alerts()
                await interaction.response.send_message(f"Twitch alert added for **{channel_name}**", ephemeral=True)
            else:
                await interaction.response.send_message("This channel is already in the list.", ephemeral=True)

        elif action.value == "remove":
            for channel in config["twitch"]:
                if channel.lower() == channel_name.lower():
                    config["twitch"].remove(channel)
                    stream_key = f"{guild_id}_{channel}"
                    if stream_key in self.twitch_online_status:
                        del self.twitch_online_status[stream_key]
                    self.save_alerts()
                    await interaction.response.send_message(f"Twitch alert removed for **{channel}**", ephemeral=True)
                    return
            await interaction.response.send_message("This channel is not in the list.", ephemeral=True)

    @alerts.command(name="list", description="List all configured alerts")
    async def alerts_list(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)

        if guild_id not in self.active_alerts or (
            not self.active_alerts[guild_id]["youtube"] and not self.active_alerts[guild_id]["twitch"]
        ):
            await interaction.response.send_message("No alerts configured for this server.")
            return

        config = self.active_alerts[guild_id]
        yt_list = []
        for yt_channel_id in config["youtube"]:
            video = await self.check_youtube_channel(yt_channel_id)
            if video:
                channel_title = video["snippet"]["channelTitle"]
                yt_list.append(f"{channel_title} (`{yt_channel_id}`)")
            else:
                yt_list.append(f"Unknown (`{yt_channel_id}`)")
        yt_list_str = "\n".join(yt_list) if yt_list else "None"

        tw_list = "\n".join(config["twitch"]) if config["twitch"] else "None"

        embed = discord.Embed(title="Configured Alerts", color=EMBED_COLOR)
        embed.add_field(name="YouTube", value=yt_list_str, inline=False)
        embed.add_field(name="Twitch", value=tw_list, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(StreamAlerts(bot))