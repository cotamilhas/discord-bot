import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
from PIL import Image
from config import EMBED_COLOR


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Responds with 'Pong!' and the bot's latency in milliseconds.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'Pong! {latency}ms')

    @app_commands.command(name="avatar", description="Displays a member's avatar or the command author's avatar.")
    @app_commands.describe(member="The member whose avatar you want to see.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=EMBED_COLOR,
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}", 
            icon_url=interaction.user.avatar.url
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Displays a member's banner or the command author's banner.")
    @app_commands.describe(member="The member whose banner you want to see.")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(
            title=f"{member.display_name}'s Banner",
            color=EMBED_COLOR
        )

        user = await self.bot.fetch_user(member.id)

        if user.banner:
            embed.set_image(url=user.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            color = user.accent_color or (
                member.color if member.color.value != 0 else discord.Color.default()
            )

            buffer = BytesIO()
            Image.new("RGB", (600, 200), color.to_rgb()).save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="banner.png")
            embed.description = "This user has a color as their banner."
            embed.set_image(url="attachment://banner.png")

            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}", 
                icon_url=interaction.user.avatar.url
            )
            await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="servericon", description="Displays the server icon, if available.")
    async def servericon(self, interaction: discord.Interaction):
        iconUrl = interaction.guild.icon.url if interaction.guild.icon else None
        embed = discord.Embed(
            title="Server Icon",
            color=EMBED_COLOR
        )
        if iconUrl:
            embed.set_image(url=iconUrl)
        else:
            embed.description = "This server does not have an icon."
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}", 
            icon_url=interaction.user.avatar.url
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Commands(bot))
