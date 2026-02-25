from __future__ import annotations

import random
from dataclasses import dataclass

from asciipal.activity_tracker import ActivityTotals

BUBBLE_CHARS = ("·", "°", "o")
FIREFLY_CHARS = ("·", "˙", "°")


@dataclass(frozen=True)
class CreatureDef:
    name: str
    right_sprites: tuple[str, ...]
    left_sprites: tuple[str, ...]
    min_keypresses: int = 0
    min_active_seconds: float = 0.0
    min_breaks: int = 0


CREATURE_DEFS: tuple[CreatureDef, ...] = (
    CreatureDef(
        name="fish",
        right_sprites=("><>",),
        left_sprites=("<><",),
        min_keypresses=500,
    ),
    CreatureDef(
        name="butterfly",
        right_sprites=("}{", ")("),
        left_sprites=("}{", ")("),
        min_active_seconds=1800.0,
    ),
    CreatureDef(
        name="snail",
        right_sprites=("@/",),
        left_sprites=("\\@",),
        min_breaks=3,
    ),
    CreatureDef(
        name="cat",
        right_sprites=("=^.^=",),
        left_sprites=("=^.^=",),
        min_keypresses=2000,
    ),
    CreatureDef(
        name="crab",
        right_sprites=("V(;,;)V", "v(;,;)v"),
        left_sprites=("V(;,;)V", "v(;,;)v"),
        min_active_seconds=5000.0,
    ),
    CreatureDef(
        name="seahorse",
        right_sprites=("S~", "~S"),
        left_sprites=("S~", "~S"),
        min_breaks=10,
    ),
)


@dataclass
class Particle:
    x: int
    y: int
    char: str


@dataclass
class ActiveCreature:
    defn: CreatureDef
    x: int
    y: int
    dx: int  # +1 = right, -1 = left


class BubbleSystem:
    """Rising bubbles whose spawn rate scales with user activity."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._bubbles: list[Particle] = []

    def update(
        self, totals: ActivityTotals, content_w: int, content_h: int, frame: int,
    ) -> list[Particle]:
        # Move existing bubbles upward with slight horizontal drift
        for b in self._bubbles:
            b.y -= 1
            b.x += self._rng.choice([-1, 0, 0, 1])
            b.x = max(0, min(b.x, content_w - 1))

        # Remove bubbles that floated above the top
        self._bubbles = [b for b in self._bubbles if b.y >= 0]

        # Spawn new bubbles based on activity
        rate = self._spawn_rate(totals)
        if rate > 0 and self._rng.random() < rate and len(self._bubbles) < 4:
            x = self._rng.randint(1, max(1, content_w - 2))
            char = self._rng.choices(BUBBLE_CHARS, weights=[3, 2, 1])[0]
            self._bubbles.append(Particle(x=x, y=content_h - 1, char=char))

        return list(self._bubbles)

    @staticmethod
    def _spawn_rate(totals: ActivityTotals) -> float:
        rate = 0.0
        rate += min(totals.total_keypresses / 200, 0.3)
        rate += min(totals.total_clicks / 100, 0.2)
        rate += min(totals.total_active_seconds / 300, 0.2)
        return min(rate, 0.6)


class FireflySystem:
    """Ambient particles that drift at night or during flow states."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._fireflies: list[Particle] = []
        self._blink_offsets: list[int] = []

    def update(
        self, is_night: bool, is_flow: bool,
        content_w: int, content_h: int, frame: int,
    ) -> list[Particle]:
        active = is_night or is_flow
        if not active:
            self._fireflies.clear()
            self._blink_offsets.clear()
            return []

        # Spawn fireflies up to limit
        max_flies = 5 if is_night else 3
        while len(self._fireflies) < max_flies:
            x = self._rng.randint(1, max(1, content_w - 2))
            y = self._rng.randint(0, max(0, content_h - 1))
            char = self._rng.choice(FIREFLY_CHARS)
            self._fireflies.append(Particle(x=x, y=y, char=char))
            self._blink_offsets.append(self._rng.randint(0, 3))

        # Drift randomly
        for f in self._fireflies:
            f.x += self._rng.choice([-1, 0, 0, 1])
            f.y += self._rng.choice([-1, 0, 0, 0, 1])
            f.x = max(0, min(f.x, content_w - 1))
            f.y = max(0, min(f.y, content_h - 1))

        # Blink: visible 3 out of every 4 frames
        visible = []
        for i, f in enumerate(self._fireflies):
            offset = self._blink_offsets[i]
            if (frame + offset) % 4 != 0:
                visible.append(f)
        return visible


class CreatureSystem:
    """Companion creatures that unlock at activity milestones."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._creatures: list[ActiveCreature] = []
        self._unlocked: set[str] = set()

    def update(
        self, totals: ActivityTotals, breaks_taken: int,
        content_w: int, content_h: int, frame: int,
    ) -> list[tuple[int, int, str, str]]:
        # Check for new unlocks
        for i, cd in enumerate(CREATURE_DEFS):
            if cd.name in self._unlocked:
                continue
            if (
                totals.total_keypresses >= cd.min_keypresses
                and totals.total_active_seconds >= cd.min_active_seconds
                and breaks_taken >= cd.min_breaks
            ):
                self._unlocked.add(cd.name)
                # Distribute creatures vertically across the content area
                y_fraction = (i + 1) / (len(CREATURE_DEFS) + 1)
                y = max(0, min(int(y_fraction * content_h), content_h - 1))
                x = self._rng.randint(0, max(0, content_w - 4))
                dx = self._rng.choice([-1, 1])
                self._creatures.append(ActiveCreature(defn=cd, x=x, y=y, dx=dx))

        # Move and render creatures
        result: list[tuple[int, int, str, str]] = []
        for c in self._creatures:
            if frame % 2 == 0:
                c.x += c.dx

            sprites = c.defn.right_sprites if c.dx > 0 else c.defn.left_sprites
            sprite = sprites[frame % len(sprites)]
            sprite_w = len(sprite)

            # Bounce at edges
            if c.x <= 0:
                c.dx = 1
                c.x = 0
            elif c.x + sprite_w >= content_w:
                c.dx = -1
                c.x = max(0, content_w - sprite_w)

            for j, ch in enumerate(sprite):
                if ch != " " and 0 <= c.x + j < content_w:
                    result.append((c.y, c.x + j, ch, c.defn.name))

        return result


class EffectsManager:
    """Coordinates bubbles, fireflies, and companion creatures."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self.bubbles = BubbleSystem(self._rng)
        self.fireflies = FireflySystem(self._rng)
        self.creatures = CreatureSystem(self._rng)

    def update(
        self,
        totals: ActivityTotals,
        breaks_taken: int,
        content_w: int,
        content_h: int,
        frame: int,
        is_night: bool = False,
        is_flow: bool = False,
    ) -> list[tuple[int, int, str, str]]:
        """Return ``(row, col, char, region_tag)`` overlays for the aquarium content area."""
        overlays: list[tuple[int, int, str, str]] = []

        for p in self.bubbles.update(totals, content_w, content_h, frame):
            overlays.append((p.y, p.x, p.char, "bubble"))

        for p in self.fireflies.update(is_night, is_flow, content_w, content_h, frame):
            overlays.append((p.y, p.x, p.char, "firefly"))

        overlays.extend(
            self.creatures.update(totals, breaks_taken, content_w, content_h, frame)
        )

        return overlays
