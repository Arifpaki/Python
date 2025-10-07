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
            # Show all commands and ignore permission checks in help listing
            self.verify_checks = False
            self.show_hidden = True

        async def send_bot_help(self, mapping):
            ctx = self.context
            prefix = ctx.clean_prefix

            MAX_FIELDS = 25          # Discord embed limit
            MAX_TOTAL = 5900         # Safety margin under 6000 char limit

            pages = []

            def add_page(title, fields, footer):
                embed = discord.Embed(title=title, color=discord.Color.blurple())
                for name, value in fields:
                    embed.add_field(name=name, value=value, inline=False)
                embed.set_footer(text=footer)
                pages.append(embed)

            for cog, cmds in mapping.items():
                filtered = await self.filter_commands(cmds, sort=True)
                if not filtered:
                    continue
                category = cog.qualified_name if cog else "Other"
                title = f"Help — {category}"
                fields = []
                total_len = len(title)

                for c in filtered:
                    usage = f"`{self.get_command_signature(c)}`"
                    desc = c.help or c.description or c.short_doc or "No description."
                    aliases = ", ".join(f"`{a}`" for a in getattr(c, "aliases", [])) or "None"
                    ctype = "Hybrid" if isinstance(c, commands.HybridCommand) else "Text"
                    name = f"{prefix}{c.qualified_name}"
                    value = f"{desc}\nUsage: {usage}\nAliases: {aliases}\nType: {ctype}"
                    # Check embed limits; start a new page if needed
                    if len(value) + len(name) + total_len > MAX_TOTAL or len(fields) >= MAX_FIELDS:
                        add_page(title, fields, f"Prefix: {prefix}")
                        fields = []
                        total_len = len(title)
                    fields.append((name, value))
                    total_len += len(name) + len(value)

                if fields:
                    add_page(title, fields, f"Prefix: {prefix}")

            if not pages:
                embed = discord.Embed(title="Help", description="No commands available.", color=discord.Color.blurple())
                embed.set_footer(text=f"Prefix: {prefix}")
                await self.get_destination().send(embed=embed)
                return

            total_pages = len(pages)
            for i, embed in enumerate(pages, start=1):
                embed.set_footer(text=f"Prefix: {prefix} • Page {i}/{total_pages}")
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

    class MyBot(commands.Bot):
        def __init__(self):
            super().__init__(command_prefix="!", intents=intents, help_command=CustomHelpCommand())

        async def setup_hook(self):
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
                    await self.load_extension(ext)
                    logging.info("Loaded extension %s", ext)
                except Exception as e:
                    logging.exception("Failed to load extension %s: %s", ext, e)
            # Ensure app commands are synced (slash commands)
            try:
                synced = await self.tree.sync()
                logging.info(f"Synced {len(synced)} application commands")
            except Exception as e:
                logging.exception("Failed to sync application commands: %s", e)

        async def on_ready(self):
            logging.info(f"Logged in as {self.user} (ID: {self.user and self.user.id})")

        async def on_command_error(self, ctx: commands.Context, error: Exception):
            # Quietly ignore unknown commands to prevent noisy logs
            if isinstance(error, commands.CommandNotFound):
                return
            # Defer other errors to the default handler
            await super().on_command_error(ctx, error)

    return MyBot()


def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    token = _read_token_from_config() or os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Bot token not set. Provide it in config.json as {\"token\": \"YOUR_TOKEN\"} "
            "or set DISCORD_TOKEN in your environment or .env file."
        )

    bot = create_bot()
    bot.run(token)


if __name__ == "__main__":
    main()
