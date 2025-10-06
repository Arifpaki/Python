from __future__ import annotations

from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands


class Tags(commands.Cog):
    """Simple in-memory tags per guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tags: Dict[int, Dict[str, str]] = {}  # guild_id -> {name: content}

    def _guild_store(self, guild_id: int) -> Dict[str, str]:
        return self.tags.setdefault(guild_id, {})

    tag = app_commands.Group(name="tag", description="Manage server tags")

    @tag.command(name="add", description="Add or update a tag")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def add(self, interaction: discord.Interaction, name: str, content: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        store = self._guild_store(interaction.guild.id)
        store[name.lower()] = content
        await interaction.response.send_message(f"Saved tag '{name}'.", ephemeral=True)

    @tag.command(name="get", description="Get a tag by name")
    async def get(self, interaction: discord.Interaction, name: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        store = self._guild_store(interaction.guild.id)
        val = store.get(name.lower())
        if not val:
            return await interaction.response.send_message("Tag not found.", ephemeral=True)
        await interaction.response.send_message(val)

    @tag.command(name="list", description="List all tags")
    async def list(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        store = self._guild_store(interaction.guild.id)
        if not store:
            return await interaction.response.send_message("No tags set.", ephemeral=True)
        names = ", ".join(sorted(store.keys()))
        await interaction.response.send_message(f"Tags: {names}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))