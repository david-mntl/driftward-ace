"""Hitbox overlap, growth and the ship's hitbox tests.

Contract: docs/contracts/systems/objects.md, Rules, Collision; docs/contracts/systems/ship.md,
Rules, Hitbox. Task: docs/contracts/DRA-29/tasks/DRA-29-07-qa-engineer.md. One test per
behavior it lists. Every expected number is computed from the GDD values below, never read
from the code under test.
"""

import pytest

from core.collision import Box, Circle, Hitbox, grow_hitbox, hitboxes_overlap
from core.ship import TOP_SIDE_SPEED, Ship, ship_hitbox, spawn

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

SHIP_W: int = 32
"""px. Source: 04-ship.md, Values, ship_w (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

BAR_W: int = 12
"""px. Source: 04-ship.md, hitbox (guess)."""

FOOT_H: int = 12
"""px. Source: 04-ship.md, hitbox (guess)."""

SPAWN_X: float = 320.0
"""Source: 03-world-and-camera.md, ship_start (guess)."""

SPAWN_Y: float = 240.0
"""Source: 03-world-and-camera.md, ship_start (guess)."""

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""


def overlap_both_ways(a: Hitbox, b: Hitbox) -> bool:
    """Return the overlap of a and b, after checking that the order doesn't matter."""
    forward: bool = hitboxes_overlap(a, b)
    assert forward == hitboxes_overlap(b, a)
    return forward


def test_shapes_overlap_when_they_share_area_and_not_when_they_only_touch() -> None:
    # Circle and circle: centers 10 apart, radii 5 and 5. Strict: touching is no overlap.
    assert not overlap_both_ways((Circle(0, 0, 5),), (Circle(10, 0, 5),))
    assert overlap_both_ways((Circle(0, 0, 5),), (Circle(9.9, 0, 5),))
    assert overlap_both_ways((Circle(0, 0, 5),), (Circle(0, 0, 5),))
    assert not overlap_both_ways((Circle(0, 0, 5),), (Circle(30, 40, 5),))
    # Box and box: shared edge and shared corner don't count.
    box: Box = Box(0, 0, 10, 10)
    assert not overlap_both_ways((box,), (Box(10, 0, 10, 10),))
    assert not overlap_both_ways((box,), (Box(0, 10, 10, 10),))
    assert not overlap_both_ways((box,), (Box(10, 10, 10, 10),))
    assert overlap_both_ways((box,), (Box(9.9, 0, 10, 10),))
    assert overlap_both_ways((box,), (Box(9, 9, 10, 10),))
    assert overlap_both_ways((box,), (Box(0, 0, 2, 2),))
    # Circle and box: edge touch (nearest box point at distance r) and a 3-4-5 corner touch.
    assert not overlap_both_ways((Circle(8, 0, 3),), (box,))
    assert overlap_both_ways((Circle(7.9, 0, 3),), (box,))
    assert not overlap_both_ways((Circle(8, 9, 5),), (box,))
    assert overlap_both_ways((Circle(7, 8, 5),), (box,))
    assert overlap_both_ways((Circle(0, 0, 1),), (box,))
    assert not overlap_both_ways((Circle(20, 20, 3),), (box,))


def test_hitboxes_overlap_when_any_shape_overlaps_and_empty_overlaps_nothing() -> None:
    far: Circle = Circle(500, 500, 5)
    near: Circle = Circle(0, 0, 5)
    target: Hitbox = (Box(0, 0, 10, 10), Box(100, 0, 10, 10))
    assert overlap_both_ways((far, near), target)
    assert overlap_both_ways((far, Circle(100, 0, 5)), target)
    assert not overlap_both_ways((far, Circle(50, 0, 5)), target)
    assert not overlap_both_ways((), target)
    assert not overlap_both_ways((), ())
    assert not overlap_both_ways((), (Circle(0, 0, 100),))


def test_grow_hitbox_grows_every_shape_on_every_side() -> None:
    grown: Hitbox = grow_hitbox((Circle(1, 2, 3), Box(5, 6, 10, 20)), GRAZE_MARGIN)
    assert grown == (
        Circle(1, 2, 3 + GRAZE_MARGIN),
        Box(5, 6, 10 + 2 * GRAZE_MARGIN, 20 + 2 * GRAZE_MARGIN),
    )
    assert grow_hitbox((), GRAZE_MARGIN) == ()
    # A box one px short of a neighbor reaches it once grown by 2.
    box: Box = Box(0, 0, 10, 10)
    neighbor: Box = Box(11, 0, 10, 10)
    assert not overlap_both_ways((box,), (neighbor,))
    assert not overlap_both_ways(grow_hitbox((box,), 0.5), (neighbor,))
    assert not overlap_both_ways(grow_hitbox((box,), 1), (neighbor,))
    assert overlap_both_ways(grow_hitbox((box,), 2), (neighbor,))


def test_ship_hitbox_is_an_inverted_t_at_the_ship_center() -> None:
    ship: Ship = spawn()
    placed: Hitbox = ship_hitbox(ship)
    bar_w: float = BAR_W
    foot_cy: float = SPAWN_Y + SHIP_H / 2 - FOOT_H / 2
    assert placed == (
        Box(SPAWN_X, SPAWN_Y, bar_w, SHIP_H),
        Box(SPAWN_X, foot_cy, SHIP_W, FOOT_H),
    )
    foot: Box = Box(SPAWN_X, foot_cy, SHIP_W, FOOT_H)
    assert foot.cy + foot.h / 2 == SPAWN_Y + SHIP_H / 2 == 256
    # An empty upper corner of the 32 x 32 square is not part of the hitbox.
    corner: Hitbox = (Circle(308, 228, 3),)
    assert not overlap_both_ways(placed, corner)
    assert not overlap_both_ways(placed, (Circle(332, 228, 3),))
    # The bar and the foot are.
    assert overlap_both_ways(placed, (Circle(320, 228, 3),))
    assert overlap_both_ways(placed, (Circle(302, 250, 3),))
    assert not overlap_both_ways(placed, (Circle(300, 250, 3),))
    assert overlap_both_ways(placed, (Circle(310, 244, 3),))
    # It follows the ship.
    moved: Hitbox = ship_hitbox(Ship(x=100.0, y=50.0, vx=0.0, vy=0.0))
    assert moved == (Box(100.0, 50.0, BAR_W, SHIP_H), Box(100.0, 60.0, SHIP_W, FOOT_H))


def test_ship_top_sideways_speed_is_the_drag_limit() -> None:
    expected: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
    top: float = TOP_SIDE_SPEED
    assert top == pytest.approx(expected)
    assert top == pytest.approx(6.58, abs=0.005)
