from __future__ import annotations

import os
from typing import Optional

import discord
from discord.ext import commands


TICKET_CATEGORY_NAME = os.getenv("TICKET_CATEGORY_NAME", "Tickets")
SUPPORT_ROLE_NAME = os.getenv("SUPPORT_ROLE_NAME", "Support")
TICKET_CHANNEL_PREFIX = os.getenv("TICKET_CHANNEL_PREFIX", "ticket")


def is_ticket_channel(channel: discord.abc.GuildChannel) -> bool:
    return isinstance(channel, discord.TextChannel) and channel.name.startswith(f"{TICKET_CHANNEL_PREFIX}-")


class Tickets(commands.Cog):
    """Simple ticket system using channels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_or_create_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if category:
            return category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        return await guild.create_category(TICKET_CATEGORY_NAME, overwrites=overwrites, reason="Initialize ticket system")

    def _support_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        return discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)

    @commands.hybrid_group(name="ticket", description="Ticket system commands.")
    @commands.guild_only()
    async def ticket(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply("Subcommands: open, close, add, remove")

    @ticket.command(name="open", description="Open a new private ticket channel.")
    async def ticket_open(self, ctx: commands.Context, *, subject: Optional[str] = None):
        if not ctx.guild:
            return await ctx.reply("This command can only be used in a server.")
        category = await self._get_or_create_category(ctx.guild)
        support_role = self._support_role(ctx.guild)

        # Create channel with permissions for the user and the support role
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

        channel_name = f"{TICKET_CHANNEL_PREFIX}-{ctx.author.name.lower().replace(' ', '-')}-{ctx.author.discriminator}"
        # Ensure unique name
        base = channel_name
        i = 1
        while discord.utils.get(ctx.guild.text_channels, name=channel_name):
            i += 1
            channel_name = f"{base}-{i}"

        channel = await ctx.guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {ctx.author} | Subject: {subject or 'No subject'}",
            reason=f"Ticket opened by {ctx.author}",
        )

        embed = discord.Embed(
            title="Ticket Created",
            description=f"{ctx.author.mention} created a ticket.\nSubject: {subject or 'No subject'}\nUse /ticket close to close.",
            color=discord.Color.blurple(),
        )
        await channel.send(embed=embed)
        await ctx.reply(f"Your ticket has been created: {channel.mention}", ephemeral=True if ctx.interaction else False)

    @ticket.command(name="close", description="Close the current ticket.")
    async def ticket_close(self, ctx: commands.Context, *, reason: Optional[str] = None):
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel) or not is_ticket_channel(ctx.channel):
            return await ctx.reply("This command must be used inside a ticket channel.")
        await ctx.reply("Closing this ticket...")
        await ctx.channel.delete(reason=reason or "Ticket closed")

    @ticket.command(name="add", description="Add a member to the current ticket.")
    async def ticket_add(self, ctx: commands.Context, member: discord.Member):
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel) or not is_ticket_channel(ctx.channel):
            return await ctx.reply("This command must be used inside a ticket channel.")
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True, embed_links=True)
        await ctx.reply(f"Added {member.mention} to this ticket.")

    @ticket.command(name="remove", description="Remove a member from the current ticket.")
    async def ticket_remove(self, ctx: commands.Context, member: discord.Member):
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel) or not is_ticket_channel(ctx.channel):
            return await ctx.reply("This command must be used inside a ticket channel.")
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.reply(f"Removed {member.mention} from this ticket.")

    @ticket.command(name="rename", description="Rename the current ticket channel.")
    async def ticket_rename(self, ctx: commands.Context, *, name: str):
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel) or not is_ticket_channel(ctx.channel):
            return await ctx.reply("This command must be used inside a ticket channel.")
        new_name = f"{TICKET_CHANNEL_PREFIX}-{name.lower().replace(' ', '-')}"
        await ctx.channel.edit(name=new_name, reason=f"Renamed by {ctx.author}")
        await ctx.reply(f"Renamed to {ctx.channel.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))