"""The satellite look: panels that swing on a sine round a still body, inside a turning field.

Two sprite strips, one row of square frames each, so a strip's frame count is its width over its
height. `satellite.png` holds the swing: body and panels, frame 0 level. `satellite_field.png`
holds the fuchsia magnetism field, one full turn round the body; it is drawn first, behind.
The swing frame comes from the core (`Satellite.swing_frame`), the same step its hitbox turns by.
The field frame steps every `field_ticks_per_frame` ticks. The art faces right; a satellite
flying left (`invert`) is mirrored. Frames are made by tools/art/satellite_swing.py.
Source: drifters/02-satellite.md, rule 8 and look_reference; 12-art-and-audio.md, rule 13.
It only draws.
"""

import logging
from pathlib import Path
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.satellite import Satellite
from ui.drifters.registry import register_view

log = logging.getLogger(__name__)

SPRITES_DIR: Final[Path] = Path(__file__).resolve().parents[2] / "assets" / "sprites"

SWING_FILE: Final[Path] = SPRITES_DIR / "satellite.png"
"""The swing strip: body and panels."""

FIELD_FILE: Final[Path] = SPRITES_DIR / "satellite_field.png"
"""The field strip: the magnetism arcs only, same frame size as the swing strip."""

_strips: dict[Path, list[pygame.Surface]] = {}
"""Each strip cut into frames. Loaded on the first draw."""

_warned_mismatch: list[bool] = [False]
"""Set once the swing strip's frame count has been logged as not matching the tuning."""


@register_view(DrifterType.SATELLITE)
def render_satellite(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the field frame, then the swing frame, centered on the rounded `center`.

    Scaled by `scale`; colors are times `brightness` (0..1). A drifter that isn't a flying
    Satellite (a stand-in, a warning copy) shows frame 0 of each, facing right.
    """
    swing: list[pygame.Surface] = _frames(SWING_FILE)
    field: list[pygame.Surface] = _frames(FIELD_FILE)
    swing_index: int = 0
    field_index: int = 0
    flip: bool = False
    if isinstance(drifter, Satellite):
        flip = drifter.invert
        if drifter.phase is Phase.ACTIVE:
            swing_index = _swing_index(drifter, len(swing))
            field_index = (drifter.ticks_in_phase // drifter.field_ticks_per_frame) % len(field)
    for image in (field[field_index], swing[swing_index]):
        _blit(surface, image, center, scale, brightness, flip)


def _swing_index(drifter: Satellite, count: int) -> int:
    """Return the core's swing step, wrapped to the strip. Logs once if the counts differ."""
    if drifter.swing_frames != count and not _warned_mismatch[0]:
        _warned_mismatch[0] = True
        log.warning(
            "%s has %d frames but the tuning says swing_frames %d: the drawing and the hitbox "
            "won't match. Rerun tools/art/satellite_swing.py.",
            SWING_FILE.name,
            count,
            drifter.swing_frames,
        )
    return drifter.swing_frame() % count


def _blit(
    surface: pygame.Surface,
    image: pygame.Surface,
    center: tuple[float, float],
    scale: float,
    brightness: float,
    flip: bool,
) -> None:
    """Blit one frame, mirrored, scaled and dimmed as asked, centered on the rounded `center`."""
    if flip:
        image = pygame.transform.flip(image, True, False)
    if scale != 1.0:
        size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
        image = pygame.transform.smoothscale(image, size)
    if brightness < 1.0:
        image = image.copy()
        level: int = round(255 * max(0.0, brightness))
        image.fill((level, level, level, 255), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(image, image.get_rect(center=(round(center[0]), round(center[1]))))


def _frames(path: Path) -> list[pygame.Surface]:
    """Load a strip of square frames once and cut it up.

    Raises ValueError when its width isn't a whole number of its height.
    """
    if path in _strips:
        return _strips[path]
    strip: pygame.Surface = pygame.image.load(str(path))
    if pygame.display.get_surface() is not None:
        strip = strip.convert_alpha()
    width, side = strip.get_size()
    if width % side != 0:
        raise ValueError(f"{path.name}: width {width} isn't a whole number of {side} px frames")
    frames: list[pygame.Surface] = [
        strip.subsurface((i * side, 0, side, side)).copy() for i in range(width // side)
    ]
    _strips[path] = frames
    log.info("%s loaded: %d frames of %dx%d px", path.name, len(frames), side, side)
    return frames
