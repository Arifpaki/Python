from __future__ import annotations

import random
import string
from typing import Optional

import discord
from discord.ext import commands


EIGHT_BALL_ANSWERS = [
    "It is certain.",
    "Without a doubt.",
    "Yes – definitely.",
    "Most likely.",
    "Outlook good.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Don't count on it.",
    "My reply is no.",
    "Outlook not so good.",
    "Very doubtful.",
]


class Fun(commands.Cog):
    """Fun and games."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Dice roll, coinflip, choose, 8ball ---------------------------------------------------------

    @commands.hybrid_command(name="roll", description="Roll dice, e.g. 2d6+1 or just d20.")
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        # Very small and safe parser: NdM(+/-K)
        try:
            work = dice.lower().replace(" ", "")
            sign = 1
            bonus = 0
            if "+" in work or "-" in work:
                if "-" in work:
                    part, b = work.split("-", 1)
                    sign = -1
                else:
                    part, b = work.split("+", 1)
                bonus = int(b)
            else:
                part = work
            if "d" not in part:
                raise ValueError
            n_str, m_str = (part.split("d", 1) if part.split("d", 1)[0] else ("1", part.split("d", 1)[1]))
            n = int(n_str) if n_str else 1
            m = int(m_str)
            n = max(1, min(n, 100))
            m = max(2, min(m, 1000))
        except Exception:
            return await ctx.reply("Format must be NdM+K (e.g., 2d6+1, d20, 3d8-2)")
        rolls = [random.randint(1, m) for _ in range(n)]
        total = sum(rolls) + sign * bonus
        desc = " + ".join(map(str, rolls))
        if bonus:
            desc += f" {'+' if sign > 0 else '-'} {abs(bonus)}"
        await ctx.reply(f"🎲 {dice} → {desc} = **{total}**")

    @commands.hybrid_command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, ctx: commands.Context):
        await ctx.reply(f"🪙 {random.choice(['Heads', 'Tails'])}")

    @commands.hybrid_command(name="choose", description="Choose between options separated by |")
    async def choose(self, ctx: commands.Context, *, options: str):
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            return await ctx.reply("Provide at least 2 options separated by |")
        await ctx.reply(f"I choose: {random.choice(choices)}")

    @commands.hybrid_command(name="eightball", description="Ask the 8ball a question.")
    async def eightball(self, ctx: commands.Context, *, question: str):
        await ctx.reply(f"🎱 {random.choice(EIGHT_BALL_ANSWERS)}")

    # Text transforms -----------------------------------------------------------------------------

    @commands.hybrid_command(name="upper", description="UPPERCASE your text.")
    async def upper(self, ctx: commands.Context, *, text: str):
        await ctx.reply(text.upper())

    @commands.hybrid_command(name="lower", description="lowercase your text.")
    async def lower(self, ctx: commands.Context, *, text: str):
        await ctx.reply(text.lower())

    @commands.hybrid_command(name="titlecase", description="Title Case your text.")
    async def titlecase(self, ctx: commands.Context, *, text: str):
        await ctx.reply(text.title())

    @commands.hybrid_command(name="reverse", description="Reverse your text.")
    async def reverse(self, ctx: commands.Context, *, text: str):
        await ctx.reply(text[::-1])

    @commands.hybrid_command(name="clap", description="Add 👏 between words.")
    async def clap(self, ctx: commands.Context, *, text: str):
        await ctx.reply(" 👏 ".join(text.split()))

    @commands.hybrid_command(name="mock", description="mOcKiFy tExT.")
    async def mock(self, ctx: commands.Context, *, text: str):
        out = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
        await ctx.reply(out)

    @commands.hybrid_command(name="space", description="Add spaces between letters.")
    async def space(self, ctx: commands.Context, *, text: str):
        await ctx.reply(" ".join(list(text)))

    @commands.hybrid_command(name="owo", description="owo/uwu-ify your text.")
    async def owo(self, ctx: commands.Context, *, text: str):
        repl = (
            text.replace("r", "w")
            .replace("l", "w")
            .replace("R", "W")
            .replace("L", "W")
            .replace("no", "nyo")
            .replace("No", "Nyo")
        )
        await ctx.reply(repl + " uwu")

    # Randomizers ---------------------------------------------------------------------------------

    @commands.hybrid_command(name="randint", description="Random integer between a and b.")
    async def randint(self, ctx: commands.Context, a: int, b: int):
        if a > b:
            a, b = b, a
        await ctx.reply(str(random.randint(a, b)))

    @commands.hybrid_command(name="randchoice", description="Random choice from comma-separated list.")
    async def randchoice(self, ctx: commands.Context, *, items: str):
        parts = [p.strip() for p in items.split(",") if p.strip()]
        if len(parts) < 2:
            return await ctx.reply("Provide at least 2 comma-separated items.")
        await ctx.reply(random.choice(parts))

    @commands.hybrid_command(name="password", description="Generate a random password.")
    async def password(self, ctx: commands.Context, length: Optional[int] = 12):
        length = max(4, min(length or 12, 64))
        chars = string.ascii_letters + string.digits
        pwd = "".join(random.choice(chars) for _ in range(length))
        await ctx.reply(pwd)

    # Simple math ---------------------------------------------------------------------------------

    @commands.hybrid_command(name="add", description="Add numbers.")
    async def add(self, ctx: commands.Context, a: float, b: float):
        await ctx.reply(str(a + b))

    @commands.hybrid_command(name="sub", description="Subtract numbers.")
    async def sub(self, ctx: commands.Context, a: float, b: float):
        await ctx.reply(str(a - b))

    @commands.hybrid_command(name="mul", description="Multiply numbers.")
    async def mul(self, ctx: commands.Context, a: float, b: float):
        await ctx.reply(str(a * b))

    @commands.hybrid_command(name="div", description="Divide numbers.")
    async def div(self, ctx: commands.Context, a: float, b: float):
        if b == 0:
            return await ctx.reply("Cannot divide by zero.")
        await ctx.reply(str(a / b))


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))