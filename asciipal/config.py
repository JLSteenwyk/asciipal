from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("~/.asciipal/config.yaml").expanduser()

POSITION_VALUES = {
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
}
COLOR_SCHEMES = {"default", "green-terminal", "pastel", "amber-terminal", "ocean"}
NOTIFICATION_LEVELS = {"gentle", "verbose", "silent"}

DEFAULT_CONFIG: dict[str, Any] = {
    "break_interval_minutes": 25,
    "break_duration_minutes": 5,
    "pomodoro_mode": False,
    "pomodoro_work_minutes": 25,
    "pomodoro_break_minutes": 5,
    "typing_fast_wpm": 80,
    "rage_click_threshold": 5,
    "dizzy_mouse_speed": 700,
    "cheering_after_minutes": 45,
    "state_cooldown_seconds": 2.0,
    "idle_timeout_seconds": 10,
    "sleep_timeout_seconds": 120,
    "position": "bottom-right",
    "character_scale": 1.0,
    "widget_mode": True,
    "widget_opacity": 0.95,
    "color_scheme": "default",
    "notifications": "gentle",
    "custom_art": {
        "idle": None,
        "sleeping": None,
        "watching": None,
        "excited": None,
        "dizzy": None,
        "alarmed": None,
        "cheering": None,
    },
    "weather_enabled": False,
    "weather_location": "",
    "weather_poll_minutes": 30,
    "time_awareness_enabled": False,
    "system_resources_enabled": True,
}


@dataclass(slots=True)
class Config:
    break_interval_minutes: int
    break_duration_minutes: int
    pomodoro_mode: bool
    pomodoro_work_minutes: int
    pomodoro_break_minutes: int
    typing_fast_wpm: int
    rage_click_threshold: int
    dizzy_mouse_speed: float
    cheering_after_minutes: int
    state_cooldown_seconds: float
    idle_timeout_seconds: int
    sleep_timeout_seconds: int
    position: str
    character_scale: float
    widget_mode: bool
    widget_opacity: float
    color_scheme: str
    notifications: str
    custom_art: dict[str, str | None] = field(default_factory=dict)
    weather_enabled: bool = False
    weather_location: str = ""
    weather_poll_minutes: int = 30
    time_awareness_enabled: bool = False
    system_resources_enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        validate_config(data)
        return cls(
            break_interval_minutes=int(data["break_interval_minutes"]),
            break_duration_minutes=int(data["break_duration_minutes"]),
            pomodoro_mode=bool(data["pomodoro_mode"]),
            pomodoro_work_minutes=int(data["pomodoro_work_minutes"]),
            pomodoro_break_minutes=int(data["pomodoro_break_minutes"]),
            typing_fast_wpm=int(data["typing_fast_wpm"]),
            rage_click_threshold=int(data["rage_click_threshold"]),
            dizzy_mouse_speed=float(data["dizzy_mouse_speed"]),
            cheering_after_minutes=int(data["cheering_after_minutes"]),
            state_cooldown_seconds=float(data["state_cooldown_seconds"]),
            idle_timeout_seconds=int(data["idle_timeout_seconds"]),
            sleep_timeout_seconds=int(data["sleep_timeout_seconds"]),
            position=str(data["position"]),
            character_scale=float(data["character_scale"]),
            widget_mode=bool(data["widget_mode"]),
            widget_opacity=float(data["widget_opacity"]),
            color_scheme=str(data["color_scheme"]),
            notifications=str(data["notifications"]),
            custom_art=dict(data["custom_art"]),
            weather_enabled=bool(data["weather_enabled"]),
            weather_location=str(data["weather_location"]),
            weather_poll_minutes=max(5, int(data["weather_poll_minutes"])),
            time_awareness_enabled=bool(data["time_awareness_enabled"]),
            system_resources_enabled=bool(data["system_resources_enabled"]),
        )


def _deep_merge(defaults: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_config(data: dict[str, Any]) -> None:
    if data["break_interval_minutes"] <= 0:
        raise ValueError("break_interval_minutes must be > 0")
    if data["break_duration_minutes"] <= 0:
        raise ValueError("break_duration_minutes must be > 0")
    if data["pomodoro_work_minutes"] <= 0:
        raise ValueError("pomodoro_work_minutes must be > 0")
    if data["pomodoro_break_minutes"] <= 0:
        raise ValueError("pomodoro_break_minutes must be > 0")
    if data["typing_fast_wpm"] <= 0:
        raise ValueError("typing_fast_wpm must be > 0")
    if data["rage_click_threshold"] <= 0:
        raise ValueError("rage_click_threshold must be > 0")
    if data["dizzy_mouse_speed"] <= 0:
        raise ValueError("dizzy_mouse_speed must be > 0")
    if data["cheering_after_minutes"] <= 0:
        raise ValueError("cheering_after_minutes must be > 0")
    if data["state_cooldown_seconds"] < 0:
        raise ValueError("state_cooldown_seconds must be >= 0")
    if data["idle_timeout_seconds"] <= 0:
        raise ValueError("idle_timeout_seconds must be > 0")
    if data["sleep_timeout_seconds"] <= data["idle_timeout_seconds"]:
        raise ValueError("sleep_timeout_seconds must be > idle_timeout_seconds")
    if data["position"] not in POSITION_VALUES:
        raise ValueError(f"position must be one of {sorted(POSITION_VALUES)}")
    if data["character_scale"] <= 0:
        raise ValueError("character_scale must be > 0")
    if not 0.2 <= float(data["widget_opacity"]) <= 1.0:
        raise ValueError("widget_opacity must be between 0.2 and 1.0")
    if data["color_scheme"] not in COLOR_SCHEMES:
        raise ValueError(f"color_scheme must be one of {sorted(COLOR_SCHEMES)}")
    if data["notifications"] not in NOTIFICATION_LEVELS:
        raise ValueError(f"notifications must be one of {sorted(NOTIFICATION_LEVELS)}")
    if not isinstance(data["custom_art"], dict):
        raise ValueError("custom_art must be a mapping")


def resolve_config_path() -> Path:
    env_path = os.getenv("ASCIIPAL_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_CONFIG_PATH


def ensure_config_file(path: Path | str | None = None) -> Path:
    target = Path(path).expanduser() if path is not None else resolve_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with target.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(DEFAULT_CONFIG, handle, sort_keys=False)
    return target


def load_config(path: Path | str | None = None) -> Config:
    target = ensure_config_file(path)
    with target.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Config YAML must be a mapping")
    merged = _deep_merge(DEFAULT_CONFIG, loaded)
    return Config.from_dict(merged)
