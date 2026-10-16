"""Hitbox overlap tables, collision invariants, the shape guards and the ship's hitbox tests.

Contract: docs/contracts/systems/drifters.md, Rules, Collision; docs/contracts/systems/ship.md,
Rules, Hitbox. Tasks: docs/contracts/DRA-29/tasks/DRA-29-07-qa-engineer.md (the two ship tests at
the end) and docs/contracts/DRA-39/tasks/DRA-39-05-qa-engineer.md (everything above them).

Every expected number is exact in binary (whole numbers, halves, sixteenths, 3-4-5 triangles) or
comes from the GDD values below or from `game/tuning/drifters/*.json`. The ship-against-every-
variant cases read those files, so a new drifter or variant is covered with no new test code.
"""

import json
import math
import typing
from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations_with_replacement
from pathlib import Path
from typing import cast

import pytest

from core import collision
from core.collision import (
    Box,
    Circle,
    Hitbox,
    Shape,
    grow_hitbox,
    hitboxes_overlap,
    place_hitbox,
)
from core.drifters.base import Drifter, DrifterType, Phase, TickContext
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
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
"""px. Source: 06-scoring.md, graze_margin (locked). Used as one growth margin."""

HAIR: float = 0.0625
"""px, 1/16: a hair, exact in binary."""

DRIFTER_TUNING_DIR: Path = Path(__file__).resolve().parents[2] / "tuning" / "drifters"
"""Where each drifter type's tuning file lives. Source: drifters.md, Rules, Tuning files."""

OFFSETS: tuple[tuple[float, float], ...] = (
    (-37.5, 12.25),
    (0.5, -0.75),
    (640.0, 480.0),
    (-640.0, -480.0),
    (HAIR, -HAIR / 2),
)
"""Moves applied to both sides of a case: negative, fractional and screen-sized, exact in binary."""

MARGINS: tuple[float, ...] = (0.5, GRAZE_MARGIN)
"""Growth margins for the grow invariant."""


@dataclass(frozen=True, slots=True)
class Case:
    """Two shapes and whether they share area. Each is checked in both orders."""

    name: str
    a: Shape
    b: Shape
    overlaps: bool


# Circle and circle. A is at the origin unless it says otherwise.
CIRCLE_CIRCLE: tuple[Case, ...] = (
    Case("edge touch right", Circle(0, 0, 5), Circle(10, 0, 5), False),
    Case("edge touch left", Circle(0, 0, 5), Circle(-10, 0, 5), False),
    Case("edge touch below", Circle(0, 0, 5), Circle(0, 10, 5), False),
    Case("edge touch above", Circle(0, 0, 5), Circle(0, -10, 5), False),
    Case("edge touch, unequal radii", Circle(0, 0, 3), Circle(7.5, 0, 4.5), False),
    Case("hair inside", Circle(0, 0, 5), Circle(10 - HAIR, 0, 5), True),
    Case("hair outside", Circle(0, 0, 5), Circle(10 + HAIR, 0, 5), False),
    Case("hair inside, unequal radii", Circle(0, 0, 3), Circle(7.5 - HAIR, 0, 4.5), True),
    Case("3-4-5 diagonal touch", Circle(0, 0, 25), Circle(30, 40, 25), False),
    Case("3-4-5 diagonal touch, negative", Circle(0, 0, 25), Circle(-30, -40, 25), False),
    Case("3-4-5 diagonal hair inside", Circle(0, 0, 25), Circle(30 - HAIR, 40, 25), True),
    Case("3-4-5 diagonal hair outside", Circle(0, 0, 25), Circle(30 + HAIR, 40, 25), False),
    Case("3-4-5 diagonal touch, offset", Circle(100, 50, 6), Circle(106, 58, 4), False),
    Case("one inside the other", Circle(0, 0, 10), Circle(1, 1, 2), True),
    Case("inside, centers apart", Circle(2, -3, 8), Circle(-1, 1, 1.5), True),
    Case(
        "internal tangent: smaller touches the inside edge", Circle(0, 0, 10), Circle(5, 0, 5), True
    ),
    Case("identical", Circle(3, 4, 5), Circle(3, 4, 5), True),
    Case("far apart", Circle(0, 0, 5), Circle(100, 100, 5), False),
    Case("far apart on one axis", Circle(0, 0, 5), Circle(0, 1000, 5), False),
)

