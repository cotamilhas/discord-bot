### AutoRole Cog

The **AutoRole** cog allows server administrators to automatically assign a role to new members when they join the server.  
The configuration is stored per server in a JSON file.

### Features
- Automatically assign a predefined role to new members.  
- Supports setting and clearing the automatic role.  
- Updates the server name in the configuration when it changes.  
- Logs detailed information in the console with colorized output.

### Commands
- **!autorole @Role** → Sets the specified role as the automatic role.  
- **!autorole clear** → Removes the automatic role configuration.  
- **!autorole** → Shows usage help if used incorrectly.  

### Events
- **on_member_join**: When a new member joins, the configured role is automatically assigned (if available).  
- **on_guild_update**: Keeps the stored server name in sync when the guild name changes.  

### Example
```
!autorole @Member
```
This will set the @Member role to be automatically assigned to all new members who join the server.

```
!autorole clear
```
This will remove the auto-role configuration for the server.

---

### Commands Cog

The **Commands** cog provides a set of basic utility slash commands for the bot.  
These commands are mostly for fun and quick access to user or server visuals.

### Features
- Measure the bot's latency.
- Display user avatars and banners.
- Display the server icon.

### Commands
- **/ping** → Responds with `Pong!` and the bot's latency in milliseconds.  
- **/avatar [user]** → Shows the avatar of the specified user, or your own if no user is provided.  
- **/banner [user]** → Shows the banner of the specified user, or your own if no user is provided.  
  - If the user has no banner, but has an accent color, the cog generates a banner image using that color.  
- **/servericon** → Displays the server's icon (only available in servers).  

#### Example
```
/ping

/avatar @User
```

---

### Events Cog

The **Events** cog manages the bot’s core events such as startup, presence, and member join/leave messages.  
It also generates custom welcome/farewell images using **PIL**.

### Features
- Prints detailed bot and server information when the bot is ready.  
- Syncs slash commands (`app_commands`) on startup.  
- Configures the bot’s presence (Playing, Streaming, Listening, Watching, or Online only).  
- Welcomes new members with a custom image (avatar + text).  
- Sends a farewell image when a member leaves.  
- Fallbacks gracefully if no system channel is available.  

### Events
- **on_ready** → Logs bot information, guilds, owners, and sets the bot’s presence.  
- **on_member_join** → Sends a custom welcome image to the system channel.  
- **on_member_remove** → Sends a custom farewell image to the system channel.  

### Image Generation
- Uses the member’s avatar cropped into a circle.  
- Applies a custom background (from `config.BACKGROUND_IMAGE`).  
- Draws text centered below the avatar (font defined by `config.FONT_PATH` and `config.FONT_SIZE`).  

### Example Output
When a user joins:  
- Channel message: an image with the user’s avatar and the text `username joined the server!`  

When a user leaves:  
- Channel message: an image with the user’s avatar and the text `username left the server!`  

---

### Fun Cog

The **Fun** cog provides lighthearted and entertaining commands for users, including dice rolls, coin flips, and avatar filters.

### Features
- Roll a six-sided die with a visual result.  
- Flip a coin and display heads or tails with images.  
- Apply filters to avatars (grayscale, invert, sepia, Portuguese overlay).  

### Commands
- **/roll** → Rolls a six-sided die and returns the result with an image.  
- **/flipcoin** → Flips a coin and displays either heads or tails with an image.  
- **/filter [filter_name] [user]** → Applies a filter to a user’s avatar.  
  - Available filters: **Grayscale**, **Invert**, **Sepia**, **Portuguese**.  
  - If no user is provided, defaults to the command invoker.  

#### Example
```
/roll
```

(Embed with dice image 5.png)

```
/filter Grayscale @User
```

Displays the target user’s avatar with a grayscale filter applied.

---

### Leveling Cog

The **Leveling** cog adds an XP and leveling system to the bot.  
Users earn XP by sending messages and can level up with activity.  
The cog also provides commands to check personal progress and view a server-wide leaderboard.

### Features
- Tracks XP and levels per member on a per-server basis.  
- Persistent data storage in a JSON file (`LEVELS_FILE`).  
- Cooldown system to prevent XP farming (5 seconds).  
- Automatic server name updates on guild changes.  
- Announces level ups in the current channel.  
- Provides personal progress and server leaderboard commands.  

### Events
- **on_message** → Grants random XP (5–15) for messages, checks for level ups, and announces them.  
- **on_guild_update** → Keeps the server name updated in the levels database.  

