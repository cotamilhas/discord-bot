import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from config import FONT_PATH, FONT_SIZE, BACKGROUND_IMAGE, BOT_PRESENCE, GAME_NAME_PRESENCE, STREAM_NAME_PRESENCE, STREAM_URL_PRESENCE, SONG_NAME_PRESENCE, MOVIE_NAME_PRESENCE


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('\nBot is Online!')
        print(f'Logged in as {self.bot.user.name} ({self.bot.user.id})\n')

        if self.bot.guilds:
            print("Guilds connected to: ")
            for guild in self.bot.guilds:
                print(f'{guild.name} ({guild.id})')
        else:
            print('The bot is not connected to any servers.')

        presenceArray = {
            0: ("Playing", lambda: discord.Game(name=GAME_NAME_PRESENCE)),
            1: ("Streaming", lambda: discord.Streaming(
                name=STREAM_NAME_PRESENCE,
                url=STREAM_URL_PRESENCE
            )),
            2: ("Listening", lambda: discord.Activity(
                type=discord.ActivityType.listening,
                name=SONG_NAME_PRESENCE
            )),
            3: ("Watching", lambda: discord.Activity(
                type=discord.ActivityType.watching,
                name=MOVIE_NAME_PRESENCE
            )),
        }

        activity = presenceArray.get(BOT_PRESENCE)

        if activity:
            description, activityName = activity
            await self.bot.change_presence(activity=activityName())
            print(f"Bot presence set to: {BOT_PRESENCE}: {description}")
        else:
            print(f"Invalid BOT_PRESENCE value: {BOT_PRESENCE}")

    async def createImage(self, member, text):
        avatarUrl = str(member.avatar.url)

        avatarImg = Image.open(io.BytesIO(
            requests.get(avatarUrl).content)).resize((185, 185))

        mask = Image.new('L', (185, 185), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 185, 185), fill=255)

        background = Image.open(BACKGROUND_IMAGE).resize((500, 300))

        contour = Image.new('RGBA', (185 + 6, 185 + 6), (255, 255, 255, 0))
        contourDraw = ImageDraw.Draw(contour)
        contourDraw.ellipse((0, 0, 185 + 6, 185 + 6),
                            outline=(255, 255, 255, 255), width=3)

        contour.paste(avatarImg, (3, 3), mask)

        contourX = (500 - 191) // 2
        contourY = (300 - 191) // 2
        background.paste(contour, (contourX, contourY), contour)

        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        textBBox = draw.textbbox((0, 0), text, font=font)
        textX = (500 - (textBBox[2] - textBBox[0])) // 2
        draw.text((textX, 260), text, font=font, fill=(255, 255, 255))

        with io.BytesIO() as img:
            background.save(img, 'PNG')
            img.seek(0)
            return discord.File(img, 'output.png')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        channel = guild.system_channel

        if not channel:
            print(
                f"{member} joined, but no System Message Channel available to announce it.")
            return

        text = f'{member} joined the server!'
        file = await self.createImage(member, text)
        await channel.send(file=file)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        channel = guild.system_channel

        if not channel:
            print(
                f"{member} left, but no System Message Channel available to announce it.")
            return

        text = f'{member} left the server!'
        file = await self.createImage(member, text)
        await channel.send(file=file)


async def setup(bot):
    await bot.add_cog(Events(bot))
