from __future__ import annotations

from typing import Dict, List

import discord
from discord import app_commands
from discord.ext import commands


class PollView(discord.ui.View):
    def __init__(self, question: str, options: List[str], author_id: int, timeout: float | None = 300):
        super().__init__(timeout=timeout)
        self.question = question
        self.options = options
        self.author_id = author_id
        self.votes: Dict[int, int] = {}  # user_id -> option_index
        self.counts: List[int] = [0 for _ in options]
        # Dynamically add up to 10 buttons (Discord's suggested practical limit)
        for idx, label in enumerate(options):
            style = discord.ButtonStyle.primary if idx == 0 else discord.ButtonStyle.secondary
            self.add_item(self._make_button(idx, label[:80], style))

    def _make_button(self, index: int, label: str, style: discord.ButtonStyle) -> discord.ui.Button:
        button = discord.ui.Button(label=label, style=style, custom_id=f"poll:{index}")

        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            prev = self.votes.get(uid)
            if prev is not None:
                if prev == index:
                    # Toggle off
                    self.votes.pop(uid, None)
                    self.counts[index] -= 1
                else:
                    # Move vote
                    self.votes[uid] = index
                    self.counts[prev] -= 1
                    self.counts[index] += 1
            else:
                self.votes[uid] = index
                self.counts[index] += 1
            await interaction.response.edit_message(embed=self.render_embed())

        button.callback = callback  # type: ignore
        return button

    def render_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Poll", description=self.question, color=discord.Color.blurple())
        total = max(1, sum(self.counts))
        for i, opt in enumerate(self.options):
            c = self.counts[i]
            pct = int(100 * c / total)
            bar_len = 12
            filled = int(bar_len * c / total)
            bar = "█" * filled + "░" * (bar_len - filled)
            embed.add_field(name=f"{opt}", value=f"{bar} {c} ({pct}%)", inline=False)
        embed.set_footer(text="Click a button to vote. Click again to remove your vote.")
        return embed

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


class Polls(commands.Cog):
    """Create simple button polls."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a quick poll with button voting.")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        opts = [o.strip() for o in options.split("|") if o.strip()]
        if len(opts) < 2 or len(opts) > 10:
            return await interaction.response.send_message("Provide 2–10 options separated by |", ephemeral=True)
        view = PollView(question, opts, interaction.user.id)
        embed = view.render_embed()
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))