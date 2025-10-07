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

    # Define a custom, embed-based help command
    import discord

    class CustomHelpCommand(commands.HelpCommand):
        def __init__(self):
            super().__init__(command_attrs={"help": "Show help for commands."})

        async def send_bot_help(self, mapping):
            ctx = self.context
            prefix = ctx.clean_prefix
            embed = discord.Embed(title="Help", color=discord.Color.blurple())
            embed.description = (
                f"Use {prefix}help <command> for command info.\n"
                f"Use {prefix}help <category> to list commands in a category."
            )
            for cog, cmds in mapping.items():
                filtered = await self.filter_commands(cmds, sort=True)
                if not filtered:
                    continue
                name = cog.qualified_name if cog else "Other"
                value = " ".join(f"`{c.name}`" for c in filtered[:10])
                if len(filtered) > 10:
                    value += f"\n… {len(filtered)-10} more. Use `{prefix}help {name}`"
                embed.add_field(name=name, value=value or "No commands available.", inline=False)
            embed.set_footer(text=f"Prefix: {prefix}")
            await self.get_destination().send(embed=embed)

        async def send_cog_help(self, cog):
            prefix = self.context.clean_prefix
            entries = await self.filter_commands(cog.get_commands(), sort=True)
            embed = discord.Embed(title=f"{cog.qualified_name} Commands", color=discord.Color.blurple())
            if cog.description:
                embed.description = cog.description
            for command in entries:
                brief = command.short_doc or "No description."
                embed.add_field(name=f"{prefix}{command.qualified_name}", value=brief, inline=False)
            await self.get_destination().send(embed=embed)

        async def send_group_help(self, group):
            prefix = self.context.clean_prefix
            embed = discord.Embed(title=group.qualified_name, color=discord.Color.blurple())
            embed.add_field(name="Usage", value=f"`{self.get_command_signature(group)}`", inline=False)
            desc = group.help or group.description or group.short_doc
            if desc:
                embed.description = desc
            subs = await self.filter_commands(group.commands, sort=True)
            for sub in subs:
                embed.add_field(name=f"{prefix}{sub.qualified_name}", value=sub.short_doc or "No description.", inline=False)
            await self.get_destination().send(embed=embed)

        async def send_command_help(self, command):
            embed = discord.Embed(title=command.qualified_name, color=discord.Color.blurple())
            embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False)
            desc = command.help or command.description or command.short_doc
            if desc:
                embed.description = desc
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in command.aliases), inline=False)
            if command.cog:
                embed.add_field(name="Category", value=command.cog.qualified_name, inline=True)
            embed.add_field(
                name="Type",
                value=("Hybrid" if isinstance(command, commands.HybridCommand) else "Text"),
                inline=True,
            )
            await self.get_destination().send(embed=embed)

        def get_command_signature(self, command):
            return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}".strip()

    # Use a fixed "!" prefix and register the custom help command
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=CustomHelpCommand())

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
