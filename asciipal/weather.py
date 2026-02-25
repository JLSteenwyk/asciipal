from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from threading import Event, Lock, Thread

from asciipal.config import Config


@dataclass(slots=True)
class WeatherCondition:
    code: int
    description: str
    effect: str


@dataclass(slots=True)
class WeatherEffect:
    above: list[str]
    below: list[str]


EFFECTS: dict[str, WeatherEffect] = {
    "clear": WeatherEffect(
        above=["° . ° . °", ". ° . ° ."],
        below=["", ""],
    ),
    "cloudy": WeatherEffect(
        above=["~ ░ ~ ░ ~", "░ ~ ░ ~ ░"],
        below=["", ""],
    ),
    "rain": WeatherEffect(
        above=["░ ╽ ░ ╽ ░", "╽ ░ ╽ ░ ╽"],
        below=["", ""],
    ),
    "heavy_rain": WeatherEffect(
        above=["╽╽ ╽╽ ╽╽╽", "╽╽╽ ╽╽ ╽╽"],
        below=["", ""],
    ),
    "snow": WeatherEffect(
        above=["* + * + *", "+ * + * +"],
        below=["", ""],
    ),
    "thunder": WeatherEffect(
        above=["! ╽ ! ╽ !", "╽ ! ╽ ! ╽"],
        below=["", ""],
    ),
    "fog": WeatherEffect(
        above=["░░░░░░░░░", "▒▒▒▒▒▒▒▒▒"],
        below=["", ""],
    ),
    "sleet": WeatherEffect(
        above=["╽ * ╽ * ╽", "* ╽ * ╽ *"],
        below=["", ""],
    ),
}

# Map WWO weather condition codes (used by wttr.in) to effect categories.
WWO_CODE_MAP: dict[int, str] = {
    # Clear / Sunny
    113: "clear",
    # Partly cloudy
    116: "cloudy",
    # Cloudy
    119: "cloudy",
    # Overcast
    122: "cloudy",
    # Mist
    143: "fog",
    # Patchy rain possible
    176: "rain",
    # Patchy snow possible
    179: "snow",
    # Patchy sleet possible
    182: "sleet",
    # Patchy freezing drizzle possible
    185: "sleet",
    # Thundery outbreaks possible
    200: "thunder",
    # Blowing snow
    227: "snow",
    # Blizzard
    230: "snow",
    # Fog
    248: "fog",
    # Freezing fog
    260: "fog",
    # Patchy light drizzle
    263: "rain",
    # Light drizzle
    266: "rain",
    # Freezing drizzle
    281: "sleet",
    # Heavy freezing drizzle
    284: "sleet",
    # Patchy light rain
    293: "rain",
    # Light rain
    296: "rain",
    # Moderate rain at times
    299: "rain",
    # Moderate rain
    302: "rain",
    # Heavy rain at times
    305: "heavy_rain",
    # Heavy rain
    308: "heavy_rain",
    # Light freezing rain
    311: "sleet",
    # Moderate or heavy freezing rain
    314: "sleet",
    # Light sleet
    317: "sleet",
    # Moderate or heavy sleet
    320: "sleet",
    # Patchy light snow
    323: "snow",
    # Light snow
    326: "snow",
    # Patchy moderate snow
    329: "snow",
    # Moderate snow
    332: "snow",
    # Patchy heavy snow
    335: "snow",
    # Heavy snow
    338: "snow",
    # Ice pellets
    350: "sleet",
    # Light rain shower
    353: "rain",
    # Moderate or heavy rain shower
    356: "heavy_rain",
    # Torrential rain shower
    359: "heavy_rain",
    # Light sleet showers
    362: "sleet",
    # Moderate or heavy sleet showers
    365: "sleet",
    # Light snow showers
    368: "snow",
    # Moderate or heavy snow showers
    371: "snow",
    # Light showers of ice pellets
    374: "sleet",
    # Moderate or heavy showers of ice pellets
    377: "sleet",
    # Patchy light rain with thunder
    386: "thunder",
    # Moderate or heavy rain with thunder
    389: "thunder",
    # Patchy light snow with thunder
    392: "thunder",
    # Moderate or heavy snow with thunder
    395: "thunder",
}


def code_to_effect(code: int) -> str | None:
    return WWO_CODE_MAP.get(code)


class WeatherManager:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._current_effect: str | None = None
        self._lock = Lock()
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if not self._config.weather_enabled:
            return
        self._stop.clear()
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _poll_loop(self) -> None:
        interval = max(self._config.weather_poll_minutes, 5) * 60
        while not self._stop.is_set():
            try:
                self._fetch_weather()
            except Exception:
                pass
            self._stop.wait(timeout=interval)

    def _fetch_weather(self) -> None:
        location = self._config.weather_location or ""
        url = f"https://wttr.in/{location}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "asciipal"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        code = int(data["current_condition"][0]["weatherCode"])
        effect = code_to_effect(code)
        with self._lock:
            self._current_effect = effect

    def clear_effect(self) -> None:
        with self._lock:
            self._current_effect = None

    def current_effect(self, frame: int) -> tuple[str, str] | None:
        if not self._config.weather_enabled:
            return None
        with self._lock:
            effect_name = self._current_effect
        if effect_name is None:
            return None
        effect = EFFECTS.get(effect_name)
        if effect is None:
            return None
        idx = frame % 2
        return (effect.above[idx], effect.below[idx])
