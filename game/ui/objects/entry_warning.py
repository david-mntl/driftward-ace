"""The entry warning: a glow with spikes and a half-size copy of the object, drawn at its entry.

Source: docs/contracts/systems/objects.md, Presentation, Entry warning; 07-objects.md,
entry_warning values (guess). The whole warning fits inside the object's own width. One image
is built per object on its first warning frame and blitted every frame after. It only draws.
"""

from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, Final

import pygame

from core.objects.base import GameObject, ObjectType

if TYPE_CHECKING:
    from ui.objects.registry import ObjectView

log = logging.getLogger(__name__)

ENTRY_WARNING_GLOW: Final[tuple[int, int, int]] = (255, 220, 120)
"""Glow and spike color, RGB. Source: 07-objects.md, entry_warning_glow (guess)."""

ENTRY_WARNING_SCALE: Final[float] = 0.5
"""Size of the object's copy inside the warning, 0..1. Source: 07-objects.md,
entry_warning_look: half size (guess)."""

SPIKE_COUNT_MIN: Final[int] = 6
"""Fewest spikes in one warning. Source: 07-objects.md, entry_warning_spikes (guess)."""

SPIKE_COUNT_MAX: Final[int] = 9
"""Most spikes in one warning. Source: 07-objects.md, entry_warning_spikes (guess)."""

WARNING_SIZE_RATIO: Final[float] = 1.0
"""Warning diameter as a share of the object's width, 0..1. Source: 07-objects.md,
entry_warning_size: the whole warning fits inside the object's own width (guess)."""

GLOW_RATIO: Final[float] = 0.75
"""Glow radius as a share of the warning's radius, 0..1. A placeholder choice, not in the GDD:
objects.md, Rationale."""

type _Key = tuple[int, ObjectType, str]

_IMAGES: dict[_Key, pygame.Surface] = {}
"""Built warning images, one per object. Dropped when the object turns ACTIVE."""


def draw_entry_warning(surface: pygame.Surface, obj: GameObject, view: ObjectView) -> None:
    """Blit the object's warning image centered on `obj.warning_center()`, rounded to px.

    Builds the image on the first call for the object, and reuses it after.
    """
    key: _Key = _key(obj)
    image: pygame.Surface | None = _IMAGES.get(key)
    if image is None:
        image = _build_image(obj, view)
        _IMAGES[key] = image
    center_x, center_y = obj.warning_center()
    surface.blit(image, image.get_rect(center=(round(center_x), round(center_y))))


def drop_entry_warning(obj: GameObject) -> None:
    """Forget the warning image of `obj`. Does nothing when it has none."""
    _IMAGES.pop(_key(obj), None)


def _key(obj: GameObject) -> _Key:
    """Return the cache key: the image depends only on these three facts."""
    return (obj.uid, obj.object_type, obj.variant)


def _build_image(obj: GameObject, view: ObjectView) -> pygame.Surface:
    """Return the warning image: glow, spikes, then the object's copy on top.

    Square, side 2 * ceil(R) + 1, with the warning's center on its middle pixel, so nothing
    lies more than R from the center, where R = WARNING_SIZE_RATIO * width / 2, px.
    """
    radius: float = WARNING_SIZE_RATIO * obj.width / 2
    half: int = math.ceil(radius)
    image: pygame.Surface = pygame.Surface((2 * half + 1, 2 * half + 1), pygame.SRCALPHA)
    center: tuple[int, int] = (half, half)
    pygame.draw.circle(image, ENTRY_WARNING_GLOW, center, GLOW_RATIO * radius)
    _draw_spikes(image, center, obj.uid, radius)
    view(image, obj, (float(half), float(half)), ENTRY_WARNING_SCALE)
    return image


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
