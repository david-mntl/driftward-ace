"""Hitbox shapes and their overlap test.

A hitbox is a tuple of circles, upright boxes and lines. Shapes hold offsets from their
owner's center until `place_hitbox` moves them to screen positions. Overlap is strict:
shapes that only touch at an edge or a point don't overlap. A line is a capsule: every point
within half its thickness of a segment. Stdlib only, pure, no frame time, no randomness.

Source: docs/contracts/systems/drifters.md, Interface and Rules, Collision.
"""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

_Point = tuple[float, float]
_BoxCorners = tuple[_Point, _Point, _Point, _Point]


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


@dataclass(frozen=True, slots=True)
class Line:
    """A line hitbox shape: straight from A to B, a set thickness, round ends, px."""

    ax: float
    """End A x, px. An offset from the owner's center until placed, then screen x."""

    ay: float
    """End A y, px, y down. An offset until placed, then screen y."""

    bx: float
    """End B x, px. An offset from the owner's center until placed, then screen x."""

    by: float
    """End B y, px, y down. An offset until placed, then screen y."""

    thickness: float
    """Full thickness, px. Greater than 0. Every point within thickness / 2 of segment AB."""


Shape = Circle | Box | Line

Hitbox = tuple[Shape, ...]
"""One or more shapes. An empty hitbox touches nothing."""


def place_hitbox(hitbox: Hitbox, x: float, y: float) -> Hitbox:
    """Return the hitbox with every shape moved by (x, y), px.

    Offsets from the owner's center become screen positions. A line moves both ends.
    Raises TypeError for a shape that is not a Circle, a Box or a Line.
    """
    return tuple(_move_shape(shape, x, y) for shape in hitbox)


def hitboxes_overlap(a: Hitbox, b: Hitbox) -> bool:
    """Return True when any shape of `a` overlaps any shape of `b`. Both must be placed.

    Shapes that only touch at an edge or a point don't overlap. An empty hitbox overlaps
    nothing. Raises TypeError for a shape that is not a Circle, a Box or a Line, even when the
    other hitbox is empty. Source: drifters.md, Rules, Collision.
    """
    _require_known_shapes(a)
    _require_known_shapes(b)
    return any(_shapes_overlap(sa, sb) for sa in a for sb in b)


def grow_hitbox(hitbox: Hitbox, margin: float) -> Hitbox:
    """Return the hitbox with every shape grown by `margin` px on every side.

    A circle's radius grows by the margin. A box's w and h grow by twice the margin.
    A line's thickness grows by twice the margin, so it grows on each side and at both ends.
    Centers and line ends don't move. Raises TypeError for a shape that is not a Circle, a
    Box or a Line.
    Source: 06-scoring.md, rule 3.
    """
    return tuple(_grow_shape(shape, margin) for shape in hitbox)


def _unknown_shape(shape: object) -> TypeError:
    """Return the error for an object that is not a Circle, a Box or a Line.

    Nothing is treated as a box by default. Source: drifters.md, Rules, Collision.
    """
    return TypeError(f"unknown shape kind '{type(shape).__name__}'")


def _require_known_shapes(hitbox: Hitbox) -> None:
    """Raise TypeError when any shape of `hitbox` is not a Circle, a Box or a Line."""
    for shape in hitbox:
        if not isinstance(shape, Circle | Box | Line):
            raise _unknown_shape(shape)


def _move_shape(shape: Shape, x: float, y: float) -> Shape:
    """Return `shape` with its center moved by (x, y), px."""
    if isinstance(shape, Circle):
        return Circle(shape.cx + x, shape.cy + y, shape.r)
    if isinstance(shape, Box):
        return Box(shape.cx + x, shape.cy + y, shape.w, shape.h)
    if isinstance(shape, Line):
        return Line(shape.ax + x, shape.ay + y, shape.bx + x, shape.by + y, shape.thickness)
    raise _unknown_shape(shape)


def _grow_shape(shape: Shape, margin: float) -> Shape:
    """Return `shape` grown by `margin` px on every side."""
    if isinstance(shape, Circle):
        return Circle(shape.cx, shape.cy, shape.r + margin)
    if isinstance(shape, Box):
        return Box(shape.cx, shape.cy, shape.w + 2 * margin, shape.h + 2 * margin)
    if isinstance(shape, Line):
        return Line(shape.ax, shape.ay, shape.bx, shape.by, shape.thickness + 2 * margin)
    raise _unknown_shape(shape)


def _shapes_overlap(a: Shape, b: Shape) -> bool:
    """Return True when two placed shapes share area."""
    if isinstance(a, Line):
        return _line_overlaps(a, b)
    if isinstance(b, Line):
        return _line_overlaps(b, a)
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
    return _point_box_dist_sq((circle.cx, circle.cy), box) < circle.r * circle.r


