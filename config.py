import os

TOKEN = "" # Change this to your bot token

COMMAND_PREFIX = "?" # Change this to your desired command prefix

FONT_PATH = os.path.join(os.path.dirname(__file__), "stuff", "arial.ttf") # Change this to the path of your font file
FONT_SIZE = 22 # Change this to the size of your font
BACKGROUND_IMAGE = os.path.join(os.path.dirname(__file__), "stuff", "background.png") # Change this to the path of your background image

BOT_PRESENCE = 0 # 0 - Playing Status; 1 - Streaming Status; 2 - Listening Status; 3 - Watching Status.
GAME_NAME_PRESENCE = "Game" # Change this to the game you want to show in the presence
STREAM_NAME_PRESENCE = "Stream" # Change this to the stream you want to show in the presence
STREAM_URL_PRESENCE = "https://www.twitch.tv/cotamilhas" # Twitch Link or YouTube Live Link
SONG_NAME_PRESENCE = "Song" # Change this to the song you want to show in the presence
MOVIE_NAME_PRESENCE = "Movie" # Change this to the movie you want to show in the presence
