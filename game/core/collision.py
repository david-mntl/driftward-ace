"""Hitbox shapes and their overlap test.

A hitbox is a tuple of circles and upright boxes. Shapes hold offsets from their owner's
center until `place_hitbox` moves them to screen positions. Overlap is strict: shapes that
only touch at an edge or a point don't overlap. Stdlib only, pure, no frame time, no
randomness.

Source: docs/contracts/systems/objects.md, Interface and Rules, Collision.
"""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Circle:
    """A circle hitbox shape, px."""

    cx: float
    """Center x, px. An offset from the owner's center until placed, then screen x."""

    cy: float
    """Center y, px, y down. An offset until placed, then screen y."""

    r: float
    """Radius, px. Greater than 0."""


@dataclass(frozen=True, slots=True)
class Box:
    """An upright box hitbox shape, px. Boxes never rotate."""

    cx: float
    """Center x, px. An offset from the owner's center until placed, then screen x."""

    cy: float
    """Center y, px, y down. An offset until placed, then screen y."""

    w: float
    """Full width, px. Greater than 0."""

    h: float
    """Full height, px. Greater than 0."""


Shape = Circle | Box

Hitbox = tuple[Shape, ...]
"""One or more shapes. An empty hitbox touches nothing."""


def place_hitbox(hitbox: Hitbox, x: float, y: float) -> Hitbox:
    """Return the hitbox with every shape moved by (x, y), px.

    Offsets from the owner's center become screen positions.
    """
    return tuple(_move_shape(shape, x, y) for shape in hitbox)


def hitboxes_overlap(a: Hitbox, b: Hitbox) -> bool:
    """Return True when any shape of `a` overlaps any shape of `b`. Both must be placed.

    Shapes that only touch at an edge or a point don't overlap. An empty hitbox overlaps
    nothing. Source: objects.md, Rules, Collision.
    """
    return any(_shapes_overlap(sa, sb) for sa in a for sb in b)


def grow_hitbox(hitbox: Hitbox, margin: float) -> Hitbox:
    """Return the hitbox with every shape grown by `margin` px on every side.

    A circle's radius grows by the margin. A box's w and h grow by twice the margin.
    Centers don't move. Source: 06-scoring.md, rule 3.
    """
    return tuple(_grow_shape(shape, margin) for shape in hitbox)


def _move_shape(shape: Shape, x: float, y: float) -> Shape:
    """Return `shape` with its center moved by (x, y), px."""
    if isinstance(shape, Circle):
        return Circle(shape.cx + x, shape.cy + y, shape.r)
    return Box(shape.cx + x, shape.cy + y, shape.w, shape.h)


def _grow_shape(shape: Shape, margin: float) -> Shape:
    """Return `shape` grown by `margin` px on every side."""
    if isinstance(shape, Circle):
        return Circle(shape.cx, shape.cy, shape.r + margin)
    return Box(shape.cx, shape.cy, shape.w + 2 * margin, shape.h + 2 * margin)


def _shapes_overlap(a: Shape, b: Shape) -> bool:
    """Return True when two placed shapes share area."""
    if isinstance(a, Circle):
        if isinstance(b, Circle):
            return _circles_overlap(a, b)
        return _circle_box_overlap(a, b)
    if isinstance(b, Circle):
        return _circle_box_overlap(b, a)
    return _boxes_overlap(a, b)


def _circles_overlap(a: Circle, b: Circle) -> bool:
    """Circle and circle: distance between centers is less than the sum of radii."""
    dx: float = a.cx - b.cx
    dy: float = a.cy - b.cy
    reach: float = a.r + b.r
    return dx * dx + dy * dy < reach * reach


def _boxes_overlap(a: Box, b: Box) -> bool:
    """Box and box: the center gaps are less than the half-size sums on both axes."""
    return abs(a.cx - b.cx) < (a.w + b.w) / 2 and abs(a.cy - b.cy) < (a.h + b.h) / 2


def _circle_box_overlap(circle: Circle, box: Box) -> bool:
    """Circle and box: the box point nearest the circle's center is closer than r."""
    nearest_x: float = min(max(circle.cx, box.cx - box.w / 2), box.cx + box.w / 2)
    nearest_y: float = min(max(circle.cy, box.cy - box.h / 2), box.cy + box.h / 2)
    dx: float = circle.cx - nearest_x
    dy: float = circle.cy - nearest_y
    return dx * dx + dy * dy < circle.r * circle.r
