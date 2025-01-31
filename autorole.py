import discord
from discord.ext import commands
from discord import app_commands
import json
from colorama import Fore, Style
from config import SERVER_OPTIONS


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

    @app_commands.command(name="setautorole", description="Set the automatic role for new members.")
    @app_commands.describe(role="The role to be automatically assigned.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setautorole(self, interaction: discord.Interaction, role: discord.Role):
        guildId = str(interaction.guild.id)
        
        if role.name == "@everyone":
            await interaction.response.send_message("You cannot set @everyone as the automatic role.", ephemeral=True)
            return

        self.updateGuildConfig(guildId, "autorole", role.id)
        self.updateGuildConfig(guildId, "server_name", interaction.guild.name)
        
        await interaction.response.send_message(f"The automatic role has been set to: {role.mention}")
        print(f"Auto role set to {Fore.CYAN}{role.name}{Style.RESET_ALL} in server {Fore.CYAN}{interaction.guild.name}{Style.RESET_ALL}.")

    @app_commands.command(name="clearautorole", description="Remove the automatic role from the server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearautorole(self, interaction: discord.Interaction):
        guildId = str(interaction.guild.id)
        
        data = self.loadConfig()
        if guildId in data and "autorole" in data[guildId]:
            del data[guildId]["autorole"]
            self.saveConfig(data)
            await interaction.response.send_message("The automatic role has been removed from this server.")
            print(f"Auto role removed for server {Fore.CYAN}{interaction.guild.name}{Style.RESET_ALL}.")
        else:
            await interaction.response.send_message("No automatic role has been configured for this server.", ephemeral=True)
            print(f"No auto role configured for server {Fore.CYAN}{interaction.guild.name}{Style.RESET_ALL}.")

    @setautorole.error
    async def setlogchannelError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to set the automatic role.", ephemeral=True)        

    @clearautorole.error
    async def clearlogchannelError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to clear the automatic role.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guildId = str(member.guild.id)
        guildConfig = self.getGuildConfig(guildId)
        roleId = guildConfig.get("autorole")
        if roleId:
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
            print(f"No automatic role configured for server {Fore.CYAN}'{member.guild.name}'{Style.RESET_ALL}.")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
