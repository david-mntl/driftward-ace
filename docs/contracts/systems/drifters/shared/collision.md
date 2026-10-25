# Drifters, collision
Part of: drifters
Read when: you change hitbox shapes, the overlap test or the push-out.

## Interface

### game/core/collision.py
```python
# Imports: stdlib only.


@dataclass(frozen=True, slots=True)
class Circle:
    """A circle hitbox shape, px."""

    cx: float  # center x: offset from the owner's center in a variant's hitbox; screen x once placed
    cy: float  # center y, same, y down
    r: float  # radius, px, > 0


@dataclass(frozen=True, slots=True)
class Box:
    """An upright box hitbox shape, px. Boxes never rotate."""

    cx: float  # center x, as Circle.cx
    cy: float  # center y, as Circle.cy
    w: float  # full width, px, > 0
    h: float  # full height, px, > 0


@dataclass(frozen=True, slots=True)
class Line:  # DRA-47
    """A line hitbox shape: straight from A to B, a set thickness, round ends, px."""

    ax: float  # end A x: offset from the owner's center in a variant's hitbox; screen x once placed
    ay: float  # end A y, same, y down
    bx: float  # end B x, same
    by: float  # end B y, same
    thickness: float  # full thickness, px, > 0. Every point within thickness / 2 of segment AB


@dataclass(frozen=True, slots=True)
class Polygon:  # DRA-86
    """A convex polygon hitbox shape: a filled shape with straight edges, px."""

    points: tuple[tuple[float, float], ...]  # its corners in order around the edge, either way
    # round, at least 3. Offsets from the owner's center in a variant's hitbox; screen px once
    # placed, y down. Convex, no two points the same, no three neighbours on one line. Trusted:
    # core builds every polygon (island_hitbox), nothing reads one from a file


Shape = Circle | Box | Line | Polygon  # Line from DRA-47, Polygon from DRA-86
Hitbox = tuple[Shape, ...]  # one or more shapes. Empty () = touches nothing
Direction = tuple[float, float]  # DRA-86. A unit vector, screen px, y down: (0.0, -1.0) is up

SURFACE_TOLERANCE: Final[float] = 1e-9  # DRA-86. px. An overlap this deep or less counts as
# touching for deeply_overlaps and exit_distance. Not a game value (Rationale)


def place_hitbox(hitbox: Hitbox, x: float, y: float) -> Hitbox:
    ...
    # Every shape moved by (x, y): offsets from the owner's center become screen positions.
    # A line moves both ends; a polygon every point.


def hitboxes_overlap(a: Hitbox, b: Hitbox) -> bool:
    ...
    # True when any shape of a overlaps any shape of b. Both placed. Pure.


def grow_hitbox(hitbox: Hitbox, margin: float) -> Hitbox:
    ...
    # Each shape grown by margin on every side: Circle r + margin; Box w + 2 margin, h + 2 margin;
    # Line thickness + 2 margin, ends unchanged (it grows on each side and at both ends).
    # Polygon (DRA-86): the polygon itself, then one Line per edge, point i to point i + 1 (the
    # last to the first), thickness 2 × margin. So a hitbox may come back with more shapes.


# All three raise TypeError("unknown shape kind '<class name>'") for an object that is not a
# Circle, a Box, a Line or a Polygon (DRA-39, Line from DRA-47, Polygon from DRA-86). Nothing is
# ever treated as a box by default.


def deeply_overlaps(moving: Hitbox, solid: Hitbox) -> bool:
    ...  # DRA-86
    # True when some shape of moving overlaps some shape of solid by more than SURFACE_TOLERANCE
    # (Rules, Push-out). Both placed. Pure.


def push_directions(moving: Hitbox, solid: Hitbox) -> tuple[Direction, ...]:
    ...  # DRA-86
    # The directions the push-out tries, in order: up, down, left, right, then each polygon
    # edge's outward and inward normal, solid's polygons first, then moving's, with no repeats
    # (Rules, Push-out). Pure.


def exit_distance(moving: Hitbox, solid: Hitbox, direction: Direction) -> float:
    ...  # DRA-86
    # px >= 0: how far moving must move along direction until no shape of it overlaps a shape of
    # solid at all. 0.0 when deeply_overlaps(moving, solid) is False. Both placed. Pure.


# deeply_overlaps, push_directions and exit_distance take boxes and polygons only: any other shape
# raises TypeError("<function name> takes boxes and polygons, not '<class name>'"), e.g.
# "exit_distance takes boxes and polygons, not 'Circle'". DRA-86.
```

