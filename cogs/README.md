# Cogs Overview

This directory contains modular features ("cogs") for the Discord bot. Each cog adds specific functionality to your server, ranging from moderation and logging to music playback and fun commands.

All cogs are optional and modular — enable or remove them as needed. Each cog may require its own configuration file or credentials (see each cog's docstring or code for details).

## Requirements & Notes

- The project uses Python (see the repository root README for the required Python version).
- Common Python libraries used by cogs include: discord.py, Pillow (PIL), and any extras for specific cogs (e.g., youtube handling libraries, spotipy). See `requirements.txt` for the full list.
- For music playback, FFMPEG is required on the host system. Install from https://ffmpeg.org/ or via your package manager (e.g., `sudo apt install ffmpeg`).
- Treat Discord IDs as strings when persisting data or sending them to services that may use JavaScript (to avoid integer precision issues).
- Configuration is usually stored per-server. Back up JSON or DB files before large changes.

---

## AutoRole Cog

Automatically assigns a predefined role to new members when they join. Configuration is stored per server.

Features
- Automatically assign a role to new members
- Set and clear the automatic role
- Updates stored server name on change
- Console logging

Commands
- `!autorole @Role` — Set the role to assign
- `!autorole clear` — Remove auto-role configuration

Events
- Assign role on member join
- Update stored server name on guild update

Configuration
- The cog stores role IDs and guild IDs in the bot's persistent storage (JSON/DB). Use role mentions in commands to configure.

---

## Commands Cog

Provides basic utility slash commands for quick access to user or server visuals.

Features
- Measure bot latency
- Display user avatars and banners
- Display server icon

Commands
- `/ping` — Shows latency
- `/avatar [user]` — Shows avatar
- `/banner [user]` — Shows banner or generates one from accent color
- `/servericon` — Shows server icon

Notes
- Avatar/banner commands may fetch user profile assets — respect rate limits and permissions.

---

## Events Cog

Manages core bot events like startup, presence, member join/leave messages, and generates custom welcome/farewell images using Pillow (PIL).

Features
- Prints bot/server info on ready
- Syncs slash commands
- Sets bot presence
- Custom welcome/farewell images
- Handles missing system channel

Events
- Logs info on ready
- Sends welcome/farewell images

Image Generation
- User avatar in a circle
- Custom background and text

Configuration
- Ensure the bot has permissions to send images and access member avatars.

---

## Fun Cog

Offers entertaining commands such as dice rolls, coin flips, and avatar filters.

Features
- Roll a die with visual result
- Flip a coin and display result
- Apply filters (grayscale, invert, sepia, Portuguese overlay) to avatars

Commands
- `/roll` — Rolls a die
- `/flipcoin` — Flips a coin
- `/filter [filter_name] [user]` — Applies a filter to an avatar

Notes
- Image filters use Pillow; large images may take longer to process.

---

## Leveling Cog

Implements an XP and leveling system where users level up by sending messages. Includes commands for progress and leaderboards.

Features
- Track XP and levels per member/server
- Persistent JSON storage
- Cooldown to prevent XP farming
- Server name sync
- Announces level ups
- Progress and leaderboard commands

Commands
- `/level [member]` — Show level and XP
- `/leaderboard` — Show top members

Leveling System
- XP needed increases by 50 per level from a 100 XP base (configurable in code)
- Excess XP carries over after level up

Storage
- Level data is stored persistently (JSON by default). Consider migrating to a database for larger servers.

---

## ServerLogs Cog

Provides advanced logging for nearly all server events, helping moderators and admins keep track of activities.

Features
- Logs message edits/deletions
- Logs voice state changes
- Logs member joins/leaves, bans, kicks, and updates
- Logs server, role, channel, invite, thread, integration, and webhook changes

Commands
- `!logchannel` — Set log channel
- `!logchannel clear` — Remove log channel configuration

Configuration
- Stores server-specific log channels and info in JSON. Make sure the bot has permissions to view audit logs and post in the configured channel.

---

## Moderation Cog

Adds moderation commands for banning, kicking, timing out, unbanning, and removing timeouts.

Features
- Ban, kick, timeout, unban, remove timeout
- Prevents self/bot moderation
- Permission checks

Commands
- `/ban`, `/kick`, `/timeout`, `/unban`, `/untimeout`

Components
- Custom UI for unban with pagination and select menus

Permissions
- Moderation commands check for required roles/permissions before executing.

---

## Music Cog

Enables music playback via YouTube and Spotify, with support for queues and interactive navigation.

Note: If you're on Windows, this cog may have issues. A Linux host is recommended until the problem is diagnosed. Also ensure [FFMPEG](https://ffmpeg.org/) is installed.

Features
- Play from YouTube/Spotify
- Queue, skip, stop, pause, resume, now playing
- Interactive queue navigation
- Help command
- Error handling and debug mode

Commands
- `!play`, `!skip`, `!stop`, `!pause`, `!resume`, `!queue`, `!nowplaying`, `!help`

Dependencies
- Requires FFMPEG and usually an external downloader/player library (e.g., yt-dlp). Check the cog source for exact dependencies.

---

## Stream Alerts Cog

Automates notifications for YouTube uploads and Twitch streams.

Features
- YouTube RSS feed tracking
- Twitch live status tracking
- Configurable alert channel
- Persistent storage
- Robust error handling
- Session management

Commands
- `/alerts channel` — Set alert channel
- `/alerts youtube add/remove` — Manage YouTube alerts
- `/alerts twitch add/remove` — Manage Twitch alerts
- `/alerts list` — List configured alerts

Notes
- For frequent polling, ensure the host handles rate limits and has reliable uptime.

---

## Ticket Cog

Implements a support ticket system with private channels for user requests and staff management.

Features
- Configurable ticket panel
- One-click private ticket creation
- Duplicate ticket prevention
- Ticket closure with reason
- Persistent tickets
- Logging of ticket actions

Commands
- `!ticket` — Set up ticket panel (Admin only)

Workflow
- Admin sets up panel
- User opens ticket via button
- Staff can close ticket or add reason
- Actions are logged

---

## Enabling / Disabling Cogs

- Cogs live in the `cogs/` directory and are loaded by the bot's startup routine.
- To disable a cog, remove or comment out its load call in `main.py` (or move it out of the `cogs/` directory), or use dynamic load/unload commands if implemented.
