from __future__ import annotations

from time import monotonic
from unittest.mock import MagicMock

from asciipal.break_manager import BreakManager
from asciipal.config import Config, DEFAULT_CONFIG, _deep_merge
from asciipal.overlay import MenuCallbacks
from asciipal.weather import EFFECTS, WeatherManager


def _make_config(**overrides) -> Config:
    data = _deep_merge(DEFAULT_CONFIG, overrides)
    return Config.from_dict(data)


class TestForceBreak:
    def test_force_break(self) -> None:
        config = _make_config()
        bm = BreakManager(config)
        now = monotonic()
        bm.force_break(now)
        assert bm._on_break is True

    def test_force_break_while_on_break(self) -> None:
        config = _make_config()
        bm = BreakManager(config)
        now = monotonic()
        bm.force_break(now)
        assert bm._on_break is True
        # Call again — no error, state unchanged
        bm.force_break(now + 1)
        assert bm._on_break is True


class TestSkipBreak:
    def test_skip_break(self) -> None:
        config = _make_config()
        bm = BreakManager(config)
        now = monotonic()
        bm.start_break(now)
        assert bm._on_break is True
        bm.skip_break(now + 1)
        assert bm._on_break is False
        assert bm._active_start == now + 1


class TestWeatherClearEffect:
    def test_clear_effect(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="Test")
        manager = WeatherManager(config)
        # Manually set an effect
        manager._current_effect = "clear"
        assert manager.current_effect(0) is not None
        manager.clear_effect()
        assert manager.current_effect(0) is None


class TestToggleWeatherCallback:
    def test_toggle_weather(self) -> None:
        config = _make_config(weather_enabled=False)
        # Import here to avoid tkinter issues
        from asciipal.app import AsciiPalApp

        app = AsciiPalApp(config, headless=True, show_summary=False)
        assert app.config.weather_enabled is False
        app._menu_toggle_weather()
        assert app.config.weather_enabled is True
        app._menu_toggle_weather()
        assert app.config.weather_enabled is False
        app.shutdown()


class TestMenuCallbacksDataclass:
    def test_instantiate_with_mocks(self) -> None:
        callbacks = MenuCallbacks(
            on_take_break=MagicMock(),
            on_skip_break=MagicMock(),
            on_toggle_weather=MagicMock(),
            on_open_config=MagicMock(),
            on_quit=MagicMock(),
        )
        assert callable(callbacks.on_take_break)
        assert callable(callbacks.on_skip_break)
        assert callable(callbacks.on_toggle_weather)
        assert callable(callbacks.on_open_config)
        assert callable(callbacks.on_quit)
