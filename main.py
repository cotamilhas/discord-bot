import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from config import TOKEN, EMBED_COLOR
from datetime import datetime, timezone

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def loadCogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Cog loaded: {extension}")
            except Exception as e:
                print(f"Error loading {extension}: {e}")

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
            embed.add_field(
                name=f"Command: /{cmd.name}",
                value=f"**Description**: {cmd.description}\n\n**Usage**: `/{cmd.name}`",
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
    

if __name__ == "__main__":
    async def main():
        await loadCogs()
        await bot.start(TOKEN)
    asyncio.run(main())