# Box and box. Box(cx, cy, w, h). A is Box(0, 0, 10, 10) (edges at -5 and 5) unless it says
# otherwise.
BOX_BOX: tuple[Case, ...] = (
    Case("edge touch right", Box(0, 0, 10, 10), Box(10, 0, 10, 10), False),
    Case("edge touch left", Box(0, 0, 10, 10), Box(-10, 0, 10, 10), False),
    Case("edge touch below", Box(0, 0, 10, 10), Box(0, 10, 10, 10), False),
    Case("edge touch above", Box(0, 0, 10, 10), Box(0, -10, 10, 10), False),
    Case("edge touch, shifted along the edge", Box(0, 0, 10, 10), Box(10, 3, 10, 10), False),
    Case("edge touch, unequal sizes", Box(0, 0, 4, 20), Box(5, 0, 6, 4), False),
    Case("edge touch, halves", Box(0, 0, 3, 5), Box(3.5, 0, 4, 2), False),
    Case("edge hair inside right", Box(0, 0, 10, 10), Box(10 - HAIR, 0, 10, 10), True),
    Case("edge hair inside above", Box(0, 0, 10, 10), Box(0, -10 + HAIR, 10, 10), True),
    Case("edge hair inside, unequal sizes", Box(0, 0, 4, 20), Box(5 - HAIR, 0, 6, 4), True),
    Case("edge hair outside", Box(0, 0, 10, 10), Box(10 + HAIR, 0, 10, 10), False),
    Case("corner touch", Box(0, 0, 10, 10), Box(10, 10, 10, 10), False),
    Case("corner touch, opposite corner", Box(0, 0, 10, 10), Box(-10, -10, 10, 10), False),
    Case("corner touch, other diagonal", Box(0, 0, 10, 10), Box(10, -10, 10, 10), False),
    Case("corner touch, unequal sizes", Box(0, 0, 4, 2), Box(4, 2.5, 6, 3), False),
    Case("corner hair inside", Box(0, 0, 10, 10), Box(10 - HAIR, 10 - HAIR, 10, 10), True),
    Case(
        "corner hair inside, other diagonal",
        Box(0, 0, 10, 10),
        Box(-10 + HAIR, 10 - HAIR, 10, 10),
        True,
    ),
    Case("hair inside on x, touching on y", Box(0, 0, 10, 10), Box(10 - HAIR, 10, 10, 10), False),
    Case("hair inside on y, touching on x", Box(0, 0, 10, 10), Box(10, 10 - HAIR, 10, 10), False),
    Case("one inside the other", Box(0, 0, 10, 10), Box(0, 0, 2, 2), True),
    Case("inside, off center, edge flush", Box(0, 0, 10, 10), Box(3, -3, 4, 4), True),
    Case("inside, reversed sizes", Box(0, 0, 2, 2), Box(0, 0, 10, 10), True),
    Case("cross: wide over tall", Box(0, 0, 20, 2), Box(0, 0, 2, 20), True),
    Case("identical", Box(3, 4, 10, 10), Box(3, 4, 10, 10), True),
    Case("far apart", Box(0, 0, 10, 10), Box(100, 100, 10, 10), False),
    Case("far apart on one axis", Box(0, 0, 10, 10), Box(0, 1000, 10, 10), False),
)

