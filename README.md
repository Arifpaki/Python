# Discord Bot with Tickets and Useful Commands

This project provides a Discord bot written in Python using discord.py. It includes:
- Ticket system (create, close, add/remove users, rename)
- Useful utility commands (ping, uptime, userinfo, serverinfo, say)
- Basic moderation commands (purge, kick, ban, unban)
- Fun commands (dice, 8ball, choose, text utilities)
- Islamic reminders: customizable Jumu'ah reminder and daily Qur'an ayah + hadith (via public APIs)
- MegaPack of ~300 safe/“halal” slash commands grouped under `/pack`

## Features

- Hybrid commands: use as slash commands or with a prefix (default `!`)
- Ticket channels created under a private "Tickets" category
- 300 safe text-transform slash commands under `/pack` grouped by categories
- Customizable Islamic reminders (channel, timezone, times, headers)
- Configurable via environment variables

## Setup

1) Create a Discord application and bot:
- https://discord.com/developers/applications
- Create Application → Bot → Copy Token
- Enable Privileged Gateway Intents: PRESENCE INTENT (optional), SERVER MEMBERS INTENT, MESSAGE CONTENT INTENT

2) Clone and set environment variables:
- Create a `.env` file in the project root (optional) or export variables in your shell:

```
DISCORD_TOKEN=your-bot-token-here
COMMAND_PREFIX=!
TICKET_CATEGORY_NAME=Tickets
SUPPORT_ROLE_NAME=Support
TICKET_CHANNEL_PREFIX=ticket
LOG_LEVEL=INFO
```

3) Install dependencies:
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

4) Run the bot:
```
python main.py
```

5) Invite the bot to your server:
- In the Developer Portal → OAuth2 → URL Generator:
  - Scopes: `bot`, `applications.commands`
  - Bot Permissions: Administrator (or select granular permissions: Manage Channels, Send Messages, Manage Messages, Kick/Ban, etc.)
- Open the generated URL to invite the bot.

## Commands Overview

- Utility:
  - `/ping`, `/uptime`, `/userinfo [member]`, `/serverinfo`, `/say <message>`
- Moderation:
  - `/purge [amount]`, `/kick <member> [reason]`, `/ban <member> [reason]`, `/unban <user>`
- Tickets (use in any channel):
  - `/ticket open [subject]` – creates a private ticket channel for you (and the Support role)
  - `/ticket close [reason]` – closes (deletes) the ticket channel (run inside the ticket)
  - `/ticket add <member>` – add a member to the current ticket channel
  - `/ticket remove <member>` – remove a member from the current ticket channel
  - `/ticket rename <name>` – rename the ticket channel
- Fun:
  - `/roll`, `/coinflip`, `/choose`, `/eightball`, `/randint`, `/randchoice`, `/password`, `/upper`, `/lower`, `/titlecase`, `/reverse`, `/clap`, `/space`, `/add`, `/sub`, `/mul`, `/div`
- Islamic reminders (slash; manage_guild required to configure):
  - `/islam status` — view current settings
  - `/islam set_channel [#channel]` — where reminders are sent
  - `/islam set_timezone <IANA tz>` — e.g., Asia/Riyadh, Europe/London
  - `/islam set_daily_time <HH:MM>` — daily reminder time (24h)
  - `/islam set_jumuah_time <HH:MM>` — Friday reminder time (24h)
  - `/islam toggle_daily <true|false>` — enable/disable daily reminders
  - `/islam toggle_jumuah <true|false>` — enable/disable Friday reminders
  - `/islam set_daily_header <text>` — set daily message header
  - `/islam set_jumuah_header <text>` — set Jumu'ah message header
  - `/islam send_now <daily|jumuah>` — test-send now
- MegaPack (~300 slash commands, safe):
  - Group root: `/pack`
  - Categories under `/pack`: `base`, `two1`.., `three1`..
  - Example:
    - `/pack base rot13 text:Hello`
    - `/pack two1 rot13_leet text:Hello`
    - `/pack three1 snake_kebab_lower text:Hello World`

Notes:
- If your server has a role named `Support`, members with that role can see and respond to tickets by default. You can change the role name with `SUPPORT_ROLE_NAME`.
- Slash command sync for hundreds of commands can take up to a minute after first run or updates.

## Project Structure

```
.
├── cogs/
│   ├── __init__.py
│   ├── afk.py
│   ├── fun.py
│   ├── islamic.py
│   ├── logs.py
│   ├── megapack.py
│   ├── moderation.py
│   ├── polls.py
│   ├── reminders.py
│   ├── starboard.py
│   ├── tags.py
│   ├── textpack.py
│   ├── tickets.py
│   └── welcome.py
├── main.py
├── requirements.txt
└── tests/
```

## Testing

Basic tests are included as a placeholder in `tests/`. Add more tests as you expand the bot.

## Contributing

- Open issues or PRs for enhancements: transcripts, persistence to a database, panel messages with buttons, etc.
- Keep code minimal and clear; follow discord.py best practices.
