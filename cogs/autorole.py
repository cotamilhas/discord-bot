import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, Style, init
from config import SERVER_OPTIONS
from typing import Optional

init(autoreset=True)

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_config(self):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, data):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id):
        data = self.load_config()
        return data.get(str(guild_id), {})

    def update_guild_config(self, guild_id, key, value):
        data = self.load_config()
        guild_id = str(guild_id)
        if guild_id not in data:
            data[guild_id] = {"server_name": "Unknown"}
        data[guild_id][key] = value
        self.save_config(data)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild_id = str(after.id)
        data = self.load_config()

        if guild_id in data:
            if data[guild_id].get("server_name") != after.name:
                data[guild_id]["server_name"] = after.name
                self.save_config(data)

    @commands.command(name="autorole")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def autorole(self, ctx: commands.Context, role: Optional[discord.Role] = None):
        guild_id = str(ctx.guild.id)
        data = self.load_config()

        if role and isinstance(role, discord.Role):
            if role.name == "@everyone":
                await ctx.send("You cannot set @everyone as the automatic role.", delete_after=5)
                return

            self.update_guild_config(guild_id, "autorole", role.id)
            self.update_guild_config(guild_id, "server_name", ctx.guild.name)

            await ctx.send(f"The automatic role has been set to: {role.mention}", delete_after=5)
            print(
                f"[AUTOROLE]: Role {Fore.CYAN}{role.name}{Style.RESET_ALL} "
                f"set as automatic in server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
            )

        elif role is None or (isinstance(role, str) and role.lower() == "clear"):
            if guild_id in data and "autorole" in data[guild_id]:
                del data[guild_id]["autorole"]
                self.save_config(data)
                await ctx.send("The automatic role has been removed from this server.", delete_after=5)
                print(
                    f"[AUTOROLE]: Automatic role removed in server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
            else:
                await ctx.send("No automatic role has been configured for this server.", delete_after=5)
                print(
                    f"[AUTOROLE][INFO]: No automatic role configured for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
        else:
            await ctx.send("Invalid usage. Examples:\n"
                           "`!autorole @Role`\n"
                           "`!autorole clear`", delete_after=10)
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        guild_config = self.get_guild_config(guild_id)
        role_id = guild_config.get("autorole")

        if role_id:
            role = discord.utils.get(member.guild.roles, id=role_id)
            if role is not None:
                try:
                    print(
                        f"[AUTOROLE] Role {Fore.CYAN}{role.name}{Style.RESET_ALL} "
                        f"automatically assigned to {Fore.GREEN}{member.display_name}{Style.RESET_ALL} "
                        f"in server {Fore.MAGENTA}{member.guild.name}{Style.RESET_ALL} "
                        f"(ID: {Fore.YELLOW}{member.guild.id}{Style.RESET_ALL})"
                    )
                    await member.add_roles(role)
                except discord.Forbidden:
                    print(
                        f"[AUTOROLE][ERROR] Insufficient permissions to assign role "
                        f"{Fore.CYAN}{role.name}{Style.RESET_ALL} "
                        f"in server {Fore.MAGENTA}{member.guild.name}{Style.RESET_ALL} "
                        f"(ID: {Fore.YELLOW}{member.guild.id}{Style.RESET_ALL})"
                    )
                except discord.HTTPException as e:
                    print(
                        f"[AUTOROLE][ERROR] Error assigning role {Fore.CYAN}{role.name}{Style.RESET_ALL} "
                        f"to {Fore.GREEN}{member.display_name}{Style.RESET_ALL}: {Fore.RED}{e}{Style.RESET_ALL}"
                    )
            else:
                print(
                    f"[AUTOROLE][WARNING]: Role with ID {Fore.YELLOW}{role_id}{Style.RESET_ALL} "
                    f"configured for server {Fore.MAGENTA}{member.guild.name}{Style.RESET_ALL} was not found."
                )
        else:
            print(
                f"[AUTOROLE][INFO]: No automatic role configured for server {Fore.MAGENTA}{member.guild.name}{Style.RESET_ALL} "
                f"(ID: {Fore.YELLOW}{member.guild.id}{Style.RESET_ALL})"
            )


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
