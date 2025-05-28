import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import re
from config import EMBED_COLOR, YTDL_SEARCH_OPTS, YTDL_DIRECT_OPTS, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, USE_SPOTIFY_API, NEXT_COLOR, BACK_COLOR

sp = None
if USE_SPOTIFY_API:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
    

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
        if self.page > 0:
            self.add_item(PreviousButton())
        if self.page < self.max_pages - 1:
            self.add_item(NextButton())

    async def update_message(self, interaction: Interaction):
        embed = self.create_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        current_page = self.queue[start:end]
        
        embed = Embed(
            title="Queue",
            description=f"Total Songs{len(self.queue)}",
            color=EMBED_COLOR
        )

        if not current_page:
            embed.description = "The song queue is empty."
        else:
            song_list = "\n".join(
                f"{i} - {song.get('title', 'Unknown title')}"
                for i, song in enumerate(current_page, start=start + 1)
            )
            embed.add_field(name="Playlist:", value=song_list, inline=False)

        embed.set_footer(text=f"Page {self.page + 1}/{self.max_pages}")
        return embed

class PreviousButton(Button):
    def __init__(self):
        super().__init__(style=BACK_COLOR, label="Back")

    async def callback(self, interaction: Interaction):
        view: QueueView = self.view
        view.page -= 1
        await view.update_message(interaction)

