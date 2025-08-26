import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from datetime import datetime, timezone
from colorama import Fore, init
from config import TOKEN, COMMAND_PREFIX, EMBED_COLOR, INTENTS, DEBUG_MODE
init(autoreset=True)


bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=INTENTS, help_command=None)

async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Command is currently on cooldown! Try again in **{error.retry_after:.2f}** seconds!",
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You don't have permission to use this command.",
            ephemeral=True
        )
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"An unexpected error occurred: `{error}`",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"An unexpected error occurred: `{error}`",
                ephemeral=True
            )

bot.tree.on_error = on_tree_error

async def loadCogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Cog loaded: {Fore.GREEN}{extension}")
            except Exception as e:
                print(f"{Fore.RED}Error loading {extension}: {e}")

    @bot.tree.command(name="help", description="Displays the help menu.")
    @app_commands.describe(command="The command you want to get help with.")
    async def help(interaction: discord.Interaction, command: str = None):
        embed = discord.Embed(
            title=f"Help for {bot.user.name}!",
            color=EMBED_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        commandCategories = {}

        for cog_name, cog in bot.cogs.items():
            commands = cog.get_app_commands()
            if commands:
                commandCategories[cog_name] = commands

        if not command:
            for category, commands in commandCategories.items():
                embed.add_field(
                    name=f"{category}",
                    value="\n".join([f"`/{cmd.name}` - {cmd.description}" for cmd in commands]),
                    inline=False
                )
            embed.add_field(
                name="Details",
                value=f"Type `/help <command>` for more details about a specific command.",
                inline=False
            )
        else:
            cmd = bot.tree.get_command(command)
            if cmd:
                params = []
                if hasattr(cmd, 'parameters'):
                    for param in cmd.parameters:
                        params.append(f"`{param.name}`: {param.description}")
                elif hasattr(cmd, '_params'):
                    params = [f"`{param.name}`: {param.description})" 
                            for param in cmd._params.values()]
                
                usage = f"/{cmd.name}"
                if params:
                    usage += " " + " ".join([f"<{param.name}>" for param in (cmd.parameters if hasattr(cmd, 'parameters') else cmd._params.values())])
                
                embed.add_field(
                    name=f"Command: /{cmd.name}",
                    value=f"**Description**: {cmd.description}\n\n**Usage**: `{usage}`",
                    inline=False
                )
                
                if params:
                    embed.add_field(
                        name="Parameters",
                        value="\n".join(params),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Command not found",
                    value="Sorry, I couldn't find that command. Check the name and try again.",
                    inline=False
                )

        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url=bot.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @bot.event
    async def on_interaction(interaction: discord.Interaction):
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
                

if __name__ == "__main__":
    async def main():
        try:
            await loadCogs()
            await bot.start(TOKEN)
        except discord.LoginFailure:
            print("The token provided is not valid! Please check your token and try again.")
        except Exception as e:
            print(f"An error occurred: {e}")
            
    asyncio.run(main())
