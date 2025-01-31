import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from config import TAILS_IMAGE, HEADS_IMAGE, EMBED_COLOR

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll a six-sided die.")
    async def roll(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        imagePath = f"stuff/dice/{result}.png"

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a **{result}**!",
            color=EMBED_COLOR()
        )

        with open(imagePath, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(imagePath))
            embed.set_image(url=f"attachment://{file.filename}")
            await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="flipcoin", description="Flip a coin and show the result.")
    async def flipcoin(self, interaction: discord.Interaction):
        outcome = random.choice(['Heads', 'Tails'])
        imagePath = TAILS_IMAGE if outcome == 'Tails' else HEADS_IMAGE

        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{outcome}**!",
            color=discord.Color.yellow()
        )

        with open(imagePath, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(imagePath))
            embed.set_image(url=f"attachment://{file.filename}")
            await interaction.response.send_message(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Fun(bot))
