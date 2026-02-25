from __future__ import annotations

import json
from pathlib import Path

import pytest

from asciipal.achievements import AchievementManager, StatsData
from asciipal.activity_tracker import ActivityTotals
from asciipal.app import parse_args, run


class TestStatsDataRoundTrip:
    def test_round_trip(self) -> None:
        original = StatsData(
            lifetime_keypresses=123,
            lifetime_clicks=45,
            lifetime_mouse_distance=6789.0,
            lifetime_active_seconds=3600.0,
            daily_breaks={"2025-01-01": 2, "2025-01-02": 3},
            break_streak=2,
            unlocked=["keypresses_1000", "active_hours_1"],
        )
        d = original.to_dict()
        restored = StatsData.from_dict(d)
        assert restored.lifetime_keypresses == original.lifetime_keypresses
        assert restored.lifetime_clicks == original.lifetime_clicks
        assert restored.lifetime_mouse_distance == original.lifetime_mouse_distance
        assert restored.lifetime_active_seconds == original.lifetime_active_seconds
        assert restored.daily_breaks == original.daily_breaks
        assert restored.break_streak == original.break_streak
        assert restored.unlocked == original.unlocked


class TestLoadMissingFile:
    def test_load_missing_file(self, tmp_path: Path) -> None:
        manager = AchievementManager(stats_path=tmp_path / "nonexistent.json")
        report = manager.format_stats_report()
        assert "Keypresses" in report