def _line_overlaps(line: Line, other: Shape) -> bool:
    """Line and any shape: the shortest distance is less than the line's half thickness plus
    the other's reach (a circle's radius, a line's half thickness, or 0 for a box).
    """
    half: float = line.thickness / 2
    a: _Point = (line.ax, line.ay)
    b: _Point = (line.bx, line.by)
    if isinstance(other, Circle):
        reach: float = half + other.r
        return _point_segment_dist_sq((other.cx, other.cy), a, b) < reach * reach
    if isinstance(other, Line):
        reach = half + other.thickness / 2
        c: _Point = (other.ax, other.ay)
        d: _Point = (other.bx, other.by)
        return _segments_dist_sq(a, b, c, d) < reach * reach
    return _segment_box_dist_sq(a, b, other) < half * half


def _cross(o: _Point, p: _Point, q: _Point) -> float:
    """Cross product of (p - o) and (q - o): its sign says which side of op the point q lies."""
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])


def _point_segment_dist_sq(p: _Point, a: _Point, b: _Point) -> float:
    """Squared distance from point `p` to segment AB. A equal to B is a point.

    Inside the segment the distance comes from the cross product, with no projection `t`, so
    whole-number and half-step inputs give an exact result and a touch is not an overlap.
    """
    abx: float = b[0] - a[0]
    aby: float = b[1] - a[1]
    apx: float = p[0] - a[0]
    apy: float = p[1] - a[1]
    length_sq: float = abx * abx + aby * aby
    along: float = apx * abx + apy * aby
    if length_sq == 0.0 or along <= 0.0:
        return apx * apx + apy * apy
    if along >= length_sq:
        bpx: float = p[0] - b[0]
        bpy: float = p[1] - b[1]
        return bpx * bpx + bpy * bpy
    cross: float = apx * aby - apy * abx
    return cross * cross / length_sq


def _within_span(a: _Point, b: _Point, p: _Point) -> bool:
    """True when `p`, known to lie on the line through A and B, is inside the segment AB."""
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _segments_meet(a: _Point, b: _Point, c: _Point, d: _Point) -> bool:
    """True when segments AB and CD cross or touch, found with cross-product signs."""
    side_c: float = _cross(a, b, c)
    side_d: float = _cross(a, b, d)
    side_a: float = _cross(c, d, a)
    side_b: float = _cross(c, d, b)
    if side_c * side_d < 0.0 and side_a * side_b < 0.0:
        return True
    return (
        (side_c == 0.0 and _within_span(a, b, c))
        or (side_d == 0.0 and _within_span(a, b, d))
        or (side_a == 0.0 and _within_span(c, d, a))
        or (side_b == 0.0 and _within_span(c, d, b))
    )


def _segments_dist_sq(a: _Point, b: _Point, c: _Point, d: _Point) -> float:
    """Squared shortest distance between segments AB and CD. 0 when they cross or touch."""
    if _segments_meet(a, b, c, d):
        return 0.0
    return min(
        _point_segment_dist_sq(a, c, d),
        _point_segment_dist_sq(b, c, d),
        _point_segment_dist_sq(c, a, b),
        _point_segment_dist_sq(d, a, b),
    )


def _point_box_dist_sq(p: _Point, box: Box) -> float:
    """Squared distance from point `p` to the filled box. 0 inside or on its edge."""
    nearest_x: float = min(max(p[0], box.cx - box.w / 2), box.cx + box.w / 2)
    nearest_y: float = min(max(p[1], box.cy - box.h / 2), box.cy + box.h / 2)
    dx: float = p[0] - nearest_x
    dy: float = p[1] - nearest_y
    return dx * dx + dy * dy


def _box_corners(box: Box) -> _BoxCorners:
    """The box's four corners, in order around its edge."""
    left: float = box.cx - box.w / 2
    right: float = box.cx + box.w / 2
    top: float = box.cy - box.h / 2
    bottom: float = box.cy + box.h / 2
    return ((left, top), (right, top), (right, bottom), (left, bottom))


def _segment_box_dist_sq(a: _Point, b: _Point, box: Box) -> float:
    """Squared shortest distance between segment AB and the filled box.

    0 when the segment meets the box, inside or on its edge. Otherwise the closest point is
    one of the segment's two ends or one of the box's four corners.
    """
    if _point_box_dist_sq(a, box) == 0.0 or _point_box_dist_sq(b, box) == 0.0:
        return 0.0
    corners: _BoxCorners = _box_corners(box)
    for index, corner in enumerate(corners):
        if _segments_meet(a, b, corner, corners[(index + 1) % len(corners)]):
            return 0.0
    return min(
        _point_box_dist_sq(a, box),
        _point_box_dist_sq(b, box),
        *(_point_segment_dist_sq(corner, a, b) for corner in corners),
    )
