"""The ship against floating islands. Contract: docs/contracts/systems/ship.md, Rules.

Task: docs/contracts/DRA-86/tasks/DRA-86-08-qa-engineer.md. One test per behavior it lists.

The island variants (shape, width, height, `arm`) come from
`game/tuning/drifters/floating_island.json` and are put together here from the contract's Diagram
(`diagram_hitbox`), never read back from `island_hitbox`. The scenes that need an exact answer
(ties, walls, the top line, the L, the T, two islands, the respawn spot) use boxes written out from
the Diagram's numbers. Every expected value is worked out in the file from the GDD values below
and the contract's rules. The ground is built by hand: `Ground(hitbox, velocity_x, velocity_y)`.
"""

import json
import logging
import math
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path
from typing import Literal, cast

import pytest

from core.collision import Box, Hitbox, Polygon, deeply_overlaps, place_hitbox
from core.ship import NO_GROUND, Ground, Ship, Thrust, block_ship, spawn, spawn_clear, step

GRAVITY: float = 0.16
"""px/tick². Source: 04-ship.md, Values, gravity (guess)."""

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

THRUST_UP: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_up (guess)."""

THRUST_DOWN: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_down (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

HALF: float = 16.0
"""Half of the ship's 32 x 32 square, px. Source: 04-ship.md, ship_w, ship_h (guess)."""

SCREEN_W: float = 640.0
"""px. Source: 03-world-and-camera.md, Values, screen_w (guess)."""

TOP_LINE_Y: float = 168.0
"""Screen y of the top line: round(480 * 0.35). Source: 03-world-and-camera.md, rule 2."""

SPAWN_X: float = 320.0
"""Source: 05-lives-and-damage.md, fall_respawn (locked)."""

SPAWN_Y: float = 240.0
"""Source: 05-lives-and-damage.md, fall_respawn (locked)."""

SCROLL_L1: float = 1.1
"""px a tick the world, and so every island, moves down at Level 1. Source: ship.md, Diagram,
Islands ("at Level 1 (the ground moves 1.1 px down a tick)")."""

HAIR: float = 5e-10
"""Half of SURFACE_TOLERANCE (1e-9, drifters.md, Interface). An overlap this deep is touching."""

SHIP_T: Hitbox = (Box(0.0, 0.0, 12.0, 32.0), Box(0.0, 10.0, 32.0, 12.0))
"""The ship's inverted T as offsets from its center. Source: ship.md, Diagram (the hitbox)."""

ISLAND_FILE: Path = (
    Path(__file__).resolve().parents[2] / "tuning" / "drifters" / "floating_island.json"
)
SHIP_LOGGER: str = "core.ship"
NO_KEY: Thrust = Thrust()

ISLAND_X: float = 320.0
ISLAND_Y: float = 330.0
"""Where an island's center is put: a whole screen's room on every side of it for a ship pushed
out, clear of the walls, the top line (168) and the floor."""

DEPTH: float = 3.0
"""How far into a surface the ship is put, px."""


# ---------------------------------------------------------------------------------------------
# The island variants, from the tuning file and the contract's Diagram
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Island:
    """One island variant and `invert` value as the tuning file states them, px."""

    name: str
    shape: str
    width: float
    height: float
    arm: float
    invert: bool

    @property
    def label(self) -> str:
        """The test id."""
        return f"{self.name}-{'inverted' if self.invert else 'upright'}"


def load_islands() -> list[Island]:
    """Return every variant of the file, with both `invert` values unless it is a rectangle."""
    data: dict[str, object] = json.loads(ISLAND_FILE.read_text())
    arm: float = float(cast(float, data["arm"]))
    raw: dict[str, dict[str, object]] = cast(dict[str, dict[str, object]], data["variants"])
    islands: list[Island] = []
    for name, variant in raw.items():
        shape: str = str(variant["shape"])
        width = float(cast(float, variant["width"]))
        height = float(cast(float, variant["height"]))
        inverts = (False,) if shape == "rectangle" else (False, True)
        islands.extend(Island(name, shape, width, height, arm, invert) for invert in inverts)
    return islands


ISLANDS: list[Island] = load_islands()


def diagram_hitbox(isl: Island) -> Hitbox:
    """Return the island's shapes from the contract's Diagram, Floating island, built here.

    `invert` mirrors the shape top to bottom: every box's `cy` and every point's y is negated.
    """
    hw, hh, arm = isl.width / 2, isl.height / 2, isl.arm
    s: float = -1.0 if isl.invert else 1.0
    if isl.shape == "rectangle":
        return (Box(0.0, 0.0, isl.width, isl.height),)
    if isl.shape == "l_shape":
        return (
            Box(0.0, s * (hh - arm / 2), isl.width, arm),
            Box(-hw + arm / 2, 0.0, arm, isl.height),
        )
    if isl.shape == "t_shape":
        return (Box(0.0, -s * (hh - arm / 2), isl.width, arm), Box(0.0, 0.0, arm, isl.height))
    assert isl.shape == "triangle"
    return (Polygon(((-hw, -s * hh), (hw, s * hh), (-hw, s * hh))),)


@dataclass(frozen=True, slots=True)
class Spot:
    """A place on an island's surface where the ship is put, relative to the island's center."""

    label: str
    side: str
    """Where the ship is: `above`, `below`, `left` or `right` of the surface."""

    face: float
    """The surface: its y for `above` and `below`, its x for `left` and `right`."""

    along: float
    """Where on the surface: the ship center's x for `above` and `below`, its y for the sides."""


