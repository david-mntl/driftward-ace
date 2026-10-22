"""Hitbox shapes and their overlap test.

A hitbox is a tuple of circles, upright boxes, lines and convex polygons. Shapes hold offsets
from their owner's center until `place_hitbox` moves them to screen positions. Overlap is
strict: shapes that only touch at an edge or a point don't overlap. A line is a capsule: every
point within half its thickness of a segment. A polygon is the filled shape inside its corners.
The push-out functions (`deeply_overlaps`, `push_directions`, `exit_distance`) measure how far
boxes and polygons overlap and which way out is shortest. Stdlib only, pure, no frame time, no
randomness.

Source: docs/contracts/systems/drifters.md, Interface and Rules, Collision and Push-out.
"""

import logging
import math
from dataclasses import dataclass
from typing import Final

log = logging.getLogger(__name__)

_Point = tuple[float, float]
_BoxCorners = tuple[_Point, _Point, _Point, _Point]
_Span = tuple[float, float]

Direction = tuple[float, float]
"""A unit vector, screen px, y down: (0.0, -1.0) is up."""

SURFACE_TOLERANCE: Final[float] = 1e-9
"""px. An overlap this deep or less counts as touching for `deeply_overlaps` and
`exit_distance`. Not a game value: it only absorbs floating point error after a push.
Source: drifters.md, Rationale, SURFACE_TOLERANCE."""

_AXIS_DIRECTIONS: Final[tuple[Direction, ...]] = ((0.0, -1.0), (0.0, 1.0), (-1.0, 0.0), (1.0, 0.0))
"""Up, down, left, right: the first directions `push_directions` returns."""


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


@dataclass(frozen=True, slots=True)
class Polygon:
    """A convex polygon hitbox shape: a filled shape with straight edges, px."""

    points: tuple[tuple[float, float], ...]
    """Corners in order around the edge, either way round, at least 3, px, y down.

    Offsets from the owner's center until placed, then screen px. Convex, no two points the
    same, no three neighbours on one line. Trusted: core builds every polygon."""


Shape = Circle | Box | Line | Polygon

Hitbox = tuple[Shape, ...]
"""One or more shapes. An empty hitbox touches nothing."""


def place_hitbox(hitbox: Hitbox, x: float, y: float) -> Hitbox:
    """Return the hitbox with every shape moved by (x, y), px.

    Offsets from the owner's center become screen positions. A line moves both ends and a
    polygon every point. Raises TypeError for a shape that is not a Circle, a Box, a Line or a
    Polygon.
    """
    return tuple(_move_shape(shape, x, y) for shape in hitbox)


def hitboxes_overlap(a: Hitbox, b: Hitbox) -> bool:
    """Return True when any shape of `a` overlaps any shape of `b`. Both must be placed.

    Shapes that only touch at an edge or a point don't overlap. An empty hitbox overlaps
    nothing. Raises TypeError for a shape that is not a Circle, a Box, a Line or a Polygon,
    even when the other hitbox is empty. Source: drifters.md, Rules, Collision.
    """
    _require_known_shapes(a)
    _require_known_shapes(b)
    return any(_shapes_overlap(sa, sb) for sa in a for sb in b)


def grow_hitbox(hitbox: Hitbox, margin: float) -> Hitbox:
    """Return the hitbox with every shape grown by `margin` px on every side.

    A circle's radius grows by the margin. A box's w and h grow by twice the margin.
    A line's thickness grows by twice the margin, so it grows on each side and at both ends.
    Centers and line ends don't move. A polygon becomes itself followed by one line per edge,
    point i to point i + 1 (the last to the first), of thickness twice the margin: together
    every point within the margin of it, so the result may hold more shapes than the input.
    Raises TypeError for a shape that is not a Circle, a Box, a Line or a Polygon.
    Source: 06-scoring.md, rule 3.
    """
    return tuple(grown for shape in hitbox for grown in _grow_shape(shape, margin))


