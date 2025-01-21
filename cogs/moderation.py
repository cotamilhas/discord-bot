import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        if reason:
            await ctx.send(f"{member.mention} was banned by {reason}.")
        else:
            await ctx.send(f"{member.mention} was banned.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        if reason:
            await ctx.send(f"{member.mention} was kicked by {reason}.")
        else:
            await ctx.send(f"{member.mention} was kicked.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
