import os
import asyncio
import discord
from discord.ext import commands
from colorama import Fore
from config import DEBUG_MODE, USE_SUB_BOT, SUB_BOT_FOLDER


class SubBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subbots_started = False

    async def cog_load(self):
        if USE_SUB_BOT and not self.subbots_started:
            asyncio.create_task(self.start_sub_bots_later())
            self.subbots_started = True

    async def start_sub_bots_later(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(3)
        await self.load_sub_bots()

    async def load_sub_bots(self):
        bots_dir = SUB_BOT_FOLDER

        if not os.path.exists(bots_dir):
            print(f"{Fore.YELLOW}[SUB-BOT] No '{bots_dir}' directory found, skipping...")
            return

        for folder in os.listdir(bots_dir):
            bot_path = os.path.join(bots_dir, folder)
            main_py = os.path.join(bot_path, "main.py")

            if os.path.isdir(bot_path) and os.path.exists(main_py):
                try:
                    print(f"{Fore.CYAN}[SUB-BOT] Launching: {Fore.GREEN}{folder}")
                    process = await asyncio.create_subprocess_exec(
                        "python", "main.py",
                        cwd=bot_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    asyncio.create_task(self.stream_subbot_output(process, folder))
                except Exception as e:
                    print(f"{Fore.RED}[SUB-BOT] Failed to start {folder}: {e}")

    async def stream_subbot_output(self, process, name):
        if not DEBUG_MODE:
            return

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(f"{Fore.MAGENTA}[{name}] {Fore.RESET}{line.decode().rstrip()}")

        err = await process.stderr.read()
        if err:
            print(f"{Fore.RED}[{name} ERROR]{Fore.RESET} {err.decode().rstrip()}")


async def setup(bot):
    await bot.add_cog(SubBot(bot))
