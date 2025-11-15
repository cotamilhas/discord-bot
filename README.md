# Discord Bot

This is a Discord bot project developed to interact with Discord servers. The bot includes multiple features to enhance server functionality and user engagement. 

**All of these cogs are optional!** You can remove them if you want — their purpose is just to give examples of what you can do.

## Features

- [x] **Custom Commands**: Define and use custom commands to tailor the bot to your server's needs.
- [x] **Moderation Tools**: Manage your server effectively with moderation features.
- [x] **Leveling System**: Allow users to gain experience and level up as they send messages.
- [x] **Logging System**: Track important server events with a comprehensive logging system.
- [x] **Fun Interactions**: Provide entertainment for server members with interactive commands.
- [x] **Music**: Play music in voice channels with commands to queue, skip, and pause.
- [x] **Alerts System**: Get notified about Twitch/YouTube streams.
- [x] **Ticket System**: Create private support channels for members with one click.

## Requirements

- Python 3.13 or higher
- `discord.py` library
- Any additional dependencies listed in the `requirements.txt` file

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/cotamilhas/discord-bot.git
   cd discord-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your bot token:
   - The project uses `config.py` in the repository root. You can add your bot token directly there:
     ```py
     TOKEN = "your-bot-token"
     ```
   - For better security, it's strongly recommended to use an environment variable or a `.env` file. Example using an environment variable in `config.py`:
     ```py
     import os
     TOKEN = os.getenv("DISCORD_BOT_TOKEN", "your-fallback-token-if-any")
     ```
     Then run the bot with the environment variable set:
     ```bash
     export DISCORD_BOT_TOKEN="your-bot-token"
     python main.py
     ```
   - If you prefer `.env`, use python-dotenv to load it in `config.py`.

4. Run the bot:
   ```bash
   python main.py
   ```

## Usage

- Customize commands and features in the bot's source code to meet your specific requirements.
- Start the bot and invite it to your Discord server.

## Multi-Bot Support

This project supports running multiple Discord bots (or sub-bots) in parallel. Each sub-bot should be placed in its own folder inside the `bots` directory, with a separate `main.py` file for each bot.

**How to add a sub-bot:**
1. Create a new folder inside the `bots` directory (e.g., `bots/other_bot`).
2. Add your sub-bot’s code, including a `main.py` entry point.
3. Each sub-bot can have its own configuration, features, and cogs.

> **Note:** Each sub-bot has its own set of cogs, which are not shared with the main bot or other sub-bots. This allows each bot to have completely independent functionality.

When you start the main bot (`python main.py`), all sub-bots in the `bots` directory with a `main.py` will be launched automatically.

This allows you to manage multiple bots from a single project, each with different tokens, functionalities, and cogs.

**Example structure:**
```
discord-bot/
├── bots/
│   ├── bot1/
│   │   ├── main.py
│   │   └── cogs/
│   └── bot2/
│       ├── main.py
│       └── cogs/
├── cogs/
├── main.py
└── config.py
```

## WARNING: Handling Large Numbers with Web Hosting Services

When working with large numbers, such as Discord user IDs or message IDs, there can be precision issues due to how some environments (notably JavaScript and certain hosting services) handle large integers. In JavaScript, numbers are represented as IEEE-754 doubles and integers above the safe integer limit (2^53 - 1) can lose precision.

Discord IDs are large integers and should often be treated as strings when you need to serialize, store, or transmit them to services that might use JavaScript or other languages with limited integer precision.

Recommendations:
- Store IDs as strings in JSON, databases, or configuration files to avoid precision loss.
- When interfacing with JavaScript services or hosting platforms, pass IDs as strings and only convert to integers where the language/runtime safely supports it.
- In Python (where large integers are handled safely), you can convert ID strings to int when needed, but be cautious when sending those values to external services that may not preserve precision.
- If you parse or manipulate IDs in client-side code (browser or Node), keep them as strings and use libraries that support big integers if numerical operations are required.

Being aware of these limitations helps avoid subtle bugs like incorrect user or message references, failed lookups, or mismatched logs when using cross-language integrations.

## Contributing

Contributions are welcome! Feel free to fork this repository, create a new branch, and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

Tell me if you'd like any other specific edits (add badges, change Python version, add examples, or push the change to the repo/PR).
