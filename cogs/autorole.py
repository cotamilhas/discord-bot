import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, init
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

    @app_commands.command(name="autorole", description="Set or clear the automatic role for new members. (Admin only)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Set Role", value="setRole"),
        app_commands.Choice(name="Clear Role", value="clearRole")
    ])
    @app_commands.describe(
        role="The role to automatically assign (only needed when using 'Set')"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def autorole(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        role: Optional[discord.Role] = None
    ):
        guild_id = str(interaction.guild.id)
        data = self.load_config()

        if mode.value == "setRole":
            if role is None:
                await interaction.response.send_message("You must specify a role when setting autorole.", ephemeral=True)
                return

            if role.name == "@everyone":
                await interaction.response.send_message("You cannot set @everyone as the automatic role.", ephemeral=True)
                return

            self.update_guild_config(guild_id, "autorole", role.id)
            self.update_guild_config(guild_id, "server_name", interaction.guild.name)

            await interaction.response.send_message(f"The automatic role has been set to: {role.mention}", ephemeral=True)
            print(f"Auto role set to {Fore.CYAN}{role.name} in server {Fore.CYAN}{interaction.guild.name}.")

        elif mode.value == "clearRole":
            if guild_id in data and "autorole" in data[guild_id]:
                del data[guild_id]["autorole"]
                self.save_config(data)
                await interaction.response.send_message("The automatic role has been removed from this server.")
                print(f"Auto role removed for server {Fore.CYAN}{interaction.guild.name}.")
            else:
                await interaction.response.send_message("No automatic role has been configured for this server.", ephemeral=True)
                print(f"No auto role configured for server {Fore.CYAN}{interaction.guild.name}.")     
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        guild_config = self.get_guild_config(guild_id)
        role_id = guild_config.get("autorole")
        if role_id:
            role = discord.utils.get(member.guild.roles, id=role_id)
            if role is not None:
                try:
                    print(f"Role {Fore.CYAN}{role.name} automatically assigned to "
                          f"{Fore.CYAN}{member.display_name} "
                          f"in server {Fore.CYAN}{member.guild.name}.")
                    await member.add_roles(role)
                except discord.Forbidden:
                    print(f"Insufficient permissions to assign the role {Fore.CYAN}'{role.name}' "
                          f"in server {Fore.CYAN}{member.guild.name}.")
                except discord.HTTPException as e:
                    print(f"Error assigning the role: {Fore.CYAN}{e}")
            else:
                print(f"The role with ID {Fore.CYAN}'{role_id}' configured for server "
                      f"{Fore.CYAN}{member.guild.name} was not found.")
        else:
            print(f"No automatic role configured for server {Fore.CYAN}'{member.guild.name}'.")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
