from __future__ import annotations

import platform
import tkinter as tk
from dataclasses import dataclass
from tkinter import font
from typing import TYPE_CHECKING, Callable

from asciipal.config import Config

if TYPE_CHECKING:
    from asciipal.app import ColoredDisplay


@dataclass
class MenuCallbacks:
    on_take_break: Callable[[], None]
    on_skip_break: Callable[[], None]
    on_toggle_weather: Callable[[], None]
    on_open_config: Callable[[], None]
    on_quit: Callable[[], None]


COLOR_MAP: dict[str, tuple[str, str]] = {
    "default": ("#3D3B37", "#F7F5F0"),
    "green-terminal": ("#5CAA5C", "#0A1208"),
    "pastel": ("#4A4650", "#F0E6DF"),
    "amber-terminal": ("#D4A050", "#18100A"),
    "ocean": ("#6AACB0", "#0C1620"),
}

# In widget mode the background is transparent/dark, so text must be light.
WIDGET_FG: dict[str, str] = {
    "default": "#E8E0D0",
    "green-terminal": "#5CAA5C",
    "pastel": "#E8DDD6",
    "amber-terminal": "#D4A050",
    "ocean": "#6AACB0",
}

# Per-region foreground colors for each color scheme.
# Keys are (scheme, region_tag) → hex color.  ``None`` means "use scheme fg".
_REGION_COLORS_RAW: dict[str, dict[str, str | None]] = {
    "default": {
        "dino": "#7D9B76",
        "plant": "#5A7A52",
        "border": "#C4BDB2",
        "bubble": "#9AC4D8",
        "firefly": "#E8D5A0",
        "fish": "#C89882",
        "butterfly": "#B8A5C8",
        "snail": "#A09080",
        "cat": "#C8A870",
        "crab": "#B87868",
        "seahorse": "#7BA8A0",
        "weather": "#A8A098",
        "progress": "#9A9488",
        "status": None,
        "achievement": "#C8A060",
        "weather_panel": "#A8A098",
        "sysinfo": "#9A9488",
        "pomodoro": "#B87878",
        "goal": "#C8A868",
        "streak": "#B88860",
        "biome": "#8A7D6D",
        "water": "#8BB8C8",
        "sand": "#B8A898",
        "default": None,
    },
    "green-terminal": {
        "dino": "#5CAA5C",
        "plant": "#4A8A4A",
        "border": "#2A4A20",
        "bubble": "#5A9A9A",
        "firefly": "#B8A860",
        "fish": "#A87858",
        "butterfly": "#8A6A8A",
        "snail": "#7A6A4A",
        "cat": "#9A8A50",
        "crab": "#8A5A4A",
        "seahorse": "#4A8A6A",
        "weather": "#4A7A4A",
        "progress": "#3A6A3A",
        "status": None,
        "achievement": "#B8A050",
        "weather_panel": "#4A7A4A",
        "sysinfo": "#3A6A3A",
        "pomodoro": "#8A5A4A",
        "goal": "#B8A050",
        "streak": "#9A7A40",
        "biome": "#5A5A3A",
        "water": "#4A8A8A",
        "sand": "#5A5030",
        "default": None,
    },
    "pastel": {
        "dino": "#7A9A68",
        "plant": "#8AAA70",
        "border": "#ADA0B8",
        "bubble": "#8AB8D0",
        "firefly": "#D8D0A0",
        "fish": "#D0A8B0",
        "butterfly": "#BEA0BE",
        "snail": "#B8A8A0",
        "cat": "#D0B890",
        "crab": "#C8A0A0",
        "seahorse": "#88B0AA",
        "weather": "#98AEC0",
        "progress": "#B8AAA0",
        "status": None,
        "achievement": "#C8A878",
        "weather_panel": "#98AEC0",
        "sysinfo": "#A8A8B8",
        "pomodoro": "#C8A0A0",
        "goal": "#D0C098",
        "streak": "#C8AA90",
        "biome": "#AAA098",
        "water": "#8AB8D0",
        "sand": "#C0B8B0",
        "default": None,
    },
    "amber-terminal": {
        "dino": "#C08840",
        "plant": "#B89040",
        "border": "#6A5420",
        "bubble": "#C8B890",
        "firefly": "#C8C070",
        "fish": "#B87840",
        "butterfly": "#C0A050",
        "snail": "#8A6030",
        "cat": "#B88840",
        "crab": "#A06830",
        "seahorse": "#C0A048",
        "weather": "#B8A050",
        "progress": "#A89040",
        "status": None,
        "achievement": "#C8B070",
        "weather_panel": "#B8A050",
        "sysinfo": "#A89040",
        "pomodoro": "#A06830",
        "goal": "#C8B070",
        "streak": "#B89040",
        "biome": "#7A6850",
        "water": "#C8B890",
        "sand": "#8A6030",
        "default": None,
    },
    "ocean": {
        "dino": "#5A9A70",
        "plant": "#5A8A60",
        "border": "#2A6080",
        "bubble": "#8AB8C8",
        "firefly": "#C8C090",
        "fish": "#B08868",
        "butterfly": "#8A6AAA",
        "snail": "#7A7068",
        "cat": "#B09868",
        "crab": "#987060",
        "seahorse": "#5A9A90",
        "weather": "#5AA0B0",
        "progress": "#5A98A0",
        "status": None,
        "achievement": "#B8A868",
        "weather_panel": "#5AA0B0",
        "sysinfo": "#4A8A98",
        "pomodoro": "#987060",
        "goal": "#B8A868",
        "streak": "#A08060",
        "biome": "#5A5848",
        "water": "#5AA0B0",
        "sand": "#5A5848",
        "default": None,
    },
}

