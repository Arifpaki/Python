from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Tuple

import codecs
import os
import discord
from discord import app_commands
from discord.ext import commands


Transform = Callable[[str], str]


# Base transform functions (safe/halal text utilities)
def t_upper(s: str) -> str:
    return s.upper()


def t_lower(s: str) -> str:
    return s.lower()


def t_title(s: str) -> str:
    return s.title()


def t_reverse(s: str) -> str:
    return s[::-1]


def t_clap(s: str) -> str:
    return " 👏 ".join(s.split())


def t_space(s: str) -> str:
    return " ".join(list(s))


def t_rot13(s: str) -> str:
    return codecs.decode(s, "rot_13")


def t_novowels(s: str) -> str:
    vowels = "aeiouAEIOU"
    return "".join(c for c in s if c not in vowels)


def t_onlyvowels(s: str) -> str:
    vowels = "aeiouAEIOU"
    return "".join(c for c in s if c in vowels)


def t_leet(s: str) -> str:
    table = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "A": "4", "E": "3", "I": "1", "O": "0", "S": "5"})
    return s.translate(table)


def t_mirror(s: str) -> str:
    return s + " | " + s[::-1]


def t_snake(s: str) -> str:
    return "_".join(s.lower().split())


def t_kebab(s: str) -> str:
    return "-".join(s.lower().split())


def t_camel(s: str) -> str:
    parts = s.split()
    if not parts:
        return ""
    head, *tail = parts
    return head.lower() + "".join(p.capitalize() for p in tail)


def t_pascal(s: str) -> str:
    return "".join(p.capitalize() for p in s.split())


BASE_TRANSFORMS: List[Tuple[str, str, Transform]] = [
    ("upper", "UPPERCASE text", t_upper),
    ("lower", "lowercase text", t_lower),
    ("titlecase", "Title Case text", t_title),
    ("reverse", "Reverse text", t_reverse),
    ("clap", "Add 👏 between words", t_clap),
    ("space", "Add spaces between letters", t_space),
    ("rot13", "Apply ROT13", t_rot13),
    ("novowels", "Remove vowels", t_novowels),
    ("onlyvowels", "Keep only vowels", t_onlyvowels),
    ("leet", "1337-ify text", t_leet),
    ("mirror", "Mirror text left|right", t_mirror),
    ("snake", "snake_case the text", t_snake),
    ("kebab", "kebab-case the text", t_kebab),
    ("camel", "camelCase the text", t_camel),
    ("pascal", "PascalCase the text", t_pascal),
]

NAME_TO_FN: Dict[str, Transform] = {n: fn for n, _, fn in BASE_TRANSFORMS}


def chunked(seq: Iterable, size: int) -> List[List]:
    out: List[List] = []
    cur: List = []
    for item in seq:
        cur.append(item)
        if len(cur) >= size:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def apply_chain(text: str, chain: List[str]) -> str:
    out = text
    for name in chain:
        out = NAME_TO_FN[name](out)
    return out


class MegaPack(commands.Cog):
    """Large, safe (halal) pack of ~300 slash commands for text transforms."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.root = app_commands.Group(name="pack", description="Large pack of text transforms (safe/halal)")

    async def cog_load(self) -> None:
        # Build base group
        base_group = app_commands.Group(name="base", description="Base transforms")
        for name, desc, fn in BASE_TRANSFORMS:
            async def _base_cb(interaction: discord.Interaction, text: str, __fn=fn):
                await interaction.response.send_message(__fn(text))
            cmd = app_commands.Command(name=name, description=desc, callback=_base_cb)
            base_group.add_command(cmd)

        self.root.add_command(base_group)

        # Build two-step chains dynamically
        bases = [n for n, _, _ in BASE_TRANSFORMS]
        two_chains = [(a, b) for a in bases for b in bases if a != b]

        # Target approx 300 total commands
        target = int(os.getenv("PACK_COMMAND_TARGET", "300"))
        base_count = len(BASE_TRANSFORMS)
        two_count = len(two_chains)
        remaining = max(0, target - (base_count + two_count))

        # Spread two-step chains into groups of ~24 for better UX
        two_chunks = chunked(two_chains, 24)

        for idx, chunk in enumerate(two_chunks, start=1):
            grp = app_commands.Group(name=f"two{idx}", description="Two-step transforms")
            for a, b in chunk:
                chain = [a, b]
                async def _two_cb(interaction: discord.Interaction, text: str, __chain=chain):
                    await interaction.response.send_message(apply_chain(text, __chain))
                name = f"{a}_{b}"
                desc = f"{a} then {b}"
                cmd = app_commands.Command(name=name, description=desc, callback=_two_cb)
                grp.add_command(cmd)
            self.root.add_command(grp)

        # Build N three-step chains to reach the target
        three_chains: List[Tuple[str, str, str]] = []
        if remaining > 0:
            for a in bases:
                for b in bases:
                    if b == a:
                        continue
                    for c in bases:
                        if c == a or c == b:
                            continue
                        three_chains.append((a, b, c))
                        if len(three_chains) >= remaining:
                            break
                    if len(three_chains) >= remaining:
                        break
                if len(three_chains) >= remaining:
                    break

            three_chunks = chunked(three_chains, 25)
            for idx, chunk in enumerate(three_chunks, start=1):
                grp = app_commands.Group(name=f"three{idx}", description="Three-step transforms")
                for a, b, c in chunk:
                    chain = [a, b, c]
                    async def _three_cb(interaction: discord.Interaction, text: str, __chain=chain):
                        await interaction.response.send_message(apply_chain(text, __chain))
                    name = f"{a}_{b}_{c}"
                    desc = f"{a} then {b} then {c}"
                    cmd = app_commands.Command(name=name, description=desc, callback=_three_cb)
                    grp.add_command(cmd)
                self.root.add_command(grp)

        # Finally add the root group to the app command tree
        try:
            self.bot.tree.add_command(self.root)
        except Exception:
            # In case of reload, remove and re-add
            self.bot.tree.remove_command(self.root.name)
            self.bot.tree.add_command(self.root)

    def cog_unload(self) -> None:
        try:
            self.bot.tree.remove_command(self.root.name)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MegaPack(bot))