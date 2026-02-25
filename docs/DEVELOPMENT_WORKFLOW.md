# AsciiPal Development Workflow

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

or

```bash
make install
```

## Daily Loop

1. Build one small slice (single module + tests).
2. Run checks locally:

```bash
pytest -q
ruff check .
mypy asciipal
```

or

```bash
make check
```

3. Manual smoke test:

```bash
asciipal --print-state
asciipal --headless --max-ticks 20
asciipal --doctor
asciipal --print-config
asciipal --headless --demo --duration-seconds 20
```

4. If GUI permissions are ready, run full app:

```bash
asciipal
```

## Milestone Mapping

- Foundation: `pyproject.toml`, CLI entrypoint, package scaffold.
- Config: `asciipal/config.py`.
- Input and metrics: `asciipal/input_monitor.py`, `asciipal/activity_tracker.py`.
- Behavior engine: `asciipal/state_machine.py`, `asciipal/break_manager.py`.
- Display: `asciipal/overlay.py`, `asciipal/character.py`.
- Integration: `asciipal/app.py`, `asciipal/platform_support.py`.
- Validation: `tests/` + lint/type checks.

## Current Constraints

- Wayland support is limited by platform restrictions on global input capture.
- macOS requires Accessibility permissions for input monitoring.
- Overlay transparency behavior varies slightly by desktop environment.
- If Tk initialization fails, app falls back to headless mode and prints a startup note.
- For a stronger widget look, keep `widget_mode: true` and increase `character_scale`.
