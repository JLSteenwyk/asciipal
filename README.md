# AsciiPal — Your ASCII Desktop Companion

> A lightweight desktop pet that watches your keyboard and mouse activity, reacts with expressive ASCII art animations, and reminds you to take breaks.

```
              .
               __
              / _)
     _.----._/ /
    /         /
 __/ (  | (  |
/__.-'|_|--|_|
```

## Overview

AsciiPal is a small, always-on-top desktop companion rendered entirely in ASCII/Unicode characters. It lives in a transparent overlay on your screen, passively monitors your input activity (keystrokes, mouse movement, clicks), and responds with personality — celebrating productivity streaks, reacting to frantic clicking, dozing off when you're idle, and gently nudging you to take breaks.

Think of it as a modern, privacy-respecting, open-source take on the classic desktop pet — minus the bloat, minus the malware.

## Features

### Reactive Character States

AsciiPal transitions between 9 expressive states based on your input patterns:

| State | Trigger | Description |
|-------|---------|-------------|
| **Idle** | No input for 10s | Default resting state |
| **Sleeping** | No input for 2min | Dozing off |
| **Watching** | Slow, steady typing | Paying attention |
| **Excited** | Fast typing (80+ WPM) | Celebrating your flow |
| **Dizzy** | Rapid mouse movement | Overwhelmed by motion |
| **Alarmed** | Rage-clicking (5+/sec) | Startled by clicks |
| **Cheering** | 45min productivity streak | Celebrating you |
| **Sweating** | High CPU load | Feeling the heat |
| **Eating** | Idle with plants nearby | Munching on the garden |

Each state has custom 2-frame ASCII art animations bundled in `asciipal/assets/art/`.

### Break Reminders

- Configurable activity-based break timer (default: every 25 minutes)
- **Pomodoro mode** with separate work/break cycle timers
- Gentle escalation: suggestion → insistence → tantrum
- Right-click context menu to take or skip breaks
- Tracks breaks taken per session and across days

### Living Aquarium

Your workspace is an underwater scene with a water surface, sandy ground, and a garden that grows with your activity.

**Plant growth** progresses through 8 levels as you accumulate active time:

| Level | Active Time | Garden |
|-------|-------------|--------|
| 1 | 5 min | 1 sprout |
| 2 | 10 min | Sprout grows |
| 3 | 20 min | 2nd sprout appears |
| 4 | 30 min | Both grow |
| 5 | 45 min | 3rd sprout |
| 6 | 1 hour | All grow taller |
| 7 | 90 min | 4th plant |
| 8 | 2 hours | Full garden with flowers |

Plants evolve from sprouts (`i`) to buds to blooms (`\w/`) to flowers (`(@)`). A progress bar below the scene shows how close you are to the next level.

**Biome decorations** appear as you accumulate monthly active hours, adding ambient detail to the scene.

### Bubbles, Fireflies & Companions

- **Rising bubbles** float upward, spawning faster with more activity
- **Fireflies** drift and blink around the character at night or during flow states
- **Companion creatures** unlock as you hit milestones:

| Creature | Sprite | Unlock |
|----------|--------|--------|
| Fish | `><>` | 500 keypresses |
| Butterfly | `}{` | 30 min active time |
| Snail | `@/` | 3 breaks taken |
| Cat | `=^.^=` | 2,000 keypresses |
| Crab | `V(;,;)V` | 83 min active time |
| Seahorse | `S~` | 10 breaks taken |

All effects overlay in empty spaces — they never obscure the character or plants.

### Weather

