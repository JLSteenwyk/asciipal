from __future__ import annotations

import platform
import subprocess
import time
from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class BatterySnapshot:
    percent: int
    charging: bool
    available: bool


def _get_battery() -> BatterySnapshot:
    """Detect battery status using platform-specific methods."""
    system = platform.system()
    if system == "Darwin":
        return _get_battery_macos()
    if system == "Linux":
        return _get_battery_linux()
    if system == "Windows":
        return _get_battery_windows()
    return BatterySnapshot(percent=0, charging=False, available=False)


def _get_battery_macos() -> BatterySnapshot:
    try:
        output = subprocess.check_output(
            ["pmset", "-g", "batt"], text=True, timeout=5,
        )
        for line in output.splitlines():
            if "InternalBattery" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    info = parts[1]
                    pct_str = info.split("%")[0].strip()
                    percent = int(pct_str)
                    charging = "charging" in info.lower() and "discharging" not in info.lower()
                    return BatterySnapshot(percent=percent, charging=charging, available=True)
    except Exception:
        pass
    return BatterySnapshot(percent=0, charging=False, available=False)


def _get_battery_linux() -> BatterySnapshot:
    import glob
    paths = glob.glob("/sys/class/power_supply/BAT*/capacity")
    if not paths:
        return BatterySnapshot(percent=0, charging=False, available=False)
    try:
        bat_dir = paths[0].rsplit("/", 1)[0]
        with open(paths[0]) as f:
            percent = int(f.read().strip())
        status_path = f"{bat_dir}/status"
        charging = False
        try:
            with open(status_path) as f:
                charging = f.read().strip().lower() in ("charging", "full")
        except OSError:
            pass
        return BatterySnapshot(percent=percent, charging=charging, available=True)
    except Exception:
        return BatterySnapshot(percent=0, charging=False, available=False)


def _get_battery_windows() -> BatterySnapshot:
    try:
        import ctypes

        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_byte),
                ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong),
            ]

        status = SYSTEM_POWER_STATUS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        if status.BatteryFlag == 128:  # No battery
            return BatterySnapshot(percent=0, charging=False, available=False)
        percent = min(status.BatteryLifePercent, 100)
        charging = status.ACLineStatus == 1
        return BatterySnapshot(percent=percent, charging=charging, available=True)
    except Exception:
        return BatterySnapshot(percent=0, charging=False, available=False)


class BatteryManager:
    def __init__(self, poll_interval: float = 60.0) -> None:
        self._poll_interval = poll_interval
        self._lock = Lock()
        self._cached: BatterySnapshot | None = None
        self._last_poll: float = 0.0

    def snapshot(self) -> BatterySnapshot:
        now = time.monotonic()
        with self._lock:
            if self._cached is not None and (now - self._last_poll) < self._poll_interval:
                return self._cached
        try:
            snap = _get_battery()
        except Exception:
            snap = BatterySnapshot(percent=0, charging=False, available=False)
        with self._lock:
            self._cached = snap
            self._last_poll = now
        return snap

    def format_line(self) -> str | None:
        """Return battery display string, or None if no battery detected."""
        snap = self.snapshot()
        if not snap.available:
            return None
        icon = " \u26a1" if snap.charging else ""
        return f"Battery: {snap.percent}%{icon}"
