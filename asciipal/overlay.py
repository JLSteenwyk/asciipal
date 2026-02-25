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
    "default": ("#111111", "#f5f5f5"),
    "green-terminal": ("#7CFC00", "#001100"),
    "pastel": ("#2d3142", "#f4d6cc"),
    "amber-terminal": ("#FFB000", "#1A0A00"),
    "ocean": ("#00CED1", "#0A1628"),
}

# In widget mode the background is transparent/dark, so text must be light.
WIDGET_FG: dict[str, str] = {
    "default": "#FFFFFF",
    "green-terminal": "#7CFC00",
    "pastel": "#f4d6cc",
    "amber-terminal": "#FFB000",
    "ocean": "#00CED1",
}

# Per-region foreground colors for each color scheme.
# Keys are (scheme, region_tag) → hex color.  ``None`` means "use scheme fg".
_REGION_COLORS_RAW: dict[str, dict[str, str | None]] = {
    "default": {
        "dino": "#4CAF50",
        "plant": "#2E7D32",
        "border": "#9E9E9E",
        "bubble": "#42A5F5",
        "firefly": "#FFD54F",
        "fish": "#FF7043",
        "butterfly": "#CE93D8",
        "snail": "#8D6E63",
        "weather": "#90A4AE",
        "progress": "#78909C",
        "status": None,
        "achievement": "#FFA000",
        "weather_panel": "#90A4AE",
        "sysinfo": "#78909C",
        "default": None,
    },
    "green-terminal": {
        "dino": "#00FF7F",
        "plant": "#32CD32",
        "border": "#3A5F0B",
        "bubble": "#00FFFF",
        "firefly": "#FFFF00",
        "fish": "#FF6347",
        "butterfly": "#FF69B4",
        "snail": "#CD853F",
        "weather": "#66BB6A",
        "progress": "#4CAF50",
        "status": None,
        "achievement": "#FFD700",
        "weather_panel": "#66BB6A",
        "sysinfo": "#4CAF50",
        "default": None,
    },
    "pastel": {
        "dino": "#6A994E",
        "plant": "#A7C957",
        "border": "#B8A9C9",
        "bubble": "#89CFF0",
        "firefly": "#FDFD96",
        "fish": "#FFB7C5",
        "butterfly": "#DDA0DD",
        "snail": "#C9ADA7",
        "weather": "#A0C4FF",
        "progress": "#C9ADA7",
        "status": None,
        "achievement": "#F4A261",
        "weather_panel": "#A0C4FF",
        "sysinfo": "#B8C0D0",
        "default": None,
    },
    "amber-terminal": {
        "dino": "#FF6F00",
        "plant": "#FFAB00",
        "border": "#8D6E00",
        "bubble": "#FFECB3",
        "firefly": "#FFFF8D",
        "fish": "#FF8F00",
        "butterfly": "#FFD700",
        "snail": "#D2691E",
        "weather": "#FFD54F",
        "progress": "#FFC107",
        "status": None,
        "achievement": "#FFE082",
        "weather_panel": "#FFD54F",
        "sysinfo": "#FFC107",
        "default": None,
    },
    "ocean": {
        "dino": "#00E676",
        "plant": "#66BB6A",
        "border": "#0277BD",
        "bubble": "#B3E5FC",
        "firefly": "#FFF59D",
        "fish": "#FF8A65",
        "butterfly": "#E040FB",
        "snail": "#A1887F",
        "weather": "#4FC3F7",
        "progress": "#4DD0E1",
        "status": None,
        "achievement": "#FFD54F",
        "weather_panel": "#4FC3F7",
        "sysinfo": "#26C6DA",
        "default": None,
    },
}

# Widget-mode variants — light-on-dark.  Same structure as above.
_WIDGET_REGION_COLORS_RAW: dict[str, dict[str, str | None]] = {
    "default": {
        "dino": "#66BB6A",
        "plant": "#43A047",
        "border": "#B0BEC5",
        "bubble": "#64B5F6",
        "firefly": "#FFE082",
        "fish": "#FF8A65",
        "butterfly": "#CE93D8",
        "snail": "#A1887F",
        "weather": "#B0BEC5",
        "progress": "#90A4AE",
        "status": None,
        "achievement": "#FFB300",
        "weather_panel": "#B0BEC5",
        "sysinfo": "#90A4AE",
        "default": None,
    },
}

ALL_REGION_TAGS = (
    "dino", "plant", "border", "bubble", "firefly",
    "fish", "butterfly", "snail", "weather", "progress",
    "status", "achievement", "weather_panel", "sysinfo", "default",
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
        family = self._pick_font_family()
        self.text_font = font.Font(family=family, size=base_size)
        self.text_widget.configure(font=self.text_font)

        # Configure color tags
        region_colors = _resolve_region_colors(config.color_scheme, fg, config.widget_mode)
        for tag, color in region_colors.items():
            self.text_widget.tag_configure(tag, foreground=color)

        self._configure_transparency()
        self.text_widget.pack(fill="both", expand=True)

        # Width stabilisation — ratchets up to the widest content seen.
        self._min_text_width = 0

        # Drag support — bind to both root and text_widget for reliability
        self._user_dragged = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        for widget in (self.root, self.text_widget):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<Double-Button-1>", self._on_double_click)

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

    def set_min_width(self, width: int) -> None:
        self._min_text_width = max(self._min_text_width, width)
        self.text_widget.configure(width=self._min_text_width)

    def update_text(self, text: str) -> None:
        """Backward-compatible plain-text update (no color tags)."""
        lines = text.split("\n")
        max_w = max((len(l) for l in lines), default=0)
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

        lines = text.split("\n")
        max_w = max((len(l) for l in lines), default=0)
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
        return "#1a1a2e"