# Widget-mode variants — light-on-dark.  Same structure as above.
_WIDGET_REGION_COLORS_RAW: dict[str, dict[str, str | None]] = {
    "default": {
        "dino": "#8AAA82",
        "plant": "#6A8A62",
        "border": "#9A9890",
        "bubble": "#7AAAB8",
        "firefly": "#C8C0A0",
        "fish": "#B89880",
        "butterfly": "#A898B0",
        "snail": "#8A8070",
        "cat": "#B8A070",
        "crab": "#A87868",
        "seahorse": "#6A9A90",
        "weather": "#9A9890",
        "progress": "#8A8880",
        "status": None,
        "achievement": "#B8A068",
        "weather_panel": "#9A9890",
        "sysinfo": "#8A8880",
        "pomodoro": "#A87878",
        "goal": "#B8A068",
        "streak": "#A88860",
        "biome": "#7A7868",
        "water": "#7AAAB8",
        "sand": "#9A9080",
        "default": None,
    },
}

ALL_REGION_TAGS = (
    "dino", "plant", "border", "bubble", "firefly",
    "fish", "butterfly", "snail", "cat", "crab", "seahorse",
    "weather", "progress",
    "status", "achievement", "weather_panel", "sysinfo",
    "pomodoro", "goal", "streak", "biome",
    "water", "sand", "default",
)


def _resolve_region_colors(
    scheme: str, fg: str, widget_mode: bool,
) -> dict[str, str]:
    """Return ``{tag: hex_color}`` for the given scheme."""
    if widget_mode:
        raw = _WIDGET_REGION_COLORS_RAW.get(scheme, _WIDGET_REGION_COLORS_RAW.get("default", {}))
    else:
        raw = _REGION_COLORS_RAW.get(scheme, _REGION_COLORS_RAW.get("default", {}))
    result: dict[str, str] = {}
    for tag in ALL_REGION_TAGS:
        color = raw.get(tag)
        result[tag] = color if color is not None else fg
    return result


