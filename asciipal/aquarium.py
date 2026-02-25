from __future__ import annotations

from asciipal.activity_tracker import ActivityTotals

BIRD_DOWN = "\\v/"
BIRD_UP = "/^\\"


def _bird_count(totals: ActivityTotals) -> int:
    """Determine how many birds should fly based on activity."""
    n = 0
    n += min(totals.total_keypresses // 100, 3)
    n += min(totals.total_clicks // 50, 3)
    n += min(int(totals.total_mouse_distance) // 10000, 2)
    return min(n, 8)


def _plant_level(totals: ActivityTotals) -> int:
    """Determine plant growth level (0-4) from active time."""
    secs = totals.total_active_seconds
    if secs < 60:
        return 0
    if secs < 180:
        return 1
    if secs < 300:
        return 2
    if secs < 600:
        return 3
    return 4


def _scatter_birds(count: int, width: int, frame: int) -> str:
    """Place birds at evenly-spaced positions. Wings flap each frame."""
    if count <= 0 or width < 4:
        return ""
    buf = list(" " * width)
    gap = width // (count + 1)
    for i in range(count):
        x = gap * (i + 1) + ((frame + i) % 3 - 1)
        x = max(0, min(x, width - 3))
        sprite = BIRD_DOWN if (i + frame) % 2 == 0 else BIRD_UP
        for j, ch in enumerate(sprite):
            if 0 <= x + j < width:
                buf[x + j] = ch
    return "".join(buf)


def _build_plants(level: int, width: int, frame: int) -> list[str]:
    """Build multi-line seaweed that sways. Height = level (1-4 rows)."""
    if level <= 0 or width < 4:
        return []
    positions = [2, width // 4, width // 2, 3 * width // 4, width - 3]
    num_cols = min(level + 1, len(positions))
    lines: list[str] = []
    for row in range(level):
        buf = list(" " * width)
        for i in range(num_cols):
            pos = positions[i]
            ch = "(" if (row + i + frame) % 2 == 0 else ")"
            if 0 <= pos < width:
                buf[pos] = ch
        lines.append("".join(buf))
    return lines


def build_aquarium_scene(
    totals: ActivityTotals, content_w: int, frame: int,
) -> tuple[list[str], list[str]]:
    """Return (bird_lines, plant_lines) for aquarium decorations.

    Birds fly above the character. Plants grow at ground level.
    """
    bird_lines: list[str] = []
    plant_lines: list[str] = []

    birds = _bird_count(totals)
    level = _plant_level(totals)

    if birds > 0:
        line = _scatter_birds(birds, content_w, frame)
        if line.strip():
            bird_lines.append(line)

    if level > 0:
        plant_lines = _build_plants(level, content_w, frame)

    return bird_lines, plant_lines
