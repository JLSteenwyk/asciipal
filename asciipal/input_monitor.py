from __future__ import annotations

from dataclasses import dataclass
from platform import system
from threading import Lock
from time import monotonic
from typing import Callable

_IMPORT_ERROR: str | None = None

try:
    # pyobjc 12+ moved AXIsProcessTrusted out of the HIServices lazy-import
    # table, but pynput still reads it from there.  Patch before importing
    # pynput so its darwin listener can find the symbol.
    import platform as _plat

    if _plat.system() == "Darwin":
        try:
            import HIServices as _hs  # type: ignore[import-untyped]
            import ApplicationServices as _as  # type: ignore[import-untyped]

            if not hasattr(_hs, "AXIsProcessTrusted"):
                _hs.AXIsProcessTrusted = _as.AXIsProcessTrusted  # type: ignore[attr-defined]
        except Exception:
            pass

    from pynput import keyboard, mouse
except Exception as exc:  # pragma: no cover - depends on runtime environment
    keyboard = None
    mouse = None
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


@dataclass(slots=True)
class InputCallbacks:
    on_keypress: Callable[[float], None]
    on_click: Callable[[float], None]
    on_mouse_move: Callable[[float, float, float], None]


class InputMonitor:
    def __init__(self, callbacks: InputCallbacks) -> None:
        self.callbacks = callbacks
        self._keyboard_listener = None
        self._mouse_listener = None
        self._started = False
        self._lock = Lock()
        self._last_mouse_pos: tuple[float, float] | None = None

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            if keyboard is None or mouse is None:
                self._started = True
                return

            self._keyboard_listener = keyboard.Listener(on_press=self._on_keypress)
            self._mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
            if self._keyboard_listener is not None:
                self._keyboard_listener.start()
            if self._mouse_listener is not None:
                self._mouse_listener.start()
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if self._keyboard_listener is not None:
                self._keyboard_listener.stop()
            if self._mouse_listener is not None:
                self._mouse_listener.stop()
            self._started = False

    def is_supported(self) -> bool:
        return keyboard is not None and mouse is not None

    def unavailable_reason(self) -> str | None:
        if self.is_supported():
            return None
        if _IMPORT_ERROR:
            return f"input backend unavailable ({_IMPORT_ERROR})"
        if system() == "Darwin":
            return "input backend unavailable (check Accessibility permission)"
        return "input backend unavailable"

    def _on_keypress(self, _key) -> None:
        self.callbacks.on_keypress(monotonic())

    def _on_click(self, x: float, y: float, _button, pressed: bool) -> None:
        if not pressed:
            return
        ts = monotonic()
        self.callbacks.on_click(ts)
        if self._last_mouse_pos is not None:
            dx = x - self._last_mouse_pos[0]
            dy = y - self._last_mouse_pos[1]
            self.callbacks.on_mouse_move(dx, dy, ts)
        self._last_mouse_pos = (x, y)

    def _on_move(self, x: float, y: float) -> None:
        ts = monotonic()
        if self._last_mouse_pos is None:
            self._last_mouse_pos = (x, y)
            return
        dx = x - self._last_mouse_pos[0]
        dy = y - self._last_mouse_pos[1]
        self.callbacks.on_mouse_move(dx, dy, ts)
        self._last_mouse_pos = (x, y)
