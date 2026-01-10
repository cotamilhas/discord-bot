# 🤖 Discord Bot

This is a Discord bot project developed to interact with Discord servers. The bot includes multiple features to enhance server functionality and user engagement.

> **All of these cogs are optional!**  
> You can remove them if you want — their purpose is just to give examples of what you can do.

---

## ✨ Features

- ✅ **Custom Commands** – Define and use custom commands to tailor the bot to your server's needs.
- ✅ **Moderation Tools** – Manage your server effectively with moderation features.
- ✅ **Leveling System** – Allow users to gain experience and level up as they send messages.
- ✅ **Logging System** – Track important server events with a comprehensive logging system.
- ✅ **Fun Interactions** – Provide entertainment for server members with interactive commands.
- ✅ **Music** – Play music in voice channels with commands to queue, skip, and pause.
- ✅ **Alerts System** – Get notified about Twitch/YouTube streams.
- ✅ **Ticket System** – Create private support channels for members with one click.

---

## 📦 Requirements

- **Python 3.13 or higher**  
- **`discord.py` library**  
- Any additional dependencies listed in `requirements.txt`

---

## 🚀 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/cotamilhas/discord-bot.git
cd discord-bot
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure the bot token

The project uses `config.py` in the repository root.

**Basic setup:**
```py
TOKEN = "your-bot-token"
```

**Recommended (environment variable):**
```py
import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "your-fallback-token-if-any")
```

Run the bot with:
```bash
export DISCORD_BOT_TOKEN="your-bot-token"
python main.py
```

> If you prefer `.env`, you can use **python-dotenv** to load it inside `config.py`.

### 4️⃣ Run the bot
```bash
python main.py
```

---

## 🛠️ Usage

- Customize commands and features in the bot’s source code to meet your specific requirements.  
- Start the bot and invite it to your Discord server.

---

<details>
<summary>🧩 Multi-Bot Support (click to expand)</summary>

This project supports running **multiple Discord bots (or sub-bots)** in parallel.

Each sub-bot should be placed in its own folder inside the `bots` directory, with a separate `main.py` file.

### How to add a sub-bot

1. Create a new folder inside the `bots` directory (e.g. `bots/other_bot`)  
2. Add your sub-bot’s code, including a `main.py` entry point  
3. Each sub-bot can have its own configuration, features, and cogs

> **Note:** Each sub-bot has its own set of cogs, which are not shared with the main bot or other sub-bots.  
> This allows each bot to have completely independent functionality.

When you start the main bot:
```bash
python main.py
```

All sub-bots inside the `bots` directory that contain a `main.py` file will be launched automatically.

### Example project structure
```text
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
</details>

<details>
<summary>⚠️ Handling Large Numbers with Web Hosting Services (click to expand)</summary>

When working with large numbers, such as Discord user IDs or message IDs, there can be precision issues due to how some environments (notably JavaScript and certain hosting services) handle large integers.

In JavaScript, numbers are represented as **IEEE-754 doubles**, and integers above the safe integer limit (`2^53 - 1`) can lose precision.

Discord IDs are large integers and should often be treated as **strings** when you need to serialize, store, or transmit them to services that might use JavaScript or other languages with limited integer precision.

### Recommendations

- Store IDs as **strings** in JSON, databases, or configuration files  
- Pass IDs as strings when interfacing with JavaScript services or hosting platforms  
- Convert IDs to `int` only in Python or environments that safely support large integers  
- In browser or Node.js environments, keep IDs as strings or use BigInt-compatible libraries

Being aware of these limitations helps avoid subtle bugs such as:  
- Incorrect user or message references  
- Failed lookups  
- Mismatched logs across systems
</details>

---

## 🤝 Contributing

Contributions are welcome!  
Feel free to fork this repository, create a new branch, and submit a pull request.

---

## 📄 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for more details.