def deeply_overlaps(moving: Hitbox, solid: Hitbox) -> bool:
    """Return True when a shape of `moving` overlaps a shape of `solid` by more than
    SURFACE_TOLERANCE px. Both must be placed, boxes and polygons only.

    The overlap of a pair is its smallest overlap over every edge normal of both shapes.
    Raises TypeError for any other shape. Source: drifters.md, Rules, Push-out.
    """
    _require_boxes_and_polygons("deeply_overlaps", moving)
    _require_boxes_and_polygons("deeply_overlaps", solid)
    return any(
        _pair_depth(p, q) > SURFACE_TOLERANCE for p in _polygons(moving) for q in _polygons(solid)
    )


def push_directions(moving: Hitbox, solid: Hitbox) -> tuple[Direction, ...]:
    """Return the unit directions the push-out tries, in order.

    Up, down, left, right; then each polygon edge's outward and inward normal, the polygons of
    `solid` first, then those of `moving`. A direction within SURFACE_TOLERANCE of an earlier
    one on both components is left out. Boxes add nothing past the first four.
    Raises TypeError for a shape that is not a box or a polygon.
    Source: drifters.md, Rules, Push-out.
    """
    _require_boxes_and_polygons("push_directions", moving)
    _require_boxes_and_polygons("push_directions", solid)
    directions: list[Direction] = list(_AXIS_DIRECTIONS)
    for shape in (*solid, *moving):
        if not isinstance(shape, Polygon):
            continue
        for normal in _unit_normals(shape.points):
            for candidate in (normal, (-normal[0], -normal[1])):
                if not _has_direction(directions, candidate):
                    directions.append(candidate)
    return tuple(directions)


def exit_distance(moving: Hitbox, solid: Hitbox, direction: Direction) -> float:
    """Return how far `moving` must move along `direction` to clear `solid`, px, 0 or more.

    Clear means no shape of `moving` overlaps any shape of `solid`; an edge touch is clear.
    0.0 when `deeply_overlaps` is False. Pairs whose blocked spans chain into each other, such
    as the two boxes of an L, count as one surface. Both must be placed, boxes and polygons
    only. Raises TypeError for any other shape. Source: drifters.md, Rules, Push-out.
    """
    _require_boxes_and_polygons("exit_distance", moving)
    _require_boxes_and_polygons("exit_distance", solid)
    if not deeply_overlaps(moving, solid):
        return 0.0
    spans: list[_Span] = []
    for p in _polygons(moving):
        for q in _polygons(solid):
            span: _Span | None = _blocked_span(p, q, direction)
            if span is not None:
                spans.append(span)
    t: float = 0.0
    blocking: _Span | None = _first_containing(spans, t)
    while blocking is not None:
        t = blocking[1]
        blocking = _first_containing(spans, t)
    return t


def _unknown_shape(shape: object) -> TypeError:
    """Return the error for an object that is not a Circle, a Box, a Line or a Polygon.

    Nothing is treated as a box by default. Source: drifters.md, Rules, Collision.
    """
    return TypeError(f"unknown shape kind '{type(shape).__name__}'")


def _require_known_shapes(hitbox: Hitbox) -> None:
    """Raise TypeError when any shape of `hitbox` is not a Circle, a Box, a Line or a Polygon."""
    for shape in hitbox:
        if not isinstance(shape, Circle | Box | Line | Polygon):
            raise _unknown_shape(shape)


def _require_boxes_and_polygons(function_name: str, hitbox: Hitbox) -> None:
    """Raise TypeError naming `function_name` when a shape of `hitbox` is not a Box or Polygon."""
    for shape in hitbox:
        if not isinstance(shape, Box | Polygon):
            raise TypeError(
                f"{function_name} takes boxes and polygons, not '{type(shape).__name__}'"
            )


def _move_shape(shape: Shape, x: float, y: float) -> Shape:
    """Return `shape` with its center moved by (x, y), px."""
    if isinstance(shape, Circle):
        return Circle(shape.cx + x, shape.cy + y, shape.r)
    if isinstance(shape, Box):
        return Box(shape.cx + x, shape.cy + y, shape.w, shape.h)
    if isinstance(shape, Line):
        return Line(shape.ax + x, shape.ay + y, shape.bx + x, shape.by + y, shape.thickness)
    if isinstance(shape, Polygon):
        return Polygon(tuple((px + x, py + y) for px, py in shape.points))
    raise _unknown_shape(shape)


