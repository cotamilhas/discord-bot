import discord
from discord.ext import commands
from discord import Interaction, Embed
from discord.ui import View, Button
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import re
import traceback
from typing import List, Dict, Optional, Tuple
from config import EMBED_COLOR, YTDL_SEARCH_OPTS, YTDL_DIRECT_OPTS
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, USE_SPOTIFY_API
from config import NEXT_COLOR, BACK_COLOR, COOKIES_FILE, DEBUG_MODE
from urllib.parse import urlparse

sp: Optional[spotipy.Spotify] = None
if USE_SPOTIFY_API:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

class QueueView(View):
    def __init__(self, queue: List[Dict[str, str]], page: int = 0):
        super().__init__(timeout=60)
        self.queue = queue
        self.page = page
        self.items_per_page = 10
        self.max_pages = max(1, (len(queue) - 1) // self.items_per_page + 1)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        back_button = PreviousButton()
        next_button = NextButton()
        back_button.disabled = self.page == 0
        next_button.disabled = self.page >= self.max_pages - 1
        self.add_item(back_button)
        self.add_item(next_button)

    def create_embed(self) -> Embed:
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        songs = self.queue[start:end]
        embed = Embed(
            title="Queue",
            description=f"Total Songs: {len(self.queue)}" if self.queue else "The song queue is empty.",
            color=EMBED_COLOR
        )
        if songs:
            embed.add_field(
                name="Playlist:",
                value="\n".join(f"{i + start + 1} - {song['title']}" for i, song in enumerate(songs)),
                inline=False
            )
        embed.set_footer(text=f"Page {self.page + 1}/{self.max_pages}")
        return embed

    async def back(self, interaction: Interaction):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def next(self, interaction: Interaction):
        self.page = min(self.max_pages - 1, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class PreviousButton(Button):
    def __init__(self):
        super().__init__(style=BACK_COLOR, label="Back")

    async def callback(self, interaction: Interaction):
        view: QueueView = self.view
        await view.back(interaction)

class NextButton(Button):
    def __init__(self):
        super().__init__(style=NEXT_COLOR, label="Next")

    async def callback(self, interaction: Interaction):
        view: QueueView = self.view
        await view.next(interaction)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, List[Tuple[str, str, Optional[str]]]] = {}
        self.playing_now: Dict[int, Optional[Tuple[str, str]]] = {}

    def is_spotify_url(self, url: str) -> bool:
        if not USE_SPOTIFY_API:
            return False
        parsed = urlparse(url)
        host = parsed.hostname
        return host == "open.spotify.com"

    async def extract_spotify_titles(self, url: str) -> List[str]:
        if not sp:
            if DEBUG_MODE:
                print("[MUSIC][WARNING] Spotify API not initialized")
            return []
        
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Processing Spotify URL: {url}")
            
            url_parts = url.split("/")
            if len(url_parts) < 5:
                if DEBUG_MODE:
                    print(f"[MUSIC][ERROR] Invalid Spotify URL format: {url}")
                return []
            
            resource_type = url_parts[-2]
            resource_id = url_parts[-1].split("?")[0]
            
            if resource_type == "track":
                track = sp.track(resource_id)
                if track and track.get('name') and track.get('artists'):
                    return [f"{track['name']} {track['artists'][0]['name']}"]
            elif resource_type == "playlist":
                return self._get_playlist_titles(resource_id)
            elif resource_type == "album":
                return self._get_album_titles(resource_id)
            elif resource_type == "artist":
                return self._get_artist_titles(resource_id)
            else:
                if DEBUG_MODE:
                    print(f"[MUSIC][ERROR] Unsupported Spotify resource type: {resource_type}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] Spotify extraction error: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
        
        return []

    def _get_playlist_titles(self, playlist_id: str) -> List[str]:
        titles = []
        results = sp.playlist_tracks(playlist_id)
        for item in results.get('items', []):
            if item and item.get('track') and item['track'].get('name') and item['track'].get('artists'):
                titles.append(f"{item['track']['name']} {item['track']['artists'][0]['name']}")
        while results.get('next'):
            results = sp.next(results)
            for item in results.get('items', []):
                if item and item.get('track') and item['track'].get('name') and item['track'].get('artists'):
                    titles.append(f"{item['track']['name']} {item['track']['artists'][0]['name']}")
        return titles

    def _get_album_titles(self, album_id: str) -> List[str]:
        titles = []
        results = sp.album_tracks(album_id)
        album = sp.album(album_id)
        if not album or not album.get('name'):
            return []
        album_name = album['name']
        for track in results.get('items', []):
            if track and track.get('name') and track.get('artists'):
                titles.append(f"{track['name']} {track['artists'][0]['name']} {album_name}")
        while results.get('next'):
            results = sp.next(results)
            for track in results.get('items', []):
                if track and track.get('name') and track.get('artists'):
                    titles.append(f"{track['name']} {track['artists'][0]['name']} {album_name}")
        return titles

    def _get_artist_titles(self, artist_id: str) -> List[str]:
        titles = []
        artist = sp.artist(artist_id)
        if not artist or not artist.get('name'):
            return []
        top_tracks_data = sp.artist_top_tracks(artist_id, country='PT')
        for track in top_tracks_data.get('tracks', []):
            if track and track.get('name'):
                titles.append(f"{track['name']} - {artist['name']}")
        return titles

    async def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] ensure_voice called for user: {ctx.author}")
            
            if not ctx.author.voice or not ctx.author.voice.channel:
                embed = Embed(description="You must be in a voice channel!", color=EMBED_COLOR)
                await ctx.send(embed=embed, ephemeral=True)
                return None
            
            voice_channel = ctx.author.voice.channel
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            
            if not vc:
                vc = await voice_channel.connect()
            elif vc.channel != voice_channel:
                await vc.move_to(voice_channel)
            
            return vc
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] ensure_voice: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            embed = Embed(description=f"Error connecting to voice: {str(e)}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return None

    async def yt_search(self, query: str) -> List[Dict[str, str]]:
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] YouTube search for: {query}")
            is_url = bool(re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', query))
            opts = YTDL_SEARCH_OPTS.copy()
            if COOKIES_FILE:
                opts['cookiefile'] = COOKIES_FILE
            else:
                opts.pop('cookiefile', None)
            if is_url:
                opts.pop('default_search', None)
            
            with yt_dlp.YoutubeDL(opts) as ytdl:
                info = ytdl.extract_info(query, download=False)
                entries = info.get('entries', [info]) if 'entries' in info else [info]
                
                results = []
                for e in entries:
                    if e and e.get('title') and e.get('id'):
                        results.append({
                            "title": e.get("title"),
                            "url": f"https://www.youtube.com/watch?v={e.get('id')}",
                            "thumbnail": e.get("thumbnail")
                        })
                return results
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] YouTube search error: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            return []

    def create_source(self, url: str) -> Optional[discord.FFmpegPCMAudio]:
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Creating audio source for: {url}")
            with yt_dlp.YoutubeDL(YTDL_DIRECT_OPTS) as ytdl:
                if COOKIES_FILE:
                    ytdl.params['cookiefile'] = COOKIES_FILE
                else:
                    ytdl.params.pop('cookiefile', None)
                info = ytdl.extract_info(url, download=False)
                if not info or not info.get('url'):
                    return None
                return discord.FFmpegPCMAudio(
                    info['url'],
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn -ac 2 -ar 48000 -f s16le'
                )
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] create_source: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            return None

    async def play_next(self, interaction_or_ctx, vc: discord.VoiceClient):
        try:
            guild_id = interaction_or_ctx.guild.id
            queue = self.queues.get(guild_id, [])
            if not queue:
                self.playing_now[guild_id] = None
                await self.bot.change_presence(activity=None)
                if vc.is_connected():
                    await vc.disconnect()
                return
            
            title, url, thumbnail = queue.pop(0)
            self.queues[guild_id] = queue
            self.playing_now[guild_id] = (title, url)
            
            source = self.create_source(url)
            if not source:
                await self.play_next(interaction_or_ctx, vc)
                return
            
            vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction_or_ctx, vc)) if not e else None)
            
            activity_name = f"{title.split(' - ')[0]} – {title.split(' - ')[1]}" if " - " in title else title
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
            await self.bot.change_presence(activity=activity)
            
            embed = Embed(title="Now Playing", description=f"[{title}]({url})", color=EMBED_COLOR)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text=f"Requested by {interaction_or_ctx.author.display_name}", icon_url=interaction_or_ctx.author.display_avatar.url)
            
            await interaction_or_ctx.channel.send(embed=embed)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] play_next: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")

    @commands.command(name='play', aliases=["p"], help='Plays a song from YouTube or Spotify')
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str):
        try:
            vc = await self.ensure_voice(ctx)
            if not vc:
                return
            
            queue = self.queues.setdefault(ctx.guild.id, [])
            
            if self.is_spotify_url(query):
                await ctx.send("Processing the Spotify link. It may take a few seconds to add all the songs to the queue.")
                titles = await self.extract_spotify_titles(query)
                if not titles:
                    await ctx.send("Could not process Spotify link.")
                    return
                
                for title in titles:
                    results = await self.yt_search(title)
                    if results:
                        entry = results[0]
                        queue.append((entry["title"], entry["url"], entry["thumbnail"]))
                        if not vc.is_playing():
                            await self.play_next(ctx, vc)
                    await asyncio.sleep(0.5)
            else:
                entries = await self.yt_search(query)
                if not entries:
                    embed = Embed(description="No results found.", color=EMBED_COLOR)
                    await ctx.send(embed=embed)
                    return
                
                queue.extend([(e["title"], e["url"], e["thumbnail"]) for e in entries])
                
                embed = Embed(
                    title="Added to Queue" if len(entries) == 1 else "Playlist Added",
                    description=f"[{entries[0]['title']}]({entries[0]['url']})" if len(entries) == 1 else f"Added {len(entries)} songs to queue.",
                    color=EMBED_COLOR
                )
                if entries[0].get("thumbnail"):
                    embed.set_thumbnail(url=entries[0]["thumbnail"])
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                await ctx.send(embed=embed)
                
                if not vc.is_playing():
                    await self.play_next(ctx, vc)
            
            await ctx.message.add_reaction("👍")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[MUSIC][ERROR] play command: {e}")
                print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            await ctx.send(f"Error: {str(e)}")

    @commands.command(name='skip', aliases=["s", "next", "n"], help='Skips the current song')
    @commands.guild_only()
    async def skip(self, ctx: commands.Context):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_playing():
            vc.stop()
            embed = Embed(description="⏭️ Skipped current song.", color=EMBED_COLOR)
        else:
            embed = Embed(description="Nothing is playing.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")

    @commands.command(name='stop', aliases=["disconnect", "leave", "l", "d"], help='Stops the music and disconnects from the voice channel')
    @commands.guild_only()
    async def disconnect(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            embed = Embed(description="I'm not in a voice channel.", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return
        self.queues[guild_id] = []
        self.playing_now[guild_id] = None
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        await vc.disconnect()
        embed = Embed(description="Disconnected and cleared queue.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")

    @commands.command(name='pause', aliases=["ps"], help='Pauses the current song')
    @commands.guild_only()
    async def pause(self, ctx: commands.Context):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_playing():
            vc.pause()
            embed = Embed(description="⏸️ Paused.", color=EMBED_COLOR)
        else:
            embed = Embed(description="Nothing is playing.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")

    @commands.command(name='resume', aliases=["r"], help='Resumes the paused song')
    @commands.guild_only()
    async def resume(self, ctx: commands.Context):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_paused():
            vc.resume()
            embed = Embed(description="▶️ Resumed.", color=EMBED_COLOR)
        else:
            embed = Embed(description="Music is not paused.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")

    @commands.command(name='queue', aliases=["q"], help='Shows the current music queue')
    @commands.guild_only()
    async def queue(self, ctx: commands.Context):
        queue = self.queues.get(ctx.guild.id, [])
        view = QueueView([{"title": t} for t, _, _ in queue])
        embed = view.create_embed()
        await ctx.send(embed=embed, view=view)
        await ctx.message.add_reaction("👍")

    @commands.command(name='nowplaying', aliases=["np"], help='Shows the currently playing song')
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context):
        song = self.playing_now.get(ctx.guild.id)
        if song:
            title, url = song
            embed = Embed(title="Now Playing", description=f"[{title}]({url})", color=EMBED_COLOR)
        else:
            embed = Embed(description="Nothing is playing.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")

    @commands.command(name='help', aliases=["commands"], help='Shows the list of music commands')
    @commands.guild_only()
    async def help_command(self, ctx):
        embed = Embed(title="Music Commands", color=EMBED_COLOR)
        commands_list = [
            "`!play` <query> - Plays a song from YouTube or Spotify",
            "`!skip` - Skips the current song",
            "`!stop` - Stops the music and disconnects from the voice channel",
            "`!pause` - Pauses the current song",
            "`!resume` - Resumes the paused song",
            "`!queue` - Shows the current music queue",
            "`!nowplaying` - Shows the currently playing song"
        ]
        embed.description = "\n".join(commands_list)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")


async def setup(bot):
    await bot.add_cog(Music(bot))