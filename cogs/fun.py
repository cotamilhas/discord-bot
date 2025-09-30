import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import random
import os
from PIL import Image, ImageOps
import requests
from io import BytesIO
from config import TAILS_IMAGE, HEADS_IMAGE, EMBED_COLOR, FILTERS_FOLDER

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll a six-sided die.")
    async def roll(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        image_path = f"stuff/dice/{result}.png"

        if not os.path.exists(image_path):
            await interaction.response.send_message("Error: Dice image not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Dice Roll",
            description=f"You rolled a **{result}**!",
            color=EMBED_COLOR
        )

        with open(image_path, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{file.filename}")
            await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="flipcoin", description="Flip a coin and show the result.")
    async def flipcoin(self, interaction: discord.Interaction):
        outcome = random.choice(['Heads', 'Tails'])
        image_path = TAILS_IMAGE if outcome == 'Tails' else HEADS_IMAGE

        embed = discord.Embed(
            title="Coin Flip",
            description=f"The coin landed on **{outcome}**!",
            color=discord.Color.yellow()
        )

        with open(image_path, 'rb') as imageFile:
            file = discord.File(imageFile, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{file.filename}")
            await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="filter", description="Apply a filter to an avatar.")
    @app_commands.describe(
        filter_name="The filter to apply.",
        user="Optional user to apply the filter to (defaults to you)."
    )
    @app_commands.choices(filter_name=[
        app_commands.Choice(name="Grayscale", value="grayscale"),
        app_commands.Choice(name="Invert", value="invert"),
        app_commands.Choice(name="Sepia", value="sepia"),
        app_commands.Choice(name="Portuguese", value="portuguese")
    ])
    async def filter(self, interaction: discord.Interaction, filter_name: app_commands.Choice[str], user: Optional[discord.User] = None):
        target_user = user or interaction.user
        avatar_url = target_user.display_avatar.url

        await interaction.response.defer()

        try:
            response = requests.get(avatar_url)
            avatar_image = Image.open(BytesIO(response.content)).convert("RGBA")

            if filter_name.value == 'grayscale':
                filtered_image = ImageOps.grayscale(avatar_image).convert("RGBA")

            elif filter_name.value == 'invert':
                r, g, b, a = avatar_image.split()
                rgb_image = Image.merge("RGB", (r, g, b))
                inverted_image = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted_image.split()
                filtered_image = Image.merge("RGBA", (r2, g2, b2, a))

            elif filter_name.value == 'sepia':
                img = avatar_image.convert("RGB")
                pixels = img.load()
                for y in range(img.height):
                    for x in range(img.width):
                        r, g, b = img.getpixel((x, y))
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        tr, tg, tb = min(255, tr), min(255, tg), min(255, tb)
                        pixels[x, y] = (tr, tg, tb)
                filtered_image = img.convert("RGBA")

            elif filter_name.value == 'portuguese':
                filter_path = os.path.join(FILTERS_FOLDER, "portuguese.png")
                if not os.path.exists(filter_path):
                    await interaction.followup.send("Error: Portuguese filter image not found.", ephemeral=True)
                    return

                filter_image = Image.open(filter_path).convert("RGBA")
                filter_image = filter_image.resize(avatar_image.size)

                opacity = 0.2
                alpha = filter_image.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                filter_image.putalpha(alpha)

                filtered_image = Image.alpha_composite(avatar_image, filter_image)

            output_buffer = BytesIO()
            filtered_image.save(output_buffer, format='PNG')
            output_buffer.seek(0)

            file = discord.File(fp=output_buffer, filename="filtered_avatar.png")
            embed = discord.Embed(
                title=f"{target_user.name}'s Avatar with {filter_name.name} Filter",
                color=EMBED_COLOR
            )
            embed.set_image(url="attachment://filtered_avatar.png")
            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(f"[FUN] An error occurred while applying the filter: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Fun(bot))
