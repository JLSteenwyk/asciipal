from __future__ import annotations

import platform
import tkinter as tk
from tkinter import font

from asciipal.config import Config


COLOR_MAP: dict[str, tuple[str, str]] = {
    "default": ("#111111", "#f5f5f5"),
    "green-terminal": ("#7CFC00", "#001100"),
    "pastel": ("#2d3142", "#f4d6cc"),
}

# In widget mode the background is transparent/dark, so text must be light.
WIDGET_FG: dict[str, str] = {
    "default": "#FFFFFF",
    "green-terminal": "#7CFC00",
    "pastel": "#f4d6cc",
}


class Overlay:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.root = tk.Tk()
        self.root.withdraw()  # Hide while we configure — avoids chrome flash
        self.root.title("AsciiPal")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        fg, bg = COLOR_MAP.get(config.color_scheme, COLOR_MAP["default"])
        label_bg = bg
        pad_x = 60
        pad_y = 40
        if config.widget_mode:
            pad_x = 40
            pad_y = 30
            label_bg = self._transparent_bg_color()
            fg = WIDGET_FG.get(config.color_scheme, "#FFFFFF")

        self.root.configure(bg=label_bg)

        self.label = tk.Label(
            self.root,
            text="(•‿•)",
            fg=fg,
            bg=label_bg,
            padx=pad_x,
            pady=pad_y,
            justify="center",
            anchor="center",
            borderwidth=0,
            highlightthickness=0,
            cursor="fleur",
        )
        base_size = max(int(64 * config.character_scale), 10)
        family = self._pick_font_family()
        self.text_font = font.Font(family=family, size=base_size)
        self.label.configure(font=self.text_font)
        self._configure_transparency()
        self.label.pack(fill="both", expand=True)

        # Width stabilisation — ratchets up to the widest content seen.
        self._min_text_width = 0

        # Drag support — bind to both root and label for reliability
        self._user_dragged = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        for widget in (self.root, self.label):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<Double-Button-1>", self._on_double_click)

        self.root.deiconify()  # Show now that everything is configured
        self.root.after(10, self._place_window)

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        if not self._user_dragged and abs(dx) < 3 and abs(dy) < 3:
            return
        self._user_dragged = True
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _on_double_click(self, event: tk.Event) -> None:
        self._user_dragged = False
        self._place_window()

    def set_min_width(self, width: int) -> None:
        self._min_text_width = max(self._min_text_width, width)
        self.label.configure(width=self._min_text_width)

    def update_text(self, text: str) -> None:
        lines = text.split("\n")
        max_w = max((len(l) for l in lines), default=0)
        if max_w > self._min_text_width:
            self._min_text_width = max_w
            self.label.configure(width=self._min_text_width)
        self.label.configure(text=text)
        self.root.update_idletasks()
        if not self._user_dragged:
            self._place_window()

    def run(self, tick_fn, tick_ms: int = 250) -> None:
        def _tick() -> None:
            tick_fn()
            self.root.after(tick_ms, _tick)

        self.root.after(tick_ms, _tick)
        self.root.mainloop()

    def _place_window(self) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        margin = 24
        position = self.config.position

        if "left" in position:
            x = margin
        elif "right" in position:
            x = sw - w - margin
        else:
            x = (sw - w) // 2

        if "top" in position:
            y = margin
        elif "bottom" in position:
            y = sh - h - margin
        else:
            y = (sh - h) // 2

        self.root.geometry(f"+{x}+{y}")

    def _configure_transparency(self) -> None:
        try:
            self.root.attributes("-alpha", self.config.widget_opacity)
        except tk.TclError:
            pass

        if not self.config.widget_mode:
            return

        system = platform.system()
        # On macOS, rely solely on -alpha. Using -transparent True causes
        # the window to become click-through, which breaks drag.
        if system == "Windows":
            try:
                transparent_key = self._transparent_bg_color()
                self.root.configure(bg=transparent_key)
                self.root.wm_attributes("-transparentcolor", transparent_key)
            except tk.TclError:
                pass

    def _pick_font_family(self) -> str:
        candidates = {
            "Darwin": ["Menlo", "Monaco", "Courier"],
            "Windows": ["Consolas", "Courier New", "Lucida Console"],
            "Linux": ["DejaVu Sans Mono", "Liberation Mono", "Monospace"],
        }
        by_platform = candidates.get(platform.system(), ["Monospace", "Courier"])
        available = set(font.families(self.root))
        for family in by_platform:
            if family in available:
                return family
        return "Courier"

    def _transparent_bg_color(self) -> str:
        return "#1a1a2e"
