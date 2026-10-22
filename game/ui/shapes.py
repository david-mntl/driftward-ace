"""Draws placed hitbox shapes: the shared helper for the ship view and the debug outlines.

Source: docs/contracts/systems/drifters.md, ui/shapes.py. It only draws. It never fills the
background, never flips the display, never logs per frame and never catches an error.
"""

import logging
import math

import pygame

from core.collision import Box, Circle, Hitbox, Line, Polygon, Shape

log = logging.getLogger(__name__)


def draw_shape(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    shape: Shape,
    width: int = 0,
) -> None:
    """Draw one placed shape in `color`, screen px. `width` 0 fills, 1 is a 1 px outline.

    A box is the rectangle with top-left (round(cx - w / 2), round(cy - h / 2)) and size
    round(w) by round(h). A circle has center (round(cx), round(cy)) and radius round(r).
    A line is the band of its thickness around segment AB with round ends (see `_draw_line`).
    A polygon is filled by the pixel-center rule or outlined 1 px (see `_draw_polygon`).
    Raises TypeError for any other shape kind.
    """
    if isinstance(shape, Circle):
        _draw_circle(surface, color, shape, width)
    elif isinstance(shape, Box):
        _draw_box(surface, color, shape, width)
    elif isinstance(shape, Line):
        _draw_line(surface, color, shape, width)
    elif isinstance(shape, Polygon):
        _draw_polygon(surface, color, shape, width)
    else:
        raise TypeError(f"unknown shape kind '{type(shape).__name__}'")


def draw_hitbox(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    hitbox: Hitbox,
    width: int = 0,
) -> None:
    """Draw every shape of a placed hitbox, in order. `width` as in `draw_shape`."""
    for shape in hitbox:
        draw_shape(surface, color, shape, width)


def _draw_box(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    box: Box,
    width: int,
) -> None:
    """Draw a placed box as a rectangle."""
    left: int = round(box.cx - box.w / 2)
    top: int = round(box.cy - box.h / 2)
    rect = pygame.Rect(left, top, round(box.w), round(box.h))
    pygame.draw.rect(surface, color, rect, width)


def _draw_circle(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    circle: Circle,
    width: int,
) -> None:
    """Draw a placed circle."""
    center: tuple[int, int] = (round(circle.cx), round(circle.cy))
    pygame.draw.circle(surface, color, center, round(circle.r), width)


def _draw_line(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    line: Line,
    width: int,
) -> None:
    """Draw a placed line: a filled band, or for any other `width` a 1 px outline of it."""
    if width == 0:
        _fill_line(surface, color, line)
    else:
        _outline_line(surface, color, line)


def _fill_line(surface: pygame.Surface, color: tuple[int, int, int], line: Line) -> None:
    """Fill the rectangle around AB, then a disc at each end. A == B draws the disc only."""
    radius: int = round(line.thickness / 2)
    if not _is_point(line):
        pygame.draw.polygon(surface, color, _band_corners(line))
    pygame.draw.circle(surface, color, (round(line.ax), round(line.ay)), radius)
    pygame.draw.circle(surface, color, (round(line.bx), round(line.by)), radius)


def _outline_line(surface: pygame.Surface, color: tuple[int, int, int], line: Line) -> None:
    """Draw the two long sides and the outer half of each end circle, all 1 px.

    A == B draws a 1 px circle outline.
    """
    radius: int = round(line.thickness / 2)
    center_a: tuple[int, int] = (round(line.ax), round(line.ay))
    center_b: tuple[int, int] = (round(line.bx), round(line.by))
    if _is_point(line):
        pygame.draw.circle(surface, color, center_a, radius, 1)
        return
    a_up, b_up, b_down, a_down = _band_corners(line)
    pygame.draw.line(surface, color, a_up, b_up, 1)
    pygame.draw.line(surface, color, a_down, b_down, 1)
    heading: float = math.atan2(line.ay - line.by, line.bx - line.ax)
    _draw_half_circle(surface, color, center_b, radius, heading)
    _draw_half_circle(surface, color, center_a, radius, heading + math.pi)


def _draw_half_circle(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    center: tuple[int, int],
    radius: int,
    facing: float,
) -> None:
    """Draw a 1 px arc of the half circle facing `facing` (radians, counterclockwise on screen)."""
    rect = pygame.Rect(center[0] - radius, center[1] - radius, 2 * radius, 2 * radius)
    pygame.draw.arc(surface, color, rect, facing - math.pi / 2, facing + math.pi / 2, 1)


def _draw_polygon(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    polygon: Polygon,
    width: int,
) -> None:
    """Draw a placed polygon: filled row by row, or for any other `width` a 1 px outline."""
    if width == 0:
        _fill_polygon(surface, color, polygon)
        return
    corners: list[tuple[int, int]] = [(round(px), round(py)) for px, py in polygon.points]
    pygame.draw.polygon(surface, color, corners, 1)


def _fill_polygon(surface: pygame.Surface, color: tuple[int, int, int], polygon: Polygon) -> None:
    """Fill every pixel whose center (x + 0.5, y + 0.5) lies inside or on the polygon."""
    ys: list[float] = [py for _, py in polygon.points]
    first_row: int = math.ceil(min(ys) - 0.5)
    last_row: int = math.floor(max(ys) - 0.5)
    for row in range(first_row, last_row + 1):
        crossings: list[float] = _row_crossings(polygon, row + 0.5)
        first_col: int = math.ceil(min(crossings) - 0.5)
        last_col: int = math.floor(max(crossings) - 0.5)
        if last_col >= first_col:
            span = pygame.Rect(first_col, row, last_col - first_col + 1, 1)
            pygame.draw.rect(surface, color, span)


def _row_crossings(polygon: Polygon, yc: float) -> list[float]:
    """x where the line y = yc meets each edge that reaches it. A flat edge on yc gives both ends.

    Never empty for a `yc` between the polygon's lowest and highest point.
    """
    crossings: list[float] = []
    points: tuple[tuple[float, float], ...] = polygon.points
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1], strict=True):
        if not min(y0, y1) <= yc <= max(y0, y1):
            continue
        if y0 == y1:
            crossings.extend((x0, x1))
        else:
            crossings.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
    return crossings


def _is_point(line: Line) -> bool:
    """True when A and B are the same point."""
    return line.ax == line.bx and line.ay == line.by


def _band_corners(line: Line) -> list[tuple[float, float]]:
    """Corners A+n, B+n, B-n, A-n of the band, with n the unit normal of AB times thickness / 2."""
    dx: float = line.bx - line.ax
    dy: float = line.by - line.ay
    length: float = math.hypot(dx, dy)
    half: float = line.thickness / 2
    nx: float = -dy / length * half
    ny: float = dx / length * half
    return [
        (line.ax + nx, line.ay + ny),
        (line.bx + nx, line.by + ny),
        (line.bx - nx, line.by - ny),
        (line.ax - nx, line.ay - ny),
    ]