### Commands
- **/level [member]** → Displays the level, current XP, and XP needed for the next level of a user.  
- **/leaderboard** → Shows the top 10 members ranked by level and XP.  

### Leveling System
- Required XP increases by **50** each level after the base **100 XP**.  
- Formula: `required_xp = 100 + (level - 1) * 50`  
- Excess XP carries over after a level up.  

#### Leaderboard
- Top 3 users are displayed with medal icons (gold, silver, bronze).  
- Remaining users are listed with numeric positions.  
- Displayed in a styled embed.  

#### Example
```
/level @User

/leaderboard
```

@User is at level **3** with **120 XP**.
Needs **30 XP** more to level up!

🥇 User1 - Level: 10 | XP: 220

🥈 User2 - Level: 9 | XP: 175

🥉 User3 - Level: 8 | XP: 95

▫️ 4. User4 - Level: 7 | XP: 80

---

### ServerLogs Cog

The **ServerLogs** cog provides advanced logging for your Discord bot, covering nearly every type of server event. It is designed to help moderators and administrators keep track of changes, actions, and events within their server.

### Features

- **Message Logging**
  - Deleted messages (content, attachments, embeds, stickers)
  - Edited messages (before and after)
  - Bulk message deletions

- **Voice State Logging**
  - Join, leave, or switch voice channels
  - Mute and deafen state changes (with audit log tracking of who applied them)

- **Member Logging**
  - Member join and leave
  - Member kick, ban, and unban (with moderator and reason when available)
  - Nickname, avatar, role, and timeout updates

- **Server Logging**
  - Server name, description, owner, AFK channel/timeout, icon, and banner updates
  - Emoji and sticker changes

- **Role Logging**
  - Role creation, deletion, and updates (name, color, permissions, etc.)

- **Channel Logging**
  - Channel creation, deletion, and updates (name, topic, NSFW, position, bitrate, etc.)
  - Channel pin updates

- **Invite Logging**
  - Invite creation and deletion

- **Thread Logging**
  - Thread creation, deletion, updates, and member joins/leaves

- **Integration Logging**
  - Integration creation, update, and deletion

- **Webhook Logging**
  - Webhook updates in channels

#### Commands

Set or clear the log channel for this server. Requires administrator permissions.

- `!logchannel`  
  Sets the current channel as the log channel.

- `!logchannel clear`  
  Clears the log channel configuration for the server.

#### Configuration

The cog stores server-specific configurations (log channel and server name) in a JSON file defined by `SERVER_OPTIONS`.  

Example entry:
```json
{
  "123456789012345678": {
    "server_name": "My Discord Server",
    "log_channel": 987654321098765432
  }
}
```

---

### Moderation Cog

The **Moderation** cog provides commands for server moderation including banning, kicking, timing out, unbanning, and removing timeouts from users.

### Features

- **Ban Users**
  - Command: `/ban`
  - Bans a user with optional reason.
  - Prevents banning yourself or the bot.
  - Requires `Ban Members` permission.

- **Kick Users**
  - Command: `/kick`
  - Kicks a user with optional reason.
  - Prevents kicking yourself or the bot.
  - Requires `Kick Members` permission.

- **Timeout Users**
  - Command: `/timeout`
  - Temporarily timeout a user for a duration in seconds, minutes, hours, or days.
  - Optional reason.
  - Requires `Moderate Members` permission.

- **Unban Users**
  - Command: `/unban`
  - Displays a paginated list of banned users with a select menu to unban.
  - Requires `Ban Members` permission.

- **Remove Timeout**
  - Command: `/untimeout`
  - Removes the timeout from a member.
  - Requires `Moderate Members` permission.

## Components

### `UnbanView`
- Custom Discord UI View with:
  - Pagination buttons (⬅️ / ➡️)
  - Select menu to pick a user to unban
- Handles unban logic and errors (NotFound, Forbidden, etc.)

### Pagination
- Displays bans in pages of 10 users per page.
- Footer shows current page number.

---

### Music Cog

The **Music** cog provides music playback functionalities using YouTube and optionally Spotify. It supports queues, now playing info, and interactive queue navigation.

### Features

- **Play Music**
  - Command: `!play <query>`
  - Plays music from YouTube or Spotify.
  - Automatically adds multiple tracks for Spotify playlists/albums.
  - Requires the user to be in a voice channel.

- **Skip Music**
  - Command: `!skip`
  - Skips the currently playing song.

- **Stop/Disconnect**
  - Command: `!stop`
  - Stops the music, clears the queue, and disconnects from the voice channel.

