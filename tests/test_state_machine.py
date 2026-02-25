from __future__ import annotations

from asciipal.activity_tracker import ActivitySnapshot
from asciipal.config import Config, DEFAULT_CONFIG
from asciipal.state_machine import StateMachine


def _config() -> Config:
    return Config.from_dict(dict(DEFAULT_CONFIG))


def test_sleeping_beats_other_states() -> None:
    machine = StateMachine(_config(), cooldown_seconds=0)
    snap = ActivitySnapshot(
        typing_wpm=200,
        click_rate=20,
        mouse_speed=1000,
        seconds_since_input=150,
        total_active_seconds=9999,
    )
    result = machine.update(snap, now=10)
    assert result.state == "sleeping"


def test_excited_when_fast_typing() -> None:
    machine = StateMachine(_config(), cooldown_seconds=0)
    snap = ActivitySnapshot(
        typing_wpm=120,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=1,
        total_active_seconds=30,
    )
    result = machine.update(snap, now=10)
    assert result.state == "excited"


def test_dizzy_threshold_comes_from_config() -> None:
    cfg_data = dict(DEFAULT_CONFIG)
    cfg_data["dizzy_mouse_speed"] = 50
    machine = StateMachine(Config.from_dict(cfg_data), cooldown_seconds=0)
    snap = ActivitySnapshot(
        typing_wpm=0,
        click_rate=0,
        mouse_speed=60,
        seconds_since_input=1,
        total_active_seconds=10,
    )
    result = machine.update(snap, now=10)
    assert result.state == "dizzy"


def test_default_cooldown_from_config_is_applied() -> None:
    cfg_data = dict(DEFAULT_CONFIG)
    cfg_data["state_cooldown_seconds"] = 5.0
    machine = StateMachine(Config.from_dict(cfg_data))

    snap1 = ActivitySnapshot(
        typing_wpm=100,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=1,
        total_active_seconds=10,
    )
    snap2 = ActivitySnapshot(
        typing_wpm=0,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=cfg_data["idle_timeout_seconds"] + 1,
        total_active_seconds=10,
    )
    first = machine.update(snap1, now=10)
    second = machine.update(snap2, now=12)
    assert first.state == "excited"
    assert second.state == "excited"
