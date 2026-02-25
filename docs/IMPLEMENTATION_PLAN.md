# AsciiPal Implementation Plan and Workflow

## Objective
Build a lightweight desktop companion that reacts to keyboard/mouse activity with ASCII states, shows break reminders, and keeps all processing local.

## Recommended Language and Stack

### Decision
Use **Python 3.10+** for `v0.1` (MVP), then re-evaluate after real usage.

### Why Python is still the right first choice
- Fastest path to a working cross-platform prototype with `tkinter` + `pynput`.
- Lowest implementation risk for state machine, timing logic, and config-heavy behavior.
- Easy packaging for testers and contributors.

### Known Python limits
- Overlay polish and animation smoothness can be weaker than native toolkits.
- OS-level input and window behavior can require platform-specific handling.
- Long-term desktop UX may be better in a native stack.

### Re-evaluation gate
Reconsider stack after MVP if any of these are true:
- Overlay rendering looks or feels unstable.
- Input hooks are unreliable on target platforms.
- Packaging/distribution is too fragile.

If migration is needed, strongest candidate is:
- **Rust + Tauri** (or Rust + native UI) for performance, platform APIs, and durable desktop packaging.

## Architecture (MVP)
Target package structure:

```text
asciipal/
├── __main__.py
├── app.py
├── character.py
├── state_machine.py
├── input_monitor.py
├── activity_tracker.py
├── break_manager.py
├── overlay.py
├── config.py
└── assets/
    └── art/
```

## Build Plan (Phased)

### Phase 1: Foundation
- Initialize package, entrypoint, and project metadata (`pyproject.toml`).
- Add basic app lifecycle and clean shutdown.
- Add a tiny event bus or callback wiring strategy between modules.

**Exit criteria**
- `asciipal` command runs and exits cleanly.

### Phase 2: Config and Defaults
- Implement YAML config loader with defaults.
- Create `~/.asciipal/config.yaml` on first run.
- Validate config values and fail with clear messages.

**Exit criteria**
- Config is auto-created, loaded, and applied.

### Phase 3: Input and Metrics
- Implement keyboard/mouse listeners in `input_monitor.py`.
- Aggregate metrics only: WPM estimate, click rate, mouse intensity.
- Do not persist individual key contents.

**Exit criteria**
- Live metrics stream updates in memory with no raw keystroke logging.

### Phase 4: State Machine
- Implement states: idle, sleeping, watching, excited, dizzy, alarmed, cheering.
- Add transition guards/cooldowns to prevent jitter.
- Map metric thresholds to deterministic transitions.

**Exit criteria**
- Given simulated inputs, state transitions are correct and stable.

### Phase 5: Overlay and Character Rendering
- Create transparent, always-on-top Tkinter overlay.
- Render ASCII art by state.
- Add position, scale, and color scheme controls.

**Exit criteria**
- Character appears and visibly changes state in real time.

### Phase 6: Break Manager
- Add activity-based break reminders and optional Pomodoro mode.
- Implement escalation flow: gentle -> firm -> tantrum.
- Surface reminder stage in character output.

**Exit criteria**
- Reminders trigger at configured intervals and escalate as expected.

### Phase 7: Integration and Hardening
- Wire all modules in `app.py`.
- Add platform checks and user guidance (especially macOS accessibility).
- Handle listener failures gracefully.

**Exit criteria**
- End-to-end run works on at least one primary platform (macOS first).

### Phase 8: Testing and Release Readiness
- Unit tests for metrics, state transitions, break logic, config validation.
- Integration test with mocked input event stream.
- Add lint/type checks (ruff + mypy).

**Exit criteria**
- Tests pass, quality checks pass, MVP is releasable.

## Workflow to Execute the Plan

### 1) Sprint setup (Day 0)
- Define MVP acceptance criteria and target platform order.
- Create issue list from phases and assign priorities.
- Lock dependency versions.

### 2) Core implementation loop (Days 1-5)
For each phase:
1. Implement smallest vertical slice.
2. Run manual smoke test.
3. Add/adjust tests.
4. Refactor only if it improves reliability or clarity.
5. Merge only when exit criteria are met.

### 3) End-to-end stabilization (Days 6-7)
- Run long-session manual test (>= 2 hours).
- Verify state transitions, reminders, and idle/sleep behavior.
- Validate config edge cases and startup recovery.

### 4) Pre-release checklist
- Confirm privacy guarantees in code and docs.
- Confirm behavior on macOS + one secondary OS.
- Build release notes and known limitations.

## Definition of Done (MVP)
- Overlay is visible, responsive, and always-on-top.
- State transitions reflect actual user activity patterns.
- Break reminders are configurable and reliable.
- Config file is generated and respected.
- No raw keystroke content is recorded or transmitted.
- Basic tests and lint/type checks are in place.

## Post-MVP Priorities
- System tray integration and pause/resume controls.
- Multi-monitor awareness.
- Plugin/reaction system.
- Optional sound effects.
- Packaging polish for non-technical users.
