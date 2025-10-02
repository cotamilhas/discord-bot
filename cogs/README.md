# Cogs Overview

This directory contains modular features ("cogs") for the Discord bot. Each cog adds specific functionality to your server, ranging from moderation and logging to music playback and fun commands.

## AutoRole Cog

Automatically assigns a predefined role to new members when they join. Configuration is stored per server.

**Features**
- Automatically assign a role to new members
- Set and clear the automatic role
- Updates stored server name on change
- Console logging

**Commands**
- `!autorole @Role` — Set the role to assign
- `!autorole clear` — Remove auto-role configuration

**Events**
- Assign role on member join
- Update stored server name on guild update

---

## Commands Cog

Provides basic utility slash commands for fun and quick access to user or server visuals.

**Features**
- Measure bot latency
- Display user avatars and banners
- Display server icon

**Commands**
- `/ping` — Shows latency
- `/avatar [user]` — Shows avatar
- `/banner [user]` — Shows banner or generates one from accent color
- `/servericon` — Shows server icon

---

## Events Cog

Manages core bot events like startup, presence, member join/leave messages, and generates custom welcome/farewell images using PIL.

**Features**
- Prints bot/server info on ready
- Syncs slash commands
- Sets bot presence
- Custom welcome/farewell images
- Handles missing system channel

**Events**
- Logs info on ready
- Sends welcome/farewell images

**Image Generation**
- User avatar in a circle
- Custom background and text

---

## Fun Cog

Offers entertaining commands such as dice rolls, coin flips, and avatar filters.

**Features**
- Roll a die with visual result
- Flip a coin and display result
- Apply filters (grayscale, invert, sepia, Portuguese overlay) to avatars

**Commands**
- `/roll` — Rolls a die
- `/flipcoin` — Flips a coin
- `/filter [filter_name] [user]` — Applies a filter to an avatar

---

## Leveling Cog

Implements an XP and leveling system where users level up by sending messages. Includes commands for progress and leaderboards.

**Features**
- Track XP and levels per member/server
- Persistent JSON storage
- Cooldown to prevent XP farming
- Server name sync
- Announces level ups
- Progress and leaderboard commands

**Commands**
- `/level [member]` — Show level and XP
- `/leaderboard` — Show top members

**Leveling System**
- XP needed increases by 50 per level from 100 XP base
- Excess XP carries over after level up

---

## ServerLogs Cog

Provides advanced logging for nearly all server events, helping moderators and admins keep track of activities.

**Features**
- Logs message edits/deletions
- Logs voice state changes
- Logs member joins/leaves, bans, kicks, and updates
- Logs server, role, channel, invite, thread, integration, and webhook changes

**Commands**
- `!logchannel` — Set log channel
- `!logchannel clear` — Remove log channel configuration

**Configuration**
- Stores server-specific log channels and info in JSON

---

## Moderation Cog

Adds moderation commands for banning, kicking, timing out, unbanning, and removing timeouts.

**Features**
- Ban, kick, timeout, unban, remove timeout
- Prevents self/bot moderation
- Permission checks

**Commands**
- `/ban`, `/kick`, `/timeout`, `/unban`, `/untimeout`

**Components**
- Custom UI for unban with pagination and select menus

---

## Music Cog

Enables music playback via YouTube and Spotify, with support for queues and interactive navigation.

**Features**
- Play from YouTube/Spotify
- Queue, skip, stop, pause, resume, now playing
- Interactive queue navigation
- Help command
- Error handling and debug mode

**Commands**
- `!play`, `!skip`, `!stop`, `!pause`, `!resume`, `!queue`, `!nowplaying`, `!help`

---

## Stream Alerts Cog

Automates notifications for YouTube uploads and Twitch streams.

**Features**
- YouTube RSS feed tracking
- Twitch live status tracking
- Configurable alert channel
- Persistent storage
- Robust error handling
- Session management

**Commands**
- `/alerts channel`, `/alerts youtube add/remove`, `/alerts twitch add/remove`, `/alerts list`

---

## Ticket Cog

Implements a support ticket system with private channels for user requests and staff management.

**Features**
- Configurable ticket panel
- One-click private ticket creation
- Duplicate ticket prevention
- Ticket closure with reason
- Persistent tickets
- Logging of ticket actions

**Commands**
- `!ticket` — Set up ticket panel (Admin only)

**Workflow**
- Admin sets up panel
- User opens ticket via button
- Staff can close ticket or add reason
- Actions are logged

---

**Note:** All cogs are designed to be modular and may require specific configuration files for data persistence and customization.

If you need more details for a particular cog, let me know!