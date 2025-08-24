import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from colorama import Fore, init
from config import FONT_PATH, FONT_SIZE, BACKGROUND_IMAGE, BOT_PRESENCE, GAME_NAME_PRESENCE, STREAM_NAME_PRESENCE, STREAM_URL_PRESENCE, SONG_NAME_PRESENCE, MOVIE_NAME_PRESENCE
init(autoreset=True)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\n{Fore.GREEN}Bot is Online!")
        print(f"Logged in as {Fore.GREEN}{self.bot.user.name} {Fore.YELLOW}({self.bot.user.id})\n")

        if self.bot.guilds:
            print(f"{Fore.CYAN}Guilds connected to:")
            for guild in self.bot.guilds:
                print(f"{Fore.GREEN}{guild.name} {Fore.YELLOW}({guild.id})")
        else:
            print(f"{Fore.RED}The bot is not connected to any servers.\n")

        presence_array = {
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

        activity = presence_array.get(BOT_PRESENCE)

        if activity:
            description, activity_name = activity
            await self.bot.change_presence(activity=activity_name())
            print(f"\nBot presence set to: {Fore.GREEN}{BOT_PRESENCE}{Fore.WHITE}: {Fore.CYAN}{description}\n")
        else:
            print(f"\n{Fore.RED}Invalid BOT_PRESENCE value: {BOT_PRESENCE}")

        await self.bot.tree.sync()
        print(Fore.GREEN + "Slash commands synchronized successfully!")

    async def createImage(self, member, text):
        avatar_url = str(member.avatar.url)
        
        avatar_img = Image.open(io.BytesIO(requests.get(avatar_url).content)).convert("RGBA")
        avatar_size = 370
        avatar_resized = avatar_img.resize((avatar_size, avatar_size), Image.LANCZOS)
        
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        avatar_final = avatar_resized.resize((185, 185), Image.LANCZOS)
        mask_final = mask.resize((185, 185), Image.LANCZOS)
        
        background = Image.open(BACKGROUND_IMAGE).convert("RGBA").resize((500, 300))
        
        contour_size = 191 * 2
        contour = Image.new('RGBA', (contour_size, contour_size), (255, 255, 255, 0))
        contour_draw = ImageDraw.Draw(contour)
        contour_draw.ellipse((0, 0, contour_size, contour_size), outline=(255, 255, 255, 255), width=6 * 2)
        
        contour_final = contour.resize((191, 191), Image.LANCZOS)
        contour_final.paste(avatar_final, (3, 3), mask_final)
        
        contourX = (500 - 191) // 2
        contourY = (300 - 191) // 2
        background.paste(contour_final, (contourX, contourY), contour_final)
        
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
                f"{Fore.YELLOW}{member} joined, but no System Message Channel available to announce it.")
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
                f"{Fore.YELLOW}{member} left, but no System Message Channel available to announce it.")
            return
        
        text = f'{member.display_name} left the server!'
        file = await self.createImage(member, text)
        await channel.send(file=file)


async def setup(bot):
    await bot.add_cog(Events(bot))
