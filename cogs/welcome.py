from __future__ import annotations

import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0") or 0)
WELCOME_MESSAGE = os.getenv(
    "WELCOME_MESSAGE",
    "Welcome to the server, {member}! Please review the rules and enjoy your stay.",
)


def _welcome_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    if WELCOME_CHANNEL_ID:
        ch = guild.get_channel(WELCOME_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
    if guild.system_channel and isinstance(guild.system_channel, discord.TextChannel):
        return guild.system_channel
    # Fallback: first text channel
    for ch in guild.text_channels:
        return ch
    return None


class Welcome(commands.Cog):
    """Welcome/leave messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ch = _welcome_channel(member.guild)
        if ch:
            msg = WELCOME_MESSAGE.format(member=member.mention, guild=member.guild.name)
            try:
                await ch.send(msg)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = _welcome_channel(member.guild)
        if ch:
            try:
                await ch.send(f"{member.mention} has left the server.")
            except Exception:
                pass

    @app_commands.command(name="welcome_test", description="Send a test welcome message.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_test(self, interaction: discord.Interaction):
        ch = _welcome_channel(interaction.guild) if interaction.guild else None
        if not ch:
            return await interaction.response.send_message("No suitable channel found.", ephemeral=True)
        msg = WELCOME_MESSAGE.format(member=interaction.user.mention, guild=interaction.guild.name if interaction.guild else "this server")
        await ch.send(msg)
        await interaction.response.send_message("Welcome message sent.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))