- **Pause / Resume**
  - Commands: `!pause`, `!resume`
  - Pauses or resumes the currently playing track.

- **Queue**
  - Command: `!queue`
  - Shows a paginated view of the current queue.
  - Supports interactive buttons: **Back** and **Next**.

- **Now Playing**
  - Command: `!nowplaying`
  - Shows the currently playing track.

- **Help**
  - Command: `!help`
  - Lists all available music commands.

## Components

### `QueueView`
- A custom Discord UI view with:
  - Pagination buttons (Back / Next)
  - Displays songs in pages of 10
  - Footer shows current page / total pages

### `PreviousButton` / `NextButton`
- Handles pagination of the queue in the UI.

### Spotify Integration
- Uses `spotipy` with client credentials.
- Supports track, playlist, album, and artist URLs.
- Converts Spotify tracks to YouTube links automatically.

### YouTube Search
- Uses `yt_dlp` to search or play YouTube videos directly.
- Supports URL or search query.
- Handles cookies if provided in configuration.

### Error Handling
- Gracefully handles:
  - No voice channel
  - No results
  - Playback errors
  - Spotify API issues

### Debug Mode
- Prints debug info if `DEBUG_MODE` is enabled in config.

---

### Stream Alerts Cog

The **StreamAlerts** cog provides automated notifications for **YouTube** and **Twitch** channels in Discord servers.

### Features

- **YouTube Alerts**
  - Tracks channel uploads via RSS feeds.
  - Sends notifications to a configured Discord channel.
  - Shows video title, channel name, thumbnail, and link.
  - Runs every 5 minutes.

- **Twitch Alerts**
  - Tracks live status, stream title, game, viewers, and avatar.
  - Sends notifications when a streamer goes live.
  - Runs every 3 minutes.
  - Uses DecAPI for lightweight API queries.

- **Persistent Storage**
  - Alerts are saved in a JSON file defined by `ALERTS_FILE`.
  - Tracks last seen YouTube videos and Twitch online status.

- **Commands (App Commands / Slash)**
  - `/alerts channel [channel]` → Set the Discord channel for alerts.
  - `/alerts youtube add/remove <channel_id>` → Add or remove YouTube channels to watch.
  - `/alerts twitch add/remove <channel_name>` → Add or remove Twitch channels to watch.
  - `/alerts list` → List all configured alerts for the server.

- **Error Handling & Robustness**
  - Handles connection errors, timeouts, rate limits, and XML parsing issues.
  - Implements retries with exponential backoff.
  - Automatically restarts tasks on critical failures.

- **Session Management**
  - Reuses a single `aiohttp` session for all requests.
  - Automatically recreates session if closed.

---

### Ticket Cog

The **Ticket** cog provides a complete support ticket system for your Discord server. It allows members to create private channels for support requests, while administrators and staff can manage, close, and log tickets efficiently.

### Features
- Configurable ticket panel set up by administrators.  
- Users can open private ticket channels with one click.  
- Prevents duplicate tickets per user.  
- Option to close tickets instantly or provide a reason.  
- Automatic deletion of ticket channels after closure.  
- Persistent tickets restored after bot restart.  
- Logging of ticket actions (created, closed, reason) to a specified channel.  

### Commands
- **!ticket** → Sets up the ticket panel in the current channel. (Admin only)  

### Ticket Workflow
1. Administrator runs `!ticket` in a designated support channel.  
2. The bot posts a **Ticket System** embed with an **Open Ticket** button.  
3. When a user clicks, a private channel is created (`ticket-username`).  
4. Inside the ticket, the user can:  
   - Click **Close Ticket** → closes and deletes the ticket in 10 seconds.  
   - Click **Close with Reason** → prompts for a reason before closing.  
5. All actions are logged in the configured log channel.  

### Logging
- Logs are stored in the log channel configured in `server_options.json`.  
- Color-coded embeds for actions:  
  - Blue → Ticket created  
  - Orange → Ticket closed  
  - Red → Ticket closed with reason    

### Example
```
!ticket
```

Bot posts in the ticket

```
Support Ticket
Hello @Member! Support will be with you shortly.
Click the button below to close this ticket.
```

and the it will be saved in `serveroptions.json` until it's closed

```
{
  "123456789012345678": {
    "server_name": "My Discord Server",
    "ticket_panel": 987654321098765432,
    "open_tickets": [112233445566778899],
    "log_channel": 223344556677889900
  }
}
```
















