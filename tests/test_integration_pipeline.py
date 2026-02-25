from __future__ import annotations

from asciipal.activity_tracker import ActivityTracker
from asciipal.config import Config, DEFAULT_CONFIG
from asciipal.state_machine import StateMachine


def test_pipeline_transitions_from_excited_to_sleeping() -> None:
    cfg = Config.from_dict(dict(DEFAULT_CONFIG))
    tracker = ActivityTracker(window_seconds=10)
    tracker.session_start_time = 0
    tracker.last_input_time = 0
    machine = StateMachine(cfg, cooldown_seconds=0)

    for ts in [1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4]:
        tracker.record_keypress(ts)
    active_state = machine.update(tracker.snapshot(3), now=3).state
    assert active_state in {"excited", "watching"}

    sleeping_state = machine.update(tracker.snapshot(200), now=200).state
    assert sleeping_state == "sleeping"