## Rules

Collision (`core/collision.py`). Source: 07-drifters.md, rule 8; 06-scoring.md, rule 3; 91-decision-log.md, row 35:
- A hitbox is one or more circles, upright boxes, lines (from DRA-47) and convex polygons (from DRA-86). Each shape's position (`cx`, `cy`; a line's `ax`, `ay`, `bx`, `by`; a polygon's `points`) is an offset from the owner's center until `place_hitbox` moves it to a screen position.
- Two shapes overlap when they share area. Shapes that only touch at an edge or a point don't overlap: the tests are strict (`<`). Accepted by the Director (scope report DRA-29, Decision log, 2026-10-15). Circle and circle: distance between centers < r1 + r2. Box and box: |Δcx| < (w1 + w2) / 2 and |Δcy| < (h1 + h2) / 2. Circle and box: the box point nearest the circle's center is at a distance < r.
- **Line** (DRA-47). A line is every point within `thickness / 2` of the segment AB: straight, at any angle, with round ends. A line whose A and B are the same point is a circle of radius `thickness / 2`. With `h = thickness / 2`. Source: 07-drifters.md, rule 8; 91-decision-log.md, rows 47 and 60:
  - Line and circle: the shortest distance from the circle's center to segment AB < h + r.
  - Line and line: the shortest distance between the two segments < h1 + h2. Segments that cross or touch are at distance 0.
  - Line and box: the shortest distance between segment AB and the box (the filled rectangle) < h. A segment that meets the box, inside or on its edge, is at distance 0.
  - Distances are compared squared, with no square root: the point-to-segment distance uses the clamped projection `t = clamp(((P − A) · (B − A)) / |B − A|², 0, 1)` (or P to A when A equals B), and a crossing is found with cross-product signs. When segments don't meet, their shortest distance is the smallest of the four end-to-other-segment distances; a segment that doesn't meet a box is closest at one of its two ends or at one of the box's four corners. So whole numbers, halves and 3-4-5 triangles give exact results, as for the other shapes.
