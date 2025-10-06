import os
import logging

from discord import Intents
from discord.ext import commands

try:
    # Load .env if present
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # Optional dependency; continue if not installed
    pass


def create_bot() -> commands.Bot:
    intents = Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True

    bot = commands.Bot(command_prefix=os.getenv("COMMAND_PREFIX", "!"), intents=intents)

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
    ]
    for ext in extensions:
        try:
            bot.load_extension(ext)
            logging.info("Loaded extension %s", ext)
        except Exception as e:
            logging.exception("Failed to load extension %s: %s", ext, e)


def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN not set. Create a bot at https://discord.com/developers/applications, "
            "add a Bot, copy the token, and set it as DISCORD_TOKEN in your environment or .env file."
        )

    bot = create_bot()
    load_cogs(bot)

    bot.run(token)


if __name__ == "__main__":
    main()
