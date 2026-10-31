"""Ship view: the ship sprite, leaning with its sideways speed, with air streaks and a flame jet
per held arrow.

Three sprite strips, one row of equal frames each, laid out by tools/art/ship_final.py. The
centre of every frame is the ship's centre, so a frame is blitted centered on the ship and the
hitbox never moves with the look. `ship.png` holds 3 lean frames: left, centre, right.
`ship_flame.png` holds 8 flame frames, 2 flicker frames for each jet in the order up, left,
right, down; a jet is named for the arrow that fires it. `ship_streaks.png` holds 4 wider frames
of air streaks trailing left, for a ship moving right: short then long, 2 flicker frames each.
Streaks and flames are drawn first, behind the body.
Source: docs/design/gdd/04-ship.md, look; 12-art-and-audio.md, rules 9 and 13. The view only
draws. It never fills the background, never flips the display, never logs per frame, never
catches an error and never changes the ship.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pygame

from core.ship import Ship, Thrust

log = logging.getLogger(__name__)

SPRITES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "assets" / "sprites"

BODY_FILE: Final[Path] = SPRITES_DIR / "ship.png"
"""The lean strip: 5 frames, left 2, left 1, centre, right 1, right 2."""

FLAME_FILE: Final[Path] = SPRITES_DIR / "ship_flame.png"
"""The flame strip: 8 frames, 2 flicker frames each for up, left, right, down."""

STREAK_FILE: Final[Path] = SPRITES_DIR / "ship_streaks.png"
"""The air streak strip: 4 frames, short then long, 2 flicker frames each. Wider than the body."""

BODY_FRAMES: Final[int] = 3
"""Lean frames: left, centre, right."""

STREAK_FRAMES: Final[int] = 4

FLICKER_FRAMES: Final[int] = 2
"""Flicker frames per jet."""

JET_ORDER: Final[tuple[str, ...]] = ("up", "left", "right", "down")
FLAME_FRAMES: Final[int] = len(JET_ORDER) * FLICKER_FRAMES


@dataclass(frozen=True, slots=True)
class ShipLook:
    """The ship's look values, from tuning/ship_look.json. Look only: none changes play."""

    lean_speed: float
    """Sideways speed, px/tick, from which the ship leans. > 0."""

    streak_speed: float
    """Sideways speed, px/tick, from which short air streaks show. > 0."""

    streak_long_speed: float
    """Sideways speed, px/tick, from which long air streaks show. > streak_speed."""

    flame_ticks_per_frame: int
    """Ticks a flame flicker frame is shown. >= 1."""


DEFAULT_SHIP_LOOK: Final[ShipLook] = ShipLook(
    lean_speed=1.0, streak_speed=1.0, streak_long_speed=4.0, flame_ticks_per_frame=4
)
"""Guesses, tuned by eye. Top sideways speed is about 6.6 px/tick (04-ship.md)."""

_strips: dict[Path, list[pygame.Surface]] = {}
"""Each strip cut into frames. Loaded on the first draw."""


def lean_step(vx: float, look: ShipLook) -> int:
    """Return -1 (lean left), 0 (centre) or +1 (lean right), from the sideways speed `vx`.

    `vx` is px/tick, + is right. Look only.
    """
    if abs(vx) < look.lean_speed:
        return 0
    return 1 if vx > 0 else -1


def streak_level(vx: float, look: ShipLook) -> int | None:
    """Return 0 (short streaks), 1 (long streaks) or None (no streaks) for the speed `vx`."""
    speed: float = abs(vx)
    if speed >= look.streak_long_speed:
        return 1
    if speed >= look.streak_speed:
        return 0
    return None


def active_jets(thrust: Thrust) -> tuple[str, ...]:
    """Return the jets that fire for the keys held, in draw order. Opposite keys cancel."""
    jets: list[str] = []
    if thrust.up and not thrust.down:
        jets.append("up")
    if thrust.left and not thrust.right:
        jets.append("left")
    if thrust.right and not thrust.left:
        jets.append("right")
    if thrust.down and not thrust.up:
        jets.append("down")
    return tuple(jets)


def draw_ship(
    surface: pygame.Surface,
    ship: Ship,
    thrust: Thrust | None = None,
    tick: int = 0,
    look: ShipLook = DEFAULT_SHIP_LOOK,
) -> None:
    """Blit the air streaks and the flames of the held keys, then the lean frame, centered on the
    rounded ship.

    `thrust` None means the ship is not flying (paused, waiting to respawn): no streaks and no
    flame, only the lean. `tick` (>= 0) steps the flicker. Parts outside the surface are clipped.
    """
    body: list[pygame.Surface] = _frames(BODY_FILE, BODY_FRAMES)
    center: tuple[int, int] = (round(ship.x), round(ship.y))
    if thrust is not None:
        flicker: int = (tick // look.flame_ticks_per_frame) % FLICKER_FRAMES
        _draw_streaks(surface, ship.vx, center, flicker, look)
        flame: list[pygame.Surface] = _frames(FLAME_FILE, FLAME_FRAMES)
        for jet in active_jets(thrust):
            image: pygame.Surface = flame[JET_ORDER.index(jet) * FLICKER_FRAMES + flicker]
            surface.blit(image, image.get_rect(center=center))
    frame: pygame.Surface = body[1 + lean_step(ship.vx, look)]
    surface.blit(frame, frame.get_rect(center=center))


def _draw_streaks(
    surface: pygame.Surface,
    vx: float,
    center: tuple[int, int],
    flicker: int,
    look: ShipLook,
) -> None:
    """Blit the air streaks for the speed `vx`: trailing left for a ship moving right, mirrored
    for one moving left. Nothing below `streak_speed`."""
    level: int | None = streak_level(vx, look)
    if level is None:
        return
    image: pygame.Surface = _frames(STREAK_FILE, STREAK_FRAMES)[level * FLICKER_FRAMES + flicker]
    if vx < 0:
        image = pygame.transform.flip(image, True, False)
    surface.blit(image, image.get_rect(center=center))


def _frames(path: Path, count: int) -> list[pygame.Surface]:
    """Load a strip of `count` equal frames once and cut it up.

    Raises ValueError when the strip's width isn't `count` frames, or when the body and flame
    frames differ in size (they are blitted on the same center). The streak frames are wider
    on purpose.
    """
    if path not in _strips:
        strip: pygame.Surface = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            strip = strip.convert_alpha()
        width, height = strip.get_size()
        if width % count != 0:
            raise ValueError(f"{path.name}: width {width} isn't {count} equal frames")
        side: int = width // count
        _strips[path] = [strip.subsurface((i * side, 0, side, height)).copy() for i in range(count)]
        log.info("%s loaded: %d frames of %dx%d px", path.name, count, side, height)
        _check_same_size()
    return _strips[path]


def _check_same_size() -> None:
    """Raise ValueError when both strips are loaded and their frames differ in size."""
    if BODY_FILE in _strips and FLAME_FILE in _strips:
        body_size: tuple[int, int] = _strips[BODY_FILE][0].get_size()
        flame_size: tuple[int, int] = _strips[FLAME_FILE][0].get_size()
        if body_size != flame_size:
            raise ValueError(
                f"{BODY_FILE.name} frames are {body_size} but {FLAME_FILE.name} frames are "
                f"{flame_size}: rerun tools/art/ship_final.py"
            )
