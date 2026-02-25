from __future__ import annotations

from unittest.mock import patch

from asciipal.battery import BatteryManager, BatterySnapshot


class TestBatteryManager:
    def test_available_battery_shows_percent(self) -> None:
        mgr = BatteryManager(poll_interval=0.0)
        snap = BatterySnapshot(percent=87, charging=False, available=True)
        with patch("asciipal.battery._get_battery", return_value=snap):
            line = mgr.format_line()
        assert line is not None
        assert "87%" in line

    def test_charging_shows_icon(self) -> None:
        mgr = BatteryManager(poll_interval=0.0)
        snap = BatterySnapshot(percent=87, charging=True, available=True)
        with patch("asciipal.battery._get_battery", return_value=snap):
            line = mgr.format_line()
        assert line is not None
        assert "\u26a1" in line

    def test_unavailable_returns_none(self) -> None:
        mgr = BatteryManager(poll_interval=0.0)
        snap = BatterySnapshot(percent=0, charging=False, available=False)
        with patch("asciipal.battery._get_battery", return_value=snap):
            line = mgr.format_line()
        assert line is None

    def test_caching(self) -> None:
        mgr = BatteryManager(poll_interval=60.0)
        snap = BatterySnapshot(percent=50, charging=False, available=True)
        with patch("asciipal.battery._get_battery", return_value=snap):
            s1 = mgr.snapshot()
            s2 = mgr.snapshot()
        assert s1 is s2

    def test_error_fallback(self) -> None:
        mgr = BatteryManager(poll_interval=60.0)
        with patch("asciipal.battery._get_battery", side_effect=OSError("fail")):
            snap = mgr.snapshot()
        assert snap.available is False
        # Cached snapshot should still be the error fallback
        assert mgr.format_line() is None
