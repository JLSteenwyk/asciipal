from __future__ import annotations

import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class ResourceSnapshot:
    disk_used_gb: float
    disk_total_gb: float
    mem_used_gb: float
    mem_total_gb: float
    cpu_load: float = 0.0


def _get_disk_usage() -> tuple[float, float]:
    """Return ``(used_gb, total_gb)`` for the root filesystem."""
    usage = shutil.disk_usage("/")
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)
    return used_gb, total_gb


def _get_memory_usage() -> tuple[float, float]:
    """Return ``(used_gb, total_gb)`` with platform-specific strategies."""
    system = platform.system()
    if system == "Darwin":
        return _get_memory_macos()
    if system == "Linux":
        return _get_memory_linux()
    if system == "Windows":
        return _get_memory_windows()
    return 0.0, 0.0


def _get_memory_macos() -> tuple[float, float]:
    total_bytes = int(subprocess.check_output(
        ["sysctl", "-n", "hw.memsize"],
    ).strip())
    total_gb = total_bytes / (1024 ** 3)

    vm_output = subprocess.check_output(["vm_stat"]).decode()
    page_size = 4096
    free_pages = 0
    inactive_pages = 0
    speculative_pages = 0
    for line in vm_output.splitlines():
        if "page size of" in line:
            page_size = int(line.split()[-2])
        elif line.startswith("Pages free:"):
            free_pages = int(line.split()[-1].rstrip("."))
        elif line.startswith("Pages inactive:"):
            inactive_pages = int(line.split()[-1].rstrip("."))
        elif line.startswith("Pages speculative:"):
            speculative_pages = int(line.split()[-1].rstrip("."))

    free_bytes = (free_pages + inactive_pages + speculative_pages) * page_size
    used_gb = (total_bytes - free_bytes) / (1024 ** 3)
    return max(used_gb, 0.0), total_gb


def _get_memory_linux() -> tuple[float, float]:
    with open("/proc/meminfo") as f:
        info = {}
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                info[key] = int(parts[1])  # value in kB

    total_kb = info.get("MemTotal", 0)
    available_kb = info.get("MemAvailable", 0)
    total_gb = total_kb / (1024 ** 2)
    used_gb = (total_kb - available_kb) / (1024 ** 2)
    return max(used_gb, 0.0), total_gb


def _get_memory_windows() -> tuple[float, float]:
    import ctypes
    import ctypes.wintypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.wintypes.DWORD),
            ("dwMemoryLoad", ctypes.wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))  # type: ignore[attr-defined]
    total_gb = stat.ullTotalPhys / (1024 ** 3)
    used_gb = (stat.ullTotalPhys - stat.ullAvailPhys) / (1024 ** 3)
    return used_gb, total_gb


def _get_cpu_load() -> float:
    """Return 1-minute load average normalized by CPU count, or 0.0 on Windows."""
    try:
        import os
        load = os.getloadavg()[0]
        cpus = os.cpu_count() or 1
        return load / cpus
    except (OSError, AttributeError):
        return 0.0


class SystemResourcesManager:
    def __init__(self, poll_interval: float = 30.0) -> None:
        self._poll_interval = poll_interval
        self._lock = Lock()
        self._cached: ResourceSnapshot | None = None
        self._last_poll: float = 0.0

    def snapshot(self) -> ResourceSnapshot | None:
        now = time.monotonic()
        with self._lock:
            if self._cached is not None and (now - self._last_poll) < self._poll_interval:
                return self._cached
        try:
            disk_used, disk_total = _get_disk_usage()
        except Exception:
            disk_used, disk_total = 0.0, 0.0
        try:
            mem_used, mem_total = _get_memory_usage()
        except Exception:
            mem_used, mem_total = 0.0, 0.0
        try:
            cpu_load = _get_cpu_load()
        except Exception:
            cpu_load = 0.0
        snap = ResourceSnapshot(
            disk_used_gb=disk_used,
            disk_total_gb=disk_total,
            mem_used_gb=mem_used,
            mem_total_gb=mem_total,
            cpu_load=cpu_load,
        )
        with self._lock:
            self._cached = snap
            self._last_poll = now
        return snap

    def is_system_saturated(self, threshold: float = 0.8) -> bool:
        """Return True if CPU load exceeds the given threshold."""
        snap = self.snapshot()
        if snap is None:
            return False
        return snap.cpu_load >= threshold

    def format_lines(self) -> list[str]:
        """Return disk and RAM usage as separate short strings."""
        snap = self.snapshot()
        if snap is None:
            return []
        return [
            f"Disk: {snap.disk_used_gb:.1f}/{snap.disk_total_gb:.1f} GB",
            f"RAM: {snap.mem_used_gb:.1f}/{snap.mem_total_gb:.1f} GB",
        ]

    def format_line(self) -> str:
        lines = self.format_lines()
        return "  |  ".join(lines)