class Overlay:
    def __init__(self, config: Config, menu_callbacks: MenuCallbacks | None = None) -> None:
        self.config = config
        self._menu_callbacks = menu_callbacks
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

        self.text_widget = tk.Text(
            self.root,
            fg=fg,
            bg=label_bg,
            padx=pad_x,
            pady=pad_y,
            wrap="none",
            state="disabled",
            insertwidth=0,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="fleur",
        )
        base_size = max(int(64 * config.character_scale), 10)
        self._font_size = base_size
        family = self._pick_font_family()
        self.text_font = font.Font(family=family, size=base_size)
        self.text_widget.configure(font=self.text_font)

        # Configure color tags
        self._bold_font = font.Font(family=family, size=base_size, weight="bold")
        region_colors = _resolve_region_colors(config.color_scheme, fg, config.widget_mode)
        for tag, color in region_colors.items():
            if tag == "dino":
                self.text_widget.tag_configure(tag, foreground=color, font=self._bold_font)
            else:
                self.text_widget.tag_configure(tag, foreground=color)

        self._configure_transparency()
        self.text_widget.pack(fill="both", expand=True)

        # Width stabilisation — ratchets up to the widest content seen.
        self._min_text_width = 0
        self._last_plain_text: str | None = None
        self._last_colored_text: str | None = None
        self._last_colored_regions: list[list[str]] | None = None

        # Drag support — bind to both root and text_widget for reliability
        self._user_dragged = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        for widget in (self.root, self.text_widget):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<Double-Button-1>", self._on_double_click)
            # Scroll-wheel zoom (macOS/Windows)
            widget.bind("<MouseWheel>", self._on_mousewheel)
            # Scroll-wheel zoom (Linux)
            widget.bind("<Button-4>", lambda e: self._on_scroll(1))
            widget.bind("<Button-5>", lambda e: self._on_scroll(-1))

        # Context menu
        self._menu: tk.Menu | None = None
        if self._menu_callbacks is not None:
            self._menu = tk.Menu(self.root, tearoff=0)
            self._menu.add_command(label="Take a Break", command=self._menu_callbacks.on_take_break)
            self._menu.add_command(label="Skip Break", command=self._menu_callbacks.on_skip_break)
            self._menu.add_separator()
            self._menu.add_command(label="Toggle Weather", command=self._menu_callbacks.on_toggle_weather)
            self._menu.add_separator()
            self._menu.add_command(label="Open Config", command=self._menu_callbacks.on_open_config)
            self._menu.add_separator()
            self._menu.add_command(label="Quit", command=self._menu_callbacks.on_quit)
            for widget in (self.root, self.text_widget):
                widget.bind("<Button-3>", self._show_context_menu)
                widget.bind("<Button-2>", self._show_context_menu)
                widget.bind("<Control-Button-1>", self._show_context_menu)

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

    def _on_mousewheel(self, event: tk.Event) -> None:
        if platform.system() == "Darwin":
            delta = 1 if event.delta > 0 else -1
        else:
            delta = 1 if event.delta > 0 else -1
        self._on_scroll(delta)

    def _on_scroll(self, delta: int) -> None:
        step = 2 if delta > 0 else -2
        self._font_size = max(8, min(120, self._font_size + step))
        self.text_font.configure(size=self._font_size)
        self._bold_font.configure(size=self._font_size)

    def set_min_width(self, width: int) -> None:
        self._min_text_width = max(self._min_text_width, width)
        self.text_widget.configure(width=self._min_text_width)

    def update_text(self, text: str) -> None:
        """Backward-compatible plain-text update (no color tags)."""
        if text == self._last_plain_text:
            return
        self._last_plain_text = text
        self._last_colored_text = None
        self._last_colored_regions = None

        lines = text.split("\n")
        max_w = max((len(ln) for ln in lines), default=0)
        if max_w > self._min_text_width:
            self._min_text_width = max_w
            self.text_widget.configure(width=self._min_text_width)
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)
        self.text_widget.configure(state="disabled")
        self.root.update_idletasks()
        if not self._user_dragged:
            self._place_window()

    def update_colored(self, display: ColoredDisplay) -> None:
        """Update the widget with colored text using region tags."""
        text = display.text
        regions = display.regions
        if text == self._last_colored_text and self._last_colored_regions == regions:
            return
        self._last_colored_text = text
        # Store a snapshot to avoid issues if caller mutates after passing.
        self._last_colored_regions = [row[:] for row in regions]
        self._last_plain_text = None

        lines = text.split("\n")
        max_w = max((len(ln) for ln in lines), default=0)
        if max_w > self._min_text_width:
            self._min_text_width = max_w
            self.text_widget.configure(width=self._min_text_width)

        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)

        # Apply color tags row by row
        for row_idx, row_tags in enumerate(regions):
            if row_idx >= len(lines):
                break
            line = lines[row_idx]
            tk_row = row_idx + 1  # tk.Text lines are 1-indexed
            col = 0
            while col < len(row_tags) and col < len(line):
                tag = row_tags[col]
                if tag == "default":
                    col += 1
                    continue
                # Find the end of this contiguous span of the same tag
                span_start = col
                while col < len(row_tags) and col < len(line) and row_tags[col] == tag:
                    col += 1
                start_idx = f"{tk_row}.{span_start}"
                end_idx = f"{tk_row}.{col}"
                self.text_widget.tag_add(tag, start_idx, end_idx)

        self.text_widget.configure(state="disabled")
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

    def _show_context_menu(self, event: tk.Event) -> None:
        if self._menu is not None:
            self._menu.tk_popup(event.x_root, event.y_root)

    def _transparent_bg_color(self) -> str:
        return "#1E1D1B"
