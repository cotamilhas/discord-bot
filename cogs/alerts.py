import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
from datetime import datetime
import json
import os
import ssl
from config import ALERTS, ALERTS_FILE, YOUTUBE_API_KEY, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET


class StreamAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_alerts = {}
        self.last_checked = {
            'youtube': {},
            'twitch': {}
        }
        self.session = None

        if not os.path.exists(ALERTS_FILE):
            os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
            with open(ALERTS_FILE, "w") as f:
                json.dump({"alerts": {}, "last_checked": {"youtube": {}, "twitch": {}}}, f, indent=2)

        self.load_alerts()

        if ALERTS:
            self.youtube_check.start()
            self.twitch_check.start()
        else:
            print("[Alerts] ALERTS is disabled in config.py")

    async def create_session(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit_per_host=5,
            force_close=True,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(total=30)
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
        if not self.session or self.session.closed:
            await self.create_session()

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'type': 'video',
            'order': 'date',
            'maxResults': 1,
            'key': YOUTUBE_API_KEY
        }

        try:
            async with self.session.get(url, params=params, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('items'):
                        return data['items'][0]
        except Exception as e:
            print(f"YouTube error: {e}")

        return None

    async def check_twitch_channel(self, channel_name: str):
        if not self.session or self.session.closed:
            await self.create_session()

        try:
            auth_url = "https://id.twitch.tv/oauth2/token"
            auth_data = {
                'client_id': TWITCH_CLIENT_ID,
                'client_secret': TWITCH_CLIENT_SECRET,
                'grant_type': 'client_credentials'
            }

            async with self.session.post(auth_url, data=auth_data, ssl=False) as auth_response:
                if auth_response.status == 200:
                    auth_data = await auth_response.json()
                    access_token = auth_data['access_token']

                    headers = {
                        'Client-ID': TWITCH_CLIENT_ID,
                        'Authorization': f'Bearer {access_token}'
                    }

                    stream_url = f"https://api.twitch.tv/helix/streams?user_login={channel_name}"
                    async with self.session.get(stream_url, headers=headers, ssl=False) as stream_response:
                        if stream_response.status == 200:
                            stream_data = await stream_response.json()
                            if stream_data.get('data'):
                                return stream_data['data'][0]
        except Exception as e:
            print(f"Twitch error: {e}")

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
                                title="New YouTube Video",
                                description=f"**{channel_name}** just uploaded a new video!",
                                color=0xff0000,
                                timestamp=datetime.now()
                            )
                            embed.add_field(name=f"**{channel_name}** just uploaded a new video!", value=title, inline=False)
                            embed.add_field(name="Watch on YouTube", value=url, inline=False)
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
                    if stream:
                        stream_id = stream['id']
                        last_stream = self.last_checked['twitch'].get(twitch_channel)

                        if last_stream != stream_id:
                            self.last_checked['twitch'][twitch_channel] = stream_id
                            self.save_alerts()

                            title = stream['title']
                            game_name = stream['game_name']
                            viewer_count = stream['viewer_count']
                            url = f"https://www.twitch.tv/{twitch_channel}"
                            thumbnail = stream['thumbnail_url'].replace("{width}", "1280").replace("{height}", "720")

                            embed = discord.Embed(
                                title="Twitch Stream Live",
                                color=0x9146ff,
                                timestamp=datetime.now()
                            )
                            embed.add_field(name=f"**{twitch_channel}** is now live!", value=title, inline=False)

                            if game_name:
                                embed.add_field(name="Game", value=game_name, inline=True)
                                
                            embed.add_field(name="Viewers", value=str(viewer_count), inline=True)
                            embed.add_field(name="Watch on Twitch", value=url, inline=False)
                            embed.set_image(url=thumbnail)
                            embed.set_footer(text="Twitch", icon_url="https://img.icons8.com/?size=100&id=18103&format=png")

                            await channel.send(embed=embed)
                except Exception as e:
                    print(f"Error checking Twitch channel {twitch_channel}: {e}")

    @youtube_check.before_loop
    @twitch_check.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()
        await self.create_session()

    def cog_unload(self):
        if ALERTS:
            self.youtube_check.cancel()
            self.twitch_check.cancel()
        self.save_alerts()
        asyncio.create_task(self.close_session())


async def setup(bot):
    await bot.add_cog(StreamAlerts(bot))
