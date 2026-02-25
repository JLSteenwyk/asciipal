from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from asciipal.config import Config


@dataclass(slots=True)
class TimeOfDayEffect:
    above: list[str]
    below: list[str]


TIME_PERIODS: dict[str, TimeOfDayEffect] = {
    "morning": TimeOfDayEffect(
        above=["☀ ~ ☀ ~ ☀", "~ ☀ ~ ☀ ~"],
        below=["", ""],
    ),
    "afternoon": TimeOfDayEffect(
        above=["", ""],
        below=["", ""],
    ),
    "evening": TimeOfDayEffect(
        above=["☽ . ☽ . ☽", ". ☽ . ☽ ."],
        below=["~ . ~ . ~", ". ~ . ~ ."],
    ),
    "night": TimeOfDayEffect(
        above=["★ . ★ . ★", ". ★ . ★ ."],
        below=["z z z z z", " z z z z "],
    ),
}


def get_period(hour: int) -> str:
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


class TimeAwarenessManager:
    def __init__(self, config: Config) -> None:
        self._config = config

    def current_effect(self, frame: int, now: datetime | None = None) -> tuple[str, str] | None:
        if not self._config.time_awareness_enabled:
            return None
        dt = now if now is not None else datetime.now()
        period = get_period(dt.hour)
        effect = TIME_PERIODS[period]
        idx = frame % 2
        return (effect.above[idx], effect.below[idx])
