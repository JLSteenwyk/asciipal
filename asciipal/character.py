from __future__ import annotations

from pathlib import Path

from asciipal.config import Config

FRAME_SEPARATOR = "\n---\n"

ALL_STATES = ("idle", "sleeping", "watching", "excited", "dizzy", "alarmed", "cheering")

DEFAULT_ART = {
    "idle": "(•‿•)",
    "sleeping": "(-‿-) zzZ",
    "watching": "(°‿°)",
    "excited": "\\(★‿★)/",
    "dizzy": "(@‿@)~",
    "alarmed": "(╯°□°)╯",
    "cheering": "\\(°▽°)/",
}


class CharacterRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._cache: dict[str, list[str]] = {}
        self._assets_dir = Path(__file__).resolve().parent / "assets" / "art"

        # Preload all bundled states so we can compute max_art_width.
        self._global_max_width = 0
        for state in ALL_STATES:
            for frame in self._frames_for(state):
                for line in frame.split("\n"):
                    self._global_max_width = max(self._global_max_width, len(line))

    @property
    def max_art_width(self) -> int:
        return self._global_max_width

    def art_for(self, state: str, frame: int = 0) -> str:
        frames = self._frames_for(state)
        return frames[frame % len(frames)]

    def frame_count(self, state: str) -> int:
        return len(self._frames_for(state))

    def _frames_for(self, state: str) -> list[str]:
        custom_path = self.config.custom_art.get(state)
        if custom_path:
            return self._load_custom_frames(custom_path, state)
        bundled = self._load_bundled_frames(state)
        if bundled is not None:
            return bundled
        return [DEFAULT_ART.get(state, "(•_•)")]

    def _parse_frames(self, text: str) -> list[str]:
        raw = text.split(FRAME_SEPARATOR)
        raw = [f for f in raw if f.strip()]
        if not raw:
            return ["(•_•)"]
        # Pad all lines across all frames to the same width so the
        # widget never changes size between animation frames.
        max_w = 0
        for frame in raw:
            for line in frame.split("\n"):
                max_w = max(max_w, len(line))
        padded: list[str] = []
        for frame in raw:
            lines = frame.split("\n")
            padded.append("\n".join(l.ljust(max_w) for l in lines))
        return padded

    def _load_custom_frames(self, path: str, state: str) -> list[str]:
        key = f"custom:{path}"
        if key in self._cache:
            return self._cache[key]
        try:
            text = Path(path).expanduser().read_text(encoding="utf-8").strip("\n")
            if not text.strip():
                return [DEFAULT_ART.get(state, "(•_•)")]
            frames = self._parse_frames(text)
            self._cache[key] = frames
            return frames
        except OSError:
            return [DEFAULT_ART.get(state, "(•_•)")]

    def _load_bundled_frames(self, state: str) -> list[str] | None:
        key = f"bundle:{state}"
        if key in self._cache:
            return self._cache[key]
        path = self._assets_dir / f"{state}.txt"
        try:
            text = path.read_text(encoding="utf-8").strip("\n")
            if not text.strip():
                return None
            frames = self._parse_frames(text)
            self._cache[key] = frames
            return frames
        except OSError:
            return None
