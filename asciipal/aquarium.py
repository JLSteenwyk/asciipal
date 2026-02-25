from __future__ import annotations

from asciipal.activity_tracker import ActivityTotals

PLANT_THRESHOLDS = [60, 180, 300, 600]


def _plant_level(totals: ActivityTotals) -> int:
    """Determine plant growth level (0-4) from active time."""
    secs = totals.total_active_seconds
    for i, threshold in enumerate(PLANT_THRESHOLDS):
        if secs < threshold:
            return i
    return len(PLANT_THRESHOLDS)


def _plant_progress(totals: ActivityTotals) -> tuple[int, float]:
    """Return (current_level, fraction_to_next).

    At max level (4), fraction is 1.0.
    """
    secs = totals.total_active_seconds
    level = _plant_level(totals)
    if level >= len(PLANT_THRESHOLDS):
        return level, 1.0
    threshold = PLANT_THRESHOLDS[level]
    prev = PLANT_THRESHOLDS[level - 1] if level > 0 else 0
    return level, (secs - prev) / (threshold - prev)


def _build_progress_bar(level: int, progress: float, width: int) -> str:
    """Render ``[####--------] Plant 2/4`` fitted to exactly *width* chars.

    At max level: ``[############] MAX``
    """
    max_level = len(PLANT_THRESHOLDS)
    if level >= max_level:
        suffix = " MAX"
    else:
        suffix = f" Plant {level}/{max_level}"
    # bar_inner = width - len("[]") - len(suffix)
    bar_inner = width - 2 - len(suffix)
    if bar_inner < 1:
        bar_inner = 1
    filled = int(bar_inner * progress)
    filled = max(0, min(filled, bar_inner))
    bar = "[" + "#" * filled + "-" * (bar_inner - filled) + "]" + suffix
    return bar[:width]


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
    """Return (progress_lines, plant_lines) for aquarium decorations.

    Progress bar shows how close the user is to the next plant.
    Plants grow at ground level.
    """
    progress_lines: list[str] = []
    plant_lines: list[str] = []

    level = _plant_level(totals)
    lvl, frac = _plant_progress(totals)
    bar = _build_progress_bar(lvl, frac, content_w)
    progress_lines.append(bar)

    if level > 0:
        plant_lines = _build_plants(level, content_w, frame)

    return progress_lines, plant_lines
