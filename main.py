import discord
from discord.ext import commands
import os
import asyncio
from config import TOKEN, COMMAND_PREFIX

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


async def loadCogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Cog loaded: {extension}")
            except Exception as e:
                print(f"Error loading {extension}: {e}")

if __name__ == "__main__":
    async def main():
        await loadCogs()
        await bot.start(TOKEN)
    asyncio.run(main())