def spots(isl: Island) -> list[Spot]:
    """Return the outer surfaces of the island the ship can be pushed off, straight faces only.

    Each is a face of one box of the Diagram's shapes with the ship's whole foot (or bar) on it and
    no other part of the island near. The triangle's slope is in `test_..._triangle_slope`.
    """
    hw, hh, arm = isl.width / 2, isl.height / 2, isl.arm
    if isl.shape == "rectangle":
        return [
            Spot("top", "above", -hh, 0.0),
            Spot("bottom", "below", hh, 0.0),
            Spot("left side", "left", -hw, 0.0),
            Spot("right side", "right", hw, 0.0),
        ]
    if isl.shape == "l_shape" and not isl.invert:
        return [
            Spot("bar top", "above", hh - arm, 0.0),
            Spot("upright top", "above", -hh, -hw + arm / 2),
            Spot("bottom", "below", hh, 0.0),
            Spot("upright left side", "left", -hw, 0.0),
            Spot("upright right side", "right", -hw + arm, -hh / 2),
            Spot("bar right end", "right", hw, hh - arm / 2),
        ]
    if isl.shape == "l_shape":
        return [
            Spot("bar top", "above", -hh, 0.0),
            Spot("bar bottom", "below", -hh + arm, 0.0),
            Spot("upright bottom", "below", hh, -hw + arm / 2),
            Spot("upright left side", "left", -hw, 0.0),
            Spot("upright right side", "right", -hw + arm, hh / 2),
            Spot("bar right end", "right", hw, -hh + arm / 2),
        ]
    if isl.shape == "t_shape" and not isl.invert:
        return [
            Spot("bar top", "above", -hh, -hw / 2),
            Spot("bar bottom", "below", -hh + arm, -hw / 2),
            Spot("stem bottom", "below", hh, 0.0),
            Spot("bar left end", "left", -hw, -hh + arm / 2),
            Spot("stem left side", "left", -arm / 2, hh / 2),
            Spot("bar right end", "right", hw, -hh + arm / 2),
            Spot("stem right side", "right", arm / 2, hh / 2),
        ]
    if isl.shape == "t_shape":
        return [
            Spot("bar top", "above", hh - arm, -hw / 2),
            Spot("stem top", "above", -hh, 0.0),
            Spot("bar bottom", "below", hh, -hw / 2),
            Spot("bar left end", "left", -hw, hh - arm / 2),
            Spot("stem left side", "left", -arm / 2, -hh / 2),
            Spot("bar right end", "right", hw, hh - arm / 2),
            Spot("stem right side", "right", arm / 2, -hh / 2),
        ]
    assert isl.shape == "triangle"
    # The triangle has no face on the right: its right side is the slope.
    if not isl.invert:
        return [
            Spot("base", "below", hh, -hw / 2),
            Spot("straight side", "left", -hw, 0.0),
        ]
    return [
        Spot("flat top", "above", -hh, -hw / 2),
        Spot("straight side", "left", -hw, 0.0),
    ]


def ship_on(spot: Spot, depth: float) -> Ship:
    """Return a ship at rest `depth` px into the surface, the island's center at (ISLAND_X, Y)."""
    if spot.side == "above":
        return Ship(ISLAND_X + spot.along, ISLAND_Y + spot.face - HALF + depth, 0.0, 0.0)
    if spot.side == "below":
        return Ship(ISLAND_X + spot.along, ISLAND_Y + spot.face + HALF - depth, 0.0, 0.0)
    if spot.side == "left":
        return Ship(ISLAND_X + spot.face - HALF + depth, ISLAND_Y + spot.along, 0.0, 0.0)
    assert spot.side == "right"
    return Ship(ISLAND_X + spot.face + HALF - depth, ISLAND_Y + spot.along, 0.0, 0.0)


def island_ground(isl: Island, vx: float = 0.0, vy: float = 0.0) -> Ground:
    """Return the island placed at (ISLAND_X, ISLAND_Y) as the ground, moving (vx, vy)."""
    return Ground(place_hitbox(diagram_hitbox(isl), ISLAND_X, ISLAND_Y), vx, vy)


def box_ground(*boxes: tuple[float, float, float, float]) -> Ground:
    """Return still ground of boxes given as (center x, center y, width, height), screen px."""
    return Ground(tuple(Box(*box) for box in boxes))


def clear_of(ship: Ship, ground: Ground) -> bool:
    """True when the ship's T is not inside the ground (touching is clear)."""
    return not deeply_overlaps(place_hitbox(SHIP_T, ship.x, ship.y), ground.hitbox)


def corner_offsets() -> list[tuple[float, float]]:
    """Return the eight corners of the ship's two boxes as offsets from its center."""
    corners: list[tuple[float, float]] = []
    for part in SHIP_T:
        assert isinstance(part, Box)
        corners.extend(
            (part.cx + sx * part.w, part.cy + sy * part.h)
            for sx in (-0.5, 0.5)
            for sy in (-0.5, 0.5)
        )
    return corners


def slope_normal(isl: Island) -> tuple[float, float]:
    """Return the triangle's slope outward unit normal, from the file's width and height.

    Source: drifters.md, Diagram, Floating island: (120, -320) / 341.76 upright, (120, 320)
    inverted, at 320 x 120.
    """
    length: float = math.hypot(isl.width, isl.height)
    return (isl.height / length, (isl.width if isl.invert else -isl.width) / length)


def deepest_corner(normal: tuple[float, float]) -> tuple[float, float]:
    """Return the ship's corner that goes deepest into a surface with this outward normal."""
    return min(corner_offsets(), key=lambda c: c[0] * normal[0] + c[1] * normal[1])


