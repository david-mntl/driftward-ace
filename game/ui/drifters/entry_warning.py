"""The entry warning: a glow with spikes and a half-size copy of the drifter, drawn at its entry.

Source: docs/contracts/systems/drifters.md, Presentation, Entry warning; 07-drifters.md,
entry_warning values (guess). The whole warning fits inside the drifter's own width. One image
is built per drifter on its first warning frame and blitted every frame after. It only draws.
"""

from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, Final

import pygame

from core.drifters.base import Drifter, DrifterType

if TYPE_CHECKING:
    from ui.drifters.registry import DrifterView

log = logging.getLogger(__name__)

ENTRY_WARNING_GLOW: Final[tuple[int, int, int]] = (255, 220, 120)
"""Glow and spike color, RGB. Source: 07-drifters.md, entry_warning_glow (guess)."""

ENTRY_WARNING_SCALE: Final[float] = 0.5
"""Size of the drifter's copy inside the warning, 0..1. Source: 07-drifters.md,
entry_warning_look: half size (guess)."""

SPIKE_COUNT_MIN: Final[int] = 6
"""Fewest spikes in one warning. Source: 07-drifters.md, entry_warning_spikes (guess)."""

SPIKE_COUNT_MAX: Final[int] = 9
"""Most spikes in one warning. Source: 07-drifters.md, entry_warning_spikes (guess)."""

WARNING_SIZE_RATIO: Final[float] = 1.0
"""Warning diameter as a share of the drifter's width, 0..1. Source: 07-drifters.md,
entry_warning_size: the whole warning fits inside the drifter's own width (guess)."""

GLOW_RATIO: Final[float] = 0.75
"""Glow radius as a share of the warning's radius, 0..1. A placeholder choice, not in the GDD:
drifters.md, Rationale."""

type _Key = tuple[int, DrifterType, str, float]

_IMAGES: dict[_Key, pygame.Surface] = {}
"""Built warning images, one per drifter. Dropped when the drifter turns ACTIVE."""


def draw_entry_warning(surface: pygame.Surface, drifter: Drifter, view: DrifterView) -> None:
    """Blit the drifter's warning image centered on `drifter.warning_center()`, rounded to px.

    Builds the image on the first call for the drifter, and reuses it after.
    """
    key: _Key = _key(drifter)
    image: pygame.Surface | None = _IMAGES.get(key)
    if image is None:
        image = _build_image(drifter, view)
        _IMAGES[key] = image
    center_x, center_y = drifter.warning_center()
    surface.blit(image, image.get_rect(center=(round(center_x), round(center_y))))


def drop_entry_warning(drifter: Drifter) -> None:
    """Forget the warning image of `drifter`. Does nothing when it has none."""
    _IMAGES.pop(_key(drifter), None)


def _key(drifter: Drifter) -> _Key:
    """Return the cache key: the image depends only on these four facts."""
    return (drifter.uid, drifter.drifter_type, drifter.variant, drifter.warning_tilt_degrees())


def _build_image(drifter: Drifter, view: DrifterView) -> pygame.Surface:
    """Return the warning image: glow, spikes, then the drifter's copy on top.

    The copy is drawn at full brightness, turned by `drifter.warning_tilt_degrees()`.

    Square, side 2 * ceil(R) + 1, with the warning's center on its middle pixel, so nothing
    lies more than R from the center, where R = WARNING_SIZE_RATIO * width / 2, px.
    """
    radius: float = WARNING_SIZE_RATIO * drifter.width / 2
    half: int = math.ceil(radius)
    image: pygame.Surface = pygame.Surface((2 * half + 1, 2 * half + 1), pygame.SRCALPHA)
    center: tuple[int, int] = (half, half)
    pygame.draw.circle(image, ENTRY_WARNING_GLOW, center, GLOW_RATIO * radius)
    _draw_spikes(image, center, drifter.uid, radius)
    _draw_copy(image, drifter, view)
    return image


def _draw_copy(image: pygame.Surface, drifter: Drifter, view: DrifterView) -> None:
    """Draw the half-size copy centered on `image`, turned counterclockwise by the drifter's tilt.

    A turned copy is drawn on its own transparent surface first, so turning never touches the glow.
    """
    center: tuple[float, float] = (image.get_width() // 2, image.get_height() // 2)
    tilt: float = drifter.warning_tilt_degrees()
    if tilt == 0.0:
        view(image, drifter, center, ENTRY_WARNING_SCALE, 1.0)
        return
    copy: pygame.Surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    view(copy, drifter, center, ENTRY_WARNING_SCALE, 1.0)
    turned: pygame.Surface = pygame.transform.rotate(copy, tilt)
    image.blit(turned, turned.get_rect(center=(round(center[0]), round(center[1]))))


def _draw_spikes(
    image: pygame.Surface,
    center: tuple[int, int],
    seed: int,
    radius: float,
) -> None:
    """Draw 6 to 9 1 px spikes from `center`, each out of the glow and not past `radius`.

    Count, then an angle and a length per spike, from `random.Random(seed)`.
    """
    rng: random.Random = random.Random(seed)
    for _ in range(rng.randint(SPIKE_COUNT_MIN, SPIKE_COUNT_MAX)):
        angle: float = rng.uniform(0, math.tau)
        length: float = rng.uniform(GLOW_RATIO * radius, radius)
        tip: tuple[float, float] = (
            center[0] + length * math.cos(angle),
            center[1] + length * math.sin(angle),
        )
        pygame.draw.line(image, ENTRY_WARNING_GLOW, center, tip, 1)
