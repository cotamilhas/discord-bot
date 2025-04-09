import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from datetime import datetime, timezone
from colorama import Fore, Style
from config import TOKEN, EMBED_COLOR, intents
from flask import Flask, jsonify, render_template, request
from threading import Thread
import time

# Flask app setup
app = Flask(__name__)

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Load cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Cog loaded: {extension}")
            except Exception as e:
                print(f"Error loading {extension}: {e}")

# Help command
@bot.tree.command(name="help", description="Displays the help menu.")
@app_commands.describe(command="The command you want to get help with.")
async def help(interaction: discord.Interaction, command: str = None):
    embed = discord.Embed(
        title=f"Help for {bot.user.name}!",
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    command_categories = {}

    for cog_name, cog in bot.cogs.items():
        commands = cog.get_app_commands()
        if commands:
            command_categories[cog_name] = commands

    if not command:
        for category, commands in command_categories.items():
            embed.add_field(
                name=f"{category}",
                value="\n".join([f"/{cmd.name} - {cmd.description}" for cmd in commands]),
                inline=False
            )
        embed.add_field(
            name="Details",
            value="Type /help <command> for more details about a specific command.",
            inline=False
        )
    else:
        cmd = bot.tree.get_command(command)
        if cmd:
            embed.add_field(
                name=f"Command: /{cmd.name}",
                value=f"**Description**: {cmd.description}\n\n**Usage**: /{cmd.name}",
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

@help.error
async def help_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    error_message = f"An error occurred: {error}"
    print(f"{Fore.GREEN}[ERROR]{Style.RESET_ALL} {error}")

    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(error_message, ephemeral=True)
        else:
            await interaction.followup.send_message(error_message, ephemeral=True)
    except Exception as e:
        print(f"[ERROR] Failed to send error message: {e}")

# Flask routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/servers")
def get_servers():
    servers = [
        {
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count
        }
        for guild in bot.guilds
    ]
    return jsonify(servers)

@app.route("/channels/<guild_id>")
def get_channels(guild_id):
    guild = discord.utils.get(bot.guilds, id=int(guild_id))
    if not guild:
        return jsonify({"error": "Server not found."}), 404

    channels = [
        {"id": str(channel.id), "name": channel.name}
        for channel in guild.channels
        if channel.type in [discord.ChannelType.text, discord.ChannelType.voice]
    ]
    return jsonify(channels)

@app.route("/send/<channel_id>", methods=["POST"])
def send_message(channel_id):
    data = request.get_json()
    message = data.get("message")
    if not message:
        return jsonify({"error": "Message not provided"}), 400

    channel = bot.get_channel(int(channel_id))
    if channel:
        bot.loop.create_task(channel.send(message))
        return jsonify({"success": f"Message sent to {channel.name}"}), 200
    return jsonify({"error": "Channel not found"}), 404

# Main entry point
if __name__ == "__main__":
    async def start_bot():
        # Load all cogs and start the bot
        await load_cogs()
        await bot.start(TOKEN)

    def run_flask():
        # Start the Flask app
        app.run(debug=True, use_reloader=False)

    # Run Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start the bot
    time.sleep(3)
    asyncio.run(start_bot())
    
