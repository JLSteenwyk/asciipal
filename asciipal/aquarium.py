from __future__ import annotations

from asciipal.activity_tracker import ActivityTotals

PLANT_THRESHOLDS = [300, 600, 1200, 1800, 2700, 3600, 5400, 7200]
#                   5m   10m  20m   30m   45m   60m   90m   120m

# Per-column plant species based on maturity (current_level - birth_level)
# Each species: (frame_0_rows, frame_1_rows)
# Each row is exactly 3 chars wide, centered on column position
PLANT_SPRITES: dict[str, tuple[list[str], list[str]]] = {
    "sprout": (                          # age 0-1
        [" i ", " | "],
        [" i ", " | "],
    ),
    "bud": (                             # age 2-3
        [" , ", "~| ", " | "],
        [" . ", " |~", " | "],
    ),
    "bloom": (                           # age 4-5
        ["\\w/", " |~", " | "],
        ["\\w/", "~| ", " | "],
    ),
    "flower": (                          # age 6+
        ["(@)", "\\|/", " |~", " | "],
        ["(@)", "\\|/", "~| ", " | "],
    ),
}

# The level at which each plant column first appears
PLANT_BIRTH_LEVELS = [1, 3, 5, 7, 8]


def _plant_level(totals: ActivityTotals) -> int:
    """Determine plant growth level (0-8) from active time."""
    secs = totals.total_active_seconds
    for i, threshold in enumerate(PLANT_THRESHOLDS):
        if secs < threshold:
            return i
    return len(PLANT_THRESHOLDS)


def _plant_progress(totals: ActivityTotals) -> tuple[int, float]:
    """Return (current_level, fraction_to_next).

    At max level (8), fraction is 1.0.
    """
    secs = totals.total_active_seconds
    level = _plant_level(totals)
    if level >= len(PLANT_THRESHOLDS):
        return level, 1.0
    threshold = PLANT_THRESHOLDS[level]
    prev = PLANT_THRESHOLDS[level - 1] if level > 0 else 0
    return level, (secs - prev) / (threshold - prev)


def _build_progress_bar(level: int, progress: float, width: int) -> str:
    """Render a full-width progress bar fitted to exactly *width* chars."""
    bar_inner = width - 2  # account for [ and ]
    if bar_inner < 1:
        bar_inner = 1
    filled = int(bar_inner * progress)
    filled = max(0, min(filled, bar_inner))
    bar = "[" + "▰" * filled + "▱" * (bar_inner - filled) + "]"
    return bar[:width]


def _plant_dimensions(level: int) -> tuple[int, int]:
    """Return (num_cols, height) for staggered plant growth.

    Level → (num_columns, height)
      1  →  (1, 1)    one sprout
      2  →  (1, 2)    it grows
      3  →  (2, 2)    second sprout
      4  →  (2, 3)    both grow
      5  →  (3, 3)    third appears
      6  →  (3, 4)    all grow
      7  →  (4, 4)    fourth appears
      8  →  (5, 5)    full garden
    """
    if level <= 0:
        return (0, 0)
    mapping = {
        1: (1, 1),
        2: (1, 2),
        3: (2, 2),
        4: (2, 3),
        5: (3, 3),
        6: (3, 4),
        7: (4, 4),
        8: (5, 5),
    }
    return mapping.get(level, (5, 5))


def _plant_species_name(col_index: int, current_level: int) -> str:
    """Return species name for a plant column based on its maturity."""
    birth = PLANT_BIRTH_LEVELS[col_index] if col_index < len(PLANT_BIRTH_LEVELS) else 1
    age = max(current_level - birth, 0)
    if age <= 1:
        return "sprout"
    if age <= 3:
        return "bud"
    if age <= 5:
        return "bloom"
    return "flower"


def _build_plants(level: int, width: int, frame: int) -> list[str]:
    """Build multi-line flower sprites with staggered growth."""
    if level <= 0 or width < 4:
        return []
    num_cols, height = _plant_dimensions(level)
    positions = [2, width // 4, width // 2, 3 * width // 4, width - 3]
    num_cols = min(num_cols, len(positions))
    grid = [list(" " * width) for _ in range(height)]
    for i in range(num_cols):
        pos = positions[i]
        species = _plant_species_name(i, level)
        full_sprite = PLANT_SPRITES[species][frame % 2]
        # Show top N rows (flower head first, stem revealed as height grows)
        visible = full_sprite[:min(height, len(full_sprite))]
        start_row = height - len(visible)
        for r, sprite_row in enumerate(visible):
            grid_row = start_row + r
            for j, ch in enumerate(sprite_row):
                col = pos - 1 + j
                if 0 <= col < width and ch != " ":
                    grid[grid_row][col] = ch
    return ["".join(row) for row in grid]


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


import random as _rng_mod

BIOME_DECORATIONS: dict[int, list[str]] = {
    0: [],
    1: [".", "\u00b7"],
    2: [",", "'"],
    3: [",", "'", "\u00b7", "."],
    4: ["\u00b0", "\u00b7", ",", "'"],
}


def biome_stage(hours: float) -> int:
    """Return biome stage 0-4 based on monthly active hours."""
    if hours < 5:
        return 0
    if hours < 15:
        return 1
    if hours < 30:
        return 2
    if hours < 50:
        return 3
    return 4


def build_biome_decorations(
    stage: int, w: int, h: int, frame: int, rng: _rng_mod.Random | None = None,
) -> list[tuple[int, int, str]]:
    """Return deterministic decoration placements for the given biome stage."""
    if stage <= 0:
        return []
    chars = BIOME_DECORATIONS.get(stage, BIOME_DECORATIONS[4])
    count = stage * 3
    if rng is None:
        rng = _rng_mod.Random(stage * 1000 + w)
    result: list[tuple[int, int, str]] = []
    for _ in range(count):
        r = rng.randint(0, max(0, h - 1))
        c = rng.randint(0, max(0, w - 1))
        ch = rng.choice(chars)
        result.append((r, c, ch))
    return result
