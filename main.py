import discord
from discord.ext import commands
import os
import asyncio
from config import TOKEN, COMMAND_PREFIX, EMBED_COLOR
from datetime import datetime, timezone

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=COMMAND_PREFIX,
                   intents=intents, help_command=None)


async def loadCogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Cog loaded: {extension}")
            except Exception as e:
                print(f"Error loading {extension}: {e}")


@bot.command(help="Display the help menu.")
async def help(ctx, args=None):
    embed = discord.Embed(title=f"{bot.user.name}'s Help!", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
    commandCategories = {}

    for command in bot.commands:
        category = command.cog_name or "Uncategorized"
        if category not in commandCategories:
            commandCategories[category] = []
        commandCategories[category].append(command)

    if not args:
        for category, commands in commandCategories.items():
            embed.add_field(
                name=f"{category} Commands",
                value="\n".join([f"{i+1}. `{cmd.name}` - {cmd.help or 'No description provided.'}" for i, cmd in enumerate(commands)]),
                inline=False
            )
        embed.add_field(
            name="Details",
            value=f"Type `{COMMAND_PREFIX}help <command>` for more details about each command.",
            inline=False
        )

    elif args in [cmd.name for cmd in bot.commands]:
        command = bot.get_command(args)
        embed.add_field(
            name=f"Command: {args}",
            value=f"**Description**: {command.help or 'No description provided.'}\n\n**Usage**: `{COMMAND_PREFIX}{args} <arguments>`",
            inline=False
        )

    else:
        embed.add_field(
            name="Command not found",
            value="Sorry, I couldn't find that command. Please check the command name and try again.",
            inline=False
        )

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    embed.set_thumbnail(url=bot.user.avatar.url)

    await ctx.send(embed=embed)

if __name__ == "__main__":
    async def main():
        await loadCogs()
        await bot.start(TOKEN)
    asyncio.run(main())
