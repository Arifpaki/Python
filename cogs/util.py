from __future__ import annotations

import platform
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


class Util(commands.Cog):
    """General utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._start_time = time.time()

    @commands.hybrid_command(name="ping", description="Check bot latency.")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.reply(f"Pong! {latency_ms}ms")

    @commands.hybrid_command(name="uptime", description="Show how long the bot has been running.")
    async def uptime(self, ctx: commands.Context):
        delta = int(time.time() - self._start_time)
        days, remainder = divmod(delta, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        await ctx.reply(f"Uptime: {' '.join(parts)}")

    @commands.hybrid_command(name="userinfo", description="Get info about a user.")
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        member = member or ctx.author
        roles = ", ".join(r.mention for r in member.roles if r.name != "@everyone") or "None"
        embed = discord.Embed(title=f"User info - {member}", color=member.top_role.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.add_field(name="Roles", value=roles, inline=False)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Get info about this server.")
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            return await ctx.reply("This command can only be used in a server.")
        text_channels = sum(1 for c in g.channels if isinstance(c, discord.TextChannel))
        voice_channels = sum(1 for c in g.channels if isinstance(c, discord.VoiceChannel))
        embed = discord.Embed(title=f"Server info - {g.name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=g.icon.url if g.icon else discord.Embed.Empty)
        embed.add_field(name="ID", value=str(g.id), inline=True)
        embed.add_field(name="Members", value=str(g.member_count), inline=True)
        embed.add_field(name="Channels", value=f"{text_channels} text / {voice_channels} voice", inline=True)
        embed.add_field(name="Owner", value=g.owner.mention if g.owner else "Unknown", inline=True)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="say", description="Have the bot repeat your message.")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, message: str):
        await ctx.message.delete() if ctx.interaction is None else None
        await ctx.send(message)

    @commands.hybrid_command(name="about", description="Show bot information.")
    async def about(self, ctx: commands.Context):
        embed = discord.Embed(title="Bot Information", color=discord.Color.green())
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Util(bot))