- **Polygon** (DRA-86). A polygon is the filled convex shape inside its corners, edges included. Its edges run from point `i` to point `i + 1`, the last back to the first. A box counts as the polygon of its four corners. Source: 07-drifters.md, rule 8; drifters/05-floating-islands.md, hitbox:
  - Polygon and polygon, polygon and box: separating axes. The axes are the edge normals of both shapes, `(−dy, dx)` for each edge `(dx, dy)`, not made unit (the test compares projections, so length doesn't matter, and whole numbers stay exact). They overlap when, on every axis, the two projection ranges share more than a point: `max(min_a, min_b) < min(max_a, max_b)`.
  - Polygon and circle: the circle's center lies inside or on the polygon, or the shortest distance from the center to an edge segment is < r.
  - Polygon and line: with `h = thickness / 2`, an end of the line lies inside or on the polygon, or the segment AB meets an edge segment, or the shortest distance between AB and an edge segment is < h.
  - Distances are compared squared and crossings found with cross-product signs, as for the line. "Inside or on" for a point is: every edge's cross product with the point has the polygon's own sign, or 0. The polygon's sign is the sign of its area (twice the area is `Σ (x_i × y_(i+1) − x_(i+1) × y_i)`); it may be either, so either point order works.
- The result never depends on the order: `hitboxes_overlap(a, b) == hitboxes_overlap(b, a)`.
- `hitboxes_overlap(a, b)` is True when any shape of `a` overlaps any shape of `b`. An empty hitbox overlaps nothing.
- `grow_hitbox` grows each shape by the margin on every side: a circle's radius grows by it, a box grows by it on all four sides (w and h by twice the margin), a line's thickness grows by twice the margin, so it grows on each side and at both ends (DRA-47). Centers and line ends don't move. A polygon (DRA-86) becomes itself plus one line per edge, from corner to corner, of thickness twice the margin, in edge order right after it: together exactly every point within the margin of the polygon, with round corners. So `grow_hitbox` returns one shape per circle, box and line, and `1 + edges` shapes per polygon, each shape's results in its place. Source: 06-scoring.md, rule 3; 91-decision-log.md, row 47.
- **Unknown shape kind** (DRA-39). `place_hitbox`, `grow_hitbox` and `hitboxes_overlap` raise `TypeError("unknown shape kind '<class name>'")` for any shape that is not a `Circle`, a `Box`, a `Line` or a `Polygon`. A new shape kind must be handled in all three, and gets its own collision cases (test tasks DRA-39-05, DRA-47-07, DRA-86-07). Source: scope report DRA-39, Limits (collision tests and guards).
- Pure. No logging, no randomness.

Push-out (`core/collision.py`, DRA-86). The measure the ship's island block and the respawn spot use (`docs/contracts/systems/ship.md`, Rules, Islands). It works on boxes and polygons only, the shapes of the ship and the islands. Source: drifters/05-floating-islands.md, rule 4 ("moved out the shortest way, just to the surface"); 05-lives-and-damage.md, rule 2.3 ("the nearest clear spot straight above or below"); scope report DRA-39, Decision log ("collision that can tell how deep and which way to push the ship out"):
- **Pairs and axes.** For each shape `p` of `moving` and each shape `q` of `solid`, both as polygons, the axes are the outward unit normals of every edge of `p` and of `q`. On an axis `a`, a shape's range is `[min, max]` of its corners' dot products with `a`. The overlap of the pair on `a` is `min(max_p, max_q) − max(min_p, min_q)`, and the pair's depth is the smallest overlap over its axes (negative or 0 when they are apart). An outward normal of edge `(dx, dy)` is `(dy, −dx) / length` when the polygon's area sign (Polygon, above) is positive, else `(−dy, dx) / length`: for the box from (0, 0) to (1, 1) the top edge's outward normal is (0, −1), up.
- **`deeply_overlaps(moving, solid)`** is True when some pair's depth is > `SURFACE_TOLERANCE`. So an overlap of a billionth of a px, which a push can leave behind in floating point, counts as touching. `hitboxes_overlap` keeps its strict rule; only the push-out uses the tolerance.
- **`exit_distance(moving, solid, direction)`.** With `moving` moved by `t × direction`, `t ≥ 0`, a pair overlaps on axis `a` while `max_p + t × k > min_q` and `min_p + t × k < max_q`, with `k = direction · a`. Each axis with `k ≠ 0` keeps `t` inside one open interval; an axis with `k = 0` keeps every `t` or none. The pair's blocked span is the intersection of its axes' intervals: one open interval `(low, high)`, maybe empty. Then: 0.0 when `deeply_overlaps(moving, solid)` is False. Otherwise `t = 0`, and while some pair's span has `low < t < high`, `t` becomes that span's `high`; the result is the last `t`. So it steps through spans that chain into each other, the L's two boxes or two overlapping islands, and stops at the first spot where no shape overlaps at all (an edge touching is clear). The result is exact for whole and half px on boxes moved up, down, left or right.
- **`push_directions(moving, solid)`**, in this order: `(0.0, −1.0)` up, `(0.0, 1.0)` down, `(−1.0, 0.0)` left, `(1.0, 0.0)` right; then, for each polygon of `solid` in hitbox order and each of its edges in order, its outward unit normal, then that normal turned round (inward); then the same for each polygon of `moving`. A direction within `SURFACE_TOLERANCE` of an earlier one on both components is left out. Boxes add no direction past the first four. For the ship against any island this is the four axis directions, plus the triangle's three normals both ways round, less the ones already there (its flat sides' normals are axis directions): up, down, left, right, the slope's outward normal, the slope's inward normal.
- These three raise `TypeError("<function name> takes boxes and polygons, not '<class name>'")` for any other shape, in either hitbox. Pure.
- What a push is for, and which direction is used, is the ship's rule (`systems/ship.md`).