def assert_ship(
    ship: Ship, x: float, y: float, vx: float | None = None, vy: float | None = None
) -> None:
    """Position (and speed when given) equal to the numbers, to a millionth of a px."""
    assert ship.x == pytest.approx(x, abs=1e-6)
    assert ship.y == pytest.approx(y, abs=1e-6)
    if vx is not None:
        assert ship.vx == pytest.approx(vx, abs=1e-6)
    if vy is not None:
        assert ship.vy == pytest.approx(vy, abs=1e-6)


# ---------------------------------------------------------------------------------------------
# Rules, Islands, 1 to 3: pushed out the shortest way, to the surface and no further
# ---------------------------------------------------------------------------------------------

SPOT_CASES = [
    pytest.param(isl, spot, id=f"{isl.label}-{spot.label}")
    for isl in ISLANDS
    for spot in spots(isl)
]


@pytest.mark.parametrize(("isl", "spot"), SPOT_CASES)
def test_ship_is_pushed_out_of_the_island_to_the_surface_and_no_further(
    isl: Island, spot: Spot
) -> None:
    ground = island_ground(isl)
    inside = ship_on(spot, DEPTH)
    touching = ship_on(spot, 0.0)
    assert not clear_of(inside, ground)

    pushed = block_ship(inside, ground)

    assert_ship(pushed, touching.x, touching.y, 0.0, 0.0)
    assert pushed.against_island is True
    assert clear_of(pushed, ground)


@pytest.mark.parametrize(
    "isl", [i for i in ISLANDS if i.shape == "triangle"], ids=lambda i: i.label
)
def test_ship_is_pushed_off_the_triangle_slope_to_the_surface(isl: Island) -> None:
    ground = island_ground(isl)
    normal = slope_normal(isl)
    corner = deepest_corner(normal)
    # The slope passes through the island's center. The corner touching it is on that line.
    touching = Ship(ISLAND_X - corner[0], ISLAND_Y - corner[1], 0.0, 0.0)
    inside = Ship(
        touching.x - DEPTH * normal[0], touching.y - DEPTH * normal[1], 0.0, 0.0
    )  # DEPTH px along the normal into the island
    assert clear_of(touching, ground)
    assert not clear_of(inside, ground)

    pushed = block_ship(inside, ground)

    assert_ship(pushed, touching.x, touching.y, 0.0, 0.0)
    assert pushed.against_island is True
    assert clear_of(pushed, ground)


# ---------------------------------------------------------------------------------------------
# Rules, Islands, 4: the speed into the surface
# ---------------------------------------------------------------------------------------------