def _grow_shape(shape: Shape, margin: float) -> tuple[Shape, ...]:
    """Return `shape` grown by `margin` px on every side: one shape, or a polygon's 1 + edges."""
    if isinstance(shape, Circle):
        return (Circle(shape.cx, shape.cy, shape.r + margin),)
    if isinstance(shape, Box):
        return (Box(shape.cx, shape.cy, shape.w + 2 * margin, shape.h + 2 * margin),)
    if isinstance(shape, Line):
        return (Line(shape.ax, shape.ay, shape.bx, shape.by, shape.thickness + 2 * margin),)
    if isinstance(shape, Polygon):
        edge_lines: tuple[Shape, ...] = tuple(
            Line(a[0], a[1], b[0], b[1], 2 * margin) for a, b in _edges(shape.points)
        )
        return (shape, *edge_lines)
    raise _unknown_shape(shape)


def _shapes_overlap(a: Shape, b: Shape) -> bool:
    """Return True when two placed shapes share area."""
    if isinstance(a, Line):
        return _line_overlaps(a, b)
    if isinstance(b, Line):
        return _line_overlaps(b, a)
    if isinstance(a, Polygon):
        return _polygon_overlaps(a, b)
    if isinstance(b, Polygon):
        return _polygon_overlaps(b, a)
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
    if isinstance(other, Polygon):
        return _line_polygon_overlap(line, other)
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


def _edges(points: tuple[_Point, ...]) -> tuple[tuple[_Point, _Point], ...]:
    """The edges of a polygon: point i to point i + 1, the last back to the first."""
    return tuple(zip(points, points[1:] + points[:1], strict=True))


def _area_sign(points: tuple[_Point, ...]) -> float:
    """1.0 when the points run with positive area (twice the area is Σ x_i y_(i+1) - x_(i+1)
    y_i), else -1.0.
    """
    twice_area: float = sum(a[0] * b[1] - b[0] * a[1] for a, b in _edges(points))
    return 1.0 if twice_area > 0.0 else -1.0


def _polygons(hitbox: Hitbox) -> tuple[tuple[_Point, ...], ...]:
    """The corners of every box and polygon of `hitbox`. Other shapes are skipped."""
    corners: list[tuple[_Point, ...]] = []
    for shape in hitbox:
        if isinstance(shape, Box):
            corners.append(_box_corners(shape))
        elif isinstance(shape, Polygon):
            corners.append(shape.points)
    return tuple(corners)


def _raw_normals(points: tuple[_Point, ...]) -> tuple[_Point, ...]:
    """The edge normals (-dy, dx) of a polygon, not made unit."""
    return tuple((a[1] - b[1], b[0] - a[0]) for a, b in _edges(points))


def _unit_normals(points: tuple[_Point, ...]) -> tuple[Direction, ...]:
    """The outward unit normal of every edge: (dy, -dx) / length for positive area, else
    (-dy, dx) / length.
    """
    sign: float = _area_sign(points)
    normals: list[Direction] = []
    for a, b in _edges(points):
        dx: float = b[0] - a[0]
        dy: float = b[1] - a[1]
        length: float = math.hypot(dx, dy)
        normals.append((sign * dy / length, -sign * dx / length))
    return tuple(normals)


def _projection(points: tuple[_Point, ...], axis: _Point) -> _Span:
    """The (min, max) of the corners' dot products with `axis`."""
    dots: list[float] = [p[0] * axis[0] + p[1] * axis[1] for p in points]
    return (min(dots), max(dots))


def _axes_overlap(p: tuple[_Point, ...], q: tuple[_Point, ...], axis: _Point) -> float:
    """How far the projections of `p` and `q` on `axis` overlap, negative when apart."""
    low_p, high_p = _projection(p, axis)
    low_q, high_q = _projection(q, axis)
    return min(high_p, high_q) - max(low_p, low_q)


def _polygons_overlap(p: tuple[_Point, ...], q: tuple[_Point, ...]) -> bool:
    """Convex and convex: on every edge normal of both, the projections share more than a
    point.
    """
    return all(_axes_overlap(p, q, axis) > 0.0 for axis in (*_raw_normals(p), *_raw_normals(q)))


