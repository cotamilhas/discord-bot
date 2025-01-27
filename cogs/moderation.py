import discord
from discord.ext import commands
from colorama import Fore, Style


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Ban a user from the server.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        if reason:
            await ctx.send(f"{member.mention} was banned by {reason}.")
            print(Fore.RED + f"{ctx.author} banned {member} for {reason}." + Fore.RESET)
        else:
            await ctx.send(f"{member.mention} was banned.")
            print(Fore.RED + f"{ctx.author} banned {member}." + Fore.RESET)

    @commands.command(help="Kick a user from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        if reason:
            await ctx.send(f"{member.mention} was kicked for {reason}.")
            print(Fore.YELLOW + f"{ctx.author} kicked {member} for {reason}." + Fore.RESET)
        else:
            await ctx.send(f"{member.mention} was kicked.")
            print(Fore.YELLOW + f"{ctx.author} kicked {member}." + Fore.RESET)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
