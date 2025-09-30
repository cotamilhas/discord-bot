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
from config import EMBED_COLOR, YTDL_SEARCH_OPTS, YTDL_DIRECT_OPTS 
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, USE_SPOTIFY_API
from config import NEXT_COLOR, BACK_COLOR, COOKIES_FILE, DEBUG_MODE

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)) if USE_SPOTIFY_API else None

class QueueView(View):
    def __init__(self, queue, page=0):
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

    def create_embed(self):
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
                value="\n".join(f"{i+start+1} - {song['title']}" for i, song in enumerate(songs)),
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
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.playing_now = {}

    def is_spotify_url(self, url):
        return USE_SPOTIFY_API and "open.spotify.com" in url

    async def extract_spotify_titles(self, url):
        if not sp: 
            print("[MUSIC][WARNING] Spotify API not initialized")
            return []
        
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Processing Spotify URL: {url}")
            
            if "track/" in url:
                url_parts = url.split("track/")
                if len(url_parts) < 2:
                    print(f"[MUSIC][ERROR] Invalid track URL format: {url}")
                    return []
                    
                track_id_part = url_parts[1].split("?")[0]
                if not track_id_part:
                    print(f"[MUSIC][ERROR] Could not extract track ID from: {url}")
                    return []
                
                track = sp.track(track_id_part)
                if track and track.get('name') and track.get('artists'):
                    return [f"{track['name']} {track['artists'][0]['name']}"]
                else:
                    print(f"[MUSIC][ERROR] Invalid track data received from Spotify")
                    return []
                    
            elif "playlist/" in url:
                url_parts = url.split("playlist/")
                if len(url_parts) < 2:
                    print(f"[MUSIC][ERROR] Invalid playlist URL format: {url}")
                    return []
                    
                playlist_id = url_parts[1].split("?")[0]
                if not playlist_id:
                    print(f"[MUSIC][ERROR] Could not extract playlist ID from: {url}")
                    return []
                
                results = sp.playlist_tracks(playlist_id)
                titles = []
                
                for item in results.get('items', []):
                    if item and item.get('track') and item['track'].get('name') and item['track'].get('artists'):
                        titles.append(f"{item['track']['name']} {item['track']['artists'][0]['name']}")
                
                while results.get('next'):
                    try:
                        results = sp.next(results)
                        for item in results.get('items', []):
                            if item and item.get('track') and item['track'].get('name') and item['track'].get('artists'):
                                titles.append(f"{item['track']['name']} {item['track']['artists'][0]['name']}")
                    except Exception as e:
                        print(f"[ERROR] Error processing playlist pagination: {e}")
                        break
                
                return titles
                
            elif "album/" in url:
                url_parts = url.split("album/")
                if len(url_parts) < 2:
                    print(f"[MUSIC][ERROR] Invalid album URL format: {url}")
                    return []
                    
                album_id = url_parts[1].split("?")[0]
                if not album_id:
                    print(f"[MUSIC][ERROR] Could not extract album ID from: {url}")
                    return []
                
                results = sp.album_tracks(album_id)
                album = sp.album(album_id)
                
                if not album or not album.get('name'):
                    print(f"[MUSIC][ERROR] Could not get album info")
                    return []
                
                album_name = album['name']
                titles = []
                
                for track in results.get('items', []):
                    if track and track.get('name') and track.get('artists'):
                        titles.append(f"{track['name']} {track['artists'][0]['name']} {album_name}")
                
                while results.get('next'):
                    try:
                        results = sp.next(results)
                        for track in results.get('items', []):
                            if track and track.get('name') and track.get('artists'):
                                titles.append(f"{track['name']} {track['artists'][0]['name']} {album_name}")
                    except Exception as e:
                        print(f"[MUSIC][ERROR] Error processing album pagination: {e}")
                        break
                
                return titles
                
            elif "artist/" in url:
                url_parts = url.split("artist/")
                if len(url_parts) < 2:
                    print(f"[MUSIC][ERROR] Invalid artist URL format: {url}")
                    return []
                    
                artist_id = url_parts[1].split("?")[0]
                if not artist_id:
                    print(f"[MUSIC][ERROR] Could not extract artist ID from: {url}")
                    return []
                
                artist = sp.artist(artist_id)
                if not artist or not artist.get('name'):
                    print(f"[MUSIC][ERROR] Could not get artist info")
                    return []
                
                top_tracks_data = sp.artist_top_tracks(artist_id, country='PT')
                top_tracks = top_tracks_data.get('tracks', [])
                
                titles = []
                for track in top_tracks:
                    if track and track.get('name'):
                        artist_url = artist.get('external_urls', {}).get('spotify', '')
                        titles.append(f"{track['name']} - {artist['name']} ({artist_url})")
                
                return titles
                
        except Exception as e:
            print(f"[MUSIC][ERROR] Spotify extraction error: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
        
        return []

    async def ensure_voice(self, ctx):
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] ensure_voice called for user: {ctx.author}")

            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send(
                    embed=Embed(description="You must be in a voice channel!", color=EMBED_COLOR), 
                    ephemeral=True
                )
                return None

            voice_channel = ctx.author.voice.channel
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] User is in voice channel: {voice_channel.name}")

            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Current voice client: {vc}")

            if not vc:
                if DEBUG_MODE:
                    print(f"[MUSIC][DEBUG] Connecting to {voice_channel.name}")
                vc = await voice_channel.connect()
                print(f"[MUSIC][INFO] Connected to {voice_channel.name}")
            elif vc.channel != voice_channel:
                if DEBUG_MODE:
                    print(f"[MUSIC][DEBUG] Moving from {vc.channel.name} to {voice_channel.name}")
                await vc.move_to(voice_channel)
                print(f"[MUSIC][INFO] Moved to {voice_channel.name}")

            return vc

        except Exception as e:
            print(f"[MUSIC][ERROR] ensure_voice: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            await ctx.send(embed=Embed(description=f"Error connecting to voice: {str(e)}", color=EMBED_COLOR))
            return None

    async def yt_search(self, query):
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] YouTube search for: {query}")
            is_url = re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', query)
            opts = YTDL_SEARCH_OPTS.copy()
            if COOKIES_FILE:
                opts['cookiefile'] = COOKIES_FILE
                if DEBUG_MODE:
                    print(f"[MUSIC][DEBUG] Using cookies file: {COOKIES_FILE}")
            else:
                opts.pop('cookiefile', None)
                print("[MUSIC][WARNING] No cookies file found, proceeding without it")
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
                
                if DEBUG_MODE:
                    print(f"[MUSIC][DEBUG] Found {len(results)} YouTube results")
                return results
                
        except Exception as e:
            print(f"[MUSIC][ERROR] YouTube search error: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            return []

    def create_source(self, url):
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Creating audio source for: {url}")
            with yt_dlp.YoutubeDL(YTDL_DIRECT_OPTS) as ytdl:
                if COOKIES_FILE:
                    ytdl.params['cookiefile'] = COOKIES_FILE
                    if DEBUG_MODE:
                        print(f"[MUSIC][DEBUG] Using cookies file: {COOKIES_FILE}")
                else:
                    ytdl.params.pop('cookiefile', None)
                    print("[MUSIC][WARNING] No cookies file found, proceeding without it")
                info = ytdl.extract_info(url, download=False)
                if not info or not info.get('url'):
                    print(f"[MUSIC][ERROR] Could not extract stream URL")
                    return None
                return discord.FFmpegPCMAudio(
                    info['url'],
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn -f s16le'
                )
        except Exception as e:
            print(f"[MUSIC][ERROR] create_source: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            return None

    async def play_next(self, interaction, vc):
        try:
            queue = self.queues.get(interaction.guild.id, [])
            if not queue:
                if DEBUG_MODE:
                    print("[MUSIC][DEBUG] Queue is empty, disconnecting")
                self.playing_now[interaction.guild.id] = None
                await self.bot.change_presence(activity=None)
                if vc.is_connected():
                    await vc.disconnect()
                return
                
            title, url, thumbnail = queue.pop(0)
            self.queues[interaction.guild.id] = queue
            self.playing_now[interaction.guild.id] = (title, url)
            
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Playing next song: {title}")
            
            source = self.create_source(url)
            if not source:
                print(f"[MUSIC][ERROR] Could not create audio source, skipping")
                await self.play_next(interaction, vc)
                return
            
            vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction, vc)) if not e else print(f"[ERROR] Playback error: {e}"))

            if " - " in title:
                artist, song = title.split(" - ", 1)
                activity_name = f"{artist} – {song}"
            else:
                activity_name = title

            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=activity_name
            )
            
            await self.bot.change_presence(activity=activity)

            embed = Embed(title="Now Playing", description=f"[{title}]({url})", color=EMBED_COLOR)
            if thumbnail: 
                embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text=f"Requested by {interaction.author.display_name}", icon_url=interaction.author.display_avatar.url)
            
            await interaction.channel.send(embed=embed)
            
        except Exception as e:
            print(f"[MUSIC][ERROR] play_next: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")

    @commands.command(name='play', aliases=["p"], help='Plays a song from YouTube or Spotify')
    @commands.guild_only()
    async def play(self, ctx, *, query: str):
        try:
            if DEBUG_MODE:
                print(f"[MUSIC][DEBUG] Play command called with query: {query}")
            
            vc = await self.ensure_voice(ctx)
            if not vc:
                if DEBUG_MODE: 
                    print("[MUSIC][DEBUG] Could not ensure voice connection")
                return

            queue = self.queues.setdefault(ctx.guild.id, [])
            
            if self.is_spotify_url(query):
                if DEBUG_MODE:
                    print("[MUSIC][DEBUG] Processing Spotify URL")
                await ctx.send("Processing the Spotify link. It may take a few seconds to add all the songs to the queue.")
                titles = await self.extract_spotify_titles(query)
                if not titles:
                    await ctx.send("[MUSIC] Could not process Spotify link.")
                    return
                    
                if DEBUG_MODE:
                    print(f"[MUSIC][DEBUG] Extracted {len(titles)} titles from Spotify")
                
                for i, title in enumerate(titles):
                    results = await self.yt_search(title)
                    if results and len(results) > 0:
                        entry = results[0]
                        queue.append((entry["title"], entry["url"], entry["thumbnail"]))
                        if i == 0 and not vc.is_playing():
                            await self.play_next(ctx, vc)
                    await asyncio.sleep(0.5)
                    
            else:
                if DEBUG_MODE:
                    print("[MUSIC][DEBUG] Processing YouTube search/URL")
                entries = await self.yt_search(query)
                if not entries:
                    await ctx.send(embed=Embed(description="No results found.", color=EMBED_COLOR))
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
            print(f"[MUSIC][ERROR] play command: {e}")
            print(f"[MUSIC][ERROR] Traceback: {traceback.format_exc()}")
            await ctx.send(f"Error: {str(e)}")

    @commands.command(name='skip', aliases=["s", "next", "n"], help='Skips the current song')
    @commands.guild_only()
    async def skip(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_playing():
            vc.stop()
            await ctx.send(embed=Embed(description="⏭️ Skipped current song.", color=EMBED_COLOR))
        else:
            await ctx.send(embed=Embed(description="Nothing is playing.", color=EMBED_COLOR))
        
        await ctx.message.add_reaction("👍")

    @commands.command(name='stop', aliases=["disconnect", "leave", "l", "d"], help='Stops the music and disconnects from the voice channel')
    @commands.guild_only()
    async def disconnect(self, ctx):
        guild_id = ctx.guild.id
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            await ctx.send(embed=Embed(description="I'm not in a voice channel.", color=EMBED_COLOR))
            return
        self.queues[guild_id] = []
        self.playing_now[guild_id] = None
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        await vc.disconnect()
        await ctx.send(embed=Embed(description="Disconnected and cleared queue.", color=EMBED_COLOR))

        await ctx.message.add_reaction("👍")

    @commands.command(name='pause', aliases=["ps"], help='Pauses the current song')
    @commands.guild_only()
    async def pause(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send(embed=Embed(description="⏸️ Paused.", color=EMBED_COLOR))
        else:
            await ctx.send(embed=Embed(description="Nothing is playing.", color=EMBED_COLOR))

        await ctx.message.add_reaction("👍")

    @commands.command(name='resume', aliases=["r"], help='Resumes the paused song')
    @commands.guild_only()
    async def resume(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send(embed=Embed(description="▶️ Resumed.", color=EMBED_COLOR))
        else:
            await ctx.send(embed=Embed(description="Music is not paused.", color=EMBED_COLOR))

        await ctx.message.add_reaction("👍")

    @commands.command(name='queue', aliases=["q"], help='Shows the current music queue')
    @commands.guild_only()
    async def queue(self, ctx):
        queue = self.queues.get(ctx.guild.id, [])
        view = QueueView([{"title": t} for t, _, _ in queue])
        embed = view.create_embed()
        await ctx.send(embed=embed, view=view)

        await ctx.message.add_reaction("👍")

    @commands.command(name='nowplaying', aliases=["np"], help='Shows the currently playing song')
    @commands.guild_only()
    async def nowplaying(self, ctx):
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