class NextButton(Button):
    def __init__(self):
        super().__init__(style=NEXT_COLOR, label="Next")

    async def callback(self, interaction: Interaction):
        view: QueueView = self.view
        view.page += 1
        await view.update_message(interaction)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.playing_now = {}
        self.search_tasks = {}
        
    def is_spotify_url(self, query):
        return USE_SPOTIFY_API and "open.spotify.com" in query
    
    async def extract_spotify_titles(self, url):
        if not USE_SPOTIFY_API:
            return []
            
        try:
            if "track/" in url:
                track_id = url.split("track/")[1].split("?")[0]
                track = sp.track(track_id)
                return [f"{track['name']} {track['artists'][0]['name']}"]
                
            elif "playlist/" in url:
                playlist_id = url.split("playlist/")[1].split("?")[0]
                results = sp.playlist_tracks(playlist_id)
                titles = [
                    f"{item['track']['name']} {item['track']['artists'][0]['name']}" 
                    for item in results['items'] 
                    if item.get('track')
                ]
                
                while results['next']:
                    results = sp.next(results)
                    titles.extend(
                        f"{item['track']['name']} {item['track']['artists'][0]['name']}" 
                        for item in results['items'] 
                        if item.get('track')
                    )
                    
                return titles
                
            elif "album/" in url:
                album_id = url.split("album/")[1].split("?")[0]
                results = sp.album_tracks(album_id)
                album = sp.album(album_id)
                album_name = album['name']
                
                titles = [
                    f"{track['name']} {track['artists'][0]['name']} {album_name}"
                    for track in results['items']
                    if track.get('name') and track.get('artists')
                ]
                
                while results['next']:
                    results = sp.next(results)
                    titles.extend(
                        f"{track['name']} {track['artists'][0]['name']} {album_name}"
                        for track in results['items']
                        if track.get('name') and track.get('artists')
                    )
                    
                return titles
            
            elif "artist/" in url:
                artist_id = url.split("artist/")[1].split("?")[0]
                artist = sp.artist(artist_id)
                top_tracks = sp.artist_top_tracks(artist_id, country='PT')['tracks']
                titles = [
                    f"{track['name']} - {artist['name']} ({artist['external_urls']['spotify']})"
                    for track in top_tracks
                ]
                
                return titles
                
            return []
        except Exception as e:
            print(f"[ERROR] Spotify: {e}")
            return []

    async def ensure_voice(self, interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=Embed(description="You must be in a voice channel!", color=EMBED_COLOR),
                ephemeral=True
            )
            return None
            
        voice_channel = interaction.user.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        
        if not vc:
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)
            
        return vc

    async def yt_search(self, query):
        is_url = re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', query)
        ytdl_opts = YTDL_SEARCH_OPTS.copy()
        
        if is_url:
            ytdl_opts.pop('default_search', None)
            
        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            info = ytdl.extract_info(query, download=False)
            
            if 'entries' in info:
                return [
                    {
                        "title": entry.get("title"),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "thumbnail": entry.get("thumbnail")
                    }
                    for entry in info['entries'] if entry
                ]
            elif info.get('title'):
                return [{
                    "title": info['title'],
                    "url": f"https://www.youtube.com/watch?v={info['id']}",
                    "thumbnail": info.get('thumbnail')
                }]
            return []

    def create_source(self, url):
        with yt_dlp.YoutubeDL(YTDL_DIRECT_OPTS) as ytdl:
            info = ytdl.extract_info(url, download=False)
            return discord.FFmpegPCMAudio(
                info['url'], 
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            )

    async def play_next(self, interaction, vc):
        queue = self.queues.get(interaction.guild.id, [])
        if not queue:
            self.playing_now[interaction.guild.id] = None
            await vc.disconnect()
            return
            
        title, url, thumbnail = queue.pop(0)
        self.queues[interaction.guild.id] = queue
        self.playing_now[interaction.guild.id] = (title, url)
        
        def after_playing(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(
                self.play_next(interaction, vc), 
                self.bot.loop
            )
            
        vc.play(self.create_source(url), after=after_playing)
        
        embed = Embed(
            title="Now Playing",
            description=f"[{title}]({url})",
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=thumbnail or f"https://img.youtube.com/vi/{url.split('v=')[-1]}/hqdefault.jpg")
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)

    async def process_spotify_playlist(self, interaction, spotify_titles, vc):
        if not spotify_titles:
            return
            
        embed = Embed(description="Processing Spotify playlist...", color=EMBED_COLOR)
        await interaction.followup.send(embed=embed)
        
        for i, title in enumerate(spotify_titles):
            if interaction.guild.id not in self.search_tasks or self.search_tasks[interaction.guild.id].cancelled():
                return
                
            results = await self.yt_search(title)
            if results:
                entry = results[0]
                self.queues.setdefault(interaction.guild.id, []).append(
                    (entry["title"], entry["url"], entry["thumbnail"])
                )
                
                if i == 0 and not vc.is_playing():
                    await self.play_next(interaction, vc)
                    
            await asyncio.sleep(3)

    @app_commands.command(name="play", description="Play a song or playlist from YouTube or Spotify")
    @app_commands.describe(query="Search term or URL")
    async def play(self, interaction: discord.Interaction, query: str):
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
            
        await interaction.response.defer()
        
        if interaction.guild.id in self.search_tasks:
            self.search_tasks[interaction.guild.id].cancel()
            
        if self.is_spotify_url(query):
            spotify_titles = await self.extract_spotify_titles(query)
            if not spotify_titles:
                await interaction.followup.send("Could not process Spotify link.", ephemeral=True)
                return
                
            task = asyncio.create_task(self.process_spotify_playlist(interaction, spotify_titles, vc))
            self.search_tasks[interaction.guild.id] = task
        else:
            entries = await self.yt_search(query)
            if not entries:
                await interaction.followup.send(
                    embed=Embed(description="No results found.", color=EMBED_COLOR)
                )
                return
                
            queue = self.queues.setdefault(interaction.guild.id, [])
            queue.extend((e["title"], e["url"], e["thumbnail"]) for e in entries)
            
            embed = Embed(
                title="Added to Queue" if len(entries) == 1 else "Playlist Added",
                description=f"[{entries[0]['title']}]({entries[0]['url']})" if len(entries) == 1 
                          else f"Added {len(entries)} songs to queue.",
                color=EMBED_COLOR
            )
            
            if len(entries) == 1 and entries[0].get("thumbnail"):
                embed.set_thumbnail(url=entries[0]["thumbnail"])
                
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
            if not vc.is_playing():
                await self.play_next(interaction, vc)
    
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        
        if vc and vc.is_playing():
            vc.stop()
            await interaction.followup.send(
                embed=Embed(description="Skipped current song.", color=EMBED_COLOR)
            )
        else:
            await interaction.followup.send(
                embed=Embed(description="Nothing is playing.", color=EMBED_COLOR),
                ephemeral=True
            )

    @app_commands.command(name="disconnect", description="Disconnect the bot from voice")
    async def disconnect(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        
        if not vc or not vc.is_connected():
            await interaction.followup.send(
                embed=Embed(description="I'm not in a voice channel.", color=EMBED_COLOR),
                ephemeral=True
            )
            return
            
        if guild_id in self.search_tasks:
            self.search_tasks[guild_id].cancel()
            del self.search_tasks[guild_id]
            
        self.queues[guild_id] = []
        self.playing_now[guild_id] = None
        
        if vc.is_playing() or vc.is_paused():
            vc.stop()
            
        await vc.disconnect()
        await interaction.followup.send(
            embed=Embed(description="Disconnected and cleared queue.", color=EMBED_COLOR)
        )

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.pause()
            embed = discord.Embed(
                description="Paused.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="Nothing is playing.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resume", description="Resume paused music")
    async def resume(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_paused():
            vc.resume()
            embed = discord.Embed(
                description="Resumed.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="Music is not paused.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="queue", description="Show the song queue")
    async def queue(self, interaction: Interaction):
        guild_id = interaction.guild.id
        queue = self.queues.get(guild_id, [])

        view = QueueView([{"title": title} for title, url, thumb in queue])
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="nowplaying", description="Show the current song")
    async def nowplaying(self, interaction: discord.Interaction):
        song = self.playingNow.get(interaction.guild.id)
        if song:
            title, url = song
            embed = discord.Embed(
                title="Now Playing",
                description=f"[{title}]({url})",
                color=EMBED_COLOR
            )
        else:
            embed = discord.Embed(
                description="Nothing is playing.",
                color=EMBED_COLOR
            )
            
        await interaction.response.send_message(embed=embed)
 

async def setup(bot):
    await bot.add_cog(Music(bot))