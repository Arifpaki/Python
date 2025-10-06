from __future__ import annotations

import asyncio
import json
import os
import random
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


CONFIG_DIR = Path("data")
CONFIG_FILE = CONFIG_DIR / "islam.json"

TIME_RE = re.compile(r"^(?:[01]?\d|2[0-3]):[0-5]\d$")


@dataclass
class GuildSettings:
    channel_id: Optional[int] = None
    timezone: str = "UTC"
    daily_time: str = "09:00"
    jumuah_time: str = "12:00"
    enable_daily: bool = True
    enable_jumuah: bool = True
    daily_header: str = "Daily Qur'an ayah and hadith"
    jumuah_header: str = "Jumu'ah Mubarak"
    last_daily_date: Optional[str] = None
    last_jumuah_date: Optional[str] = None


class IslamicReminders(commands.Cog):
    """Customizable Jumu'ah reminder and daily Qur'an ayah + hadith, using public APIs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._store: Dict[str, Any] = {"guilds": {}}  # type: ignore
        self._load()
        self.scheduler.start()

    # ----------------------------- Persistence -----------------------------

    def _load(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                self._store = json.loads(CONFIG_FILE.read_text("utf-8"))
            except Exception:
                self._store = {"guilds": {}}
        else:
            self._store = {"guilds": {}}

    def _save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = json.dumps(self._store, indent=2, ensure_ascii=False)
        CONFIG_FILE.write_text(tmp, encoding="utf-8")

    def _get_guild_settings(self, guild_id: int) -> GuildSettings:
        g = self._store["guilds"].get(str(guild_id))
        if not g:
            gs = GuildSettings()
            self._store["guilds"][str(guild_id)] = asdict(gs)
            self._save()
            return gs
        # Ensure any new fields get defaults
        cur = GuildSettings(**{**GuildSettings().__dict__, **g})
        # Write back to persist defaults if missing previously
        self._store["guilds"][str(guild_id)] = asdict(cur)
        return cur

    def _set_guild_settings(self, guild_id: int, gs: GuildSettings) -> None:
        self._store["guilds"][str(guild_id)] = asdict(gs)
        self._save()

    # ----------------------------- Helpers -----------------------------

    def _parse_time(self, t: str) -> Optional[str]:
        t = t.strip()
        if TIME_RE.fullmatch(t):
            # zero-pad to HH:MM
            h, m = t.split(":")
            return f"{int(h):02d}:{int(m):02d}"
        return None

    def _tz(self, name: str):
        if ZoneInfo is None:
            return None
        try:
            return ZoneInfo(name)
        except Exception:
            return None

    async def _get_channel(self, guild: discord.Guild, gs: GuildSettings) -> Optional[discord.TextChannel]:
        if gs.channel_id:
            ch = guild.get_channel(gs.channel_id)
            if isinstance(ch, discord.TextChannel):
                return ch
        if guild.system_channel and isinstance(guild.system_channel, discord.TextChannel):
            return guild.system_channel
        # Fallback to first text channel
        for ch in guild.text_channels:
            return ch
        return None

    # ----------------------------- API fetchers -----------------------------

    async def fetch_random_ayah(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        # Try alquran.cloud with Arabic + English editions
        try:
            url = "https://api.alquran.cloud/v1/ayah/random/editions/quran-uthmani,en.asad"
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
            d = data.get("data")
            if isinstance(d, list) and d:
                arab = next((x for x in d if x.get("edition", {}).get("language") == "ar"), d[0])
                eng = next((x for x in d if x.get("edition", {}).get("language") == "en"), d[0])
                surah = arab.get("surah", {})
                ref = f"{surah.get('englishName', 'Surah')} {surah.get('number', '')}:{arab.get('numberInSurah', '')}"
                return {
                    "arabic": arab.get("text", ""),
                    "english": eng.get("text", ""),
                    "reference": ref,
                    "source": "api.alquran.cloud",
                }
            elif isinstance(d, dict):
                surah = d.get("surah", {})
                ref = f"{surah.get('englishName', 'Surah')} {surah.get('number', '')}:{d.get('numberInSurah', '')}"
                return {
                    "arabic": d.get("text", ""),
                    "english": "",
                    "reference": ref,
                    "source": "api.alquran.cloud",
                }
        except Exception:
            pass
        # Fallback basic
        return {
            "arabic": "Bismillah.",
            "english": "",
            "reference": "Qur'an",
            "source": "fallback",
        }

    async def fetch_random_hadith(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        # Use gading.dev hadith API - no key needed
        try:
            book = random.choice(["bukhari", "muslim"])
            max_n = 7000 if book == "bukhari" else 4000
            n = random.randint(1, max_n)
            url = f"https://api.hadith.gading.dev/books/{book}?range={n}-{n}"
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
            d = data.get("data", {})
            hadiths = d.get("hadiths") or []
            if hadiths:
                h = hadiths[0]
                arab = h.get("arab") or h.get("arabic") or ""
                no = h.get("number") or str(n)
                return {
                    "text": arab,
                    "reference": f"{book.title()} {no}",
                    "source": "api.hadith.gading.dev",
                }
        except Exception:
            pass
        return {
            "text": "Hadith unavailable right now.",
            "reference": "Hadith",
            "source": "fallback",
        }

    # ----------------------------- Sending -----------------------------

    async def send_daily(self, guild: discord.Guild, gs: GuildSettings) -> None:
        ch = await self._get_channel(guild, gs)
        if not ch:
            return
        async with aiohttp.ClientSession() as session:
            ayah = await self.fetch_random_ayah(session)
            hadith = await self.fetch_random_hadith(session)

        embed = discord.Embed(title=gs.daily_header, color=discord.Color.green())
        q_text = ayah["arabic"]
        if ayah.get("english"):
            q_text += f"\n\n{ayah['english']}"
        embed.add_field(name=f"Qur'an — {ayah.get('reference','')}", value=q_text[:1024] or "-", inline=False)
        embed.add_field(name=f"Hadith — {hadith.get('reference','')}", value=(hadith["text"][:1024] or "-"), inline=False)
        embed.set_footer(text=f"Sources: {ayah.get('source')} • {hadith.get('source')}")

        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    async def send_jumuah(self, guild: discord.Guild, gs: GuildSettings) -> None:
        ch = await self._get_channel(guild, gs)
        if not ch:
            return
        async with aiohttp.ClientSession() as session:
            ayah = await self.fetch_random_ayah(session)
            hadith = await self.fetch_random_hadith(session)

        embed = discord.Embed(title=gs.jumuah_header, description="May Allah bless your Jumu'ah.", color=discord.Color.blurple())
        q_text = ayah["arabic"]
        if ayah.get("english"):
            q_text += f"\n\n{ayah['english']}"
        embed.add_field(name=f"Qur'an — {ayah.get('reference','')}", value=q_text[:1024] or "-", inline=False)
        embed.add_field(name=f"Hadith — {hadith.get('reference','')}", value=(hadith["text"][:1024] or "-"), inline=False)
        embed.set_footer(text=f"Sources: {ayah.get('source')} • {hadith.get('source')}")

        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    # ----------------------------- Scheduler -----------------------------

    @tasks.loop(minutes=1)
    async def scheduler(self):
        # Called every minute; check each guild's local time against settings.
        now_utc = datetime.now(timezone.utc)
        for g in list(self._store.get("guilds", {}).keys()):
            gid = int(g)
            guild = self.bot.get_guild(gid)
            if not guild:
                continue
            gs = self._get_guild_settings(gid)
            tz = self._tz(gs.timezone) or timezone.utc
            local_now = now_utc.astimezone(tz)  # type: ignore[arg-type]
            hhmm = local_now.strftime("%H:%M")
            today = local_now.date().isoformat()

            # Daily
            if gs.enable_daily and self._parse_time(gs.daily_time) == hhmm and gs.last_daily_date != today:
                await self.send_daily(guild, gs)
                gs.last_daily_date = today
                self._set_guild_settings(gid, gs)

            # Jumu'ah (Friday)
            if gs.enable_jumuah and local_now.weekday() == 4 and self._parse_time(gs.jumuah_time) == hhmm and gs.last_jumuah_date != today:
                await self.send_jumuah(guild, gs)
                gs.last_jumuah_date = today
                self._set_guild_settings(gid, gs)

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    # ----------------------------- Commands -----------------------------

    islam = app_commands.Group(name="islam", description="Configure Islamic reminders")

    @islam.command(name="status", description="Show the current reminder settings.")
    async def status(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        embed = discord.Embed(title="Islamic Reminders — Status", color=discord.Color.green())
        embed.add_field(name="Channel", value=f"<#{gs.channel_id}>" if gs.channel_id else "Auto", inline=True)
        embed.add_field(name="Timezone", value=gs.timezone, inline=True)
        embed.add_field(name="Daily", value=f"{'On' if gs.enable_daily else 'Off'} at {gs.daily_time}", inline=True)
        embed.add_field(name="Jumu'ah", value=f"{'On' if gs.enable_jumuah else 'Off'} at {gs.jumuah_time} (Friday)", inline=True)
        embed.add_field(name="Daily header", value=gs.daily_header, inline=False)
        embed.add_field(name="Jumu'ah header", value=gs.jumuah_header, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @islam.command(name="set_channel", description="Set the channel for reminders.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.channel_id = channel.id if channel else interaction.channel_id
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Channel set to <#{gs.channel_id}>.", ephemeral=True)

    @islam.command(name="set_timezone", description="Set IANA timezone (e.g., Asia/Riyadh).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_timezone(self, interaction: discord.Interaction, tz: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        if ZoneInfo is None or self._tz(tz) is None:
            return await interaction.response.send_message("Invalid timezone. Use an IANA name like Asia/Riyadh or Europe/London.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.timezone = tz
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Timezone set to {tz}.", ephemeral=True)

    @islam.command(name="set_daily_time", description="Set daily reminder time (HH:MM, 24h).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_daily_time(self, interaction: discord.Interaction, time: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        t = self._parse_time(time)
        if not t:
            return await interaction.response.send_message("Invalid time. Use HH:MM 24-hour format.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.daily_time = t
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Daily reminder time set to {t}.", ephemeral=True)

    @islam.command(name="set_jumuah_time", description="Set Jumu'ah reminder time on Fridays (HH:MM, 24h).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_jumuah_time(self, interaction: discord.Interaction, time: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        t = self._parse_time(time)
        if not t:
            return await interaction.response.send_message("Invalid time. Use HH:MM 24-hour format.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.jumuah_time = t
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Jumu'ah reminder time set to {t}.", ephemeral=True)

    @islam.command(name="toggle_daily", description="Enable or disable the daily reminder.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def toggle_daily(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.enable_daily = enabled
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Daily reminders {'enabled' if enabled else 'disabled'}.", ephemeral=True)

    @islam.command(name="toggle_jumuah", description="Enable or disable the Friday Jumu'ah reminder.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def toggle_jumuah(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.enable_jumuah = enabled
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message(f"Jumu'ah reminders {'enabled' if enabled else 'disabled'}.", ephemeral=True)

    @islam.command(name="set_daily_header", description="Set the header/title for daily reminders.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_daily_header(self, interaction: discord.Interaction, header: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.daily_header = header[:200]
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message("Updated daily header.", ephemeral=True)

    @islam.command(name="set_jumuah_header", description="Set the header/title for Jumu'ah reminders.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_jumuah_header(self, interaction: discord.Interaction, header: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        gs.jumuah_header = header[:200]
        self._set_guild_settings(interaction.guild.id, gs)
        await interaction.response.send_message("Updated Jumu'ah header.", ephemeral=True)

    @islam.command(name="send_now", description="Send a reminder now (testing).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def send_now(self, interaction: discord.Interaction, kind: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        gs = self._get_guild_settings(interaction.guild.id)
        if kind.lower() not in {"daily", "jumuah", "jummah", "friday"}:
            return await interaction.response.send_message("Kind must be 'daily' or 'jumuah'.", ephemeral=True)
        if kind.lower() == "daily":
            await self.send_daily(interaction.guild, gs)
        else:
            await self.send_jumuah(interaction.guild, gs)
        await interaction.response.send_message("Sent.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(IslamicReminders(bot))