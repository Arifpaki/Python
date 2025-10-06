from __future__ import annotations

import os
from typing import Optional

import discord
from discord.ext import commands


LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0") or 0)


def _log_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    if LOG_CHANNEL_ID:
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
    return None


class Logs(commands.Cog):
    """Lightweight server logs to a specific channel (set LOG_CHANNEL_ID)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        ch = _log_channel(message.guild)
        if not ch:
            return
        content = message.content or "[no content]"
        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=content[:1000], inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        ch = _log_channel(before.guild)
        if not ch:
            return
        embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
        embed.add_field(name="Author", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=(before.content or "")[:1000], inline=False)
        embed.add_field(name="After", value=(after.content or "")[:1000], inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ch = _log_channel(member.guild)
        if not ch:
            return
        await ch.send(f"✅ {member} joined. ID: {member.id}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = _log_channel(member.guild)
        if not ch:
            return
        await ch.send(f"❌ {member} left. ID: {member.id}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))