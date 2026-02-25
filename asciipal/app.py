from __future__ import annotations

import argparse
import platform
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
import signal
import sys
from time import sleep
from time import monotonic

from asciipal.achievements import AchievementManager
from asciipal.activity_tracker import ActivityTracker
from asciipal.aquarium import build_aquarium_scene, biome_stage, build_biome_decorations
from asciipal.battery import BatteryManager
from asciipal.break_manager import BreakManager, BreakStatus
from asciipal.character import CharacterRenderer
from asciipal.effects import EffectsManager
import yaml

from asciipal.config import Config, ensure_config_file, load_config, resolve_config_path
from asciipal.input_monitor import InputCallbacks, InputMonitor
from asciipal.overlay import MenuCallbacks, Overlay
from asciipal.platform_support import runtime_summary, startup_warnings
from asciipal.state_machine import StateMachine
from asciipal.system_resources import SystemResourcesManager
from asciipal.time_awareness import TimeAwarenessManager
from asciipal.weather import WeatherManager


def _make_wave(length: int) -> str:
    """Generate a ``~.`` wave pattern of exactly *length* characters."""
    unit = "~."
    return (unit * ((length + 1) // 2))[:length]


def _merge_plants(char_art: str, plant_lines: list[str], content_w: int) -> list[str]:
    """Overlay plant characters onto centered character art lines.

    Plants align to the bottom of the character art and only fill spaces
    so they appear to grow *around* the character.
    """
    char_lines = char_art.split("\n")
    centered = [f"{line:^{content_w}}" for line in char_lines]
    if not plant_lines:
        return centered

    result_height = max(len(centered), len(plant_lines))
    # Pad centered lines at the top if plants are taller than the character
    while len(centered) < result_height:
        centered.insert(0, " " * content_w)

    plant_start = result_height - len(plant_lines)
    merged: list[str] = []
    for i, line in enumerate(centered):
        plant_idx = i - plant_start
        if 0 <= plant_idx < len(plant_lines):
            buf = list(line.ljust(content_w))
            plant_line = plant_lines[plant_idx]
            for j, ch in enumerate(plant_line):
                if j < content_w and ch != " " and buf[j] == " ":
                    buf[j] = ch
            merged.append("".join(buf))
        else:
            merged.append(line)
    return merged


@dataclass
class ColoredDisplay:
    text: str
    regions: list[list[str]]  # regions[row][col] = tag name


def _merge_plants_colored(
    char_art: str, plant_lines: list[str], content_w: int,
) -> tuple[list[str], list[list[str]]]:
    """Like ``_merge_plants`` but also returns a per-cell region grid.

    Dinosaur characters are tagged ``"dino"``, plant characters ``"plant"``,
    and spaces ``"default"``.
    """
    char_lines = char_art.split("\n")
    centered = [f"{line:^{content_w}}" for line in char_lines]
    if not plant_lines:
        regions = []
        for line in centered:
            row_tags = ["dino" if ch != " " else "default" for ch in line]
            regions.append(row_tags)
        return centered, regions

    result_height = max(len(centered), len(plant_lines))
    while len(centered) < result_height:
        centered.insert(0, " " * content_w)

    plant_start = result_height - len(plant_lines)
    merged: list[str] = []
    regions: list[list[str]] = []
    for i, line in enumerate(centered):
        plant_idx = i - plant_start
        if 0 <= plant_idx < len(plant_lines):
            buf = list(line.ljust(content_w))
            tag_row = ["dino" if ch != " " else "default" for ch in buf]
            plant_line = plant_lines[plant_idx]
            for j, ch in enumerate(plant_line):
                if j < content_w and ch != " " and buf[j] == " ":
                    buf[j] = ch
                    tag_row[j] = "plant"
            merged.append("".join(buf))
            regions.append(tag_row)
        else:
            row_tags = ["dino" if ch != " " else "default" for ch in line]
            merged.append(line)
            regions.append(row_tags)
    return merged, regions


def _compose_display(
    char_art: str,
    above_lines: list[str],
    plant_lines: list[str],
    progress_line: str,
    status_line: str,
    achievement_line: str,
    inner_w: int,
    overlays: list[tuple[int, int, str, str]] | None = None,
    weather_panel_lines: list[str] | None = None,
    sysinfo_lines: list[str] | None = None,
    anim_frame: int = 0,
    pomodoro_panel_lines: list[str] | None = None,
    goal_line: str = "",
    streak_line: str = "",
    biome_decorations: list[tuple[int, int, str]] | None = None,
) -> ColoredDisplay:
    """Build the aquarium display with water surface and sandy ground.

    Weather effects go above the character. Plants grow around the
    character. Effect overlays (bubbles, fireflies, creatures) fill
    empty spaces. Progress bar sits below the aquarium ground.

    Returns a ``ColoredDisplay`` with both the text and per-cell region tags.
    """
    # Sandy ground: soft dot pattern (borderless)
    sand_unit = "·."
    sand_fill = (sand_unit * ((inner_w + 1) // 2))[:inner_w]
    total_w = inner_w
    content_w = inner_w

    # Build content lines and region grid, all exactly content_w wide
    content_lines: list[str] = []
    content_regions: list[list[str]] = []

    # Water surface row — slow 4-phase drift for a calm, tranquil feel
    _surface_phases = (
        " · . · . · . ·",
        "· . · . · . · .",
        ". · . · . · . ·",
        " . · . · . · . ",
    )
    phase = _surface_phases[anim_frame % len(_surface_phases)]
    water_surface = (phase * ((content_w + len(phase) - 1) // len(phase)))[:content_w]
    content_lines.append(water_surface)
    content_regions.append(["water"] * content_w)

    for line in above_lines:
        if line.strip():
            centered = f"{line:^{content_w}}"
            content_lines.append(centered)
            content_regions.append(
                ["weather" if ch != " " else "default" for ch in centered]
            )

    merged_lines, merged_regions = _merge_plants_colored(char_art, plant_lines, content_w)
    for line, region_row in zip(merged_lines, merged_regions):
        centered = f"{line:^{content_w}}"
        # Re-check: centered may already be content_w wide from _merge_plants_colored
        if len(region_row) < content_w:
            extra = content_w - len(region_row)
            left_pad = extra // 2
            right_pad = extra - left_pad
            region_row = ["default"] * left_pad + region_row + ["default"] * right_pad
        content_lines.append(centered)
        content_regions.append(region_row[:content_w])

    # Apply biome decorations (only fill empty spaces)
    if biome_decorations:
        for row_idx, col, ch in biome_decorations:
            if 0 <= row_idx < len(content_lines) and 0 <= col < content_w:
                line = content_lines[row_idx]
                if col < len(line) and line[col] == " ":
                    content_lines[row_idx] = line[:col] + ch + line[col + 1:]
                    content_regions[row_idx][col] = "biome"

    # Apply effect overlays (only fill empty spaces)
    if overlays:
        for row_idx, col, ch, tag in overlays:
            if 0 <= row_idx < len(content_lines) and 0 <= col < content_w:
                line = content_lines[row_idx]
                if col < len(line) and line[col] == " ":
                    content_lines[row_idx] = line[:col] + ch + line[col + 1:]
                    content_regions[row_idx][col] = tag

    # Occasional water movement — a few drifting ~ chars, very sparse
    slow_frame = anim_frame // 3
    for row_idx in range(1, len(content_lines)):
        line = content_lines[row_idx]
        regions = content_regions[row_idx]
        buf = list(line)
        for col in range(len(buf)):
            if buf[col] == " " and regions[col] == "default":
                if (row_idx * 13 + col + slow_frame) % 31 == 0:
                    buf[col] = "~"
                    regions[col] = "water"
        content_lines[row_idx] = "".join(buf)

    # Build output parts and region rows (borderless)
    parts: list[str] = []
    all_regions: list[list[str]] = []

    for i, line in enumerate(content_lines):
        parts.append(line)
        all_regions.append(content_regions[i])

    parts.append(sand_fill)
    all_regions.append(["sand"] * total_w)

    if progress_line:
        centered = f"{progress_line:^{total_w}}"
        parts.append(centered)
        all_regions.append(
            ["progress" if ch != " " else "default" for ch in centered]
        )
    if status_line:
        centered = f"{status_line:^{total_w}}"
        parts.append(centered)
        all_regions.append(
            ["status" if ch != " " else "default" for ch in centered]
        )
    if achievement_line:
        centered = f"{achievement_line:^{total_w}}"
        parts.append(centered)
        all_regions.append(
            ["achievement" if ch != " " else "default" for ch in centered]
        )
    if goal_line:
        centered = f"{goal_line:^{total_w}}"
        parts.append(centered)
        all_regions.append(
            ["goal" if ch != " " else "default" for ch in centered]
        )
    if streak_line:
        centered = f"{streak_line:^{total_w}}"
        parts.append(centered)
        all_regions.append(
            ["streak" if ch != " " else "default" for ch in centered]
        )

    # Sub-panels below the aquarium
    sysinfo_content = sysinfo_lines if sysinfo_lines else []
    for panel_tag, panel_title, panel_content_lines in [
        ("pomodoro", "Pomodoro", pomodoro_panel_lines or []),
        ("weather_panel", "Weather", weather_panel_lines or []),
        ("sysinfo", "System", sysinfo_content),
    ]:
        if not panel_content_lines:
            continue
        # Blank separator
        parts.append("")
        all_regions.append(["default"] * total_w)
        # Top border:  ╭── Title ──...──╮
        label = f"── {panel_title} "
        fill_len = max(total_w - 2 - len(label), 0)
        top_border = f"╭{label}{'─' * fill_len}╮"
        parts.append(top_border)
        all_regions.append([panel_tag] * len(top_border))
        # Content rows
        for cl in panel_content_lines:
            padded = f"{cl:^{total_w - 4}}"
            row = f"│ {padded} │"
            row_tags = (
                [panel_tag]  # │
                + ["default"]  # space
                + [panel_tag if ch != " " else "default" for ch in padded]
                + ["default"]  # space
                + [panel_tag]  # │
            )
            parts.append(row)
            all_regions.append(row_tags)
        # Bottom border
        bot_border = f"╰{'─' * (total_w - 2)}╯"
        parts.append(bot_border)
        all_regions.append([panel_tag] * len(bot_border))

    return ColoredDisplay(text="\n".join(parts), regions=all_regions)


class AsciiPalApp:
    def __init__(
        self,
        config: Config,
        headless: bool = False,
        max_ticks: int | None = None,
        duration_seconds: int | None = None,
        demo: bool = False,
        show_summary: bool = True,
    ) -> None:
        self.config = config
        self.headless = headless
        self.max_ticks = max_ticks
        self.duration_seconds = duration_seconds
        self.demo = demo
        self.show_summary = show_summary
        self.startup_notes: list[str] = []
        self._running = True
        self._shutdown_done = False
        self._start_time = monotonic()
        self._last_headless_line = ""
        self._demo_ticks = 0
        self._demo_time = monotonic()
        self._anim_frame = 0
        self._anim_tick_counter = 0
        self._eating_ticks = 0
        self._eating_cooldown = 20
        self.tracker = ActivityTracker()
        self.state_machine = StateMachine(config)
        self.break_manager = BreakManager(config)
        self.character = CharacterRenderer(config)
        self.time_awareness = TimeAwarenessManager(config)
        self.achievements = AchievementManager()
        self.effects = EffectsManager()
        # Fixed inner width for the aquarium (must be even for wave pattern).
        raw_inner = max(self.character.max_art_width + 16, 36)
        self._display_inner_w = raw_inner + (raw_inner % 2)
        self.overlay = None
        if not headless:
            try:
                callbacks = MenuCallbacks(
                    on_take_break=self._menu_take_break,
                    on_skip_break=self._menu_skip_break,
                    on_toggle_weather=self._menu_toggle_weather,
                    on_open_config=self._menu_open_config,
                    on_quit=self._menu_quit,
                )
                self.overlay = Overlay(config, menu_callbacks=callbacks)
                self.overlay.set_min_width(self._display_inner_w)
            except Exception as exc:
                self.headless = True
                self.startup_notes.append(f"GUI overlay unavailable: {exc}. Falling back to headless mode.")
        self._goal_met = False
        self._last_session_seconds: float = 0.0
        self.weather = WeatherManager(config)
        self.system_resources = SystemResourcesManager()
        self.battery: BatteryManager | None = None
        if getattr(config, "battery_enabled", True):
            self.battery = BatteryManager()
        self.input_monitor = InputMonitor(
            InputCallbacks(
                on_keypress=self.tracker.record_keypress,
                on_click=self.tracker.record_click,
                on_mouse_move=self.tracker.record_mouse_move,
            )
        )

    def _build_pomodoro_lines(self, status: BreakStatus) -> list[str] | None:
        if not self.config.pomodoro_mode:
            return None
        if status.stage == "on_break":
            remaining = int(status.break_seconds_remaining)
            mins, secs = divmod(remaining, 60)
            return [f"\u00b7 rest: {mins}:{secs:02d}"]
        remaining = int(status.seconds_until_break)
        mins, secs = divmod(remaining, 60)
        return [f"\u00b7 focus: {mins}:{secs:02d}"]

    def _build_goal_line(self, totals, width: int) -> str:
        goal = getattr(self.config, "session_goal_minutes", 0)
        if goal <= 0:
            return ""
        elapsed_minutes = int(totals.total_active_seconds / 60)
        if elapsed_minutes >= goal:
            return "\u2022 goal reached"
        bar_w = min(10, width - 20)
        if bar_w < 1:
            bar_w = 1
        filled = int(bar_w * elapsed_minutes / goal)
        filled = max(0, min(filled, bar_w))
        bar = "\u25b0" * filled + "\u25b1" * (bar_w - filled)
        return f"\u2022 goal: {elapsed_minutes}m/{goal}m [{bar}]"

    def run(self) -> None:
        if not self.demo:
            self.input_monitor.start()
        self.weather.start()
        self._register_signal_handlers()
        if self.headless:
            tick_count = 0
            while self._running:
                self.tick()
                tick_count += 1
                if self.max_ticks is not None and tick_count >= self.max_ticks:
                    break
                sleep(0.25)
        else:
            assert self.overlay is not None
            self.overlay.run(self.tick)
        self.shutdown()
        if self.show_summary:
            self.print_summary()

    def tick(self) -> None:
        wall_now = monotonic()
        now = self._demo_time if self.demo else monotonic()
        if self.demo:
            self._simulate_input(now)
        snapshot = self.tracker.snapshot(now)
        break_status = self.break_manager.update(snapshot, now)
        transition = self.state_machine.update(snapshot, now)
        if transition.changed:
            self._anim_frame = 0
            self._anim_tick_counter = 0
        self._anim_tick_counter += 1
        if self._anim_tick_counter >= 3:
            self._anim_tick_counter = 0
            self._anim_frame += 1
        state, break_line = self._render_status(transition.state, break_status)
        art = self.character.art_for(state, self._anim_frame)

        # Collect decoration lines — only time effects go above the character
        above_lines: list[str] = []
        time_effect = self.time_awareness.current_effect(self._anim_frame)
        weather_effect = self.weather.current_effect(self._anim_frame)
        if time_effect is not None and time_effect[0]:
            above_lines.append(time_effect[0])

        # Build weather panel content (rendered below aquarium)
        weather_panel_lines: list[str] | None = None
        if weather_effect is not None and weather_effect[0]:
            condition_name = self.weather.current_condition_name() or ""
            weather_panel_lines = [f"{weather_effect[0]}  {condition_name}"]

        # Build system resources lines
        sysinfo_lines: list[str] = []
        if self.config.system_resources_enabled:
            sysinfo_lines = self.system_resources.format_lines()
            if getattr(self.config, 'cpu_load_enabled', True):
                snap = self.system_resources.snapshot()
                if snap is not None:
                    sysinfo_lines.append(f"CPU Load: {snap.cpu_load:.1f}")
                    if self.system_resources.is_system_saturated(
                        getattr(self.config, 'sweating_load_threshold', 0.8)
                    ):
                        self.state_machine.set_sweating(True)
                    else:
                        self.state_machine.set_sweating(False)

        # Battery info
        if self.battery is not None and getattr(self.config, 'battery_enabled', True):
            batt_line = self.battery.format_line()
            if batt_line is not None:
                sysinfo_lines.append(batt_line)

        # Aquarium scene: plants around character, progress bar below
        totals = self.tracker.totals(now=now)
        content_w = self._display_inner_w
        progress_lines, plant_lines = build_aquarium_scene(
            totals, content_w, self._anim_frame,
        )
        progress_line = progress_lines[0] if progress_lines else ""

        # Eating animation: dino leans down to munch on nearby plants
        if self._eating_ticks > 0:
            self._eating_ticks -= 1
            state = "eating"
            art = self.character.art_for(state, self._anim_frame)
        elif state == "idle" and plant_lines and self._eating_cooldown <= 0:
            self._eating_ticks = 8
            self._eating_cooldown = 40
            state = "eating"
            art = self.character.art_for(state, self._anim_frame)
        else:
            self._eating_cooldown -= 1

        # Effects: bubbles, fireflies, companion creatures
        non_empty_above = [x for x in above_lines if x.strip()]
        char_lines = art.split("\n")
        content_h = len(non_empty_above) + max(len(char_lines), len(plant_lines))
        hour = datetime.now().hour
        is_night = hour >= 21 or hour < 6
        is_flow = state in ("excited", "cheering")
        overlays = self.effects.update(
            totals, self.break_manager.breaks_taken,
            content_w, content_h, self._anim_frame,
            is_night=is_night, is_flow=is_flow,
        )

        achievement_line = self.achievements.update(totals, self.break_manager.breaks_taken)

        # Daily streaks
        session_seconds = totals.total_active_seconds
        delta = session_seconds - self._last_session_seconds
        self._last_session_seconds = session_seconds
        self.achievements.update_use_streak(delta)
        self.achievements.update_monthly_active(delta)
        streak_line = self.achievements.streak_line()

        # Session goals
        goal_line = self._build_goal_line(totals, content_w)
        if goal_line and "GOAL MET" in goal_line and not self._goal_met:
            self._goal_met = True
            self.state_machine.force_state("cheering")

        # Pomodoro panel
        pomodoro_lines = self._build_pomodoro_lines(break_status)

        # Biome decorations
        monthly_hours = self.achievements.current_monthly_hours()
        stage = biome_stage(monthly_hours)
        import random as _rng_mod
        biome_rng = _rng_mod.Random(stage * 1000 + content_w)
        biome_decs = build_biome_decorations(stage, content_w, content_h, self._anim_frame, biome_rng)

        if self.overlay is not None:
            colored = _compose_display(
                art, above_lines, plant_lines,
                progress_line, break_line, achievement_line or "",
                self._display_inner_w,
                overlays=overlays,
                weather_panel_lines=weather_panel_lines,
                sysinfo_lines=sysinfo_lines,
                anim_frame=self._anim_frame,
                pomodoro_panel_lines=pomodoro_lines,
                goal_line=goal_line,
                streak_line=streak_line,
                biome_decorations=biome_decs,
            )
            self.overlay.update_colored(colored)
        else:
            line = f"State={state}"
            if break_line:
                line += f" {break_line}"
            if line != self._last_headless_line:
                print(line)
                self._last_headless_line = line

        if self.duration_seconds is not None and wall_now - self._start_time >= self.duration_seconds:
            self._running = False
            if self.overlay is not None:
                self.overlay.root.quit()

    def _render_status(self, current_state: str, status: BreakStatus) -> tuple[str, str]:
        mode = self.config.notifications
        if mode == "silent":
            return current_state, ""

        if status.stage == "on_break":
            if mode == "verbose":
                minutes = int((status.break_seconds_remaining + 59) // 60)
                return "sleeping", f"Break: resting ({minutes}m left)"
            return "sleeping", "Break: resting"

        if status.should_break:
            if status.stage in {"insistence", "tantrum"}:
                state = "alarmed"
            else:
                state = "watching"
            if mode == "verbose":
                return state, f"Break: {status.stage} (due now)"
            return state, f"Break: {status.stage}"

        if mode == "verbose" and status.stage == "suggestion":
            minutes = int((status.seconds_until_break + 59) // 60)
            return current_state, f"Break soon: {minutes}m"

        return current_state, ""

    def _simulate_input(self, now: float) -> None:
        phase = self._demo_ticks % 80
        if phase < 12:
            pass
        elif phase < 28:
            if self._demo_ticks % 2 == 0:
                self.tracker.record_keypress(now)
        elif phase < 44:
            self.tracker.record_keypress(now)
        elif phase < 56:
            self.tracker.record_mouse_move(320, 280, now)
        elif phase < 68:
            self.tracker.record_click(now)
            self.tracker.record_click(now)
        else:
            pass
        self._demo_ticks += 1
        self._demo_time += 5.0

    def print_summary(self) -> None:
        totals = self.tracker.totals(now=self._demo_time if self.demo else monotonic())
        print("Session summary")
        print(f"  active_seconds={int(totals.total_active_seconds)}")
        print(f"  keypresses={totals.total_keypresses}")
        print(f"  clicks={totals.total_clicks}")
        print(f"  mouse_distance={int(totals.total_mouse_distance)}")
        print(f"  breaks_taken={self.break_manager.breaks_taken}")
        print(f"  break_seconds={int(self.break_manager.total_break_seconds)}")

    def shutdown(self) -> None:
        if self._shutdown_done:
            return
        self._shutdown_done = True
        self._running = False
        self.achievements.update_break_streak()
        self.achievements.save()
        self.weather.stop()
        self.input_monitor.stop()
        try:
            if self.overlay is not None:
                self.overlay.root.quit()
                self.overlay.root.destroy()
        except Exception:
            pass

    def _menu_take_break(self) -> None:
        self.break_manager.force_break()

    def _menu_skip_break(self) -> None:
        self.break_manager.skip_break()

    def _menu_toggle_weather(self) -> None:
        self.config.weather_enabled = not self.config.weather_enabled
        if self.config.weather_enabled:
            self.weather.start()
        else:
            self.weather.stop()
            self.weather.clear_effect()

    def _menu_open_config(self) -> None:
        config_path = str(resolve_config_path())
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", config_path])
        elif system == "Windows":
            subprocess.Popen(["notepad", config_path])
        else:
            subprocess.Popen(["xdg-open", config_path])

    def _menu_quit(self) -> None:
        self.shutdown()

    def _register_signal_handlers(self) -> None:
        def _handle(_sig, _frame) -> None:
            self.shutdown()
            raise SystemExit(0)

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASCII desktop companion")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create config file with defaults if missing, then exit.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print effective config and exit.",
    )
    parser.add_argument(
        "--print-state",
        action="store_true",
        help="Run one snapshot tick and print computed state to stdout",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without Tkinter overlay (debug mode).",
    )
    parser.add_argument(
        "--max-ticks",
        type=int,
        default=None,
        help="Maximum ticks for headless mode.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Print runtime diagnostics and exit.",
    )
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=None,
        help="Stop the app automatically after N seconds.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run without real input and generate synthetic activity for testing.",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Disable session summary output at exit.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print lifetime stats and achievements, then exit.",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    if args.init_config:
        path = ensure_config_file(path=None if args.config is None else args.config)
        print(path)
        return 0
    config = load_config(path=None if args.config is None else args.config)
    if args.print_config:
        print(yaml.safe_dump(asdict(config), sort_keys=False).strip())
        return 0
    if args.stats:
        mgr = AchievementManager()
        print(mgr.format_stats_report())
        return 0
    if args.print_state:
        tracker = ActivityTracker()
        snapshot = tracker.snapshot()
        state = StateMachine(config).update(snapshot).state
        print(state)
        return 0

    app = AsciiPalApp(
        config,
        headless=args.headless,
        max_ticks=args.max_ticks,
        duration_seconds=args.duration_seconds,
        demo=args.demo,
        show_summary=not args.no_summary,
    )
    for warning in startup_warnings():
        print(f"Note: {warning}", file=sys.stderr)
    for note in app.startup_notes:
        print(f"Note: {note}", file=sys.stderr)
    if not app.input_monitor.is_supported():
        print(
            "Warning: global input monitor unavailable. Check platform permissions/runtime.",
            file=sys.stderr,
        )
    if args.doctor:
        for line in runtime_summary(
            input_supported=app.input_monitor.is_supported(),
            headless=app.headless,
            pomodoro_mode=config.pomodoro_mode,
        ):
            print(line)
        return 0
    app.run()
    return 0
