import os
import discord
from discord.ext import commands

# Bot token
TOKEN = ""  # Change this to your bot token

# Command prefix
COMMAND_PREFIX = "?"  # Change this to your desired command prefix but since is using slash commands is kinda unnecessary

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

# Embed color
EMBED_COLOR = discord.Color.blue()  # Change this to the color you want for your embeds

# Coin Images
TAILS_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "tails.png")  # Change this to the path of your tails image
HEADS_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "heads.png")  # Change this to the path of your heads image