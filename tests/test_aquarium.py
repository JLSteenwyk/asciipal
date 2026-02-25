from __future__ import annotations

from asciipal.activity_tracker import ActivityTotals
from asciipal.aquarium import (
    _bird_count,
    _plant_level,
    _scatter_birds,
    _build_plants,
    build_aquarium_scene,
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


class TestBirdCount:
    def test_zero_activity(self) -> None:
        assert _bird_count(_totals()) == 0

    def test_keypresses_add_birds(self) -> None:
        assert _bird_count(_totals(keypresses=100)) == 1
        assert _bird_count(_totals(keypresses=200)) == 2
        assert _bird_count(_totals(keypresses=300)) == 3
        # caps at 3 from keypresses alone
        assert _bird_count(_totals(keypresses=1000)) == 3

    def test_clicks_add_birds(self) -> None:
        assert _bird_count(_totals(clicks=50)) == 1
        assert _bird_count(_totals(clicks=150)) == 3
        assert _bird_count(_totals(clicks=9999)) == 3

    def test_mouse_adds_birds(self) -> None:
        assert _bird_count(_totals(mouse_distance=10000)) == 1
        assert _bird_count(_totals(mouse_distance=20000)) == 2
        assert _bird_count(_totals(mouse_distance=999999)) == 2

    def test_combined_caps_at_eight(self) -> None:
        t = _totals(keypresses=1000, clicks=9999, mouse_distance=999999)
        assert _bird_count(t) == 8


class TestPlantLevel:
    def test_no_plants_early(self) -> None:
        assert _plant_level(_totals(active_seconds=30)) == 0

    def test_plant_thresholds(self) -> None:
        assert _plant_level(_totals(active_seconds=60)) == 1
        assert _plant_level(_totals(active_seconds=180)) == 2
        assert _plant_level(_totals(active_seconds=300)) == 3
        assert _plant_level(_totals(active_seconds=600)) == 4
        assert _plant_level(_totals(active_seconds=99999)) == 4


class TestScatter:
    def test_bird_line_has_correct_width(self) -> None:
        line = _scatter_birds(3, 34, frame=0)
        assert len(line) == 34

    def test_bird_contains_sprites(self) -> None:
        line = _scatter_birds(2, 34, frame=0)
        assert "\\v/" in line or "/^\\" in line

    def test_bird_zero_returns_empty(self) -> None:
        assert _scatter_birds(0, 34, frame=0) == ""

    def test_plants_returns_list(self) -> None:
        lines = _build_plants(2, 34, frame=0)
        assert isinstance(lines, list)
        assert len(lines) == 2

    def test_plants_lines_have_correct_width(self) -> None:
        lines = _build_plants(3, 34, frame=0)
        for line in lines:
            assert len(line) == 34

    def test_plants_contain_weed_chars(self) -> None:
        lines = _build_plants(2, 34, frame=0)
        combined = "".join(lines)
        assert any(ch in combined for ch in "()")

    def test_plants_zero_returns_empty(self) -> None:
        assert _build_plants(0, 34, frame=0) == []

    def test_plants_height_matches_level(self) -> None:
        for level in range(1, 5):
            lines = _build_plants(level, 34, frame=0)
            assert len(lines) == level


class TestBuildScene:
    def test_empty_activity_returns_empty(self) -> None:
        birds, plants = build_aquarium_scene(_totals(), 34, frame=0)
        assert birds == []
        assert plants == []

    def test_active_session_produces_birds(self) -> None:
        t = _totals(keypresses=300, clicks=100, active_seconds=300)
        birds, plants = build_aquarium_scene(t, 34, frame=0)
        assert len(birds) >= 1  # birds above

    def test_active_session_produces_plants(self) -> None:
        t = _totals(keypresses=300, clicks=100, active_seconds=300)
        birds, plants = build_aquarium_scene(t, 34, frame=0)
        assert len(plants) >= 1  # plants at ground level

    def test_bird_lines_fit_content_width(self) -> None:
        t = _totals(keypresses=500, clicks=200, mouse_distance=30000, active_seconds=700)
        birds, plants = build_aquarium_scene(t, 34, frame=0)
        for line in birds:
            assert len(line) == 34

    def test_plant_lines_fit_content_width(self) -> None:
        t = _totals(keypresses=500, clicks=200, mouse_distance=30000, active_seconds=700)
        birds, plants = build_aquarium_scene(t, 34, frame=0)
        for line in plants:
            assert len(line) == 34

    def test_animation_varies_between_frames(self) -> None:
        t = _totals(keypresses=300, clicks=100, active_seconds=300)
        b0, _ = build_aquarium_scene(t, 34, frame=0)
        b1, _ = build_aquarium_scene(t, 34, frame=1)
        # Bird wing direction flips between frames
        assert b0 != b1
