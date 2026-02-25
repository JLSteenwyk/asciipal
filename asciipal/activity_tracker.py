from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import sqrt
from time import monotonic


@dataclass(slots=True)
class ActivitySnapshot:
    typing_wpm: float
    click_rate: float
    mouse_speed: float
    seconds_since_input: float
    total_active_seconds: float


@dataclass(slots=True)
class ActivityTotals:
    total_keypresses: int
    total_clicks: int
    total_mouse_distance: float
    total_active_seconds: float


class ActivityTracker:
    def __init__(self, window_seconds: float = 10.0) -> None:
        self.window_seconds = window_seconds
        self.key_events: deque[float] = deque()
        self.click_events: deque[float] = deque()
        self.mouse_samples: deque[tuple[float, float]] = deque()
        self.last_input_time = monotonic()
        self.session_start_time = monotonic()
        self.total_keypresses = 0
        self.total_clicks = 0
        self.total_mouse_distance = 0.0

    def record_keypress(self, now: float | None = None) -> None:
        ts = monotonic() if now is None else now
        self.last_input_time = ts
        self.key_events.append(ts)
        self.total_keypresses += 1
        self._prune(ts)

    def record_click(self, now: float | None = None) -> None:
        ts = monotonic() if now is None else now
        self.last_input_time = ts
        self.click_events.append(ts)
        self.total_clicks += 1
        self._prune(ts)

    def record_mouse_move(self, dx: float, dy: float, now: float | None = None) -> None:
        ts = monotonic() if now is None else now
        distance = sqrt(dx * dx + dy * dy)
        self.last_input_time = ts
        self.mouse_samples.append((ts, distance))
        self.total_mouse_distance += distance
        self._prune(ts)

    def snapshot(self, now: float | None = None) -> ActivitySnapshot:
        ts = monotonic() if now is None else now
        self._prune(ts)
        elapsed = max(ts - self.session_start_time, 0.0)
        return ActivitySnapshot(
            typing_wpm=self._typing_wpm(ts),
            click_rate=self._click_rate(ts),
            mouse_speed=self._mouse_speed(ts),
            seconds_since_input=max(ts - self.last_input_time, 0.0),
            total_active_seconds=elapsed,
        )

    def totals(self, now: float | None = None) -> ActivityTotals:
        ts = monotonic() if now is None else now
        return ActivityTotals(
            total_keypresses=self.total_keypresses,
            total_clicks=self.total_clicks,
            total_mouse_distance=self.total_mouse_distance,
            total_active_seconds=max(ts - self.session_start_time, 0.0),
        )

    def _typing_wpm(self, now: float) -> float:
        if not self.key_events:
            return 0.0
        effective_window = min(self.window_seconds, max(now - self.key_events[0], 0.001))
        chars_per_min = len(self.key_events) * 60.0 / effective_window
        return chars_per_min / 5.0

    def _click_rate(self, now: float) -> float:
        if not self.click_events:
            return 0.0
        effective_window = min(self.window_seconds, max(now - self.click_events[0], 0.001))
        return len(self.click_events) / effective_window

    def _mouse_speed(self, now: float) -> float:
        if not self.mouse_samples:
            return 0.0
        effective_window = min(self.window_seconds, max(now - self.mouse_samples[0][0], 0.001))
        total_distance = sum(sample[1] for sample in self.mouse_samples)
        return total_distance / effective_window

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self.key_events and self.key_events[0] < cutoff:
            self.key_events.popleft()
        while self.click_events and self.click_events[0] < cutoff:
            self.click_events.popleft()
        while self.mouse_samples and self.mouse_samples[0][0] < cutoff:
            self.mouse_samples.popleft()