class TestLoadCorruptFile:
    def test_load_corrupt_file(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("not valid json!!!", encoding="utf-8")
        manager = AchievementManager(stats_path=corrupt)
        report = manager.format_stats_report()
        assert "Keypresses" in report


class TestSaveAndLoad:
    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        manager = AchievementManager(stats_path=path)
        totals = ActivityTotals(
            total_keypresses=500,
            total_clicks=100,
            total_mouse_distance=1000.0,
            total_active_seconds=300.0,
        )
        manager.update(totals, 1)
        manager.save()

        manager2 = AchievementManager(stats_path=path)
        assert manager2._stats.lifetime_keypresses == 500


class TestKeypressMilestone:
    def test_keypress_milestone(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        # Pre-seed with 999 keypresses
        seed = StatsData(lifetime_keypresses=999)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")

        manager = AchievementManager(stats_path=path)
        totals = ActivityTotals(
            total_keypresses=2,
            total_clicks=0,
            total_mouse_distance=0.0,
            total_active_seconds=0.0,
        )
        result = manager.update(totals, 0)
        assert result is not None
        assert "1,000" in result or "keypresses" in result
        assert "keypresses_1000" in manager._stats.unlocked


class TestMilestoneNoDuplicate:
    def test_no_duplicate(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(lifetime_keypresses=999)
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")

        manager = AchievementManager(stats_path=path)
        totals = ActivityTotals(
            total_keypresses=2,
            total_clicks=0,
            total_mouse_distance=0.0,
            total_active_seconds=0.0,
        )
        result1 = manager.update(totals, 0)
        assert result1 is not None
        # Drain display ticks
        for _ in range(12):
            manager.update(totals, 0)
        result2 = manager.update(totals, 0)
        assert result2 is None


class TestActiveTimeMilestone:
    def test_active_time_milestone(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        manager = AchievementManager(stats_path=path)
        totals = ActivityTotals(
            total_keypresses=0,
            total_clicks=0,
            total_mouse_distance=0.0,
            total_active_seconds=3601.0,  # > 1 hour
        )
        result = manager.update(totals, 0)
        assert result is not None
        assert "1h" in result
        assert "active_hours_1" in manager._stats.unlocked


class TestDisplayDuration:
    def test_display_persists_12_ticks(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(lifetime_keypresses=999)
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")

        manager = AchievementManager(stats_path=path)
        totals = ActivityTotals(
            total_keypresses=2,
            total_clicks=0,
            total_mouse_distance=0.0,
            total_active_seconds=0.0,
        )
        # First call triggers milestone
        result = manager.update(totals, 0)
        assert result is not None
        # Next 11 calls should still show the line (total 12 ticks)
        for i in range(11):
            result = manager.update(totals, 0)
            assert result is not None, f"Expected display on tick {i+2}"
        # 13th call should return None
        result = manager.update(totals, 0)
        assert result is None


class TestBreakStreakConsecutive:
    def test_consecutive_days(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(
            daily_breaks={
                "2025-01-01": 1,
                "2025-01-02": 2,
                "2025-01-03": 1,
            }
        )
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_break_streak()
        assert manager._stats.break_streak == 3


class TestBreakStreakGap:
    def test_gap_resets(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(
            daily_breaks={
                "2025-01-01": 1,
                "2025-01-02": 1,
                # gap on 2025-01-03
                "2025-01-04": 1,
                "2025-01-05": 1,
            }
        )
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_break_streak()
        assert manager._stats.break_streak == 2


class TestUseStreak:
    def test_consecutive_days(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(
            daily_active={
                "2025-01-01": 400.0,
                "2025-01-02": 500.0,
                "2025-01-03": 300.0,
            }
        )
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_use_streak(0)
        assert manager._stats.use_streak == 3

    def test_gap_resets_streak(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(
            daily_active={
                "2025-01-01": 400.0,
                "2025-01-02": 400.0,
                # gap on 2025-01-03
                "2025-01-04": 400.0,
                "2025-01-05": 400.0,
            }
        )
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_use_streak(0)
        assert manager._stats.use_streak == 2

    def test_below_threshold_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(
            daily_active={
                "2025-01-01": 400.0,
                "2025-01-02": 100.0,  # below 300s threshold
                "2025-01-03": 400.0,
            }
        )
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_use_streak(0)
        # Day 02 doesn't count, so streak from day 03 only
        assert manager._stats.use_streak == 1

    def test_streak_milestone_unlocks(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        daily = {}
        for i in range(1, 8):
            daily[f"2025-01-{i:02d}"] = 400.0
        seed = StatsData(daily_active=daily)
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        manager.update_use_streak(0)
        assert "use_streak_3" in manager._stats.unlocked
        assert "use_streak_7" in manager._stats.unlocked

    def test_streak_line_format(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(use_streak=5)
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        line = manager.streak_line()
        assert "5" in line
        assert "days" in line


class TestMonthlyActive:
    def test_monthly_active_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        seed = StatsData(monthly_active={"2025-01": 3600.0})
        path.write_text(json.dumps(seed.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        assert manager._stats.monthly_active["2025-01"] == 3600.0

    def test_daily_active_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        original = StatsData(
            daily_active={"2025-01-01": 500.0},
            use_streak=3,
            monthly_active={"2025-01": 7200.0},
        )
        path.write_text(json.dumps(original.to_dict()), encoding="utf-8")
        manager = AchievementManager(stats_path=path)
        assert manager._stats.daily_active == original.daily_active
        assert manager._stats.use_streak == 3
        assert manager._stats.monthly_active == original.monthly_active


class TestFormatStatsReport:
    def test_contains_expected_labels(self, tmp_path: Path) -> None:
        path = tmp_path / "stats.json"
        manager = AchievementManager(stats_path=path)
        report = manager.format_stats_report()
        assert "Keypresses" in report
        assert "Clicks" in report
        assert "Mouse Distance" in report
        assert "Active Time" in report
        assert "Break Streak" in report
        assert "Achievements" in report


class TestStatsCLIFlag:
    def test_parse_args_stats(self) -> None:
        args = parse_args(["--stats"])
        assert args.stats is True

    def test_run_stats_prints_report(self, capsys) -> None:
        code = run(["--stats"])
        captured = capsys.readouterr()
        assert code == 0
        assert "Lifetime Stats" in captured.out
