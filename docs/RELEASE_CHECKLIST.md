# AsciiPal v0.1 Release Checklist

## 1) Quality Gate
- [ ] `make check` passes (`pytest`, `ruff`, `mypy`).
- [ ] CI workflow passes on pull request.
- [ ] `asciipal --doctor` runs successfully.
- [ ] `asciipal --headless --max-ticks 40` runs successfully.

## 2) Runtime Verification
- [ ] `asciipal` overlay launches on macOS with Accessibility permission.
- [ ] Break reminder escalation observed in a manual session.
- [ ] `silent`, `gentle`, and `verbose` notification modes are verified.
- [ ] Custom ASCII art override path works for at least one state.

## 3) Privacy and Safety
- [ ] Confirm no key contents are persisted.
- [ ] Confirm no network calls are required for runtime behavior.
- [ ] Confirm warnings are shown when input capture is unavailable.
- [ ] Confirm app degrades to headless mode if overlay init fails.

## 4) Documentation
- [ ] README quick start and config keys match current behavior.
- [ ] Development workflow doc is up to date.
- [ ] Implementation plan reflects current completion status.
- [ ] Known limitations section includes Wayland restrictions.

## 5) Packaging
- [ ] Verify `pip install -e .` and `asciipal --print-state`.
- [ ] Verify packaged art files are included.
- [ ] Tag and publish release notes with platform caveats.

