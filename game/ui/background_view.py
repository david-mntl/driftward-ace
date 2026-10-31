"""Background view: the painted far layer, river light, a swirl, drifting planets, bottom glow.

Source: 12-art-and-audio.md, Background. The view only draws. It never flips the display, never
logs per frame, never catches an error and never changes the scroll. Everything it shows is a
function of one time value (`ticks`), so the same time always draws the same frame, and the sway
and the river light loop for ever, like an animated image on repeat.
"""

import logging
import math
import random
from dataclasses import dataclass

import pygame

from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

HOLE_CENTER: tuple[float, float] = (5.0, 486.0)
"""Center of the black hole in the far painting, screen px. Measured from the painting: it
changes only when the painting does."""

HOLE_RADIUS: float = 80.0
"""Radius of the black hole's dark disk in the far painting, screen px. Measured, as above."""

RIVER_START_RADIUS: float = 700.0
"""Distance from the hole where a river speck starts, px. Past the farthest screen corner."""

RIVER_FAN_DEGREES: tuple[float, float] = (-90.0, 0.0)
"""Angles the river specks start at, around the hole: 0 is right, -90 is straight up."""

RIVER_CURL: float = 0.3
"""Turn of a river speck on its way in, radians. Chosen by eye to follow the painted rivers."""

RIVER_FADE_IN: float = 0.1
RIVER_FADE_OUT: float = 0.15
"""Shares of a speck's trip it fades in and out over, 0..1."""

SWIRL_GAP: float = 6.0
SWIRL_BAND: float = 15.0
"""The swirl rides this many px outside the dark disk, spread over a band this wide."""

SPECK_RADIUS: int = 3
"""Radius of a speck's glow sprite, px."""

SPECK_LEVELS: int = 6
"""Brightness steps a speck fades through. One sprite is drawn ahead of time for each."""

SPECK_COLOR: tuple[int, int, int] = (200, 110, 255)
"""River light and swirl, RGB at full strength: a purple that leans fuchsia."""

GLOW_COLOR: tuple[int, int, int] = (255, 40, 200)
"""Bottom glow, RGB at full strength: fuchsia."""

SEED: int = 2901
"""Fixed seed for the layout of the river specks. No design meaning."""


@dataclass(frozen=True)
class BackgroundRules:
    """The background's values, from tuning/background.json. Units are in each field's doc."""

    sway_loop_ticks: int
    """Ticks the far painting's sway takes for one full loop, 1 or more."""
    planet_count: int
    """Broken planets on screen at once, 0 or more."""
    planet_speed: float
    """Px a planet moves down per tick, 0 or more."""
    planet_scale: float
    """Planet size against the shipped sprite, above 0."""
    river_light_count: int
    """River specks at most, 0 or more."""
    river_light_loop_ticks: int
    """Ticks a river speck takes from its start to the black hole, 1 or more."""
    river_light_strength: float
    """River light and swirl brightness, 0..1."""
    swirl_count: int
    """Specks circling the black hole, 0 or more."""
    swirl_loop_ticks: int
    """Ticks the swirl takes for one full turn, 1 or more."""
    glow_height: int
    """Height of the bottom glow, px, 0 or more. 0 turns it off."""
    glow_strength: float
    """Brightness of the bottom glow at the very bottom, 0..1."""


@dataclass(frozen=True)
class RiverSpeck:
    """One speck's path: where it starts around the hole and where in its loop it begins."""

    angle: float
    """Start angle around the hole, radians."""
    phase: float
    """Share of the loop it has already run at time 0, 0..1."""


@dataclass(frozen=True)
class BackgroundArt:
    """Everything the view draws, made once at startup by `build_background`."""

    sway: tuple[pygame.Surface, ...]
    """The far painting's loop, one opaque screen-size frame per step, in loop order."""
    planets: tuple[pygame.Surface, ...]
    speck_sprites: tuple[pygame.Surface, ...]
    glow: pygame.Surface | None
    river: tuple[RiverSpeck, ...]
    rules: BackgroundRules


