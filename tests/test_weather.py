from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

import pytest

from asciipal.config import Config, DEFAULT_CONFIG, _deep_merge
from asciipal.weather import (
    EFFECTS,
    WWO_CODE_MAP,
    WeatherManager,
    code_to_effect,
)


def _make_config(**overrides) -> Config:
    data = _deep_merge(DEFAULT_CONFIG, overrides)
    return Config.from_dict(data)


class TestWeatherCodeMapping:
    def test_clear_code(self) -> None:
        assert code_to_effect(113) == "clear"

    def test_cloudy_codes(self) -> None:
        assert code_to_effect(116) == "cloudy"
        assert code_to_effect(119) == "cloudy"
        assert code_to_effect(122) == "cloudy"

    def test_rain_codes(self) -> None:
        assert code_to_effect(176) == "rain"
        assert code_to_effect(293) == "rain"
        assert code_to_effect(296) == "rain"

    def test_heavy_rain_codes(self) -> None:
        assert code_to_effect(305) == "heavy_rain"
        assert code_to_effect(308) == "heavy_rain"
        assert code_to_effect(356) == "heavy_rain"

    def test_thunder_codes(self) -> None:
        assert code_to_effect(200) == "thunder"
        assert code_to_effect(386) == "thunder"

    def test_snow_codes(self) -> None:
        assert code_to_effect(179) == "snow"
        assert code_to_effect(323) == "snow"
        assert code_to_effect(338) == "snow"

    def test_fog_codes(self) -> None:
        assert code_to_effect(143) == "fog"
        assert code_to_effect(248) == "fog"
        assert code_to_effect(260) == "fog"

    def test_sleet_codes(self) -> None:
        assert code_to_effect(182) == "sleet"
        assert code_to_effect(317) == "sleet"
        assert code_to_effect(350) == "sleet"

    def test_unknown_code_returns_none(self) -> None:
        assert code_to_effect(9999) is None

    def test_all_mapped_codes_have_valid_effect(self) -> None:
        for code, effect_name in WWO_CODE_MAP.items():
            assert effect_name in EFFECTS, f"Code {code} maps to unknown effect {effect_name!r}"


class TestWeatherEffectFrames:
    @pytest.mark.parametrize("category", list(EFFECTS.keys()))
    def test_frame_0_returns_strings(self, category: str) -> None:
        effect = EFFECTS[category]
        assert isinstance(effect.above[0], str)
        assert isinstance(effect.below[0], str)

    @pytest.mark.parametrize("category", list(EFFECTS.keys()))
    def test_frame_1_returns_strings(self, category: str) -> None:
        effect = EFFECTS[category]
        assert isinstance(effect.above[1], str)
        assert isinstance(effect.below[1], str)

    @pytest.mark.parametrize("category", list(EFFECTS.keys()))
    def test_two_frames_exist(self, category: str) -> None:
        effect = EFFECTS[category]
        assert len(effect.above) == 2
        assert len(effect.below) == 2


class TestWeatherEffectWidthConsistency:
    @pytest.mark.parametrize("category", list(EFFECTS.keys()))
    def test_above_frames_same_width(self, category: str) -> None:
        effect = EFFECTS[category]
        widths = [len(f) for f in effect.above]
        assert len(set(widths)) == 1, f"{category} above frames have inconsistent widths: {widths}"

    @pytest.mark.parametrize("category", list(EFFECTS.keys()))
    def test_below_frames_same_width(self, category: str) -> None:
        effect = EFFECTS[category]
        widths = [len(f) for f in effect.below]
        assert len(set(widths)) == 1, f"{category} below frames have inconsistent widths: {widths}"


class TestWeatherManagerDisabled:
    def test_current_effect_returns_none_when_disabled(self) -> None:
        config = _make_config(weather_enabled=False)
        manager = WeatherManager(config)
        assert manager.current_effect(0) is None
        assert manager.current_effect(1) is None

    def test_start_does_nothing_when_disabled(self) -> None:
        config = _make_config(weather_enabled=False)
        manager = WeatherManager(config)
        manager.start()
        assert manager._thread is None
        manager.stop()


class TestWeatherManagerMockFetch:
    def _mock_response(self, weather_code: int) -> BytesIO:
        data = {"current_condition": [{"weatherCode": str(weather_code)}]}
        return BytesIO(json.dumps(data).encode())

    def test_fetch_sets_correct_effect(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="TestCity")
        manager = WeatherManager(config)

        mock_resp = self._mock_response(113)
        mock_resp.status = 200
        mock_resp.headers = {}

        with patch("asciipal.weather.urllib.request.urlopen", return_value=mock_resp):
            manager._fetch_weather()

        result = manager.current_effect(0)
        assert result is not None
        above, below = result
        assert above == EFFECTS["clear"].above[0]

    def test_fetch_thunder_code(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="StormCity")
        manager = WeatherManager(config)

        mock_resp = self._mock_response(200)
        mock_resp.status = 200
        mock_resp.headers = {}

        with patch("asciipal.weather.urllib.request.urlopen", return_value=mock_resp):
            manager._fetch_weather()

        result = manager.current_effect(1)
        assert result is not None
        above, below = result
        assert above == EFFECTS["thunder"].above[1]
        assert below == EFFECTS["thunder"].below[1]

    def test_fetch_unknown_code_gives_none(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="Nowhere")
        manager = WeatherManager(config)

        mock_resp = self._mock_response(9999)
        mock_resp.status = 200
        mock_resp.headers = {}

        with patch("asciipal.weather.urllib.request.urlopen", return_value=mock_resp):
            manager._fetch_weather()

        assert manager.current_effect(0) is None

    def test_current_condition_name_returns_title_cased(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="TestCity")
        manager = WeatherManager(config)

        # Set heavy_rain effect
        mock_resp = self._mock_response(305)
        mock_resp.status = 200
        mock_resp.headers = {}
        with patch("asciipal.weather.urllib.request.urlopen", return_value=mock_resp):
            manager._fetch_weather()

        name = manager.current_condition_name()
        assert name == "Heavy Rain"

    def test_current_condition_name_returns_none_when_disabled(self) -> None:
        config = _make_config(weather_enabled=False)
        manager = WeatherManager(config)
        assert manager.current_condition_name() is None

    def test_current_condition_name_returns_none_no_effect(self) -> None:
        config = _make_config(weather_enabled=True)
        manager = WeatherManager(config)
        assert manager.current_condition_name() is None

    def test_fetch_error_keeps_last_effect(self) -> None:
        config = _make_config(weather_enabled=True, weather_location="TestCity")
        manager = WeatherManager(config)

        # First set a known effect
        mock_resp = self._mock_response(113)
        mock_resp.status = 200
        mock_resp.headers = {}
        with patch("asciipal.weather.urllib.request.urlopen", return_value=mock_resp):
            manager._fetch_weather()
        assert manager.current_effect(0) is not None

        # Now simulate a fetch error — effect should remain
        with patch("asciipal.weather.urllib.request.urlopen", side_effect=Exception("network error")):
            try:
                manager._fetch_weather()
            except Exception:
                pass

        assert manager.current_effect(0) is not None
