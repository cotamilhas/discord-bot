import discord
from discord.ext import commands
import random
import os
from config import TAILS_IMAGE, HEADS_IMAGE, EMBED_COLOR


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', help="Roll a six-sided dice and send the result as an embedded message with an image of the dice face.")
    async def roll(self, ctx):
        result = random.randint(1, 6)
        imagePath = f"stuff/dice/{result}.png"

        embed = discord.Embed(
            title="Dice Roll",
            description=f"You rolled a {result}!",
            color=EMBED_COLOR()
        )

        with open(imagePath, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(imagePath))
            embed.set_image(url=f"attachment://{file.filename}")
            await ctx.send(embed=embed, file=file)

    @commands.command(name='flipcoin', aliases=['coinflip', 'coin'], help="Flip a coin and send the result as an embedded message with an image of the coin face.")
    async def coinflip(self, ctx):
        outcome = random.choice(['Heads', 'Tails'])
        imagePath = TAILS_IMAGE if outcome == 'Tails' else HEADS_IMAGE

        embed = discord.Embed(
            title="Coin Flip",
            description=f"The coin landed on {outcome}!",
            color=discord.Color.yellow()
        )

        with open(imagePath, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(imagePath))
            embed.set_image(url=f"attachment://{file.filename}")
            await ctx.send(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(Fun(bot))
