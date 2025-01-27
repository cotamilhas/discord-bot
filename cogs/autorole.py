import discord
from discord.ext import commands
import json
import os
import re
from colorama import Fore, Style
from config import SERVER_OPTIONS


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoRole = self.loadConfig()

    def loadConfig(self):
        if os.path.exists(SERVER_OPTIONS):
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def saveConfig(self):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(self.autoRole, f, indent=4, ensure_ascii=False)

    @commands.command(help="Set the auto role for new members.")
    @commands.has_permissions(manage_roles=True)
    async def setAutorole(self, ctx, *, roleInput):
        guildId = str(ctx.guild.id)
        roleId = None
        mentionMatch = re.match(r'<@&(?P<id>\d+)>', roleInput)
        if mentionMatch:
            roleId = int(mentionMatch.group('id'))
        else:
            role = discord.utils.get(ctx.guild.roles, name=roleInput)
            if role:
                roleId = role.id

        if roleId:
            role = discord.utils.get(ctx.guild.roles, id=roleId)
            if role:
                # not the best approach, but it works lol
                if role.name == "@everyone":
                    await ctx.send("You cannot set @everyone as the auto role.")
                    return

                self.autoRole[guildId] = {
                    "server_name": ctx.guild.name,
                    "role": role.id
                }
                self.saveConfig()
                await ctx.send(f"The auto role has been set to: {role.mention}")
                print(f"Auto role set to {Fore.CYAN}{role.name}{Style.RESET_ALL} in server {Fore.CYAN}{ctx.guild.name}{Style.RESET_ALL}.")
            else:
                await ctx.send(f"The role ID '{roleId}' could not be resolved. Make sure the role exists.")
                print(f"Role ID '{Fore.CYAN}{roleId}{Style.RESET_ALL}' could not be resolved in server {Fore.CYAN}{ctx.guild.name}{Style.RESET_ALL}.")
        else:
            await ctx.send(f"Could not find the role '{roleInput}'. Make sure it exists.")

    @commands.command(help="Clear the auto role for the server.")
    @commands.has_permissions(manage_roles=True)
    async def clearAutorole(self, ctx):
        guildId = str(ctx.guild.id)
        if guildId in self.autoRole:
            del self.autoRole[guildId]
            self.saveConfig()
            await ctx.send("The auto role has been removed for this server.")
            print(f"Auto role removed for server {Fore.CYAN}{ctx.guild.name}{Style.RESET_ALL}.")
        else:
            await ctx.send("No auto role was configured for this server.")
            print(f"No auto role configured for server {Fore.CYAN}{ctx.guild.name}{Style.RESET_ALL}.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guildId = str(member.guild.id)
        if guildId in self.autoRole:
            roleId = self.autoRole[guildId]["role"]
            role = discord.utils.get(member.guild.roles, id=roleId)
            if role is not None:
                try:
                    await member.add_roles(role)
                    print(f"Role {Fore.CYAN}{role.name}{Style.RESET_ALL} automatically assigned to "
                          f"{Fore.CYAN}{member.display_name}{Style.RESET_ALL} "
                          f"in server {Fore.CYAN}{member.guild.name}{Style.RESET_ALL}.")
                except discord.Forbidden:
                    print(f"Insufficient permissions to assign the role {Fore.CYAN}'{role.name}'{Style.RESET_ALL} "
                          f"in server {Fore.CYAN}{member.guild.name}{Style.RESET_ALL}.")
                except discord.HTTPException as e:
                    print(f"Error assigning the role: {Fore.CYAN}{e}{Style.RESET_ALL}")
            else:
                print(f"The role with ID {Fore.CYAN}'{roleId}'{Style.RESET_ALL} configured for server "
                      f"{Fore.CYAN}{member.guild.name}{Style.RESET_ALL} was not found.")
        else:
            print(f"No auto role configured for server {Fore.CYAN}'{member.guild.name}'{Style.RESET_ALL}.")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
