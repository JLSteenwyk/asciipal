from __future__ import annotations

from asciipal.activity_tracker import ActivityTotals
from asciipal.app import _merge_plants
from asciipal.aquarium import (
    PLANT_THRESHOLDS,
    _plant_level,
    _plant_progress,
    _build_progress_bar,
    _build_plants,
    _plant_dimensions,
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


class TestPlantLevel:
    def test_no_plants_early(self) -> None:
        assert _plant_level(_totals(active_seconds=100)) == 0

    def test_plant_thresholds(self) -> None:
        assert _plant_level(_totals(active_seconds=300)) == 1
        assert _plant_level(_totals(active_seconds=600)) == 2
        assert _plant_level(_totals(active_seconds=1200)) == 3
        assert _plant_level(_totals(active_seconds=1800)) == 4
        assert _plant_level(_totals(active_seconds=2700)) == 5
        assert _plant_level(_totals(active_seconds=3600)) == 6
        assert _plant_level(_totals(active_seconds=5400)) == 7
        assert _plant_level(_totals(active_seconds=7200)) == 8
        assert _plant_level(_totals(active_seconds=99999)) == 8


class TestPlantProgress:
    def test_zero_activity(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=0))
        assert level == 0
        assert frac == 0.0

    def test_midway_level_zero(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=150))
        assert level == 0
        assert frac == 0.5

    def test_boundary_level_one(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=300))
        assert level == 1
        assert frac == 0.0

    def test_midway_level_one(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=450))
        assert level == 1
        assert frac == 0.5

    def test_boundary_max(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=7200))
        assert level == 8
        assert frac == 1.0

    def test_beyond_max(self) -> None:
        level, frac = _plant_progress(_totals(active_seconds=99999))
        assert level == 8
        assert frac == 1.0


class TestProgressBar:
    def test_empty_bar(self) -> None:
        bar = _build_progress_bar(0, 0.0, 30)
        assert bar.startswith("[")
        assert "🌿 0/8" in bar
        assert len(bar) == 30

    def test_half_filled(self) -> None:
        bar = _build_progress_bar(1, 0.5, 30)
        assert "█" in bar
        assert "░" in bar
        assert "🌿 1/8" in bar
        assert len(bar) == 30

    def test_max_level(self) -> None:
        bar = _build_progress_bar(8, 1.0, 30)
        assert "MAX" in bar
        assert len(bar) == 30

    def test_width_fitting(self) -> None:
        for w in [20, 30, 40, 50]:
            bar = _build_progress_bar(2, 0.3, w)
            assert len(bar) == w

    def test_full_bar_at_boundary(self) -> None:
        bar = _build_progress_bar(3, 1.0, 30)
        assert "🌿 3/8" in bar
        inner_start = bar.index("[") + 1
        inner_end = bar.index("]")
        inner = bar[inner_start:inner_end]
        assert inner == "█" * len(inner)


class TestBuildPlants:
    def test_plants_returns_list(self) -> None:
        lines = _build_plants(2, 34, frame=0)
        assert isinstance(lines, list)
        # Level 2 = (1, 2) → height 2
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

    def test_staggered_dimensions(self) -> None:
        # Level 1 = (1 col, 1 row)
        lines = _build_plants(1, 34, frame=0)
        assert len(lines) == 1

        # Level 2 = (1 col, 2 rows)
        lines = _build_plants(2, 34, frame=0)
        assert len(lines) == 2

        # Level 3 = (2 cols, 2 rows)
        lines = _build_plants(3, 34, frame=0)
        assert len(lines) == 2

        # Level 4 = (2 cols, 3 rows)
        lines = _build_plants(4, 34, frame=0)
        assert len(lines) == 3

        # Level 8 = (5 cols, 5 rows)
        lines = _build_plants(8, 34, frame=0)
        assert len(lines) == 5

    def test_plant_dimensions_mapping(self) -> None:
        assert _plant_dimensions(0) == (0, 0)
        assert _plant_dimensions(1) == (1, 1)
        assert _plant_dimensions(2) == (1, 2)
        assert _plant_dimensions(3) == (2, 2)
        assert _plant_dimensions(4) == (2, 3)
        assert _plant_dimensions(5) == (3, 3)
        assert _plant_dimensions(6) == (3, 4)
        assert _plant_dimensions(7) == (4, 4)
        assert _plant_dimensions(8) == (5, 5)


class TestMergePlants:
    def test_no_plants_returns_centered_art(self) -> None:
        lines = _merge_plants("AB", [], 10)
        assert len(lines) == 1
        assert "AB" in lines[0]
        assert len(lines[0]) == 10

    def test_plants_fill_spaces_around_art(self) -> None:
        # Art is narrow and centered; plants should fill empty positions
        art = "XX"
        plant_lines = ["(  )  (  )"]  # 10 chars with parens at edges
        merged = _merge_plants(art, plant_lines, 10)
        assert len(merged) == 1
        combined = merged[0]
        assert "XX" in combined
        assert "(" in combined  # plant chars present

    def test_plants_do_not_overwrite_art(self) -> None:
        art = "ABCDEFGHIJ"  # fills entire width
        plant_lines = ["(((((((((("]
        merged = _merge_plants(art, plant_lines, 10)
        assert merged[0] == "ABCDEFGHIJ"

    def test_plants_align_to_bottom(self) -> None:
        art = "A\nB\nC"  # 3 lines
        plant_lines = ["X"]  # 1 row of plants
        merged = _merge_plants(art, plant_lines, 5)
        assert len(merged) == 3
        # Only the last line should have plant chars
        assert "X" not in merged[0]
        assert "X" not in merged[1]

    def test_taller_plants_extend_above_art(self) -> None:
        art = "X"  # 1 line
        plant_lines = [") (", "( )"]  # 2 rows
        merged = _merge_plants(art, plant_lines, 5)
        assert len(merged) == 2  # extended to fit plants


class TestBuildScene:
    def test_empty_activity_returns_progress_no_plants(self) -> None:
        progress, plants = build_aquarium_scene(_totals(), 34, frame=0)
        assert len(progress) == 1  # progress bar always shown
        assert plants == []

    def test_active_session_produces_plants(self) -> None:
        t = _totals(keypresses=300, clicks=100, active_seconds=300)
        progress, plants = build_aquarium_scene(t, 34, frame=0)
        assert len(progress) == 1
        assert len(plants) >= 1

    def test_progress_line_fits_content_width(self) -> None:
        t = _totals(active_seconds=100)
        progress, _ = build_aquarium_scene(t, 34, frame=0)
        assert len(progress[0]) == 34

    def test_plant_lines_fit_content_width(self) -> None:
        t = _totals(keypresses=500, clicks=200, mouse_distance=30000, active_seconds=7200)
        _, plants = build_aquarium_scene(t, 34, frame=0)
        for line in plants:
            assert len(line) == 34

    def test_progress_bar_shows_max_at_max_level(self) -> None:
        t = _totals(active_seconds=7200)
        progress, _ = build_aquarium_scene(t, 34, frame=0)
        assert "MAX" in progress[0]
