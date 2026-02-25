from __future__ import annotations

from pathlib import Path

import pytest

from asciipal.config import DEFAULT_CONFIG, ensure_config_file, load_config


def test_ensure_config_file_creates_default(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    ensure_config_file(cfg)
    assert cfg.exists()
    loaded = load_config(cfg)
    assert loaded.break_interval_minutes == DEFAULT_CONFIG["break_interval_minutes"]


def test_config_validation_rejects_invalid_sleep_timeout(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("idle_timeout_seconds: 60\nsleep_timeout_seconds: 30\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_config_validation_rejects_negative_state_cooldown(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("state_cooldown_seconds: -1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_config_validation_rejects_invalid_pomodoro_values(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("pomodoro_work_minutes: 0\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_config_validation_rejects_invalid_widget_opacity(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("widget_opacity: 1.5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_session_goal_minutes_default_zero() -> None:
    assert DEFAULT_CONFIG["session_goal_minutes"] == 0


def test_config_validation_rejects_negative_session_goal(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("session_goal_minutes: -1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_battery_enabled_default_true() -> None:
    assert DEFAULT_CONFIG["battery_enabled"] is True


def test_cpu_load_enabled_default_true() -> None:
    assert DEFAULT_CONFIG["cpu_load_enabled"] is True


def test_sweating_load_threshold_default() -> None:
    assert DEFAULT_CONFIG["sweating_load_threshold"] == 0.8
