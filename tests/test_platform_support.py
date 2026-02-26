from __future__ import annotations

from asciipal import platform_support


def test_linux_wayland_warning(monkeypatch) -> None:
    monkeypatch.setattr(platform_support.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    warnings = platform_support.startup_warnings()
    assert any("Wayland" in warning for warning in warnings)


def test_runtime_summary_contains_key_fields(monkeypatch) -> None:
    monkeypatch.setattr(platform_support.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("XDG_SESSION_TYPE", "aqua")
    lines = platform_support.runtime_summary(
        input_supported=True,
        headless=False,
        pomodoro_mode=False,
    )
    assert any(line.startswith("platform=Darwin") for line in lines)
    assert any(line.startswith("input_monitor_supported=True") for line in lines)


def test_runtime_summary_includes_input_reason_when_provided() -> None:
    lines = platform_support.runtime_summary(
        input_supported=False,
        input_reason="missing dependency",
        headless=False,
        pomodoro_mode=False,
    )
    assert "input_monitor_reason=missing dependency" in lines
