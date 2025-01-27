import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image
from config import EMBED_COLOR


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Responds with 'Pong!' and the bot's latency in milliseconds.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'Pong! {latency}ms')

    @commands.command(help="Displays the avatar of the specified member or the command author.")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"Avatar of {member.display_name}",
            color=EMBED_COLOR,
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", 
            icon_url=ctx.author.avatar.url
        )

        await ctx.send(embed=embed)

    @commands.command(help="Displays the banner of the specified member or the command author.")
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"Banner of {member.display_name}",
            color=EMBED_COLOR
        )

        user = await self.bot.fetch_user(member.id)

        if user.banner:
            embed.set_image(url=user.banner.url)
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
            text=f"Requested by {ctx.author.display_name}", 
            icon_url=ctx.author.avatar.url
        )
        await ctx.send(embed=embed, file=file if not user.banner else None)

    @commands.command(help="Sends the server's icon if available.")
    async def servericon(self, ctx):
        iconUrl = ctx.guild.icon.url if ctx.guild.icon else None
        embed = discord.Embed(
            title="Server Icon",
            color=EMBED_COLOR
        )
        if iconUrl:
            embed.set_image(url=iconUrl)
        else:
            embed.description = "This server does not have an icon."
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", 
            icon_url=ctx.author.avatar.url
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Commands(bot))
