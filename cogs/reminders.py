from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Tuple

import discord
from discord import app_commands
from discord.ext import commands


DURATION_RE = re.compile(r"(?:(?P<d>\d+)d)?(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?$")


def parse_duration(text: str) -> int:
    text = text.strip().lower()
    m = DURATION_RE.fullmatch(text)
    if not m:
        raise ValueError("Invalid duration. Use format like 1h30m, 45m, 10s, 1d2h.")
    d = int(m.group("d") or 0)
    h = int(m.group("h") or 0)
    m_ = int(m.group("m") or 0)
    s = int(m.group("s") or 0)
    total = d * 86400 + h * 3600 + m_ * 60 + s
    if total <= 0:
        raise ValueError("Duration must be greater than zero.")
    return total


class ReminderTask:
    def __init__(self, user_id: int, channel_id: int, message: str, seconds: int):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message = message
        self.seconds = seconds
        self.task: asyncio.Task | None = None


class Reminders(commands.Cog):
    """Simple reminders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._tasks: Dict[int, ReminderTask] = {}
        self._next_id = 1

    @app_commands.command(name="remind_in", description="Set a reminder in a duration (e.g., 1h30m).")
    async def remind_in(self, interaction: discord.Interaction, duration: str, message: str):
        try:
            seconds = parse_duration(duration)
        except ValueError as e:
            return await interaction.response.send_message(str(e), ephemeral=True)

        rid = self._next_id
        self._next_id += 1
        rt = ReminderTask(interaction.user.id, interaction.channel.id, message, seconds)
        self._tasks[rid] = rt

        async def runner():
            await asyncio.sleep(seconds)
            channel = self.bot.get_channel(rt.channel_id)
            user = interaction.user
            content = f"⏰ Reminder for {user.mention}: {rt.message}"
            try:
                if isinstance(channel, discord.TextChannel):
                    await channel.send(content)
                else:
                    await user.send(content)
            except Exception:
                # Fallback to DM
                try:
                    await user.send(content)
                except Exception:
                    pass
            finally:
                self._tasks.pop(rid, None)

        rt.task = self.bot.loop.create_task(runner())
        await interaction.response.send_message(f"Reminder set for {duration}. ID: {rid}", ephemeral=True)

    @app_commands.command(name="reminders", description="List your pending reminders.")
    async def list_reminders(self, interaction: discord.Interaction):
        mine = [(rid, t) for rid, t in self._tasks.items() if t.user_id == interaction.user.id]
        if not mine:
            return await interaction.response.send_message("You have no pending reminders.", ephemeral=True)
        lines = [f"- ID {rid}: in {t.seconds}s → {t.message}" for rid, t in mine]
        await interaction.response.send_message("Pending reminders:\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="remind_cancel", description="Cancel a reminder by ID.")
    async def cancel_reminder(self, interaction: discord.Interaction, reminder_id: int):
        t = self._tasks.get(reminder_id)
        if not t or t.user_id != interaction.user.id:
            return await interaction.response.send_message("Reminder not found.", ephemeral=True)
        if t.task and not t.task.done():
            t.task.cancel()
        self._tasks.pop(reminder_id, None)
        await interaction.response.send_message(f"Canceled reminder {reminder_id}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))