# Circle and box. A is the circle, B the box. The box is Box(0, 0, 10, 10) (edges at -5 and 5)
# unless it says otherwise.
CIRCLE_BOX: tuple[Case, ...] = (
    Case("edge touch right", Circle(8, 0, 3), Box(0, 0, 10, 10), False),
    Case("edge touch left", Circle(-8, 0, 3), Box(0, 0, 10, 10), False),
    Case("edge touch below", Circle(0, 8, 3), Box(0, 0, 10, 10), False),
    Case("edge touch above", Circle(0, -8, 3), Box(0, 0, 10, 10), False),
    Case("edge touch, centered off the middle", Circle(8, 4.5, 3), Box(0, 0, 10, 10), False),
    Case("edge touch, center in line with the corner", Circle(8, 5, 3), Box(0, 0, 10, 10), False),
    Case("edge hair inside right", Circle(8 - HAIR, 0, 3), Box(0, 0, 10, 10), True),
    Case("edge hair inside above", Circle(0, -8 + HAIR, 3), Box(0, 0, 10, 10), True),
    Case("edge hair outside", Circle(8 + HAIR, 0, 3), Box(0, 0, 10, 10), False),
    Case("3-4-5 corner touch", Circle(8, 9, 5), Box(0, 0, 10, 10), False),
    Case("3-4-5 corner touch, opposite corner", Circle(-8, -9, 5), Box(0, 0, 10, 10), False),
    Case("3-4-5 corner touch, other diagonal", Circle(8, -9, 5), Box(0, 0, 10, 10), False),
    Case("3-4-5 corner touch, steep side", Circle(-9, 8, 5), Box(0, 0, 10, 10), False),
    Case("3-4-5 corner hair inside", Circle(8 - HAIR, 9, 5), Box(0, 0, 10, 10), True),
    Case(
        "3-4-5 corner hair inside, other diagonal",
        Circle(-8 + HAIR, -9, 5),
        Box(0, 0, 10, 10),
        True,
    ),
    Case("3-4-5 corner hair outside", Circle(8 + HAIR, 9, 5), Box(0, 0, 10, 10), False),
    Case("near the corner, not touching", Circle(8, 7, 3), Box(0, 0, 10, 10), False),
    Case("center on the corner", Circle(5, 5, 1), Box(0, 0, 10, 10), True),
    Case("center on an edge", Circle(5, 0, 1), Box(0, 0, 10, 10), True),
    Case("circle inside the box", Circle(0, 0, 1), Box(0, 0, 10, 10), True),
    Case("box inside the circle", Circle(0, 0, 10), Box(0, 0, 10, 10), True),
    Case("circle around the box corners exactly", Circle(0, 0, 5), Box(0, 0, 6, 8), True),
    Case("circle inside, flush with the edge", Circle(2, 0, 3), Box(0, 0, 10, 10), True),
    Case("identical center", Circle(3, 4, 2), Box(3, 4, 2, 2), True),
    Case("far apart", Circle(20, 20, 3), Box(0, 0, 10, 10), False),
    Case("far apart on one axis", Circle(0, 1000, 3), Box(0, 0, 10, 10), False),
)

TABLES: dict[frozenset[type], tuple[Case, ...]] = {
    frozenset({Circle}): CIRCLE_CIRCLE,
    frozenset({Box}): BOX_BOX,
    frozenset({Circle, Box}): CIRCLE_BOX,
}
"""One table per unordered pair of shape kinds."""

ALL_CASES: tuple[tuple[str, Case], ...] = tuple(
    (f"{'-'.join(sorted(k.__name__ for k in kinds))}: {case.name}", case)
    for kinds, table in TABLES.items()
    for case in table
)
"""Every case of every table with an id for the test report."""


class Triangle:
    """A shape kind the collision module doesn't know."""


def overlap_both_ways(a: Hitbox, b: Hitbox) -> bool:
    """Return the overlap of a and b, after checking that the order doesn't matter."""
    forward: bool = hitboxes_overlap(a, b)
    assert forward == hitboxes_overlap(b, a)
    return forward


