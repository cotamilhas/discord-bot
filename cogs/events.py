import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from colorama import Fore, Style
from config import FONT_PATH, FONT_SIZE, BACKGROUND_IMAGE, BOT_PRESENCE, GAME_NAME_PRESENCE, STREAM_NAME_PRESENCE, STREAM_URL_PRESENCE, SONG_NAME_PRESENCE, MOVIE_NAME_PRESENCE


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'\n{Fore.GREEN}Bot is Online!{Style.RESET_ALL}')
        print(f'Logged in as {Fore.GREEN}{self.bot.user.name}{Style.RESET_ALL} ({Fore.YELLOW}{self.bot.user.id}{Style.RESET_ALL})\n')

        if self.bot.guilds:
            print(f"{Fore.CYAN}Guilds connected to:{Style.RESET_ALL}")
            for guild in self.bot.guilds:
                print(f'{Fore.GREEN}{guild.name}{Style.RESET_ALL} ({Fore.YELLOW}{guild.id}{Style.RESET_ALL})')
        else:
            print(f'{Fore.RED}The bot is not connected to any servers.{Style.RESET_ALL}\n')

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
            4: ("Only Online", lambda: None)
        }

        activity = presenceArray.get(BOT_PRESENCE)

        if activity:
            description, activityName = activity
            await self.bot.change_presence(activity=activityName())
            print(f"\nBot presence set to: {Fore.GREEN}{BOT_PRESENCE}{Style.RESET_ALL}: {Fore.CYAN}{description}{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.RED}Invalid BOT_PRESENCE value: {BOT_PRESENCE}{Style.RESET_ALL}")

    async def createImage(self, member, text):
        avatarUrl = str(member.avatar.url)
        
        avatarImg = Image.open(io.BytesIO(requests.get(avatarUrl).content)).convert("RGBA")
        avatarSize = 370
        avatarResized = avatarImg.resize((avatarSize, avatarSize), Image.LANCZOS)
        
        mask = Image.new('L', (avatarSize, avatarSize), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatarSize, avatarSize), fill=255)
        
        avatarFinal = avatarResized.resize((185, 185), Image.LANCZOS)
        maskFinal = mask.resize((185, 185), Image.LANCZOS)
        
        background = Image.open(BACKGROUND_IMAGE).convert("RGBA").resize((500, 300))
        
        contourSize = 191 * 2
        contour = Image.new('RGBA', (contourSize, contourSize), (255, 255, 255, 0))
        contourDraw = ImageDraw.Draw(contour)
        contourDraw.ellipse((0, 0, contourSize, contourSize), outline=(255, 255, 255, 255), width=6 * 2)
        
        contourFinal = contour.resize((191, 191), Image.LANCZOS)
        contourFinal.paste(avatarFinal, (3, 3), maskFinal)
        
        contourX = (500 - 191) // 2
        contourY = (300 - 191) // 2
        background.paste(contourFinal, (contourX, contourY), contourFinal)
        
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
                f"{Fore.YELLOW}{member}{Style.RESET_ALL} joined, but no System Message Channel available to announce it.")
            return
        
        text = f'{member.display_name} joined the server!'
        file = await self.createImage(member, text)
        await channel.send(file=file)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        channel = guild.system_channel

        if not channel:
            print(
                f"{Fore.YELLOW}{member}{Style.RESET_ALL} left, but no System Message Channel available to announce it.")
            return
        
        text = f'{member.display_name} left the server!'
        file = await self.createImage(member, text)
        await channel.send(file=file)

async def setup(bot):
    await bot.add_cog(Events(bot))
