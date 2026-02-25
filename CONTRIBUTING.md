# Contributing

## Local Setup

```bash
make install
```

## Before Opening a PR

```bash
make check
```

## Manual Smoke Checks

```bash
asciipal --print-state
asciipal --doctor
asciipal --headless --max-ticks 40
```

If your platform supports permissions for global input capture, run:

```bash
asciipal
```

## Scope for v0.1
- Reliability of state transitions and break reminders.
- Privacy guarantees (no raw keystroke persistence).
- Platform warning clarity and graceful fallback behavior.

