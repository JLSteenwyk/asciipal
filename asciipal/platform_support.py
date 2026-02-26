from __future__ import annotations

import os
import platform


def startup_warnings() -> list[str]:
    warnings: list[str] = []
    system = platform.system()
    if system == "Darwin":
        warnings.append(
            "macOS may require Accessibility permission: System Settings > Privacy & Security > Accessibility."
        )
    if system == "Linux":
        session = os.getenv("XDG_SESSION_TYPE", "").lower()
        if session == "wayland":
            warnings.append("Wayland may block global input capture; X11 is more reliable for now.")
    return warnings


def runtime_summary(
    input_supported: bool,
    headless: bool,
    pomodoro_mode: bool,
    input_reason: str | None = None,
) -> list[str]:
    lines: list[str] = []
    lines.append(f"platform={platform.system()}")
    lines.append(f"session_type={os.getenv('XDG_SESSION_TYPE', 'unknown')}")
    lines.append(f"input_monitor_supported={input_supported}")
    if input_reason:
        lines.append(f"input_monitor_reason={input_reason}")
    lines.append(f"headless={headless}")
    lines.append(f"pomodoro_mode={pomodoro_mode}")
    return lines
