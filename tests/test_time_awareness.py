from __future__ import annotations

from datetime import datetime

import pytest

from asciipal.config import Config, DEFAULT_CONFIG, _deep_merge
from asciipal.time_awareness import (
    TIME_PERIODS,
    TimeAwarenessManager,
    get_period,
)


def _make_config(**overrides) -> Config:
    data = _deep_merge(DEFAULT_CONFIG, overrides)
    return Config.from_dict(data)


class TestGetPeriod:
    @pytest.mark.parametrize(
        "hour,expected",
        [
            (5, "night"),
            (6, "morning"),
            (11, "morning"),
            (12, "afternoon"),
            (16, "afternoon"),
            (17, "evening"),
            (20, "evening"),
            (21, "night"),
            (0, "night"),
        ],
    )
    def test_get_period(self, hour: int, expected: str) -> None:
        assert get_period(hour) == expected


class TestEffectFrames:
    @pytest.mark.parametrize("period", list(TIME_PERIODS.keys()))
    def test_two_frames_each(self, period: str) -> None:
        effect = TIME_PERIODS[period]
        assert len(effect.above) == 2
        assert len(effect.below) == 2


class TestWidthConsistency:
    @pytest.mark.parametrize("period", list(TIME_PERIODS.keys()))
    def test_above_frames_same_width(self, period: str) -> None:
        effect = TIME_PERIODS[period]
        widths = [len(f) for f in effect.above]
        assert len(set(widths)) == 1, f"{period} above frames have inconsistent widths: {widths}"

    @pytest.mark.parametrize("period", list(TIME_PERIODS.keys()))
    def test_below_frames_same_width(self, period: str) -> None:
        effect = TIME_PERIODS[period]
        widths = [len(f) for f in effect.below]
        assert len(set(widths)) == 1, f"{period} below frames have inconsistent widths: {widths}"


class TestSkyCharacters:
    def test_morning_has_sun_chars(self) -> None:
        effect = TIME_PERIODS["morning"]
        combined = " ".join(effect.above)
        assert "☀" in combined
        assert "○" in combined

    def test_evening_has_half_moon(self) -> None:
        effect = TIME_PERIODS["evening"]
        combined = " ".join(effect.above)
        assert "◐" in combined

    def test_night_has_stars_and_crescent(self) -> None:
        effect = TIME_PERIODS["night"]
        combined = " ".join(effect.above)
        assert "★" in combined
        assert "✦" in combined
        assert "☾" in combined


class TestTimeAwarenessManager:
    def test_disabled_returns_none(self) -> None:
        config = _make_config(time_awareness_enabled=False)
        manager = TimeAwarenessManager(config)
        assert manager.current_effect(0) is None
        assert manager.current_effect(1) is None

    def test_enabled_with_specific_time(self) -> None:
        config = _make_config(time_awareness_enabled=True)
        manager = TimeAwarenessManager(config)
        result = manager.current_effect(0, now=datetime(2025, 1, 1, 8, 0))
        assert result is not None
        above, below = result
        assert above == TIME_PERIODS["morning"].above[0]

    def test_afternoon_returns_empty_strings(self) -> None:
        config = _make_config(time_awareness_enabled=True)
        manager = TimeAwarenessManager(config)
        result = manager.current_effect(0, now=datetime(2025, 1, 1, 14, 0))
        assert result is not None
        above, below = result
        assert above == ""
        assert below == ""
