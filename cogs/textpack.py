from __future__ import annotations

from typing import Callable, List, Tuple

from discord.ext import commands


# Data-driven pack of many simple prefix commands (non-slash to avoid long sync times).
# Each command applies a transform to the text and replies. Easy to scale to 300+.
Transform = Callable[[str], str]


def _rot13(s: str) -> str:
    import codecs

    return codecs.decode(s, "rot_13")


def _remove_vowels(s: str) -> str:
    vowels = "aeiouAEIOU"
    return "".join(c for c in s if c not in vowels)


def _only_vowels(s: str) -> str:
    vowels = "aeiouAEIOU"
    return "".join(c for c in s if c in vowels)


def _leet(s: str) -> str:
    table = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "A": "4", "E": "3", "I": "1", "O": "0", "S": "5"})
    return s.translate(table)


def _mirror(s: str) -> str:
    return s + " | " + s[::-1]


def _snake(s: str) -> str:
    return "_".join(s.lower().split())


def _kebab(s: str) -> str:
    return "-".join(s.lower().split())


def _camel(s: str) -> str:
    parts = s.split()
    if not parts:
        return ""
    head, *tail = parts
    return head.lower() + "".join(p.capitalize() for p in tail)


def _pascal(s: str) -> str:
    return "".join(p.capitalize() for p in s.split())


def _spongebob(s: str) -> str:
    return "".join((c.upper() if (i % 2) else c.lower()) for i, c in enumerate(s))


TRANSFORMS: List[Tuple[str, str, Transform]] = [
    ("rot13", "Apply ROT13 to text", _rot13),
    ("novowels", "Remove vowels", _remove_vowels),
    ("onlyvowels", "Keep only vowels", _only_vowels),
    ("leet", "1337-ify text", _leet),
    ("mirror", "Mirror the text left|right", _mirror),
    ("snake", "snake_case the text", _snake),
    ("kebab", "kebab-case the text", _kebab),
    ("camel", "camelCase the text", _camel),
    ("pascal", "PascalCase the text", _pascal),
    ("spongebob", "mOcKiFy tExT", _spongebob),
]


class TextPack(commands.Cog):
    """A large pack of simple, fast prefix commands built from transforms."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._register_commands()

    def _register_commands(self):
        # Register each transform as a normal prefix command (not slash) to keep slash sync fast.
        for name, desc, fn in TRANSFORMS:
            async def _cmd(ctx: commands.Context, *, text: str, __fn=fn):
                await ctx.reply(__fn(text))
            _cmd.__name__ = f"tp_{name}"
            _cmd.__doc__ = desc  # exposed in help
            cmd = commands.command(name=name, help=desc)(_cmd)
            self.bot.add_command(cmd)

        # Generate many alias commands that chain transforms to reach a high command count.
        chain_specs: List[Tuple[str, str, List[str]]] = []
        bases = [n for n, _, _ in TRANSFORMS]
        # Create combinations like rot13_leet, lower_snake, kebab_mirror, etc.
        for a in bases:
            for b in bases:
                if a == b:
                    continue
                name = f"{a}_{b}"
                desc = f"{a} then {b}"
                chain_specs.append((name, desc, [a, b]))
        # Cap the generated commands to avoid overwhelming smaller bots by default.
        chain_specs = chain_specs[:200]  # adjust higher to approach 300+

        name_to_fn = {n: fn for n, _, fn in TRANSFORMS}

        def _apply_chain(text: str, names: List[str]) -> str:
            out = text
            for n in names:
                out = name_to_fn[n](out)
            return out

        for name, desc, chain in chain_specs:
            async def _chain_cmd(ctx: commands.Context, *, text: str, __chain=chain):
                await ctx.reply(_apply_chain(text, __chain))
            _chain_cmd.__name__ = f"tp_{name}"
            _chain_cmd.__doc__ = desc
            cmd = commands.command(name=name, help=desc)(_chain_cmd)
            self.bot.add_command(cmd)


async def setup(bot: commands.Bot):
    await bot.add_cog(TextPack(bot))