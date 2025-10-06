from __future__ import annotations

import os
from typing import Dict, Optional

import discord
from discord.ext import commands


STARBOARD_CHANNEL_ID = int(os.getenv("STARBOARD_CHANNEL_ID", "0") or 0)
STARBOARD_THRESHOLD = int(os.getenv("STARBOARD_THRESHOLD", "3") or 3)


def _starboard_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    if STARBOARD_CHANNEL_ID:
        ch = guild.get_channel(STARBOARD_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
    # Fallback: find by name
    for ch in guild.text_channels:
        if ch.name.lower() == "starboard":
            return ch
    return None


class Starboard(commands.Cog):
    """Simple starboard using ⭐ reactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.posted: Dict[int, int] = {}  # original_message_id -> starboard_message_id

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            msg = await channel.fetch_message(payload.message_id)
        except Exception:
            return
        if msg.author.bot or not msg.guild:
            return
        # Count stars
        star_count = 0
        for r in msg.reactions:
            if str(r.emoji) == "⭐":
                star_count = r.count
                break
        if star_count < STARBOARD_THRESHOLD:
            return
        # Already posted?
        if msg.id in self.posted:
            return
        sb = _starboard_channel(msg.guild)
        if not sb:
            return
        embed = discord.Embed(description=msg.content or "", color=discord.Color.gold())
        embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
        embed.add_field(name="Jump", value=f"[Go to message]({msg.jump_url})", inline=False)
        if msg.attachments:
            a = msg.attachments[0]
            if a.content_type and a.content_type.startswith("image/"):
                embed.set_image(url=a.url)
        sent = await sb.send(f"⭐ **{star_count}** | {channel.mention}", embed=embed)
        self.posted[msg.id] = sent.id


async def setup(bot: commands.Bot):
    await bot.add_cog(Starboard(bot))