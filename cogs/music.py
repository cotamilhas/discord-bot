import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import re
from config import EMBED_COLOR

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.playingNow = {}

    async def ensure_voice(self, interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(
                description="You must be in a voice channel to use this command.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        voice_channel = interaction.user.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not vc:
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)
        return vc

    def yt_search(self, query):
        youtube_url_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
        is_url = re.match(youtube_url_pattern, query)

        ytdl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'default_search': 'ytsearch1' if not is_url else None,
            'extract_flat': 'in_playlist',
        }

        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            info = ytdl.extract_info(query, download=False)

            if 'entries' in info and info['entries']:
                entries = [
                    {
                        "title": entry.get("title"),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "thumbnail": entry.get("thumbnail")
                    }
                    for entry in info['entries'] if entry
                ]
                return entries

            elif info.get('title') and info.get('id'):
                return [{
                    "title": info['title'],
                    "url": f"https://www.youtube.com/watch?v={info['id']}",
                    "thumbnail": info.get('thumbnail')
                }]
            else:
                return []

    def create_source(self, url):
        ytdl_opts = {
            'format': 'bestaudio',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            info = ytdl.extract_info(url, download=False)
            return discord.FFmpegPCMAudio(info['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')

    async def play_next(self, interaction, vc):
        queue = self.queues.get(interaction.guild.id, [])
        if queue:
            title, url, thumbnail = queue.pop(0)
            self.queues[interaction.guild.id] = queue
            self.playingNow[interaction.guild.id] = (title, url)

            source = self.create_source(url)

            def after_playing(error):
                if error:
                    print(f"Playback error: {error}")
                fut = self.play_next(interaction, vc)
                asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

            vc.play(source, after=after_playing)

            embed = discord.Embed(
                title="Now Playing",
                description=f"[{title}]({url})",
                color=EMBED_COLOR
            )
            embed.set_thumbnail(url=thumbnail or f"https://img.youtube.com/vi/{url.split('v=')[-1]}/hqdefault.jpg")
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await interaction.followup.send(embed=embed)

        else:
            self.playingNow[interaction.guild.id] = None
            await vc.disconnect()

    @app_commands.command(name="play", description="Play a song or playlist from YouTube by search or link")
    @app_commands.describe(query="Search term or YouTube link")
    async def play(self, interaction: discord.Interaction, query: str):
        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        await interaction.response.defer()
        entries = self.yt_search(query)
        if not entries:
            embed = discord.Embed(
                description="No results found.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed)
            return

        queue = self.queues.setdefault(interaction.guild.id, [])
        queue.extend([(entry["title"], entry["url"], entry["thumbnail"]) for entry in entries])

        if len(entries) == 1:
            entry = entries[0]
            embed = discord.Embed(
                title="Added to Queue",
                description=f"[{entry['title']}]({entry['url']})",
                color=EMBED_COLOR
            )
            if entry.get("thumbnail"):
                embed.set_thumbnail(url=entry["thumbnail"])
        else:
            embed = discord.Embed(
                title="Playlist Added",
                description=f"Added {len(entries)} songs from playlist to the queue.",
                color=EMBED_COLOR
            )

        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

        if not vc.is_playing():
            await self.play_next(interaction, vc)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.stop()
            embed = discord.Embed(
                description="Skipped the current song.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="Nothing is playing.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stop", description="Stop the music and leave the channel")
    async def stop(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc:
            await vc.disconnect()
            self.queues[interaction.guild.id] = []
            self.playingNow[interaction.guild.id] = None
            embed = discord.Embed(
                description="Music stopped.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="I'm not in a voice channel.",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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
    async def queue(self, interaction: discord.Interaction):
        queue = self.queues.get(interaction.guild.id, [])
        if not queue:
            embed = discord.Embed(
                description="The queue is empty.",
                color=EMBED_COLOR
            )
        else:
            desc = "\n".join([f"{idx+1}. [{title}]({url})" for idx, (title, url) in enumerate(queue)])
            embed = discord.Embed(
                title="Queue",
                description=desc,
                color=EMBED_COLOR
            )
        await interaction.response.send_message(embed=embed)

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
