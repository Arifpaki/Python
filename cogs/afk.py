from __future__ import annotations

from typing import Dict, Optional

import discord
from discord import app_commands
from discord.ext import commands


class AFK(commands.Cog):
    """Simple AFK system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.afk: Dict[int, str] = {}  # user_id -> reason

    @commands.hybrid_command(name="afk", description="Set yourself as AFK with an optional reason.")
    async def afk(self, ctx: commands.Context, *, reason: Optional[str] = None):
        self.afk[ctx.author.id] = reason or "AFK"
        if ctx.interaction is not None:
            await ctx.interaction.response.send_message(
                f"You're now AFK: {self.afk[ctx.author.id]}", ephemeral=True
            )
        else:
            try:
                await ctx.reply(f"You're now AFK: {self.afk[ctx.author.id]}", delete_after=8)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Clear AFK if the user speaks
        if message.author.id in self.afk:
            reason = self.afk.pop(message.author.id)
            try:
                await message.channel.send(f"Welcome back, {message.author.mention}. Removed AFK ({reason}).", delete_after=6)
            except Exception:
                pass
        # Notify if mentioning AFK users
        if message.mentions:
            mentioned = []
            for m in message.mentions:
                if m.id in self.afk:
                    mentioned.append(f"{m.display_name}: {self.afk[m.id]}")
            if mentioned:
                try:
                    await message.channel.send("AFK users: " + "; ".join(mentioned), delete_after=10)
                except Exception:
                    pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AFK(bot))