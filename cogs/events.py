import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from colorama import Fore, init
import sys
from config import FONT_PATH, FONT_SIZE, BACKGROUND_IMAGE, DEBUG_MODE
from config import BOT_PRESENCE, GAME_NAME_PRESENCE, STREAM_NAME_PRESENCE, STREAM_URL_PRESENCE, SONG_NAME_PRESENCE, MOVIE_NAME_PRESENCE
init(autoreset=True)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'appinfo'):
            self.bot.appinfo = await self.bot.application_info()
            self.bot.owner_id = self.bot.appinfo.owner.id
        
        print(f"Logged in as {Fore.GREEN}{self.bot.user.name} {Fore.YELLOW}({self.bot.user.id})\n")
        print(f"{Fore.CYAN}Owner: {Fore.GREEN}{self.bot.appinfo.owner} {Fore.YELLOW}({self.bot.appinfo.owner.id})")
        print(f"{Fore.CYAN}Python Version: {Fore.GREEN}{sys.version}")
        print(f"{Fore.CYAN}Command Prefix: {Fore.GREEN}{self.bot.command_prefix}")

        if self.bot.guilds:
            print(f"\n{Fore.CYAN}Guilds connected to:")
            for guild in self.bot.guilds:
                print(f"{Fore.GREEN}{guild.name} {Fore.YELLOW}({guild.id})")
                print(f"Server Owner: {Fore.GREEN}{guild.owner} {Fore.YELLOW}({guild.owner.id})")
                print(f"Members: {Fore.GREEN}{guild.member_count}\n")
                
        else:
            print(f"{Fore.RED}[EVENTS] The bot is not connected to any servers.\n")

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
            print(f"Bot presence set to: {Fore.GREEN}{BOT_PRESENCE}{Fore.WHITE}: {Fore.CYAN}{description}\n")
        else:
            print(f"[EVENTS]{Fore.RED} Invalid BOT_PRESENCE value: {BOT_PRESENCE}")

    async def create_image(self, member, text):
        avatar_url = str(member.avatar.url)
        avatar_size = 400

        avatar_img = Image.open(io.BytesIO(requests.get(avatar_url).content)).convert("RGBA")
        avatar_resized = avatar_img.resize((avatar_size, avatar_size), Image.LANCZOS)

        mask = Image.new('L', (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

        background = Image.open(BACKGROUND_IMAGE).convert("RGBA").resize((1280, 720))
        
        border_size = 12
        contour_size = avatar_size + border_size * 2
        contour = Image.new('RGBA', (contour_size, contour_size), (255, 255, 255, 0))
        contour_draw = ImageDraw.Draw(contour)
        contour_draw.ellipse(
            (0, 0, contour_size - 1, contour_size - 1),
            outline=(255, 255, 255, 255),
            width=border_size
        )

        avatar_pos = (border_size, border_size)
        contour.paste(avatar_resized, avatar_pos, mask)

        contourX = (1280 - contour_size) // 2
        contourY = (720 - contour_size) // 2 - 60

        background.paste(contour, (contourX, contourY), contour)

        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        textBBox = draw.textbbox((0, 0), text, font=font)
        textX = (1280 - (textBBox[2] - textBBox[0])) // 2
        textY = contourY + contour_size + 40

        draw.text((textX, textY), text, font=font, fill=(255, 255, 255))

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

        text = f'{member.display_name} joined the {guild.name}!'
        try:
            file = await self.create_image(member, text)
            await channel.send(file=file)  
        except Exception as e:
            print(Fore.RED + f"[EVENTS] Error creating image: {e}")
            await channel.send(f"{member} joined. An error occurred while creating the image.")
            return None

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        channel = guild.system_channel

        if not channel:
            print(
                f"{Fore.YELLOW}{member} left, but no System Message Channel available to announce it.")
            return

        text = f'{member.display_name} left the {guild.name}!'
        try:
            file = await self.create_image(member, text)
            await channel.send(file=file)
        except Exception as e:
            print(Fore.RED + f"[EVENTS] Error creating image: {e}")
            await channel.send(f"{member} left. An error occurred while creating the image.")
            return None
        
    # DEBUG
    @commands.command(name="forceimage")
    async def force_image(self, ctx, member: discord.Member = None):
        if DEBUG_MODE:
            guild = ctx.guild
            if member is None:
                member = ctx.author
                
            if ctx.author.id != member.guild.owner.id:
                return
                
            text = f'{member.display_name} joined the {guild.name}!'
            try:
                file = await self.create_image(member, text)
                await ctx.send(file=file)
            except Exception as e:
                print(Fore.RED + f"[EVENTS] Error creating image: {e}")
                await ctx.send(f"{member} joined. An error occurred while creating the image.")
                return None


async def setup(bot):
    await bot.add_cog(Events(bot))
