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

    def loadConfig(self):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def saveConfig(self, data):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def getGuildConfig(self, guildId):
        data = self.loadConfig()
        return data.get(str(guildId), {})

    def updateGuildConfig(self, guildId, key, value):
        data = self.loadConfig()
        guildId = str(guildId)
        if guildId not in data:
            data[guildId] = {"server_name": "Unknown"}
        data[guildId][key] = value
        self.saveConfig(data)

    @app_commands.command(name="autorole", description="Set or clear the automatic role for new members. (Admin only)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Set Role", value="setRole"),
        app_commands.Choice(name="Clear Role", value="clearRole")
    ])
    @app_commands.describe(
        role="The role to automatically assign (only needed when using 'Set')"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        role: Optional[discord.Role] = None
    ):
        guild_id = str(interaction.guild.id)
        data = self.loadConfig()

        if mode.value == "setRole":
            if role is None:
                await interaction.response.send_message("You must specify a role when setting autorole.", ephemeral=True)
                return

            if role.name == "@everyone":
                await interaction.response.send_message("You cannot set @everyone as the automatic role.", ephemeral=True)
                return

            self.updateGuildConfig(guild_id, "autorole", role.id)
            self.updateGuildConfig(guild_id, "server_name", interaction.guild.name)

            await interaction.response.send_message(f"The automatic role has been set to: {role.mention}", ephemeral=True)
            print(f"Auto role set to {Fore.CYAN}{role.name} in server {Fore.CYAN}{interaction.guild.name}.")

        elif mode.value == "clearRole":
            if guild_id in data and "autorole" in data[guild_id]:
                del data[guild_id]["autorole"]
                self.saveConfig(data)
                await interaction.response.send_message("The automatic role has been removed from this server.")
                print(f"Auto role removed for server {Fore.CYAN}{interaction.guild.name}.")
            else:
                await interaction.response.send_message("No automatic role has been configured for this server.", ephemeral=True)
                print(f"No auto role configured for server {Fore.CYAN}{interaction.guild.name}.")

    @autorole.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to set the automatic role.", ephemeral=True)        
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guildId = str(member.guild.id)
        guildConfig = self.getGuildConfig(guildId)
        roleId = guildConfig.get("autorole")
        if roleId:
            role = discord.utils.get(member.guild.roles, id=roleId)
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
                print(f"The role with ID {Fore.CYAN}'{roleId}' configured for server "
                      f"{Fore.CYAN}{member.guild.name} was not found.")
        else:
            print(f"No automatic role configured for server {Fore.CYAN}'{member.guild.name}'.")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