def _pair_depth(p: tuple[_Point, ...], q: tuple[_Point, ...]) -> float:
    """The smallest overlap of `p` and `q` over their unit edge normals, px, 0 or less if apart."""
    return min(_axes_overlap(p, q, axis) for axis in (*_unit_normals(p), *_unit_normals(q)))


def _has_direction(directions: list[Direction], candidate: Direction) -> bool:
    """True when `candidate` is within SURFACE_TOLERANCE of a listed direction on both parts."""
    return any(
        abs(d[0] - candidate[0]) <= SURFACE_TOLERANCE
        and abs(d[1] - candidate[1]) <= SURFACE_TOLERANCE
        for d in directions
    )


def _axis_span(p: tuple[_Point, ...], q: tuple[_Point, ...], axis: Direction, k: float) -> _Span:
    """The open (low, high) range of t where `p` moved by t overlaps `q` on `axis`, where
    `k` is the movement's dot product with the axis and is not 0.
    """
    low_p, high_p = _projection(p, axis)
    low_q, high_q = _projection(q, axis)
    first: float = (high_q - low_p) / k
    second: float = (low_q - high_p) / k
    return (min(first, second), max(first, second))


def _blocked_span(
    p: tuple[_Point, ...], q: tuple[_Point, ...], direction: Direction
) -> _Span | None:
    """The open (low, high) range of t where `p` moved by t * direction overlaps `q`, or None.

    The intersection of the ranges of every unit edge normal of both. An axis square to the
    direction keeps every t when the shapes overlap on it, none when they don't.
    """
    low: float = -math.inf
    high: float = math.inf
    for axis in (*_unit_normals(p), *_unit_normals(q)):
        k: float = direction[0] * axis[0] + direction[1] * axis[1]
        if k == 0.0:
            if _axes_overlap(p, q, axis) <= 0.0:
                return None
            continue
        axis_low, axis_high = _axis_span(p, q, axis, k)
        low = max(low, axis_low)
        high = min(high, axis_high)
    if low >= high:
        return None
    return (low, high)


def _first_containing(spans: list[_Span], t: float) -> _Span | None:
    """The first span with low < t < high, or None."""
    for span in spans:
        if span[0] < t < span[1]:
            return span
    return None


def _point_in_polygon(point: _Point, points: tuple[_Point, ...]) -> bool:
    """True when `point` is inside or on the polygon: every edge's cross product with it has
    the polygon's own sign, or is 0.
    """
    sign: float = _area_sign(points)
    return all(_cross(a, b, point) * sign >= 0.0 for a, b in _edges(points))


def _polygon_overlaps(polygon: Polygon, other: Circle | Box | Polygon) -> bool:
    """Polygon and a circle, box or polygon."""
    if isinstance(other, Circle):
        return _polygon_circle_overlap(polygon, other)
    if isinstance(other, Box):
        return _polygons_overlap(polygon.points, _box_corners(other))
    return _polygons_overlap(polygon.points, other.points)


def _polygon_circle_overlap(polygon: Polygon, circle: Circle) -> bool:
    """Polygon and circle: the center is inside or on the polygon, or closer than r to an
    edge segment.
    """
    center: _Point = (circle.cx, circle.cy)
    if _point_in_polygon(center, polygon.points):
        return True
    reach: float = circle.r * circle.r
    return any(_point_segment_dist_sq(center, a, b) < reach for a, b in _edges(polygon.points))


def _line_polygon_overlap(line: Line, polygon: Polygon) -> bool:
    """Polygon and line: an end is inside or on the polygon, or segment AB is closer than half
    the thickness to an edge segment (0 when they meet).
    """
    a: _Point = (line.ax, line.ay)
    b: _Point = (line.bx, line.by)
    if _point_in_polygon(a, polygon.points) or _point_in_polygon(b, polygon.points):
        return True
    half: float = line.thickness / 2
    return any(_segments_dist_sq(a, b, c, d) < half * half for c, d in _edges(polygon.points))
