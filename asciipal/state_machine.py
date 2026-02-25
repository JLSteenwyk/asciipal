from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from asciipal.activity_tracker import ActivitySnapshot
from asciipal.config import Config

State = str


@dataclass(slots=True)
class TransitionResult:
    state: State
    changed: bool


class StateMachine:
    def __init__(self, config: Config, cooldown_seconds: float | None = None) -> None:
        self.config = config
        self.cooldown_seconds = config.state_cooldown_seconds if cooldown_seconds is None else cooldown_seconds
        self.state: State = "idle"
        self._last_transition = monotonic() - self.cooldown_seconds
        self._sweating: bool = False

    def set_sweating(self, val: bool) -> None:
        self._sweating = val

    def update(self, snapshot: ActivitySnapshot, now: float | None = None) -> TransitionResult:
        ts = monotonic() if now is None else now
        target = self._derive_target_state(snapshot)
        if target == self.state:
            return TransitionResult(self.state, changed=False)
        elapsed = ts - self._last_transition
        if elapsed < 0:
            elapsed = self.cooldown_seconds
        if elapsed < self.cooldown_seconds:
            return TransitionResult(self.state, changed=False)
        self.state = target
        self._last_transition = ts
        return TransitionResult(self.state, changed=True)

    def force_state(self, state: State, now: float | None = None) -> None:
        self.state = state
        self._last_transition = monotonic() if now is None else now

    def _derive_target_state(self, snapshot: ActivitySnapshot) -> State:
        if snapshot.seconds_since_input >= self.config.sleep_timeout_seconds:
            return "sleeping"
        if snapshot.seconds_since_input >= self.config.idle_timeout_seconds:
            return "idle"
        if snapshot.click_rate >= self.config.rage_click_threshold:
            return "alarmed"
        if snapshot.mouse_speed >= self.config.dizzy_mouse_speed:
            return "dizzy"
        if self._sweating:
            return "sweating"
        if snapshot.typing_wpm >= self.config.typing_fast_wpm:
            return "excited"
        if snapshot.total_active_seconds >= self.config.cheering_after_minutes * 60:
            return "cheering"
        if snapshot.typing_wpm > 1 or snapshot.mouse_speed > 10:
            return "watching"
        return "idle"
