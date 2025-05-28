import discord
from discord.ext import commands
from discord import app_commands
from colorama import Fore, init
init(autoreset=True)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user from the server. (Admin only)")
    @app_commands.describe(member="The user to be banned.", reason="The reason for the ban.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        await member.ban(reason=reason)
        
        if reason:
            await interaction.followup.send(f"{member.mention} was banned for: {reason}.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} banned {member} for: {reason}.")
        else:
            await interaction.followup.send(f"{member.mention} was banned.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} banned {member}.")

    @app_commands.command(name="kick", description="Kick a user from the server. (Admin only)")
    @app_commands.describe(member="The user to be kicked.", reason="The reason for the kick.")
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        await member.kick(reason=reason)
    
        if reason:
            await interaction.followup.send(f"{member.mention} was kicked for: {reason}.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} kicked {member} for: {reason}.")
        else:
            await interaction.followup.send(f"{member.mention} was kicked.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} kicked {member}.")

    @ban.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to ban members.", ephemeral=True)  

    @kick.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to kick members.", ephemeral=True)
          

async def setup(bot):
    await bot.add_cog(Moderation(bot))
