from __future__ import annotations

from asciipal.activity_tracker import ActivityTracker


def test_activity_snapshot_calculates_metrics() -> None:
    tracker = ActivityTracker(window_seconds=10)
    tracker.session_start_time = 0.0
    tracker.last_input_time = 0.0

    for ts in [1, 2, 3, 4, 5]:
        tracker.record_keypress(ts)
    for ts in [2, 3, 4]:
        tracker.record_click(ts)
    tracker.record_mouse_move(10, 0, 4)
    tracker.record_mouse_move(0, 10, 5)

    snap = tracker.snapshot(6)
    assert snap.typing_wpm > 0
    assert snap.click_rate > 0
    assert snap.mouse_speed > 0
    assert snap.seconds_since_input == 1
    assert snap.total_active_seconds == 6


def test_activity_totals_track_counts() -> None:
    tracker = ActivityTracker(window_seconds=10)
    tracker.session_start_time = 0.0
    tracker.record_keypress(1)
    tracker.record_click(2)
    tracker.record_mouse_move(3, 4, 3)
    totals = tracker.totals(10)
    assert totals.total_keypresses == 1
    assert totals.total_clicks == 1
    assert totals.total_mouse_distance == 5
    assert totals.total_active_seconds == 10
