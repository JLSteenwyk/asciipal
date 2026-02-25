from __future__ import annotations

from unittest.mock import patch

from asciipal.system_resources import (
    ResourceSnapshot,
    SystemResourcesManager,
    _get_disk_usage,
    _get_memory_usage,
)


class TestGetDiskUsage:
    def test_returns_floats(self) -> None:
        used, total = _get_disk_usage()
        assert isinstance(used, float)
        assert isinstance(total, float)

    def test_total_positive(self) -> None:
        _used, total = _get_disk_usage()
        assert total > 0

    def test_used_lte_total(self) -> None:
        used, total = _get_disk_usage()
        assert used <= total


class TestGetMemoryUsage:
    def test_returns_floats(self) -> None:
        used, total = _get_memory_usage()
        assert isinstance(used, float)
        assert isinstance(total, float)

    def test_total_positive_on_supported_platform(self) -> None:
        import platform
        if platform.system() in ("Darwin", "Linux", "Windows"):
            _used, total = _get_memory_usage()
            assert total > 0


class TestSystemResourcesManager:
    def test_snapshot_returns_resource_snapshot(self) -> None:
        mgr = SystemResourcesManager(poll_interval=30.0)
        snap = mgr.snapshot()
        assert isinstance(snap, ResourceSnapshot)

    def test_format_line_contains_disk_and_ram(self) -> None:
        mgr = SystemResourcesManager(poll_interval=30.0)
        line = mgr.format_line()
        assert "Disk:" in line
        assert "RAM:" in line

    def test_caching_returns_same_object(self) -> None:
        mgr = SystemResourcesManager(poll_interval=60.0)
        snap1 = mgr.snapshot()
        snap2 = mgr.snapshot()
        assert snap1 is snap2

    def test_graceful_fallback_on_disk_error(self) -> None:
        mgr = SystemResourcesManager(poll_interval=0.0)
        with patch(
            "asciipal.system_resources._get_disk_usage",
            side_effect=OSError("fail"),
        ):
            snap = mgr.snapshot()
        assert snap is not None
        assert snap.disk_used_gb == 0.0
        assert snap.disk_total_gb == 0.0

    def test_graceful_fallback_on_memory_error(self) -> None:
        mgr = SystemResourcesManager(poll_interval=0.0)
        with patch(
            "asciipal.system_resources._get_memory_usage",
            side_effect=OSError("fail"),
        ):
            snap = mgr.snapshot()
        assert snap is not None
        assert snap.mem_used_gb == 0.0
        assert snap.mem_total_gb == 0.0
