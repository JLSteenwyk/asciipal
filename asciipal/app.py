from __future__ import annotations

import argparse
import platform
import subprocess
from dataclasses import asdict
import signal
import sys
from time import sleep
from time import monotonic

from asciipal.achievements import AchievementManager
from asciipal.activity_tracker import ActivityTracker
from asciipal.break_manager import BreakManager, BreakStatus
from asciipal.character import CharacterRenderer
import yaml

from asciipal.config import Config, ensure_config_file, load_config, resolve_config_path
from asciipal.input_monitor import InputCallbacks, InputMonitor
from asciipal.overlay import MenuCallbacks, Overlay
from asciipal.platform_support import runtime_summary, startup_warnings
from asciipal.state_machine import StateMachine
from asciipal.time_awareness import TimeAwarenessManager
from asciipal.weather import WeatherManager


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
        self.tracker = ActivityTracker()
        self.state_machine = StateMachine(config)
        self.break_manager = BreakManager(config)
        self.character = CharacterRenderer(config)
        self.time_awareness = TimeAwarenessManager(config)
        self.achievements = AchievementManager()
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
                self.overlay.set_min_width(self.character.max_art_width)
            except Exception as exc:
                self.headless = True
                self.startup_notes.append(f"GUI overlay unavailable: {exc}. Falling back to headless mode.")
        self.weather = WeatherManager(config)
        self.input_monitor = InputMonitor(
            InputCallbacks(
                on_keypress=self.tracker.record_keypress,
                on_click=self.tracker.record_click,
                on_mouse_move=self.tracker.record_mouse_move,
            )
        )

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
        effect = self.weather.current_effect(self._anim_frame)
        if effect is not None:
            art_width = max((len(line) for line in art.splitlines()), default=0)
            above, below = effect
            if above:
                art = f"{above:^{art_width}}\n{art}"
            if below:
                art = f"{art}\n{below:^{art_width}}"
        time_effect = self.time_awareness.current_effect(self._anim_frame)
        if time_effect is not None:
            art_width = max((len(line) for line in art.splitlines()), default=0)
            t_above, t_below = time_effect
            if t_above:
                art = f"{t_above:^{art_width}}\n{art}"
            if t_below:
                art = f"{art}\n{t_below:^{art_width}}"
        if break_line:
            art = f"{art}\n{break_line}"
        totals = self.tracker.totals(now=now)
        achievement_line = self.achievements.update(totals, self.break_manager.breaks_taken)
        if achievement_line:
            art = f"{art}\n{achievement_line}"
        if self.overlay is not None:
            self.overlay.update_text(art)
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
