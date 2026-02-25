# 🖥️ AsciiPal — Your ASCII Desktop Companion

> A lightweight desktop pet that watches your keyboard and mouse activity, reacts with expressive ASCII art animations, and reminds you to take breaks.

```
    ╔══════════╗
    ║  (◕‿◕)   ║   "You've been typing for 45 minutes.
    ║  /|  |\  ║    Stretch those fingers!"
    ║   |  |   ║
    ╚══════════╝
```

## Overview

AsciiPal is a small, always-on-top desktop companion rendered entirely in ASCII/Unicode characters. It lives in a transparent overlay on your screen, passively monitors your input activity (keystrokes, mouse movement, clicks), and responds with personality — celebrating productivity streaks, reacting to frantic clicking, dozing off when you're idle, and gently nudging you to take breaks.

Think of it as a modern, privacy-respecting, open-source take on the classic desktop pet — minus the bloat, minus the malware.

## Features

### 🎭 Reactive Character States

AsciiPal transitions between expressive states based on your input patterns:

| State | Trigger | Example Art |
|-------|---------|-------------|
| **Idle** | No input for 10s | `(• ᴗ •)` |
| **Sleeping** | No input for 2min | `(－ω－) zzZ` |
| **Watching** | Slow, steady typing | `(° ᴗ °)` |
| **Excited** | Fast typing streak | `(★ ᴗ ★)` |
| **Dizzy** | Rapid mouse movement | `(@ ᴗ @)` |
| **Alarmed** | Rage-clicking detected | `(◉_◉)` |
| **Cheering** | Long productivity streak | `\\(★ ᴗ ★)/` |

### ⏰ Break Reminders

- Configurable activity-based break timer (default: every 25 minutes of continuous activity)
- Pomodoro mode with work/break cycles
- Gentle escalation: suggestion → insistence → ASCII tantrum
- Tracks total active time and breaks taken per session

### 🌱 Living Aquarium

- Plants grow *around* the character as you accumulate active time
- Four growth stages unlock at 1, 3, 5, and 10 minutes of activity
- A progress bar below the aquarium shows how close you are to the next plant level

```
[####--------------------] Plant 1/4    (growing toward level 2)
[########################] MAX          (fully grown)
```

### 🫧 Bubbles, Fireflies & Companions

- **Rising bubbles** (`·`, `°`, `o`) float upward from the bottom, spawning faster with more activity
- **Fireflies** (`*`, `+`, `·`) drift and blink around the character at night or during flow states
- **Companion creatures** unlock as you hit milestones:

| Creature | Sprite | Unlock |
|----------|--------|--------|
| Fish | `><>` | 500 keypresses |
| Butterfly | `}{` | 30 min active time |
| Snail | `@/` | 3 breaks taken |

All effects overlay in empty spaces — they never obscure the character or plants.

### 📊 Activity Awareness

- Monitors typing speed (WPM estimate)
- Tracks mouse movement intensity
- Detects click frequency and patterns
- All processing is **local** — no data leaves your machine

### 🎨 Customization

- Swap in your own ASCII art for each state
- Adjust activity thresholds and break intervals
- Choose character size and screen position
- Toggle between minimal and verbose notification modes
- Custom color schemes for the character window

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| GUI | Tkinter (transparent, always-on-top overlay) |
| Input Monitoring | `pynput` (cross-platform keyboard + mouse listener) |
| State Machine | Custom finite state machine with cooldowns and transitions |
| Config | YAML (`~/.asciipal/config.yaml`) |

## Installation

### Prerequisites

- Python 3.10 or higher
- macOS, Windows, or Linux (X11/Wayland)

### From Source

```bash
git clone <repo-url>
cd ASCIPAL
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

### Headless and Diagnostics

```bash
asciipal --headless --max-ticks 40
asciipal --doctor
asciipal --init-config
asciipal --print-config
asciipal --headless --demo --duration-seconds 30
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
typing_fast_wpm: 80          # WPM to trigger "excited" state
rage_click_threshold: 5       # clicks/sec to trigger "alarmed"
dizzy_mouse_speed: 700        # mouse speed threshold for "dizzy"
cheering_after_minutes: 45    # active minutes before "cheering"
state_cooldown_seconds: 2.0   # minimum time between state changes
idle_timeout_seconds: 10
sleep_timeout_seconds: 120

# Display
position: bottom-right        # top-left | top-right | bottom-left | bottom-right
character_scale: 1.0
widget_mode: true             # true = transparent widget style, false = panel style
widget_opacity: 0.95          # 0.2 - 1.0
color_scheme: default         # default | green-terminal | pastel
notifications: gentle         # gentle | verbose | silent

# Custom ASCII art (override any state)
custom_art:
  idle: null                  # set to file path for custom art
  sleeping: null
```

## Architecture

```
asciipal/
├── __main__.py           # Entry point
├── app.py                # Main application loop
├── character.py          # ASCII art definitions and rendering
├── state_machine.py      # State transitions and cooldown logic
├── input_monitor.py      # Keyboard and mouse listeners (pynput)
├── activity_tracker.py   # WPM, click rate, and movement calculations
├── aquarium.py           # Progress bar and plant growth decorations
├── effects.py            # Bubbles, fireflies, and companion creatures
├── break_manager.py      # Timer logic and reminder escalation
├── overlay.py            # Tkinter transparent window management
├── config.py             # YAML config loader and defaults
└── assets/
    └── art/              # ASCII art files per state (default bundled art)
```

## Privacy

AsciiPal processes all input events locally in memory. It does **not**:

- Log or store keystrokes
- Record what you type
- Send any data over the network
- Capture screenshots or window content

The input monitor only tracks **aggregate metrics** (typing speed, click frequency, mouse velocity) — never individual key values or click targets.

## Platform Notes

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | ✅ | Requires Accessibility permission |
| Windows | ✅ | Works out of the box |
| Linux (X11) | ✅ | May need `xdotool` for some features |
| Linux (Wayland) | ⚠️ | Limited — global input capture is restricted |

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
   ( ◕ ᴗ ◕ )
   /|     |\      "Go build something fun.
    |     |        I'll be here when you get back."
   / \   / \
```
