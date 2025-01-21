import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        guildId = ctx.guild.id
        await ctx.send(f'Pong! Guild ID: {guildId}')

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"Avatar of {member.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=f"Requested by {
                         ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @commands.command()
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"Banner of {member.display_name}", color=discord.Color.blue())

        user = await self.bot.fetch_user(member.id)

        if user.banner:
            embed.set_image(url=user.banner.url)
        else:
            color = user.accent_color or (
                member.color if member.color.value != 0 else discord.Color.default())

            buffer = BytesIO()
            Image.new("RGB", (600, 200), color.to_rgb()
                      ).save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="color_banner.png")
            embed.description = "This user has a color as their banner."
            embed.set_image(url="attachment://color_banner.png")

        embed.set_footer(text=f"Requested by {
                         ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed, file=file if 'file' in locals() else None)


async def setup(bot):
    await bot.add_cog(Commands(bot))