When enabled, AsciiPal fetches real weather data from [wttr.in](https://wttr.in) and displays conditions in a panel below the aquarium. Supports 8 conditions: clear, cloudy, rain, heavy rain, snow, thunder, fog, and sleet.

### Time Awareness

Optional sky effects based on time of day — sun in the morning, half-moons in the evening, stars and a crescent at night.

### System Monitoring

- **CPU load** — displayed in the System panel; triggers the "sweating" state when load is high
- **Disk usage** — used/total GB
- **RAM usage** — used/total GB
- **Battery** — percentage and charging status

### Achievements & Streaks

Milestones unlock as you accumulate lifetime stats:

- **Keypresses:** 1K, 5K, 10K, 50K, 100K
- **Active hours:** 1h, 5h, 10h, 50h, 100h
- **Mouse distance:** 10km, 50km, 100km
- **Use streaks:** 3, 7, 14, 30, 60, 100 consecutive days

View your lifetime stats anytime with `asciipal --stats`.

### Session Goals

Set a daily goal in minutes. AsciiPal shows a progress bar and triggers a cheering animation when you reach it.

### Color Schemes

Five built-in themes with per-region coloring:

| Scheme | Style |
|--------|-------|
| `default` | Warm neutral tones |
| `green-terminal` | Classic green-on-dark |
| `pastel` | Soft muted palette |
| `amber-terminal` | Retro amber monitor |
| `ocean` | Cool blue-green tones |

### Customization

- Swap in your own ASCII art for any state via file paths in config
- Adjust all activity thresholds and break intervals
- Choose from 9 screen positions
- Scroll-wheel zoom to resize the character
- Drag to reposition; double-click to reset
- Toggle between widget mode (transparent) and panel mode

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| GUI | Tkinter (transparent, always-on-top overlay) |
| Input Monitoring | `pynput` (cross-platform keyboard + mouse) |
| State Machine | Custom FSM with cooldowns and priority transitions |
| Config | YAML (`~/.asciipal/config.yaml`) |

## Installation

### Prerequisites

- Python 3.10 or higher
- macOS, Windows, or Linux (X11/Wayland)

### From Source

```bash
git clone https://github.com/JLSteenwyk/asciipal.git
cd asciipal
pip install -e .
```

### Quick Start

```bash
asciipal
```

### Dev Setup

```bash
make install
make check
```

### CLI Reference

```bash
asciipal                                    # Launch with GUI overlay
asciipal --headless --max-ticks 40          # Debug mode (no GUI)
asciipal --demo --duration-seconds 30       # Demo with synthetic input
asciipal --doctor                           # Print runtime diagnostics
asciipal --init-config                      # Create default config file
asciipal --print-config                     # Print effective config
asciipal --print-state                      # Print current computed state
asciipal --stats                            # Print lifetime stats & achievements
asciipal --no-summary                       # Suppress session summary on exit
asciipal --config /path/to/config.yaml      # Use custom config file
```

`--demo` is the fastest way to test behavior without granting input-monitoring permissions.

On macOS, you may need to grant **Accessibility permissions** for input monitoring (System Settings → Privacy & Security → Accessibility).

## Configuration

AsciiPal creates a default config file at `~/.asciipal/config.yaml` on first run.

```yaml
# Break reminders
break_interval_minutes: 25
break_duration_minutes: 5
pomodoro_mode: false
pomodoro_work_minutes: 25
pomodoro_break_minutes: 5

# Activity thresholds
typing_fast_wpm: 80
rage_click_threshold: 5
dizzy_mouse_speed: 700
cheering_after_minutes: 45
state_cooldown_seconds: 2.0
idle_timeout_seconds: 10
sleep_timeout_seconds: 120

# Display
position: bottom-right
character_scale: 1.0
widget_mode: true
widget_opacity: 0.95
color_scheme: default

# Notifications
notifications: gentle          # gentle | verbose | silent

# Optional features
weather_enabled: false
weather_location: ""           # city name or coordinates
weather_poll_minutes: 30
time_awareness_enabled: false
system_resources_enabled: true
cpu_load_enabled: true
sweating_load_threshold: 0.8
battery_enabled: true
session_goal_minutes: 0        # 0 = disabled

# Custom ASCII art (override any state with a file path)
custom_art:
  idle: null
  sleeping: null
  watching: null
  excited: null
  dizzy: null
  alarmed: null
  cheering: null
  sweating: null
```

## Architecture

```
asciipal/
├── __main__.py           # Entry point
├── app.py                # Main application loop and display composition
├── character.py          # ASCII art loading and frame animation
├── state_machine.py      # State transitions with priority and cooldowns
├── input_monitor.py      # Keyboard and mouse listeners (pynput)
├── activity_tracker.py   # WPM, click rate, and movement calculations
├── aquarium.py           # Plant growth, progress bar, biome decorations
├── effects.py            # Bubbles, fireflies, and companion creatures
├── break_manager.py      # Timer logic and break escalation
├── achievements.py       # Milestones, streaks, and lifetime stats
├── weather.py            # Weather data fetching and condition mapping
├── time_awareness.py     # Time-of-day sky effects
├── system_resources.py   # CPU, disk, and RAM monitoring
├── battery.py            # Battery status detection
├── overlay.py            # Tkinter window, color schemes, drag/zoom
├── config.py             # YAML config loader and validation
├── platform_support.py   # Platform-specific diagnostics
└── assets/
    └── art/              # Bundled ASCII art files (2 frames per state)
```

## Privacy

AsciiPal processes all input events locally in memory. It does **not**:

- Log or store keystrokes
- Record what you type
- Send any data over the network (except optional weather lookups)
- Capture screenshots or window content

The input monitor only tracks **aggregate metrics** (typing speed, click frequency, mouse velocity) — never individual key values or click targets.

## Platform Notes

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | Supported | Requires Accessibility permission |
| Windows | Supported | Works out of the box |
| Linux (X11) | Supported | May need `xdotool` for some features |
| Linux (Wayland) | Partial | Global input capture is restricted |

## Contributing

Contributions welcome! Some ideas for where to start:

- **New character art sets** — themed packs (cats, robots, pixel art, etc.)
- **Plugin system** — custom reactions to specific app contexts
- **System tray integration** — minimize to tray with stats tooltip
- **Sound effects** — optional audio reactions
- **Multi-monitor support** — character follows active display

## License

MIT

---

```
              .
               __
              / _)
     _.----._/ /        "Go build something fun.
    /         /          I'll be here when you get back."
 __/ (  | (  |
/__.-'|_|--|_|
```