def moved(shape: Shape, dx: float, dy: float) -> Shape:
    """Return `shape` moved by (dx, dy), built here, not with `place_hitbox`."""
    if isinstance(shape, Circle):
        return Circle(shape.cx + dx, shape.cy + dy, shape.r)
    return Box(shape.cx + dx, shape.cy + dy, shape.w, shape.h)


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_every_table_case_gives_its_result_in_both_orders(case_id: str, case: Case) -> None:
    assert overlap_both_ways((case.a,), (case.b,)) is case.overlaps, case_id
    assert overlap_both_ways((case.b,), (case.a,)) is case.overlaps, case_id


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_placing_both_hitboxes_by_the_same_offset_keeps_the_result(
    case_id: str, case: Case
) -> None:
    for dx, dy in OFFSETS:
        a: Hitbox = place_hitbox((case.a,), dx, dy)
        b: Hitbox = place_hitbox((case.b,), dx, dy)
        assert a == (moved(case.a, dx, dy),)
        assert overlap_both_ways(a, b) is case.overlaps, (case_id, dx, dy)


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_an_empty_hitbox_overlaps_nothing(case_id: str, case: Case) -> None:
    for shape in (case.a, case.b):
        assert not overlap_both_ways((), (shape,)), case_id
    assert not overlap_both_ways((), ()), case_id


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_adding_a_shape_to_either_side_never_removes_an_overlap(case_id: str, case: Case) -> None:
    extras: tuple[Shape, ...] = (
        Circle(5000, 5000, 1),
        Box(-5000, 5000, 4, 4),
        Circle(case.a.cx + 3000, case.a.cy, 2),
    )
    if not case.overlaps:
        return
    for extra in extras:
        hitboxes: tuple[tuple[Hitbox, Hitbox], ...] = (
            ((case.a, extra), (case.b,)),
            ((extra, case.a), (case.b,)),
            ((case.a,), (case.b, extra)),
            ((case.a,), (extra, case.b)),
            ((case.a, extra), (extra, case.b)),
        )
        for a, b in hitboxes:
            assert overlap_both_ways(a, b), case_id


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_growing_either_side_never_removes_an_overlap(case_id: str, case: Case) -> None:
    if not case.overlaps:
        return
    for margin in MARGINS:
        grown_a: Hitbox = grow_hitbox((case.a,), margin)
        grown_b: Hitbox = grow_hitbox((case.b,), margin)
        assert overlap_both_ways(grown_a, (case.b,)), (case_id, margin)
        assert overlap_both_ways((case.a,), grown_b), (case_id, margin)
        assert overlap_both_ways(grown_a, grown_b), (case_id, margin)


def test_every_shape_kind_and_every_pair_of_kinds_has_a_table() -> None:
    kinds: set[type] = set(typing.get_args(collision.Shape))
    assert kinds == {Circle, Box}, "a new shape kind needs its tables and its test updates"
    pairs: set[frozenset[type]] = {
        frozenset(pair) for pair in combinations_with_replacement(kinds, 2)
    }
    assert set(TABLES) == pairs
    for pair, table in TABLES.items():
        assert table, pair
        for case in table:
            assert {type(case.a), type(case.b)} == set(pair), (pair, case.name)


@pytest.mark.parametrize(
    "call",
    [
        lambda bad: hitboxes_overlap(bad, (Box(0, 0, 10, 10),)),
        lambda bad: hitboxes_overlap((Box(0, 0, 10, 10),), bad),
        lambda bad: hitboxes_overlap(bad, ()),
        lambda bad: hitboxes_overlap((), bad),
        lambda bad: place_hitbox(bad, 1.0, 2.0),
        lambda bad: grow_hitbox(bad, 1.0),
    ],
    ids=[
        "overlap-first",
        "overlap-second",
        "overlap-first-vs-empty",
        "overlap-second-vs-empty",
        "place",
        "grow",
    ],
)
def test_an_unknown_shape_kind_raises_type_error(call: Callable[[Hitbox], object]) -> None:
    for bad_shape in (Triangle(), object(), "circle", (0, 0, 5)):
        for bad in (
            cast(Hitbox, (bad_shape,)),
            cast(Hitbox, (Circle(0, 0, 5), bad_shape)),
            cast(Hitbox, (bad_shape, Box(0, 0, 10, 10))),
        ):
            with pytest.raises(TypeError, match="unknown shape kind"):
                call(bad)


def test_an_unknown_shape_kind_error_names_the_kind() -> None:
    bad: Hitbox = cast(Hitbox, (Triangle(),))
    with pytest.raises(TypeError, match="unknown shape kind 'Triangle'"):
        hitboxes_overlap(bad, bad)
    with pytest.raises(TypeError, match="unknown shape kind 'Triangle'"):
        place_hitbox(bad, 0.0, 0.0)
    with pytest.raises(TypeError, match="unknown shape kind 'Triangle'"):
        grow_hitbox(bad, 1.0)


