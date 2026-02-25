from __future__ import annotations

import random

from asciipal.activity_tracker import ActivityTotals
from asciipal.effects import (
    BubbleSystem,
    FireflySystem,
    CreatureSystem,
    EffectsManager,
)


def _totals(
    keypresses: int = 0,
    clicks: int = 0,
    mouse_distance: float = 0.0,
    active_seconds: float = 0.0,
) -> ActivityTotals:
    return ActivityTotals(
        total_keypresses=keypresses,
        total_clicks=clicks,
        total_mouse_distance=mouse_distance,
        total_active_seconds=active_seconds,
    )


class TestBubbleSystem:
    def test_no_bubbles_without_activity(self) -> None:
        system = BubbleSystem(random.Random(42))
        particles = system.update(_totals(), 34, 10, frame=0)
        assert particles == []

    def test_bubbles_spawn_with_activity(self) -> None:
        system = BubbleSystem(random.Random(42))
        totals = _totals(keypresses=500, clicks=200, active_seconds=600)
        any_spawned = False
        for frame in range(50):
            if system.update(totals, 34, 10, frame=frame):
                any_spawned = True
                break
        assert any_spawned

    def test_bubbles_stay_in_bounds(self) -> None:
        system = BubbleSystem(random.Random(42))
        totals = _totals(keypresses=1000, clicks=500, active_seconds=600)
        for frame in range(100):
            for p in system.update(totals, 34, 10, frame=frame):
                assert 0 <= p.x < 34
                assert 0 <= p.y < 10

    def test_bubbles_cap_at_eight(self) -> None:
        system = BubbleSystem(random.Random(42))
        totals = _totals(keypresses=9999, clicks=9999, active_seconds=9999)
        for frame in range(200):
            assert len(system.update(totals, 34, 10, frame=frame)) <= 8

    def test_bubbles_eventually_disappear(self) -> None:
        system = BubbleSystem(random.Random(42))
        active = _totals(keypresses=1000, active_seconds=600)
        # Spawn some bubbles
        for frame in range(30):
            system.update(active, 34, 10, frame=frame)
        # Stop spawning by using zero activity; existing bubbles should rise off
        idle = _totals()
        for frame in range(30, 50):
            system.update(idle, 34, 10, frame=frame)
        # After 10 more frames (content_h=10), all should be gone
        assert len(system._bubbles) == 0


class TestFireflySystem:
    def test_no_fireflies_during_day(self) -> None:
        system = FireflySystem(random.Random(42))
        assert system.update(False, False, 34, 10, frame=0) == []

    def test_fireflies_appear_at_night(self) -> None:
        system = FireflySystem(random.Random(42))
        system.update(True, False, 34, 10, frame=0)
        assert len(system._fireflies) == 5

    def test_fireflies_appear_during_flow(self) -> None:
        system = FireflySystem(random.Random(42))
        system.update(False, True, 34, 10, frame=0)
        assert len(system._fireflies) == 3

    def test_fireflies_clear_when_inactive(self) -> None:
        system = FireflySystem(random.Random(42))
        system.update(True, False, 34, 10, frame=0)
        assert len(system._fireflies) > 0
        system.update(False, False, 34, 10, frame=1)
        assert len(system._fireflies) == 0

    def test_fireflies_stay_in_bounds(self) -> None:
        system = FireflySystem(random.Random(42))
        for frame in range(100):
            for p in system.update(True, False, 34, 10, frame=frame):
                assert 0 <= p.x < 34
                assert 0 <= p.y < 10

    def test_fireflies_blink(self) -> None:
        system = FireflySystem(random.Random(42))
        counts = set()
        for frame in range(8):
            counts.add(len(system.update(True, False, 34, 10, frame=frame)))
        # Due to blinking, not all frames should have the same visible count
        assert len(counts) > 1


class TestCreatureSystem:
    def test_no_creatures_without_milestones(self) -> None:
        system = CreatureSystem(random.Random(42))
        assert system.update(_totals(), 0, 34, 10, frame=0) == []

    def test_fish_unlocks_at_500_keypresses(self) -> None:
        system = CreatureSystem(random.Random(42))
        system.update(_totals(keypresses=500), 0, 34, 10, frame=0)
        assert "fish" in system._unlocked

    def test_butterfly_unlocks_at_1800_seconds(self) -> None:
        system = CreatureSystem(random.Random(42))
        system.update(_totals(active_seconds=1800), 0, 34, 10, frame=0)
        assert "butterfly" in system._unlocked

    def test_snail_unlocks_at_3_breaks(self) -> None:
        system = CreatureSystem(random.Random(42))
        system.update(_totals(), 3, 34, 10, frame=0)
        assert "snail" in system._unlocked

    def test_no_duplicate_unlocks(self) -> None:
        system = CreatureSystem(random.Random(42))
        totals = _totals(keypresses=500)
        system.update(totals, 0, 34, 10, frame=0)
        system.update(totals, 0, 34, 10, frame=1)
        assert len(system._creatures) == 1

    def test_creatures_stay_in_bounds(self) -> None:
        system = CreatureSystem(random.Random(42))
        totals = _totals(keypresses=9999, active_seconds=9999)
        for frame in range(200):
            for row, col, ch in system.update(totals, 10, 34, 10, frame=frame):
                assert 0 <= row < 10
                assert 0 <= col < 34

    def test_creatures_bounce_at_edges(self) -> None:
        system = CreatureSystem(random.Random(42))
        totals = _totals(keypresses=500)
        for frame in range(200):
            system.update(totals, 0, 20, 10, frame=frame)
        for c in system._creatures:
            sprite_w = len(c.defn.right_sprites[0])
            assert 0 <= c.x <= 20 - sprite_w


class TestEffectsManager:
    def test_returns_overlay_tuples(self) -> None:
        mgr = EffectsManager(random.Random(42))
        totals = _totals(keypresses=1000, active_seconds=600)
        overlays = mgr.update(totals, 0, 34, 10, frame=0, is_night=True)
        assert isinstance(overlays, list)
        for item in overlays:
            assert len(item) == 3
            row, col, ch = item
            assert isinstance(row, int)
            assert isinstance(col, int)
            assert isinstance(ch, str)

    def test_no_overlays_without_triggers(self) -> None:
        mgr = EffectsManager(random.Random(42))
        overlays = mgr.update(_totals(), 0, 34, 10, frame=0)
        assert overlays == []

    def test_overlays_within_bounds(self) -> None:
        mgr = EffectsManager(random.Random(42))
        totals = _totals(keypresses=9999, clicks=9999, active_seconds=9999)
        for frame in range(100):
            for row, col, ch in mgr.update(
                totals, 10, 34, 10, frame=frame, is_night=True, is_flow=True,
            ):
                assert 0 <= row < 10
                assert 0 <= col < 34
