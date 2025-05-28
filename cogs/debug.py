import discord
from discord.ext import commands
from colorama import Fore, init
from config import DEBUG_MODE
init(autoreset=True)

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not DEBUG_MODE:
            return
        if interaction.type == discord.InteractionType.application_command:
            params = ""
            if hasattr(interaction, "data") and "options" in interaction.data:
                options = interaction.data["options"]
                params = " | Params: " + ", ".join(
                    f"{opt['name']}={opt.get('value', '')}" for opt in options
                )
            if interaction.guild:
                print(
                    f"{Fore.CYAN}[COMMAND]: /{interaction.command.name}{params} | User: {interaction.user} | Server: {interaction.guild.name} (ID: {interaction.guild.id})"
                )
            else:
                print(
                    f"{Fore.CYAN}[COMMAND]: /{interaction.command.name}{params} | User: {interaction.user} | (DM)"
                )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not DEBUG_MODE:
            return
        print(f"{Fore.RED}[ERROR]: Command '{ctx.command}' by {ctx.author} failed: {error}")

async def setup(bot):
    await bot.add_cog(Debug(bot))