from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from asciipal.activity_tracker import ActivitySnapshot
from asciipal.config import Config


@dataclass(slots=True)
class BreakStatus:
    should_break: bool
    stage: str
    seconds_until_break: float
    break_seconds_remaining: float = 0.0


class BreakManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._last_break_started: float | None = None
        self._active_start = monotonic()
        self._on_break = False
        self.breaks_taken = 0
        self.total_break_seconds = 0.0

    def update(self, snapshot: ActivitySnapshot, now: float | None = None) -> BreakStatus:
        ts = monotonic() if now is None else now
        if self._on_break:
            assert self._last_break_started is not None
            elapsed_break = ts - self._last_break_started
            if elapsed_break >= self._break_duration_seconds:
                self.breaks_taken += 1
                self.total_break_seconds += self._break_duration_seconds
                self._on_break = False
                self._active_start = ts
                return BreakStatus(False, "none", self._interval_seconds, 0.0)
            remaining_break = max(self._break_duration_seconds - elapsed_break, 0.0)
            return BreakStatus(False, "on_break", self._interval_seconds, remaining_break)

        active_elapsed = ts - self._active_start
        remaining = self._interval_seconds - active_elapsed
        is_idle = snapshot.seconds_since_input >= self.config.idle_timeout_seconds

        if remaining <= 0 and is_idle:
            self.start_break(ts)
            return BreakStatus(False, "on_break", self._interval_seconds, self._break_duration_seconds)

        if is_idle and not self.config.pomodoro_mode:
            self._active_start = ts
            return BreakStatus(False, "none", self._interval_seconds, 0.0)

        if remaining > 0:
            stage = "suggestion" if remaining <= 5 * 60 else "none"
            return BreakStatus(False, stage, max(remaining, 0.0), 0.0)

        # Break due; escalation based on overtime.
        overtime = abs(remaining)
        if overtime < 2 * 60:
            stage = "suggestion"
        elif overtime < 5 * 60:
            stage = "insistence"
        else:
            stage = "tantrum"
        return BreakStatus(True, stage, 0.0, 0.0)

    def start_break(self, now: float | None = None) -> None:
        self._on_break = True
        self._last_break_started = monotonic() if now is None else now

    def force_break(self, now: float | None = None) -> None:
        if not self._on_break:
            self.start_break(now)

    def skip_break(self, now: float | None = None) -> None:
        ts = monotonic() if now is None else now
        self._on_break = False
        self._active_start = ts

    @property
    def _interval_seconds(self) -> float:
        if self.config.pomodoro_mode:
            return self.config.pomodoro_work_minutes * 60
        return self.config.break_interval_minutes * 60

    @property
    def _break_duration_seconds(self) -> float:
        if self.config.pomodoro_mode:
            return self.config.pomodoro_break_minutes * 60
        return self.config.break_duration_minutes * 60
