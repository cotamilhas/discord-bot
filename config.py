import os
import discord
from discord.ext import commands
from discord import ButtonStyle

DEBUG_MODE = False  # Change this to True if you want to enable debug mode, otherwise False

# Bot token
TOKEN = ""  # Change this to your bot token

# Command prefix
COMMAND_PREFIX = "!"  # Change this to your desired command prefix, at the moment only Music Cog uses this prefix

# Font settings
FONT_PATH = os.path.join(os.path.dirname(__file__), "stuff", "arial.ttf")  # Change this to the path of your font file
FONT_SIZE = 22  # Change this to the size of your font

# Background image
BACKGROUND_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "background.png")  # Change this to the path of your background image

# Bot presence settings
BOT_PRESENCE = 4  # 0 - Playing Status; 1 - Streaming Status; 2 - Listening Status; 3 - Watching Status; 4 - Normal Status.
GAME_NAME_PRESENCE = "Game"  # Change this to the game you want to show in the presence
STREAM_NAME_PRESENCE = "Stream"  # Change this to the stream you want to show in the presence
STREAM_URL_PRESENCE = "https://www.twitch.tv/cotamilhas"  # Twitch Link or YouTube Live Link
SONG_NAME_PRESENCE = "Song"  # Change this to the song you want to show in the presence
MOVIE_NAME_PRESENCE = "Movie"  # Change this to the movie you want to show in the presence

# Server options
SERVER_OPTIONS = os.path.join(os.path.dirname(__file__), "stuff", "serveroptions.json")  # Change this to the path of your server options file
LEVELS_FILE = os.path.join(os.path.dirname(__file__), "stuff", "levels.json")  # Change this to the path of your levels file

ALERTS = False  # Change this to True if you want to enable alerts, otherwise False
ALERTS_FILE = os.path.join(os.path.dirname(__file__), "stuff", "alerts.json")  # Change this to the path of your alerts file

# Embed color
EMBED_COLOR = discord.Color.blue()  # Change this to the color you want for your embeds
NEXT_COLOR = ButtonStyle.green  # Change this to the color you want for your next button
BACK_COLOR = ButtonStyle.red  # Change this to the color you want for your back button

# Coin Images
TAILS_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "tails.png")  # Change this to the path of your tails image
HEADS_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "heads.png")  # Change this to the path of your heads image

# Bot Intents
INTENTS = discord.Intents.all()  # Change this to the intents you want to use

# YT_DLP Options
YTDL_SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'extract_flat': 'in_playlist',
    'ignoreerrors': True,
    'geo_bypass': True,
    'socket_timeout': 10,
    'source_address': '0.0.0.0',
    'noplaylist': True,
    'compat_opts': {
        'no-youtube-unavailable-videos': True 
    }
}

YTDL_DIRECT_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'retries': 3,
    'http_headers': {
        'Referer': 'https://www.youtube.com/',
    },
}

# Spotify API Credentials - Choose WebAPI and get your credentials
# You can get your credentials from the Spotify Developer Dashboard: https://developer.spotify.com/dashboard/create
USE_SPOTIFY_API = False  # Change this to True if you want to use the Spotify API, otherwise False
SPOTIFY_CLIENT_ID = ""  # If USE_SPOTIFY_API is True, change this to your Spotify Client ID
SPOTIFY_CLIENT_SECRET = ""  # If USE_SPOTIFY_API is True, change this to your Spotify Client Secret