def shape_from_json(raw: dict[str, object]) -> Shape:
    """Return the Circle or Box a tuning file's hitbox entry describes."""
    kind: object = raw["shape"]
    if kind == "circle":
        return Circle(
            float(cast(float, raw["cx"])),
            float(cast(float, raw["cy"])),
            float(cast(float, raw["r"])),
        )
    assert kind == "box", (
        f"unknown shape '{kind}' in a tuning file: add its table and its case here"
    )
    return Box(
        float(cast(float, raw["cx"])),
        float(cast(float, raw["cy"])),
        float(cast(float, raw["w"])),
        float(cast(float, raw["h"])),
    )


@dataclass(frozen=True, slots=True)
class VariantCase:
    """One variant of one drifter type, as its tuning file states it."""

    drifter_type: DrifterType
    variant: str | None
    """None: the type has no tuning file."""

    tuning: DrifterTuning | None
    shapes: tuple[Shape, ...]


def load_variant_cases() -> list[VariantCase]:
    """Return one case per variant of every drifter type, from `game/tuning/drifters/`."""
    cases: list[VariantCase] = []
    for drifter_type in DrifterType:
        path: Path = DRIFTER_TUNING_DIR / f"{drifter_type.value}.json"
        if not path.is_file():
            cases.append(VariantCase(drifter_type, None, None, ()))
            continue
        data: dict[str, object] = json.loads(path.read_text())
        raw_variants: dict[str, dict[str, object]] = cast(
            dict[str, dict[str, object]], data["variants"]
        )
        variants: dict[str, VariantTuning] = {}
        shapes_by_variant: dict[str, tuple[Shape, ...]] = {}
        for name, raw in raw_variants.items():
            shapes: tuple[Shape, ...] = tuple(
                shape_from_json(s) for s in cast(list[dict[str, object]], raw["hitbox"])
            )
            shapes_by_variant[name] = shapes
            variants[name] = VariantTuning(
                width=float(cast(float, raw["width"])),
                height=float(cast(float, raw["height"])),
                hitbox=shapes,
                extra=(
                    SatelliteVariantExtra(angle_degrees=float(cast(float, raw["angle_degrees"])))
                    if "angle_degrees" in raw
                    else None
                ),
            )
        tuning: DrifterTuning = DrifterTuning(
            drifters={
                drifter_type: DrifterTypeTuning(
                    variants=variants,
                    default_variant=str(data["default_variant"]),
                    speed_ratio=float(cast(float, data["speed_ratio"])),
                    entry_warning_ticks=int(cast(int, data["entry_warning_ticks"])),
                )
            },
            switches=PlaytestSwitches(),
        )
        cases.extend(
            VariantCase(drifter_type, name, tuning, shapes_by_variant[name]) for name in variants
        )
    return cases


VARIANT_CASES: list[VariantCase] = load_variant_cases()

DIRECTIONS: dict[str, tuple[int, int]] = {
    "from the left": (1, 0),
    "from the right": (-1, 0),
    "from above": (0, 1),
    "from below": (0, -1),
}
"""Where the drifter comes from, as the unit step from the drifter toward the ship."""


