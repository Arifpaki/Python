from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """Basic moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", description="Delete a number of messages.")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, amount: Optional[int] = 10):
        amount = max(1, min(amount or 10, 200))
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)

    @commands.hybrid_command(name="kick", description="Kick a member.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        await member.kick(reason=reason)
        await ctx.reply(f"Kicked {member.mention}. Reason: {reason or 'None'}")

    @commands.hybrid_command(name="ban", description="Ban a member.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        await member.ban(reason=reason)
        await ctx.reply(f"Banned {member.mention}. Reason: {reason or 'None'}")

    @commands.hybrid_command(name="unban", description="Unban a user by name#discriminator or ID.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, *, user: str):
        bans = await ctx.guild.bans()
        target = None
        if user.isdigit():
            uid = int(user)
            for ban in bans:
                if ban.user.id == uid:
                    target = ban.user
                    break
        else:
            name, _, discrim = user.partition("#")
            for ban in bans:
                u = ban.user
                if u.name == name and (not discrim or u.discriminator == discrim):
                    target = u
                    break
        if not target:
            return await ctx.reply("User not found in ban list.")
        await ctx.guild.unban(target)
        await ctx.reply(f"Unbanned {target}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))