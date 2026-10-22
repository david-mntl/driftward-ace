"""The placeholder floating island look: the shape filled green with a darker 2 px edge inside it.

Source: docs/contracts/systems/drifters.md, Presentation, Floating island; drifters/05-floating-
islands.md, placeholder_look (guess). One image is built per island look on its first frame and
blitted every frame after. It only draws.
"""

import logging
from typing import Final

import pygame

from core.collision import Box, Hitbox, Polygon, Shape, place_hitbox
from core.drifters.base import Drifter, DrifterType
from core.drifters.floating_island import FloatingIsland
from ui.drifters.registry import dim_color, register_view
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

type _Point = tuple[float, float]
type _Key = tuple[Hitbox, float, float, float]

ISLAND_FILL_COLOR: Final[tuple[int, int, int]] = (70, 160, 80)
"""Island fill, RGB. Source: drifters/05-floating-islands.md, placeholder_look (guess)."""

ISLAND_EDGE_COLOR: Final[tuple[int, int, int]] = (35, 90, 45)
"""Island edge, RGB, darker than the fill. Source: drifters/05-floating-islands.md,
placeholder_look (guess)."""

ISLAND_EDGE_WIDTH: Final[int] = 2
"""Edge width, px, drawn inside the shape. Source: drifters/05-floating-islands.md,
placeholder_look (guess)."""

_IMAGES: dict[_Key, pygame.Surface] = {}
"""Built island images, one per look. The image depends only on its key, so an entry is never
stale."""


@register_view(DrifterType.FLOATING_ISLAND)
def render_floating_island(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the island's image with its top-left at the rounded `center` less half its size.

    Every pixel lies inside the footprint box. Colors are times `brightness`. Raises TypeError
    when `drifter` is not a FloatingIsland, ValueError when `scale` is not 1.0.
    """
    if not isinstance(drifter, FloatingIsland):
        raise TypeError("render_floating_island draws a FloatingIsland")
    if scale != 1.0:
        raise ValueError("render_floating_island draws at full size only")
    image: pygame.Surface = _image_for(drifter, brightness)
    left: int = round(center[0] - drifter.width / 2)
    top: int = round(center[1] - drifter.height / 2)
    surface.blit(image, (left, top))


def _image_for(island: FloatingIsland, brightness: float) -> pygame.Surface:
    """Return the island's image, building it the first time its key is drawn."""
    key: _Key = (island.hitbox, island.width, island.height, brightness)
    image: pygame.Surface | None = _IMAGES.get(key)
    if image is None:
        image = _build_image(island, brightness)
        _IMAGES[key] = image
    return image


def _build_image(island: FloatingIsland, brightness: float) -> pygame.Surface:
    """Draw the whole shape in the edge color, then every inset shape in the fill color."""
    image = pygame.Surface((round(island.width), round(island.height)), pygame.SRCALPHA)
    placed: Hitbox = place_hitbox(island.hitbox, island.width / 2, island.height / 2)
    edge_color: tuple[int, int, int] = dim_color(ISLAND_EDGE_COLOR, brightness)
    fill_color: tuple[int, int, int] = dim_color(ISLAND_FILL_COLOR, brightness)
    for shape in placed:
        draw_shape(image, edge_color, shape)
    for shape in placed:
        draw_shape(image, fill_color, _inset(shape, ISLAND_EDGE_WIDTH))
    return image


def _inset(shape: Shape, depth: float) -> Shape:
    """Return `shape` pulled in `depth` px on every side. Raises TypeError for a Circle or Line."""
    if isinstance(shape, Box):
        return Box(shape.cx, shape.cy, shape.w - 2 * depth, shape.h - 2 * depth)
    if isinstance(shape, Polygon):
        return _inset_polygon(shape, depth)
    raise TypeError(
        f"render_floating_island draws boxes and polygons, not '{type(shape).__name__}'"
    )


def _inset_polygon(polygon: Polygon, depth: float) -> Polygon:
    """Move every edge line `depth` px along its inward normal; corner i is where lines meet.

    Corner i is the meeting point of the moved lines of edges i - 1 and i.
    """
    points: tuple[_Point, ...] = polygon.points
    inward: float = 1.0 if _signed_area(points) > 0 else -1.0
    moved: list[tuple[_Point, _Point]] = [
        _moved_edge(start, end, depth * inward)
        for start, end in zip(points, points[1:] + points[:1], strict=True)
    ]
    corners: list[_Point] = [_meet(moved[index - 1], moved[index]) for index in range(len(moved))]
    return Polygon(tuple(corners))


def _signed_area(points: tuple[_Point, ...]) -> float:
    """Twice the polygon's signed area (shoelace). Its sign tells which side is inside."""
    return sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1], strict=True)
    )


def _moved_edge(start: _Point, end: _Point, offset: float) -> tuple[_Point, _Point]:
    """Return the edge start-end moved `offset` px along its left normal (-dy, dx), unit length."""
    dx: float = end[0] - start[0]
    dy: float = end[1] - start[1]
    length: float = (dx * dx + dy * dy) ** 0.5
    shift_x: float = -dy / length * offset
    shift_y: float = dx / length * offset
    return (start[0] + shift_x, start[1] + shift_y), (end[0] + shift_x, end[1] + shift_y)


def _meet(first: tuple[_Point, _Point], second: tuple[_Point, _Point]) -> _Point:
    """Return where the infinite lines through two edges cross. The edges are never parallel."""
    (ax, ay), (bx, by) = first
    (cx, cy), (dx, dy) = second
    first_x: float = bx - ax
    first_y: float = by - ay
    second_x: float = dx - cx
    second_y: float = dy - cy
    along: float = ((cx - ax) * second_y - (cy - ay) * second_x) / (
        first_x * second_y - first_y * second_x
    )
    return ax + along * first_x, ay + along * first_y