def touching_distance(shapes: tuple[Shape, ...], toward: tuple[int, int]) -> tuple[float, bool]:
    """Return how far from the ship's center a drifter's center is when it first touches.

    The drifter sits on the ship's center line and comes from the side `toward` points away
    from. The number comes from the shapes' own sizes: edge sums for two boxes, radius plus
    half-size for a circle met on an axis. A circle met off its axis uses the Pythagorean gap,
    and the flag is False (the number is not exact). A shape the line never meets is skipped.
    """
    ship: Ship = spawn()
    on_x: bool = toward[0] != 0
    sign: int = toward[0] + toward[1]
    distances: list[tuple[float, bool]] = []
    for ship_shape in ship_hitbox(ship):
        assert isinstance(ship_shape, Box)
        s_along: float = ship_shape.cx if on_x else ship_shape.cy
        s_cross: float = ship_shape.cy if on_x else ship_shape.cx
        s_half_along: float = (ship_shape.w if on_x else ship_shape.h) / 2
        s_half_cross: float = (ship_shape.h if on_x else ship_shape.w) / 2
        center_along: float = ship.x if on_x else ship.y
        center_cross: float = ship.y if on_x else ship.x
        for shape in shapes:
            o_along: float = shape.cx if on_x else shape.cy
            o_cross: float = shape.cy if on_x else shape.cx
            cross_gap: float = abs(center_cross + o_cross - s_cross)
            base: float = (center_along - s_along) * sign + s_half_along + o_along * sign
            if isinstance(shape, Box):
                half_cross: float = (shape.h if on_x else shape.w) / 2
                half_along: float = (shape.w if on_x else shape.h) / 2
                if cross_gap < half_cross + s_half_cross:
                    distances.append((base + half_along, True))
            elif cross_gap <= s_half_cross:
                distances.append((base + shape.r, True))
            else:
                corner_gap: float = cross_gap - s_half_cross
                if corner_gap < shape.r:
                    distances.append((base + math.sqrt(shape.r**2 - corner_gap**2), False))
    assert distances, "the ship's center line never meets this hitbox"
    first: float = max(d for d, _ in distances)
    exact: bool = all(is_exact for d, is_exact in distances if d > first - 1e-6)
    return first, exact


def drifter_at(case: VariantCase, x: float, y: float) -> Drifter:
    """Spawn the case's drifter at level 1 with its center at (x, y), in WARNING."""
    assert case.tuning is not None
    return spawn_drifter(
        Placement(case.drifter_type, x=x, y=y, variant=case.variant), 1, case.tuning
    )


def activate(drifter: Drifter) -> Drifter:
    """Run `drifter` through its warning, and return it on its first ACTIVE state."""
    ctx: TickContext = TickContext(ship=spawn())
    ticks: int = 0
    while drifter.phase is Phase.WARNING:
        drifter = drifter.update(ctx)
        ticks += 1
        assert ticks <= drifter.warning_ticks
    assert drifter.phase is Phase.ACTIVE
    return drifter


@pytest.mark.parametrize(
    "case",
    VARIANT_CASES,
    ids=[f"{c.drifter_type.value}-{c.variant}" for c in VARIANT_CASES],
)
def test_ship_meets_every_variant_at_its_own_touching_distance(case: VariantCase) -> None:
    assert case.variant is not None, f"no tuning file for '{case.drifter_type.value}'"
    ship: Hitbox = ship_hitbox(spawn())
    # Centered on the ship: overlap once ACTIVE, none in WARNING, whatever the tick.
    waiting: Drifter = drifter_at(case, SPAWN_X, SPAWN_Y)
    ctx: TickContext = TickContext(ship=spawn())
    while waiting.phase is Phase.WARNING:
        assert not overlap_both_ways(waiting.current_hitbox(), ship)
        waiting = waiting.update(ctx)
    assert waiting.phase is Phase.ACTIVE
    assert waiting.current_hitbox() == place_hitbox(case.shapes, SPAWN_X, SPAWN_Y)
    assert overlap_both_ways(waiting.current_hitbox(), ship)
    for name, toward in DIRECTIONS.items():
        distance, exact = touching_distance(case.shapes, toward)
        slack: float = 0.0 if exact else 1e-9
        assert distance > 0, name
        for gap, expect in ((distance + slack, False), (distance - 0.5, True)):
            x: float = SPAWN_X - toward[0] * gap
            y: float = SPAWN_Y - toward[1] * gap
            warning: Drifter = drifter_at(case, x, y)
            assert warning.phase is Phase.WARNING
            assert not overlap_both_ways(warning.current_hitbox(), ship), (name, gap)
            active: Drifter = activate(warning)
            assert (active.x, active.y) == (x, y)
            assert overlap_both_ways(active.current_hitbox(), ship) is expect, (name, gap)


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