SIDES: dict[str, tuple[float, float]] = {
    "above": (0.0, -1.0),
    "below": (0.0, 1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}
"""Where the ship is, and the surface's outward normal there (it points out of the island)."""

ALONG: dict[str, tuple[float, float]] = {
    "above": (1.0, 0.0),
    "below": (1.0, 0.0),
    "left": (0.0, 1.0),
    "right": (0.0, 1.0),
}

RECT_SPOTS: dict[str, Spot] = {
    "above": Spot("top", "above", -60.0, 0.0),
    "below": Spot("bottom", "below", 60.0, 0.0),
    "left": Spot("left side", "left", -160.0, 0.0),
    "right": Spot("right side", "right", 160.0, 0.0),
}
"""The Diagram's rectangle, 320 x 120, centered on (ISLAND_X, ISLAND_Y)."""

RECTANGLE: Hitbox = (Box(0.0, 0.0, 320.0, 120.0),)


@pytest.mark.parametrize("side", list(SIDES))
@pytest.mark.parametrize("ground_speed", [(0.0, 0.0), (0.0, SCROLL_L1), (-0.7, SCROLL_L1)])
@pytest.mark.parametrize("into", [2.5, 0.0, -1.0], ids=["into", "none", "away"])
def test_speed_into_the_surface_drops_against_the_island_and_the_rest_stays(
    side: str, ground_speed: tuple[float, float], into: float
) -> None:
    n = SIDES[side]
    t = ALONG[side]
    along = 1.5
    # The ship's speed is the ground's plus `into` px a tick into the surface plus `along` along it.
    vx = ground_speed[0] - into * n[0] + along * t[0]
    vy = ground_speed[1] - into * n[1] + along * t[1]
    start = replace(ship_on(RECT_SPOTS[side], DEPTH), vx=vx, vy=vy)
    ground = Ground(place_hitbox(RECTANGLE, ISLAND_X, ISLAND_Y), *ground_speed)

    pushed = block_ship(start, ground)

    assert pushed.against_island is True
    if into > 0:
        # The part into the surface is gone, measured against the island. The part along stays.
        assert pushed.vx == pytest.approx(ground_speed[0] + along * t[0])
        assert pushed.vy == pytest.approx(ground_speed[1] + along * t[1])
    else:
        # Moving away from the surface or along it: the speed stays. No bounce.
        assert pushed.vx == pytest.approx(vx)
        assert pushed.vy == pytest.approx(vy)
    relative = (pushed.vx - ground_speed[0], pushed.vy - ground_speed[1])
    assert relative[0] * n[0] + relative[1] * n[1] >= -1e-9


@pytest.mark.parametrize(
    "isl", [i for i in ISLANDS if i.shape == "triangle"], ids=lambda i: i.label
)
def test_speed_into_the_slope_drops_and_the_part_along_it_stays(isl: Island) -> None:
    normal = slope_normal(isl)
    along = (-normal[1], normal[0])
    corner = deepest_corner(normal)
    touching = Ship(ISLAND_X - corner[0], ISLAND_Y - corner[1], 0.0, 0.0)
    ground_speed = (0.0, SCROLL_L1)
    into, rest = 2.5, 1.5
    vx = ground_speed[0] - into * normal[0] + rest * along[0]
    vy = ground_speed[1] - into * normal[1] + rest * along[1]
    start = replace(touching, x=touching.x - DEPTH * normal[0], y=touching.y - DEPTH * normal[1])
    start = replace(start, vx=vx, vy=vy)

    pushed = block_ship(start, Ground(island_ground(isl).hitbox, *ground_speed))

    assert pushed.vx == pytest.approx(ground_speed[0] + rest * along[0])
    assert pushed.vy == pytest.approx(ground_speed[1] + rest * along[1])


# ---------------------------------------------------------------------------------------------
# Rules, Islands, On top and Underneath: stepping on a moving island
# ---------------------------------------------------------------------------------------------

TOP0: float = 298.9
"""The rectangle's top edge before tick 1, so it is at 300 after it. Source: ship.md, Diagram,
Islands, Stand and ride."""

BOTTOM0: float = 198.9
"""The rectangle's bottom edge before tick 1, so it is at 200 after it. Source: ship.md, Diagram,
Islands, Held and carried."""


def rectangle_ground(top: float | None = None, bottom: float | None = None) -> Ground:
    """Return the Diagram's rectangle with its top (or bottom) edge at the given y, moving 1.1."""
    if top is not None:
        center_y = top + 60.0
    else:
        assert bottom is not None
        center_y = bottom - 60.0
    return Ground(place_hitbox(RECTANGLE, ISLAND_X, center_y), 0.0, SCROLL_L1)


def ride(ship: Ship, ticks: int, thrust: Thrust = NO_KEY) -> list[Ship]:
    """Step the ship `ticks` times over a rectangle whose top is at 300 after tick 1 and moves."""
    ships: list[Ship] = []
    for n in range(1, ticks + 1):
        ship = step(ship, thrust, rectangle_ground(top=TOP0 + SCROLL_L1 * n))
        ships.append(ship)
    return ships


def test_ship_standing_on_an_island_keeps_its_speed_and_rides_down_with_it() -> None:
    standing = Ship(ISLAND_X, TOP0 - HALF, 0.0, SCROLL_L1)

    ships = ride(standing, 120)

    first = ships[0]
    # The Diagram: y 282.90 + 1.26 = 284.16, 0.16 inside, pushed up to 284.00, vy 1.10.
    assert_ship(first, ISLAND_X, 284.0, 0.0, SCROLL_L1)
    for n, ship in enumerate(ships, start=1):
        assert ship.against_island is True
        assert ship.y == pytest.approx(TOP0 + SCROLL_L1 * n - HALF, abs=1e-6)
        assert ship.vy == pytest.approx(SCROLL_L1, abs=1e-9)
        assert ship.x == pytest.approx(ISLAND_X)


def test_ship_standing_on_an_island_slides_along_it_with_its_sideways_speed() -> None:
    standing = Ship(ISLAND_X, TOP0 - HALF, 0.0, SCROLL_L1)

    ships = ride(standing, 20, Thrust(right=True))

    assert all(s.against_island for s in ships)
    assert all(b.x > a.x for a, b in pairwise(ships))
    assert all(s.vy == pytest.approx(SCROLL_L1, abs=1e-9) for s in ships)


def test_up_thrust_lifts_the_ship_off_the_island() -> None:
    standing = Ship(ISLAND_X, TOP0 - HALF, 0.0, SCROLL_L1)
    riding = ride(standing, 5)[-1]
    assert riding.against_island is True

    lifted = step(riding, Thrust(up=True), rectangle_ground(top=TOP0 + SCROLL_L1 * 6))

    # vy 1.10 - 0.42 + 0.16 = 0.84, less than the island's 1.10: it comes free.
    assert lifted.vy == pytest.approx(SCROLL_L1 - THRUST_UP + GRAVITY)
    assert lifted.vy < SCROLL_L1
    assert lifted.against_island is False
    ship = lifted
    for n in range(7, 13):
        ship = step(ship, Thrust(up=True), rectangle_ground(top=TOP0 + SCROLL_L1 * n))
        assert ship.against_island is False
        assert ship.y + HALF < TOP0 + SCROLL_L1 * n


def test_ship_held_under_an_underside_with_up_thrust_moves_at_the_island_speed_never_faster() -> (
    None
):
    ship = Ship(ISLAND_X, BOTTOM0 + HALF, 0.0, SCROLL_L1)

    for n in range(1, 101):
        ship = step(ship, Thrust(up=True), rectangle_ground(bottom=BOTTOM0 + SCROLL_L1 * n))
        assert ship.against_island is True
        assert ship.y == pytest.approx(BOTTOM0 + SCROLL_L1 * n + HALF, abs=1e-6)
        assert ship.vy == pytest.approx(SCROLL_L1, abs=1e-9)
        assert ship.vy <= SCROLL_L1 + 1e-9
        if n == 1:
            # The Diagram: y 214.90 + 0.84 = 215.74 (0.26 inside), pushed down to 216.00, vy 1.10.
            assert_ship(ship, ISLAND_X, 216.0, 0.0, SCROLL_L1)


def test_side_thrust_slides_a_held_ship_out_from_under_the_island() -> None:
    right_edge = ISLAND_X + 160.0
    ship = Ship(right_edge - 10.0, BOTTOM0 + HALF, 0.0, SCROLL_L1)
    held_xs: list[float] = []

    for n in range(1, 31):
        ship = step(
            ship, Thrust(up=True, right=True), rectangle_ground(bottom=BOTTOM0 + SCROLL_L1 * n)
        )
        assert ship.vy <= SCROLL_L1 + 1e-9
        if ship.against_island:
            held_xs.append(ship.x)
            assert ship.vx > 0

    assert len(held_xs) >= 2
    assert all(b > a for a, b in pairwise(held_xs))
    # The bar's right edge is past the island's right edge: the ship is out, and it stays out.
    assert ship.x - 6.0 >= right_edge
    assert ship.against_island is False


def test_ship_under_an_island_with_no_thrust_falls_away_from_it() -> None:
    ship = Ship(ISLAND_X, BOTTOM0 + HALF, 0.0, SCROLL_L1)

    for n in range(1, 21):
        ship = step(ship, NO_KEY, rectangle_ground(bottom=BOTTOM0 + SCROLL_L1 * n))
        # vy 1.10 + 0.16 = 1.26 > 1.10: the gap opens by 0.16 more each tick.
        assert ship.against_island is False
        assert ship.vy == pytest.approx(SCROLL_L1 + GRAVITY * n)
        assert ship.y - HALF > BOTTOM0 + SCROLL_L1 * n


# ---------------------------------------------------------------------------------------------
# Rules, Islands, Slopes: no key on the triangle's slope
# ---------------------------------------------------------------------------------------------


def test_ship_with_no_key_slides_down_the_triangle_slope_and_gains_speed() -> None:
    isl = next(i for i in ISLANDS if i.shape == "triangle" and not i.invert)
    ground = island_ground(isl)
    normal = slope_normal(isl)
    corner = deepest_corner(normal)
    ship = Ship(ISLAND_X - corner[0], ISLAND_Y - corner[1], 0.0, 0.0)
    start = ship

    # First tick, the Diagram: vy 0.16, 0.16 deep vertically, 0.1498 along n; out along n by that;
    # (0, 0.16) has -0.1498 along n, removed: (0.0526, 0.0197).
    depth_along_n = GRAVITY * -normal[1]
    expected_vx = depth_along_n * normal[0]
    expected_vy = GRAVITY - depth_along_n * -normal[1]
    ship = step(ship, NO_KEY, ground)
    assert ship.against_island is True
    assert ship.vx == pytest.approx(expected_vx)
    assert ship.vy == pytest.approx(expected_vy)
    assert ship.x == pytest.approx(start.x + expected_vx)
    assert ship.y == pytest.approx(start.y + expected_vy)

    speed = math.hypot(ship.vx, ship.vy)
    for _ in range(19):
        before = ship
        ship = step(ship, NO_KEY, ground)
        now = math.hypot(ship.vx, ship.vy)
        assert ship.against_island is True
        assert now > speed
        speed = now
        assert ship.x > before.x
        assert ship.y > before.y
        # The ship's corner stays on the slope's line: no bounce, no sinking.
        on_line = (ship.x + corner[0] - ISLAND_X) * normal[0] + (
            ship.y + corner[1] - ISLAND_Y
        ) * normal[1]
        assert on_line == pytest.approx(0.0, abs=1e-6)
        assert ship.vx * normal[0] + ship.vy * normal[1] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------------------------
# Rules, Islands, 2: walls, the top line, ties
# ---------------------------------------------------------------------------------------------


def test_push_never_goes_through_a_side_wall() -> None:
    # Left: the island's left face is at x 30. The ship's foot is 14 px in it, so the shortest way
    # is left, 14 px, which puts the ship's left edge at -2. Refused: it goes up, 20 px.
    left = block_ship(Ship(28.0, 274.0, 0.0, 0.0), box_ground((90.0, 330.0, 120.0, 120.0)))
    assert_ship(left, 28.0, 254.0, 0.0, 0.0)
    # Right: the island's right face is at x 610. The ship's foot is 14 px in it: right, 14 px,
    # puts the right edge at 642. Refused: up, 20 px.
    right = block_ship(Ship(612.0, 274.0, 0.0, 0.0), box_ground((550.0, 330.0, 120.0, 120.0)))
    assert_ship(right, 612.0, 254.0, 0.0, 0.0)
    assert left.against_island is True
    assert right.against_island is True


def test_push_never_goes_above_the_top_line_and_takes_the_next_shortest_way() -> None:
    # The island is rows 140 to 260, x 260 to 380. The ship's foot is 10 px in its top: up, 10 px,
    # would put the ship's top edge at 108, above the top line (168). Left is 26 px, down 142,
    # right 126: left.
    near_the_end = block_ship(
        Ship(270.0, 134.0, 0.0, 0.0), box_ground((320.0, 200.0, 120.0, 120.0))
    )
    assert_ship(near_the_end, 244.0, 134.0, 0.0, 0.0)
    # In the middle of a 320 wide island left and right are 176: down, 142, is the next shortest.
    in_the_middle = block_ship(
        Ship(320.0, 134.0, 0.0, 0.0), box_ground((320.0, 200.0, 320.0, 120.0))
    )
    assert_ship(in_the_middle, 320.0, 276.0, 0.0, 0.0)
    # The ship's top edge may end exactly on the line: an island top at 200 puts the foot's bottom
    # at 200 and the ship's center at 184, top edge 168. One px higher (199) would put it at 167.
    on_the_line = block_ship(Ship(320.0, 194.0, 0.0, 0.0), box_ground((320.0, 260.0, 320.0, 120.0)))
    assert_ship(on_the_line, 320.0, 184.0, 0.0, 0.0)
    past_the_line = block_ship(
        Ship(320.0, 194.0, 0.0, 0.0), box_ground((320.0, 259.0, 320.0, 120.0))
    )
    assert_ship(past_the_line, 320.0, 335.0, 0.0, 0.0)  # down: the bar's top (178) to 319 is 141


def test_straight_down_is_always_left_when_every_other_way_is_refused() -> None:
    # Two islands side by side cover x 0 to 640, rows 140 to 260. Up passes the top line, left and
    # right pass the walls. Down is not refused.
    ground = box_ground((160.0, 200.0, 320.0, 120.0), (480.0, 200.0, 320.0, 120.0))

    pushed = block_ship(Ship(320.0, 134.0, 0.0, 0.0), ground)

    assert_ship(pushed, 320.0, 276.0, 0.0, 0.0)
    assert pushed.against_island is True


@pytest.mark.parametrize(
    ("ground", "ship", "expected"),
    [
        pytest.param(
            box_ground((320.0, 330.0, 120.0, 120.0)),
            Ship(320.0, 330.0, 0.0, 0.0),
            (320.0, 254.0),
            id="all-four-equal-up",
        ),
        pytest.param(
            box_ground((320.0, 330.0, 320.0, 120.0)),
            Ship(180.0, 370.0, 0.0, 0.0),
            (180.0, 406.0),
            id="down-and-left-equal-down",
        ),
        pytest.param(
            box_ground((320.0, 330.0, 120.0, 300.0)),
            Ship(320.0, 330.0, 0.0, 0.0),
            (244.0, 330.0),
            id="left-and-right-equal-left",
        ),
        pytest.param(
            box_ground((320.0, 330.0, 120.0, 120.0)),
            Ship(320.0, 330.0 + 3e-10, 0.0, 0.0),
            (320.0, 254.0),
            id="a-hair-short-down-is-still-a-tie-up",
        ),
        pytest.param(
            box_ground((320.0, 330.0, 120.0, 120.0)),
            Ship(320.0, 330.0 + 1e-6, 0.0, 0.0),
            (320.0, 406.0),
            id="a-clearly-shorter-down-wins",
        ),
    ],
)
def test_ties_go_up_then_down_then_left_then_right(
    ground: Ground, ship: Ship, expected: tuple[float, float]
) -> None:
    pushed = block_ship(ship, ground)

    assert_ship(pushed, expected[0], expected[1])
    assert pushed.against_island is True


# ---------------------------------------------------------------------------------------------
# Rules, Islands, Several islands: one push, never on the seam
# ---------------------------------------------------------------------------------------------

L_SHAPE: Hitbox = (Box(0.0, 40.0, 320.0, 40.0), Box(-140.0, 0.0, 40.0, 120.0))
"""The Diagram's l_shape: the bar, then the upright."""

T_SHAPE: Hitbox = (Box(0.0, -40.0, 320.0, 40.0), Box(0.0, 0.0, 40.0, 120.0))
"""The Diagram's t_shape: the bar, then the stem."""


def test_one_push_clears_the_two_boxes_of_the_l_at_their_seam() -> None:
    ground = Ground(place_hitbox(L_SHAPE, ISLAND_X, ISLAND_Y))
    # Relative to the island: the foot (x -126 to -94, rows 18 to 30) is 6 px into the upright
    # and 10 px into the bar. Down clears the upright at 42 but the ship's bar is then still in
    # the L's bar: 62 clears both. Left 66, up 90, right far more.
    ship = Ship(ISLAND_X - 110.0, ISLAND_Y + 14.0, 0.0, 0.0)

    pushed = block_ship(ship, ground)

    assert_ship(pushed, ISLAND_X - 110.0, ISLAND_Y + 14.0 + 62.0, 0.0, 0.0)
    assert clear_of(pushed, ground)


def test_one_push_clears_the_two_boxes_of_the_t_at_their_seam() -> None:
    ground = Ground(place_hitbox(T_SHAPE, ISLAND_X, ISLAND_Y))
    # The foot (x -46 to -14, rows -4 to 8) is 6 px into the stem and the ship's bar is 4 px up
    # into the T's bar. Down clears the T's bar at 4, but the foot is in the stem until its top
    # is at 60: 64. Up 68, right 66 + more, left 136.
    ship = Ship(ISLAND_X - 30.0, ISLAND_Y - 8.0, 0.0, 0.0)

    pushed = block_ship(ship, ground)

    assert_ship(pushed, ISLAND_X - 30.0, ISLAND_Y - 8.0 + 64.0, 0.0, 0.0)
    assert clear_of(pushed, ground)


def test_one_push_clears_two_overlapping_islands() -> None:
    # A 320 x 120 island at y 370 (rows 310 to 430) and a 120 x 120 one at y 290 (rows 230 to
    # 350) overlap. The foot is 6 px into the first and the whole ship is in the second. Out
    # sideways of the second is 76, but the first still holds the ship: 176. Up clears both: 86.
    ground = box_ground((320.0, 370.0, 320.0, 120.0), (320.0, 290.0, 120.0, 120.0))

    pushed = block_ship(Ship(320.0, 300.0, 0.0, 0.0), ground)

    assert_ship(pushed, 320.0, 214.0, 0.0, 0.0)
    assert clear_of(pushed, ground)


# ---------------------------------------------------------------------------------------------
# Rules: the step with no ground, edge touches, block_ship alone
# ---------------------------------------------------------------------------------------------


def expected_step(ship: Ship, thrust: Thrust) -> Ship:
    """The step before DRA-86: thrust, gravity, drag, fall cap, move, side walls, top line."""
    vx, vy = ship.vx, ship.vy
    if thrust.left:
        vx -= THRUST_SIDE
    if thrust.right:
        vx += THRUST_SIDE
    if thrust.up:
        vy -= THRUST_UP
    if thrust.down:
        vy += THRUST_DOWN
    vy += GRAVITY
    vx *= DRAG_X
    vy = min(vy, FALL_CAP)
    x, y = ship.x + vx, ship.y + vy
    wall: Literal["left", "right"] | None = None
    if x - HALF < 0:
        x, vx, wall = HALF, 0.0, "left"
    elif x + HALF > SCREEN_W:
        x, vx, wall = SCREEN_W - HALF, 0.0, "right"
    at_top_line = False
    if y - HALF < TOP_LINE_Y:
        y, vy, at_top_line = TOP_LINE_Y + HALF, 0.0, True
    return Ship(x, y, vx, vy, wall, at_top_line, False)


STATES: list[Ship] = [
    Ship(x, y, vx, vy, against_island=held)
    for (x, y) in [(320.0, 240.0), (20.0, 300.0), (620.0, 300.0), (320.0, 190.0), (320.0, 470.0)]
    for (vx, vy) in [(0.0, 0.0), (3.0, -2.0), (-9.0, 4.0), (9.0, -9.0), (0.0, 5.5), (0.0, 7.0)]
    for held in (False, True)
]

THRUSTS: list[Thrust] = [
    Thrust(up, down, left, right)
    for up in (False, True)
    for down in (False, True)
    for left in (False, True)
    for right in (False, True)
]

NOWHERE: Ground = Ground(place_hitbox(RECTANGLE, 320.0, -400.0), 1.5, 2.5)
"""An island far above the screen's play area, moving: it touches nothing."""


def test_step_with_no_ground_is_the_step_before_the_islands_with_against_island_false() -> None:
    empty_moving = Ground(velocity_x=1.5, velocity_y=2.5)
    for ship in STATES:
        for thrust in THRUSTS:
            want = expected_step(ship, thrust)
            for got in (
                step(ship, thrust),
                step(ship, thrust, NO_GROUND),
                step(ship, thrust, Ground()),
                step(ship, thrust, empty_moving),
                step(ship, thrust, NOWHERE),
            ):
                assert got.x == pytest.approx(want.x, abs=1e-9)
                assert got.y == pytest.approx(want.y, abs=1e-9)
                assert got.vx == pytest.approx(want.vx, abs=1e-9)
                assert got.vy == pytest.approx(want.vy, abs=1e-9)
                assert got.wall == want.wall
                assert got.at_top_line == want.at_top_line
                assert got.against_island is False


@pytest.mark.parametrize("side", list(SIDES))
@pytest.mark.parametrize("hair", [0.0, HAIR], ids=["touching", "hair-inside"])
def test_an_edge_touching_the_island_is_not_a_push(side: str, hair: float) -> None:
    ground = Ground(place_hitbox(RECTANGLE, ISLAND_X, ISLAND_Y))
    ship = replace(ship_on(RECT_SPOTS[side], hair), vx=0.5, vy=-0.5, against_island=True)

    result = block_ship(ship, ground)

    assert result == replace(ship, against_island=False)


def test_a_step_that_ends_with_the_foot_on_the_island_top_is_not_a_push() -> None:
    # vy 0.26 - 0.42 (up) + 0.16 (gravity) is 0: the ship stays where it is, touching the top.
    ground = Ground(place_hitbox(RECTANGLE, ISLAND_X, ISLAND_Y))
    ship = replace(ship_on(RECT_SPOTS["above"], 0.0), vy=0.26)

    after = step(ship, Thrust(up=True), ground)

    assert after.against_island is False
    assert_ship(after, ship.x, ship.y, 0.0, 0.0)


@pytest.mark.parametrize("isl", ISLANDS, ids=lambda i: i.label)
def test_block_ship_alone_pushes_a_ship_at_rest_the_same_way(isl: Island) -> None:
    ground = island_ground(isl, 0.0, SCROLL_L1)
    # Each island is met on its first spot at rest. The island moves 1.1 down.
    spot = spots(isl)[0]
    touching = ship_on(spot, 0.0)
    ship = ship_on(spot, DEPTH)

    pushed = block_ship(ship, ground)

    assert_ship(pushed, touching.x, touching.y)
    assert pushed.against_island is True
    assert pushed.wall is None
    assert pushed.at_top_line is False
    assert ship.against_island is False  # the input is not changed
    if spot.side == "below":
        # A ship held under an island is left with the island's downward speed.
        assert pushed.vy == pytest.approx(SCROLL_L1)
    else:
        assert pushed.vy == pytest.approx(0.0)
    assert pushed.vx == pytest.approx(0.0)


# ---------------------------------------------------------------------------------------------
# Rules: the respawn spot
# ---------------------------------------------------------------------------------------------


def assert_respawn(ship: Ship, y: float) -> None:
    """The ship at rest at (320, y) with every flag off."""
    assert ship.x == SPAWN_X
    assert ship.y == pytest.approx(y, abs=1e-6)
    assert (ship.vx, ship.vy) == (0.0, 0.0)
    assert (ship.wall, ship.at_top_line, ship.against_island) == (None, False, False)


def test_the_respawn_point_is_kept_when_no_island_holds_the_ship_there() -> None:
    assert spawn_clear(Ground()) == spawn()
    assert spawn_clear(NO_GROUND) == spawn()
    # The Diagram's table: boxes 120 x 120 centered on (320, 330) and (320, 160).
    assert_respawn(spawn_clear(box_ground((320.0, 330.0, 120.0, 120.0))), SPAWN_Y)
    assert_respawn(spawn_clear(box_ground((320.0, 160.0, 120.0, 120.0))), SPAWN_Y)
    # Touching is not holding: the ship's bar top is at 224, the foot's bottom at 256, its foot's
    # left edge at 304 and its right edge at 336.
    for touching in (
        box_ground((320.0, 164.0, 120.0, 120.0)),
        box_ground((320.0, 316.0, 120.0, 120.0)),
        box_ground((244.0, 240.0, 120.0, 120.0)),
        box_ground((396.0, 240.0, 120.0, 120.0)),
    ):
        assert_respawn(spawn_clear(touching), SPAWN_Y)
    # The ground's own speed changes nothing.
    moving = Ground(place_hitbox(RECTANGLE, 320.0, 330.0), 1.0, 1.1)
    assert_respawn(spawn_clear(moving), SPAWN_Y)


def test_the_respawn_spot_is_just_above_an_island_that_holds_the_point() -> None:
    # Box rows 240 to 360: the foot's bottom (256) is 16 in. Above: 240 - 16 = 224, top edge 208.
    held = spawn_clear(box_ground((320.0, 300.0, 120.0, 120.0)))
    assert_respawn(held, 224.0)
    assert held.x == SPAWN_X


def test_the_respawn_spot_is_below_when_above_would_pass_the_top_line() -> None:
    # Box rows 190 to 310: above is 66 up, y 174, top edge 158, past 168. Below is 86 down: 326.
    assert_respawn(spawn_clear(box_ground((320.0, 250.0, 120.0, 120.0))), 326.0)
    # Above may put the top edge exactly on the top line: rows 200 to 280, up 56 and down 56
    # (a tie), y 184, top edge 168. A box one px taller (rows 199 to 281) is 57 each way: top edge
    # 167, past the line, so below: 297.
    assert_respawn(spawn_clear(box_ground((320.0, 240.0, 120.0, 80.0))), 184.0)
    assert_respawn(spawn_clear(box_ground((320.0, 240.0, 120.0, 82.0))), 297.0)
    # Above is allowed and 46 up, but below is 16 down: the nearer one. Rows 210 to 240.
    assert_respawn(spawn_clear(box_ground((320.0, 225.0, 120.0, 30.0))), 256.0)


def test_the_respawn_spot_is_above_when_above_and_below_are_equally_near() -> None:
    # Rows 200 to 280: foot bottom 256 - 200 = 56 up, bar top 224 -> 280 = 56 down. Above.
    assert_respawn(spawn_clear(box_ground((320.0, 240.0, 120.0, 80.0))), 184.0)
    # Rows 220 to 260: 36 up, 36 down. Above.
    assert_respawn(spawn_clear(box_ground((320.0, 240.0, 120.0, 40.0))), 204.0)


def test_the_respawn_spot_is_at_rest_with_every_flag_off() -> None:
    held = spawn_clear(Ground(place_hitbox(RECTANGLE, 320.0, 300.0), 0.0, 1.1))

    assert held.vx == 0.0
    assert held.vy == 0.0
    assert held.wall is None
    assert held.at_top_line is False
    assert held.against_island is False


# ---------------------------------------------------------------------------------------------
# Rules, Logging: `island contact`
# ---------------------------------------------------------------------------------------------


def lines(caplog: pytest.LogCaptureFixture, prefix: str) -> list[str]:
    """The messages of the ship's logger that begin with `prefix`, in the order logged."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == SHIP_LOGGER and r.getMessage().startswith(prefix)
    ]


def test_island_contact_is_logged_once_when_contact_starts_by_step(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SHIP_LOGGER)
    ship = Ship(ISLAND_X, TOP0 - HALF, 0.0, SCROLL_L1)
    touched: list[bool] = []
    landed_at: list[Ship] = []

    for n in range(1, 301):
        # Ride for 10 ticks, lift off with up thrust for 3, then let go and wait for the landing.
        thrust = Thrust(up=True) if 11 <= n <= 13 else NO_KEY
        previous = ship
        ship = step(ship, thrust, rectangle_ground(top=TOP0 + SCROLL_L1 * n))
        touched.append(ship.against_island)
        if ship.against_island and not previous.against_island:
            landed_at.append(ship)
        if len(landed_at) == 2 and n >= len(touched) and sum(touched[-5:]) == 5:
            break

    # Contact on tick 1, then a lift-off (ticks 11 on), then a new landing.
    assert len(landed_at) == 2
    assert touched[:10] == [True] * 10
    assert touched[10] is False
    logged = lines(caplog, "island contact")
    assert logged == [f"island contact x={s.x:.2f} y={s.y:.2f}" for s in landed_at]


def test_island_contact_is_logged_once_when_contact_starts_by_block_ship(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SHIP_LOGGER)
    ground = Ground(place_hitbox(RECTANGLE, ISLAND_X, ISLAND_Y))
    sunk = ship_on(RECT_SPOTS["above"], DEPTH)

    first = block_ship(sunk, ground)
    held = block_ship(replace(first, y=first.y + 0.16), ground)
    again = block_ship(replace(held, y=held.y + 0.16), ground)
    assert [first.against_island, held.against_island, again.against_island] == [True] * 3
    assert len(lines(caplog, "island contact")) == 1

    free = block_ship(replace(again, y=again.y - 30.0), ground)
    assert free.against_island is False
    assert len(lines(caplog, "island contact")) == 1

    lands = block_ship(replace(free, y=free.y + 30.0 + 0.5), ground)
    assert lands.against_island is True
    assert lines(caplog, "island contact") == [
        f"island contact x={first.x:.2f} y={first.y:.2f}",
        f"island contact x={lands.x:.2f} y={lands.y:.2f}",
    ]


def test_island_contact_comes_between_wall_hit_and_top_line_stop(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SHIP_LOGGER)
    # A thin island against the left wall, rows 70 to 190, x 0 to 20. The ship hits the wall, is
    # pushed right (up is refused by the top line, down is 41 px), then the top line stops it.
    ground = box_ground((10.0, 130.0, 20.0, 120.0))
    ship = Ship(17.0, 170.0, -5.0, -5.0)

    after = step(ship, NO_KEY, ground)

    assert after.wall == "left"
    assert after.against_island is True
    assert after.at_top_line is True
    messages = [r.getMessage() for r in caplog.records if r.name == SHIP_LOGGER]
    kinds = [m.split(" x=")[0].split(" side=")[0] for m in messages]
    assert kinds == ["wall hit", "island contact", "top line stop"]
