from __future__ import annotations

from pathlib import Path

from asciipal.character import CharacterRenderer
from asciipal.config import Config, DEFAULT_CONFIG


def _config() -> Config:
    return Config.from_dict(dict(DEFAULT_CONFIG))


def test_renderer_loads_bundled_art() -> None:
    renderer = CharacterRenderer(_config())
    art = renderer.art_for("idle")
    assert "/ _)" in art
    assert "/__.-" in art


def test_renderer_returns_animation_frames() -> None:
    renderer = CharacterRenderer(_config())
    frame0 = renderer.art_for("idle", frame=0)
    frame1 = renderer.art_for("idle", frame=1)
    assert frame0 != frame1
    assert "/ _)" in frame0
    assert "/ _)" in frame1


def test_renderer_frame_wraps() -> None:
    renderer = CharacterRenderer(_config())
    count = renderer.frame_count("idle")
    assert count == 2
    frame0 = renderer.art_for("idle", frame=0)
    wrapped = renderer.art_for("idle", frame=count)
    assert frame0 == wrapped


def test_renderer_frames_have_consistent_width() -> None:
    renderer = CharacterRenderer(_config())
    for state in ("idle", "sleeping", "watching", "excited", "dizzy", "alarmed", "cheering"):
        widths = set()
        for i in range(renderer.frame_count(state)):
            frame = renderer.art_for(state, frame=i)
            for line in frame.split("\n"):
                widths.add(len(line))
        assert len(widths) == 1, f"State {state!r} has inconsistent line widths: {widths}"


def test_renderer_max_art_width() -> None:
    renderer = CharacterRenderer(_config())
    assert renderer.max_art_width > 0
    for state in ("idle", "sleeping", "watching", "excited", "dizzy", "alarmed", "cheering"):
        for i in range(renderer.frame_count(state)):
            frame = renderer.art_for(state, frame=i)
            for line in frame.split("\n"):
                assert len(line) <= renderer.max_art_width


def test_renderer_eating_art_has_two_frames() -> None:
    renderer = CharacterRenderer(_config())
    assert renderer.frame_count("eating") == 2
    frame0 = renderer.art_for("eating", frame=0)
    frame1 = renderer.art_for("eating", frame=1)
    assert frame0 != frame1
    assert "/__.-" in frame0
    assert "/__.-" in frame1


def test_renderer_custom_art_override(tmp_path: Path) -> None:
    custom = tmp_path / "idle.txt"
    custom.write_text("(custom idle)", encoding="utf-8")
    cfg = dict(DEFAULT_CONFIG)
    cfg["custom_art"] = dict(DEFAULT_CONFIG["custom_art"])
    cfg["custom_art"]["idle"] = str(custom)
    renderer = CharacterRenderer(Config.from_dict(cfg))
    assert renderer.art_for("idle") == "(custom idle)"
