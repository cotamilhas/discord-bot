
# Discord Bot

This is a Discord bot project developed to interact with Discord servers. The bot includes multiple features to enhance server functionality and user engagement.

## Features

- [x] **Custom Commands**: Define and use custom commands to tailor the bot to your server's needs.
- [x] **Moderation Tools**: Manage your server effectively with moderation features.
- [x] **Leveling System**: Allow users to gain experience and level up as they send messages.
- [x] **Logging System**: Track important server events with a comprehensive logging system.
- [x] **Fun Interactions**: Provide entertainment for server members with interactive commands.
- [x] **Music**: Play music in voice channels with commands to queue, skip, pause.


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
   - Go to `config.py` file in the root directory.
   - Add your bot token as follows:
     ```
     TOKEN="your-bot-token"
     ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Usage

- Customize commands and features in the bot's source code to meet your specific requirements.
- Start the bot and invite it to your Discord server.

## WARNING: Handling Large Numbers with Web Hosting Services
When working with large numbers, such as user IDs or message IDs, there can be issues with precision due to the way JavaScript and certain hosting environments handle large integers. Discord bots, when hosted on web services, might encounter problems with handling these large numbers, leading to incorrect or truncated data.

This problem occurs because many web hosting services and APIs may not properly support large integers, causing them to lose precision when they exceed the safe integer limit in JavaScript (2^53 - 1). This could result in values being displayed incorrectly, such as missing digits or incorrect formatting.

To avoid such issues, it's important to be aware of these limitations and implement proper handling for large numbers in your bot, especially when interacting with Discord's API or other services that require accurate, large numeric values.

## Contributing

Contributions are welcome! Feel free to fork this repository, create a new branch, and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
