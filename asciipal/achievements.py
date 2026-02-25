from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from asciipal.activity_tracker import ActivityTotals


KEYPRESS_MILESTONES = [1_000, 5_000, 10_000, 50_000, 100_000]
ACTIVE_HOUR_MILESTONES = [1, 5, 10, 50, 100]
MOUSE_KM_MILESTONES = [10, 50, 100]
UNITS_PER_KM = 100_000

DEFAULT_STATS_PATH = Path("~/.asciipal/stats.json").expanduser()


@dataclass
class StatsData:
    lifetime_keypresses: int = 0
    lifetime_clicks: int = 0
    lifetime_mouse_distance: float = 0.0
    lifetime_active_seconds: float = 0.0
    daily_breaks: dict[str, int] = field(default_factory=dict)
    break_streak: int = 0
    unlocked: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lifetime_keypresses": self.lifetime_keypresses,
            "lifetime_clicks": self.lifetime_clicks,
            "lifetime_mouse_distance": self.lifetime_mouse_distance,
            "lifetime_active_seconds": self.lifetime_active_seconds,
            "daily_breaks": dict(self.daily_breaks),
            "break_streak": self.break_streak,
            "unlocked": list(self.unlocked),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatsData:
        return cls(
            lifetime_keypresses=int(data.get("lifetime_keypresses", 0)),
            lifetime_clicks=int(data.get("lifetime_clicks", 0)),
            lifetime_mouse_distance=float(data.get("lifetime_mouse_distance", 0.0)),
            lifetime_active_seconds=float(data.get("lifetime_active_seconds", 0.0)),
            daily_breaks=dict(data.get("daily_breaks", {})),
            break_streak=int(data.get("break_streak", 0)),
            unlocked=list(data.get("unlocked", [])),
        )


class AchievementManager:
    def __init__(self, stats_path: Path | None = None) -> None:
        self._path = stats_path if stats_path is not None else DEFAULT_STATS_PATH
        self._stats = self._load()
        self._base_keypresses = self._stats.lifetime_keypresses
        self._base_clicks = self._stats.lifetime_clicks
        self._base_mouse_distance = self._stats.lifetime_mouse_distance
        self._base_active_seconds = self._stats.lifetime_active_seconds
        self._display_line: str | None = None
        self._display_ticks_remaining = 0

    def _load(self) -> StatsData:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return StatsData.from_dict(data)
        except Exception:
            return StatsData()

    def update(self, totals: ActivityTotals, breaks_taken: int) -> str | None:
        self._stats.lifetime_keypresses = self._base_keypresses + totals.total_keypresses
        self._stats.lifetime_clicks = self._base_clicks + totals.total_clicks
        self._stats.lifetime_mouse_distance = self._base_mouse_distance + totals.total_mouse_distance
        self._stats.lifetime_active_seconds = self._base_active_seconds + totals.total_active_seconds

        today = date.today().isoformat()
        self._stats.daily_breaks[today] = breaks_taken

        new_achievement = self._check_milestones()
        if new_achievement is not None:
            self._display_line = new_achievement
            self._display_ticks_remaining = 12

        if self._display_ticks_remaining > 0:
            self._display_ticks_remaining -= 1
            return self._display_line
        self._display_line = None
        return None

    def _check_milestones(self) -> str | None:
        for threshold in KEYPRESS_MILESTONES:
            aid = f"keypresses_{threshold}"
            if aid not in self._stats.unlocked and self._stats.lifetime_keypresses >= threshold:
                self._stats.unlocked.append(aid)
                return f"★ Keypresses: {threshold:,}! ★"

        hours = self._stats.lifetime_active_seconds / 3600
        for threshold in ACTIVE_HOUR_MILESTONES:
            aid = f"active_hours_{threshold}"
            if aid not in self._stats.unlocked and hours >= threshold:
                self._stats.unlocked.append(aid)
                return f"★ Active Time: {threshold}h! ★"

        km = self._stats.lifetime_mouse_distance / UNITS_PER_KM
        for threshold in MOUSE_KM_MILESTONES:
            aid = f"mouse_km_{threshold}"
            if aid not in self._stats.unlocked and km >= threshold:
                self._stats.unlocked.append(aid)
                return f"★ Mouse Distance: {threshold}km! ★"

        return None

    def update_break_streak(self) -> None:
        sorted_dates = sorted(self._stats.daily_breaks.keys(), reverse=True)
        streak = 0
        prev = None
        for iso_date in sorted_dates:
            if self._stats.daily_breaks[iso_date] < 1:
                if prev is None:
                    continue
                break
            d = date.fromisoformat(iso_date)
            if prev is None:
                streak = 1
                prev = d
            else:
                delta = (prev - d).days
                if delta == 1:
                    streak += 1
                    prev = d
                else:
                    break
        self._stats.break_streak = streak

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._stats.to_dict(), indent=2),
            encoding="utf-8",
        )

    def format_stats_report(self) -> str:
        s = self._stats
        hours = s.lifetime_active_seconds / 3600
        km = s.lifetime_mouse_distance / UNITS_PER_KM
        lines = [
            "AsciiPal Lifetime Stats",
            f"  Keypresses:      {s.lifetime_keypresses:,}",
            f"  Clicks:          {s.lifetime_clicks:,}",
            f"  Mouse Distance:  {km:.1f} km",
            f"  Active Time:     {hours:.1f} h",
            f"  Break Streak:    {s.break_streak} day(s)",
            "",
            "Achievements:",
        ]
        if s.unlocked:
            for uid in s.unlocked:
                lines.append(f"  ★ {uid}")
        else:
            lines.append("  (none yet)")
        return "\n".join(lines)