def build_background(
    sway: tuple[pygame.Surface, ...], planets: tuple[pygame.Surface, ...], rules: BackgroundRules
) -> BackgroundArt:
    """Make the sprites and the river layout ahead of time.

    Raises ValueError with no sway frame or no planet sprite.
    """
    if not sway:
        raise ValueError("background needs at least one painting frame")
    if not planets:
        raise ValueError("background needs at least one planet sprite")
    scaled: tuple[pygame.Surface, ...] = tuple(_scaled(sprite, rules) for sprite in planets)
    rng: random.Random = random.Random(SEED)
    low, high = (math.radians(degrees) for degrees in RIVER_FAN_DEGREES)
    river: tuple[RiverSpeck, ...] = tuple(
        RiverSpeck(angle=rng.uniform(low, high), phase=index / rules.river_light_count)
        for index in range(rules.river_light_count)
    )
    return BackgroundArt(
        sway=sway,
        planets=scaled,
        speck_sprites=_speck_sprites(rules.river_light_strength),
        glow=_glow(rules) if rules.glow_height > 0 else None,
        river=river,
        rules=rules,
    )


def draw_background(surface: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
    """Draw the whole background for time `ticks` (1 tick = 1/60 s, 0 or more).

    Order, back to front: the painting, river light, the swirl, the planets, the bottom glow.
    Everything but the painting is dimmer than anything the player can touch (rule 7).
    """
    _draw_painting(surface, art, ticks)
    _draw_river(surface, art, ticks)
    _draw_swirl(surface, art, ticks)
    _draw_planets(surface, art, ticks)
    if art.glow is not None:
        surface.blit(
            art.glow, (0, SCREEN_H - art.glow.get_height()), special_flags=pygame.BLEND_RGB_ADD
        )


def _draw_painting(surface: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
    """Draw the painting: the current sway frame, with the next one faded over it.

    Sets the surface alpha of two sway frames on each call, so the result never depends on an
    earlier call. The last frame fades back into the first.
    """
    frames: tuple[pygame.Surface, ...] = art.sway
    position: float = ticks / art.rules.sway_loop_ticks % 1.0 * len(frames)
    index: int = int(position) % len(frames)
    share: float = position - int(position)
    frames[index].set_alpha(None)
    surface.blit(frames[index], (0, 0))
    if len(frames) > 1 and share > 0:
        following: pygame.Surface = frames[(index + 1) % len(frames)]
        following.set_alpha(round(share * 255))
        surface.blit(following, (0, 0))


def _scaled(sprite: pygame.Surface, rules: BackgroundRules) -> pygame.Surface:
    """Return the planet sprite at planet_scale, or the sprite itself at 1."""
    if rules.planet_scale == 1.0:
        return sprite
    size: tuple[int, int] = (
        max(1, round(sprite.get_width() * rules.planet_scale)),
        max(1, round(sprite.get_height() * rules.planet_scale)),
    )
    return pygame.transform.smoothscale(sprite, size)


def _speck_sprites(strength: float) -> tuple[pygame.Surface, ...]:
    """Return SPECK_LEVELS glow dots, dimmest first, to add onto the painting.

    Each is a soft round dot in SPECK_COLOR. The color is darkened, never made see-through, so
    that adding it lights the painting and never covers it.
    """
    side: int = SPECK_RADIUS * 2 + 1
    sprites: list[pygame.Surface] = []
    for level in range(1, SPECK_LEVELS + 1):
        sprite: pygame.Surface = pygame.Surface((side, side))
        for y in range(side):
            for x in range(side):
                reach: float = 1 - math.hypot(x - SPECK_RADIUS, y - SPECK_RADIUS) / (
                    SPECK_RADIUS + 1
                )
                share: float = max(0.0, reach) ** 2 * strength * level / SPECK_LEVELS
                sprite.set_at((x, y), tuple(round(part * share) for part in SPECK_COLOR))
        sprites.append(sprite)
    return tuple(sprites)


def _glow(rules: BackgroundRules) -> pygame.Surface:
    """Return the bottom glow: fuchsia, none at the top edge, rules.glow_strength at the bottom."""
    glow: pygame.Surface = pygame.Surface((SCREEN_W, rules.glow_height))
    for y in range(rules.glow_height):
        share: float = ((y + 1) / rules.glow_height) ** 2 * rules.glow_strength
        glow.fill(tuple(round(part * share) for part in GLOW_COLOR), pygame.Rect(0, y, SCREEN_W, 1))
    return glow


def _blit_speck(
    surface: pygame.Surface, art: BackgroundArt, x: float, y: float, level: int
) -> None:
    """Add one glow dot centered on (x, y) at brightness step `level` (0 = none)."""
    if level <= 0:
        return
    sprite: pygame.Surface = art.speck_sprites[min(level, SPECK_LEVELS) - 1]
    surface.blit(
        sprite,
        (round(x) - SPECK_RADIUS, round(y) - SPECK_RADIUS),
        special_flags=pygame.BLEND_RGB_ADD,
    )


def _draw_river(surface: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
    """Draw each river speck and a dimmer tail behind it, along its curve into the black hole."""
    loop: float = art.rules.river_light_loop_ticks
    for speck in art.river:
        trip: float = (speck.phase + ticks / loop) % 1.0
        for lag, dim in ((0.0, 0), (0.012, 2)):
            progress: float = trip - lag
            if progress < 0:
                continue
            x, y = _river_point(speck.angle, progress)
            fade: float = min(progress / RIVER_FADE_IN, (1 - progress) / RIVER_FADE_OUT, 1.0)
            _blit_speck(surface, art, x, y, round(fade * SPECK_LEVELS) - dim)


def _river_point(angle: float, progress: float) -> tuple[float, float]:
    """Return the screen point of a river speck `progress` (0..1) of the way to the hole.

    It speeds up toward the hole, as the pull does, and curls by RIVER_CURL on the way.
    """
    distance: float = RIVER_START_RADIUS - (RIVER_START_RADIUS - HOLE_RADIUS) * progress**2
    turn: float = angle + RIVER_CURL * progress
    return (
        HOLE_CENTER[0] + distance * math.cos(turn),
        HOLE_CENTER[1] + distance * math.sin(turn),
    )


def _draw_swirl(surface: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
    """Draw the specks circling the black hole, one full turn every swirl_loop_ticks."""
    count: int = art.rules.swirl_count
    for index in range(count):
        turn: float = math.tau * (index / count + ticks / art.rules.swirl_loop_ticks)
        distance: float = HOLE_RADIUS + SWIRL_GAP + SWIRL_BAND * (index % 3) / 2
        _blit_speck(
            surface,
            art,
            HOLE_CENTER[0] + distance * math.cos(turn),
            HOLE_CENTER[1] + distance * math.sin(turn),
            SPECK_LEVELS - index % 3,
        )


def _draw_planets(surface: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
    """Draw the broken planets sliding straight down, each wrapping to the top as a new look.

    Planets start evenly spaced over one trip. Each trip picks the next look and a new x from
    whole-number arithmetic, so the layout is the same every run.
    """
    count: int = art.rules.planet_count
    tallest: int = max(sprite.get_height() for sprite in art.planets)
    span: float = SCREEN_H + tallest
    for index in range(count):
        travelled: float = span * index / count + art.rules.planet_speed * ticks
        trip: int = int(travelled // span)
        sprite: pygame.Surface = art.planets[(index + trip * 5) % len(art.planets)]
        x: int = (index * 211 + trip * 337) % (SCREEN_W + 100) - 50
        surface.blit(sprite, (x, round(travelled % span) - tallest))
