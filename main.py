import os
import json
import logging
from pathlib import Path

from discord import Intents
from discord.ext import commands

try:
    # Load .env if present
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # Optional dependency; continue if not installed
    pass


def _read_token_from_config() -> str | None:
    """Read bot token from config.json if available."""
    cfg_path = Path("config.json")
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        token = data.get("token")
        if isinstance(token, str) and token.strip():
            return token.strip()
    except Exception as e:
        logging.exception("Failed to read config.json: %s", e)
    return None


def create_bot() -> commands.Bot:
    intents = Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True

    # Use a fixed "!" prefix and ensure the default help command is enabled
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=commands.DefaultHelpCommand())

    @bot.event
    async def on_ready():
        logging.info(f"Logged in as {bot.user} (ID: {bot.user and bot.user.id})")
        # Ensure app commands are synced (slash commands)
        try:
            synced = await bot.tree.sync()
            logging.info(f"Synced {len(synced)} application commands")
        except Exception as e:
            logging.exception("Failed to sync application commands: %s", e)

    return bot


def load_cogs(bot: commands.Bot) -> None:
    # Explicitly list cogs to keep things simple and explicit
    extensions = [
        "cogs.util",
        "cogs.moderation",
        "cogs.tickets",
        "cogs.fun",
        "cogs.textpack",
        "cogs.megapack",
        "cogs.polls",
        "cogs.welcome",
        "cogs.logs",
        "cogs.afk",
        "cogs.tags",
        "cogs.starboard",
        "cogs.reminders",
        "cogs.islamic",
    ]
    for ext in extensions:
        try:
            bot.load_extension(ext)
            logging.info("Loaded extension %s", ext)
        except Exception as e:
            logging.exception("Failed to load extension %s: %s", ext, e)


def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    token = _read_token_from_config() or os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Bot token not set. Provide it in config.json as {\"token\": \"YOUR_TOKEN\"} "
            "or set DISCORD_TOKEN in your environment or .env file."
        )

    bot = create_bot()
    load_cogs(bot)

    bot.run(token)


if __name__ == "__main__":
    main()
