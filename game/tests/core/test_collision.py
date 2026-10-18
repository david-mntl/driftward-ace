"""Hitbox overlap tables, collision invariants, the shape guards and the ship's hitbox tests.

Contract: docs/contracts/systems/drifters.md, Rules, Collision and Chain lightning;
docs/contracts/systems/ship.md, Rules, Hitbox. Tasks: docs/contracts/DRA-29/tasks/DRA-29-07-qa-
engineer.md (the two ship tests at the end), docs/contracts/DRA-39/tasks/DRA-39-05-qa-engineer.md
(circle and box tables, guards) and docs/contracts/DRA-47/tasks/DRA-47-07-qa-engineer.md (the line
tables, the chain lightning ship cases) and docs/contracts/DRA-56/tasks/DRA-56-03-qa-engineer.md
(the fireball ship cases, the tail alone).

Every expected number is exact in binary (whole numbers, halves, sixteenths, 3-4-5 triangles) or
comes from the GDD values below or from `game/tuning/drifters/*.json`. The ship-against-every-
variant cases read those files, so a new drifter or variant is covered with no new test code.
"""

import json
import math
import typing
from collections.abc import Callable
from dataclasses import dataclass, replace
from itertools import combinations_with_replacement
from pathlib import Path
from typing import cast

import pytest

from core import collision
from core.collision import (
    Box,
    Circle,
    Hitbox,
    Line,
    Shape,
    grow_hitbox,
    hitboxes_overlap,
    place_hitbox,
)
from core.drifters.base import Drifter, DrifterType, Phase, TickContext
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightning,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
    chain_hitbox,
    layout_size,
)
from core.drifters.fireball import FireballTypeExtra, fireball_hitbox
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

# Line and line. Line(ax, ay, bx, by, thickness): a capsule, half the thickness on every side of
# the segment AB, round ends. A is Line(0, 0, 10, 0, 4) (half thickness 2) unless it says otherwise.
LINE_LINE: tuple[Case, ...] = (
    Case("parallel edges touching, below", Line(0, 0, 10, 0, 4), Line(0, 4, 10, 4, 4), False),
    Case("parallel edges touching, above", Line(0, 0, 10, 0, 4), Line(0, -4, 10, -4, 4), False),
    Case("parallel edges touching, vertical", Line(0, 0, 0, 10, 4), Line(4, 0, 4, 10, 4), False),
    Case(
        "parallel edges touching, shifted along", Line(0, 0, 10, 0, 4), Line(6, 4, 16, 4, 4), False
    ),
    Case(
        "parallel edges touching, unequal thickness",
        Line(0, 0, 10, 0, 4),
        Line(0, 3, 10, 3, 2),
        False,
    ),
    Case(
        "parallel edges hair inside",
        Line(0, 0, 10, 0, 4),
        Line(0, 4 - HAIR, 10, 4 - HAIR, 4),
        True,
    ),
    Case(
        "parallel edges hair inside, unequal thickness",
        Line(0, 0, 10, 0, 4),
        Line(0, 3 - HAIR, 10, 3 - HAIR, 2),
        True,
    ),
    Case(
        "parallel edges hair outside",
        Line(0, 0, 10, 0, 4),
        Line(0, 4 + HAIR, 10, 4 + HAIR, 4),
        False,
    ),
    Case(
        "parallel edges touching on a 3-4-5 slope",
        Line(0, 0, 30, 40, 10),
        Line(8, -6, 38, 34, 10),
        False,
    ),
    Case(
        "parallel edges touching on a 3-4-5 slope, shifted along",
        Line(0, 0, 30, 40, 10),
        Line(23, 14, 53, 54, 10),
        False,
    ),
    Case(
        "parallel edges hair inside on a 3-4-5 slope, wider by two hairs",
        Line(0, 0, 30, 40, 10 + 2 * HAIR),
        Line(23, 14, 53, 54, 10),
        True,
    ),
    Case(
        "parallel edges hair outside on a 3-4-5 slope, thinner by two hairs",
        Line(0, 0, 30, 40, 10 - 2 * HAIR),
        Line(23, 14, 53, 54, 10),
        False,
    ),
    Case("side touch: end meets the side", Line(0, 0, 10, 0, 4), Line(5, 3, 5, 13, 2), False),
    Case(
        "side hair inside: end meets the side",
        Line(0, 0, 10, 0, 4),
        Line(5, 3 - HAIR, 5, 13, 2),
        True,
    ),
    Case(
        "side hair outside: end meets the side",
        Line(0, 0, 10, 0, 4),
        Line(5, 3 + HAIR, 5, 13, 2),
        False,
    ),
    Case("round-end touch on the axis", Line(0, 0, 10, 0, 4), Line(14, 0, 24, 0, 4), False),
    Case(
        "round-end touch on the axis, other end",
        Line(0, 0, 10, 0, 4),
        Line(-14, 0, -4, 0, 4),
        False,
    ),
    Case(
        "round-end touch on the axis, vertical", Line(0, 0, 0, 10, 4), Line(0, 14, 0, 24, 4), False
    ),
    Case(
        "round-end touch on the axis, unequal thickness",
        Line(0, 0, 10, 0, 4),
        Line(13, 0, 23, 0, 2),
        False,
    ),
    Case(
        "round-end hair inside on the axis",
        Line(0, 0, 10, 0, 4),
        Line(14 - HAIR, 0, 24, 0, 4),
        True,
    ),
    Case(
        "round-end hair outside on the axis",
        Line(0, 0, 10, 0, 4),
        Line(14 + HAIR, 0, 24, 0, 4),
        False,
    ),
    Case(
        "round-end touch at a 3-4-5 angle",
        Line(0, 0, 10, 0, 10),
        Line(16, 8, 26, 8, 10),
        False,
    ),
    Case(
        "round-end touch at a 3-4-5 angle, other end",
        Line(0, 0, 10, 0, 10),
        Line(-6, -8, -16, -8, 10),
        False,
    ),
    Case(
        "round-end hair inside at a 3-4-5 angle",
        Line(0, 0, 10, 0, 10),
        Line(16 - HAIR, 8, 26, 8, 10),
        True,
    ),
    Case(
        "round-end hair outside at a 3-4-5 angle",
        Line(0, 0, 10, 0, 10),
        Line(16 + HAIR, 8, 26, 8, 10),
        False,
    ),
    Case("crossing, plus sign", Line(-10, 0, 10, 0, 2), Line(0, -10, 0, 10, 2), True),
    Case("crossing, x shape", Line(0, 0, 10, 10, 2), Line(0, 10, 10, 0, 2), True),
    Case(
        "crossing, as thin as a hair",
        Line(-10, 0, 10, 0, HAIR),
        Line(0, -10, 0, 10, HAIR),
        True,
    ),
    Case("T junction: end on the other's axis", Line(0, 0, 10, 0, 2), Line(5, 0, 5, 10, 2), True),
    Case("end on end", Line(0, 0, 10, 0, 2), Line(10, 0, 20, 0, 2), True),
    Case("meet only when extended", Line(0, 0, 10, 0, 2), Line(20, -10, 20, 10, 2), False),
    Case("meet only when extended, slanted", Line(0, 0, 10, 0, 2), Line(12, -4, 14, -8, 2), False),
    Case("one inside the other", Line(0, 0, 20, 0, 10), Line(5, 0, 10, 0, 2), True),
    Case("inside, off the axis", Line(0, 0, 20, 0, 10), Line(5, 2, 10, 2, 2), True),
    Case("identical", Line(3, 4, 13, 4, 4), Line(3, 4, 13, 4, 4), True),
    Case("identical, ends swapped", Line(13, 4, 3, 4, 4), Line(3, 4, 13, 4, 4), True),
    Case("both ends on one point: touch", Line(0, 0, 0, 0, 10), Line(10, 0, 20, 0, 10), False),
    Case(
        "both ends on one point: hair inside",
        Line(0, 0, 0, 0, 10),
        Line(10 - HAIR, 0, 20, 0, 10),
        True,
    ),
    Case("two points: touch", Line(0, 0, 0, 0, 10), Line(10, 0, 10, 0, 10), False),
    Case(
        "two points: hair inside", Line(0, 0, 0, 0, 10), Line(10 - HAIR, 0, 10 - HAIR, 0, 10), True
    ),
    Case("two points: identical", Line(3, 4, 3, 4, 10), Line(3, 4, 3, 4, 10), True),
    Case("far apart", Line(0, 0, 10, 0, 4), Line(100, 100, 110, 100, 4), False),
    Case("far apart on one axis", Line(0, 0, 10, 0, 4), Line(0, 1000, 10, 1000, 4), False),
)

# Circle and line. A is the circle, B the line. The line is Line(0, 0, 10, 0, 4) (half thickness 2)
# unless it says otherwise.
CIRCLE_LINE: tuple[Case, ...] = (
    Case("side touch, above", Circle(5, 5, 3), Line(0, 0, 10, 0, 4), False),
    Case("side touch, below", Circle(5, -5, 3), Line(0, 0, 10, 0, 4), False),
    Case("side touch, off the middle", Circle(8, 5, 3), Line(0, 0, 10, 0, 4), False),
    Case("side touch, vertical line", Circle(5, 5, 3), Line(0, 0, 0, 10, 4), False),
    Case("side touch, unequal sizes", Circle(5, 4.5, 2.5), Line(0, 0, 10, 0, 4), False),
    Case("side hair inside, above", Circle(5, 5 - HAIR, 3), Line(0, 0, 10, 0, 4), True),
    Case("side hair inside, below", Circle(5, -5 + HAIR, 3), Line(0, 0, 10, 0, 4), True),
    Case("side hair outside", Circle(5, 5 + HAIR, 3), Line(0, 0, 10, 0, 4), False),
    Case("round-end touch on the axis", Circle(15, 0, 3), Line(0, 0, 10, 0, 4), False),
    Case("round-end touch on the axis, other end", Circle(-5, 0, 3), Line(0, 0, 10, 0, 4), False),
    Case("round-end touch on the axis, vertical", Circle(0, 15, 3), Line(0, 0, 0, 10, 4), False),
    Case("round-end hair inside on the axis", Circle(15 - HAIR, 0, 3), Line(0, 0, 10, 0, 4), True),
    Case(
        "round-end hair outside on the axis", Circle(15 + HAIR, 0, 3), Line(0, 0, 10, 0, 4), False
    ),
    Case("round-end touch at a 3-4-5 angle", Circle(13, 4, 3), Line(0, 0, 10, 0, 4), False),
    Case(
        "round-end touch at a 3-4-5 angle, other end",
        Circle(-3, -4, 3),
        Line(0, 0, 10, 0, 4),
        False,
    ),
    Case("round-end touch at a 3-4-5 angle, wide", Circle(16, 8, 5), Line(0, 0, 10, 0, 10), False),
    Case(
        "round-end hair inside at a 3-4-5 angle",
        Circle(13 - HAIR, 4, 3),
        Line(0, 0, 10, 0, 4),
        True,
    ),
    Case(
        "round-end hair outside at a 3-4-5 angle",
        Circle(13 + HAIR, 4, 3),
        Line(0, 0, 10, 0, 4),
        False,
    ),
    Case("slanted line, touch", Circle(23, 14, 5), Line(0, 0, 30, 40, 10), False),
    Case("slanted line, touch on the other side", Circle(7, 26, 5), Line(0, 0, 30, 40, 10), False),
    Case("slanted line, hair inside", Circle(23 - HAIR, 14, 5), Line(0, 0, 30, 40, 10), True),
    Case("slanted line, hair outside", Circle(23 + HAIR, 14, 5), Line(0, 0, 30, 40, 10), False),
    Case("past the end on the axis: the line stops", Circle(14, 0, 1), Line(0, 0, 10, 0, 4), False),
    Case("past the end, off the axis", Circle(20, 1, 1), Line(0, 0, 10, 0, 4), False),
    Case("center in the round end", Circle(11, 0, 1), Line(0, 0, 10, 0, 4), True),
    Case("center on the line's end", Circle(10, 0, 1), Line(0, 0, 10, 0, 4), True),
    Case("center on the line", Circle(5, 0, 1), Line(0, 0, 10, 0, 4), True),
    Case("crossing: circle over the line", Circle(5, 2, 3), Line(0, 0, 10, 0, 4), True),
    Case("circle inside the line's width", Circle(5, 1, 1), Line(0, 0, 10, 0, 10), True),
    Case("line inside the circle", Circle(5, 0, 20), Line(0, 0, 10, 0, 2), True),
    Case(
        "both ends on one point: same center and size", Circle(3, 4, 5), Line(3, 4, 3, 4, 10), True
    ),
    Case("both ends on one point: touch", Circle(0, 0, 5), Line(10, 0, 10, 0, 10), False),
    Case(
        "both ends on one point: hair inside",
        Circle(0, 0, 5),
        Line(10 - HAIR, 0, 10 - HAIR, 0, 10),
        True,
    ),
    Case("both ends on one point: 3-4-5 touch", Circle(0, 0, 5), Line(6, 8, 6, 8, 10), False),
    Case("far apart", Circle(100, 100, 3), Line(0, 0, 10, 0, 4), False),
    Case("far apart on one axis", Circle(5, 1000, 3), Line(0, 0, 10, 0, 4), False),
)

# Box and line. A is the box, B the line. The box is Box(0, 0, 10, 10) (edges at -5 and 5) unless it
# says otherwise. Lines are 2 thick (half thickness 1) unless they say otherwise.
BOX_LINE: tuple[Case, ...] = (
    Case("side touch: end above", Box(0, 0, 10, 10), Line(0, -20, 0, -6, 2), False),
    Case("side touch: end below", Box(0, 0, 10, 10), Line(0, 20, 0, 6, 2), False),
    Case("side touch: end left", Box(0, 0, 10, 10), Line(-20, 0, -6, 0, 2), False),
    Case("side touch: end right", Box(0, 0, 10, 10), Line(20, 0, 6, 0, 2), False),
    Case("side hair inside: end above", Box(0, 0, 10, 10), Line(0, -20, 0, -6 + HAIR, 2), True),
    Case("side hair inside: end left", Box(0, 0, 10, 10), Line(-20, 0, -6 + HAIR, 0, 2), True),
    Case("side hair outside: end above", Box(0, 0, 10, 10), Line(0, -20, 0, -6 - HAIR, 2), False),
    Case(
        "parallel edges touching, along the top", Box(0, 0, 10, 10), Line(-3, -6, 3, -6, 2), False
    ),
    Case(
        "parallel edges touching, along the bottom", Box(0, 0, 10, 10), Line(-3, 6, 3, 6, 2), False
    ),
    Case(
        "parallel edges touching, along the left", Box(0, 0, 10, 10), Line(-6, -3, -6, 3, 2), False
    ),
    Case(
        "parallel edges touching, along the right", Box(0, 0, 10, 10), Line(6, -3, 6, 3, 2), False
    ),
    Case(
        "parallel edges touching, longer than the side",
        Box(0, 0, 10, 10),
        Line(-20, -6, 20, -6, 2),
        False,
    ),
    Case(
        "parallel edges touching, shifted along", Box(0, 0, 10, 10), Line(2, -6, 12, -6, 2), False
    ),
    Case(
        "parallel edges hair inside, along the top",
        Box(0, 0, 10, 10),
        Line(-3, -6 + HAIR, 3, -6 + HAIR, 2),
        True,
    ),
    Case(
        "parallel edges hair inside, along the right",
        Box(0, 0, 10, 10),
        Line(6 - HAIR, -3, 6 - HAIR, 3, 2),
        True,
    ),
    Case(
        "parallel edges hair outside, along the top",
        Box(0, 0, 10, 10),
        Line(-3, -6 - HAIR, 3, -6 - HAIR, 2),
        False,
    ),
    Case(
        "round-end touch on a corner at a 3-4-5 angle",
        Box(0, 0, 10, 10),
        Line(8, 9, 20, 30, 10),
        False,
    ),
    Case(
        "round-end touch on a corner, opposite corner",
        Box(0, 0, 10, 10),
        Line(-8, -9, -20, -30, 10),
        False,
    ),
    Case(
        "round-end touch on a corner, other diagonal",
        Box(0, 0, 10, 10),
        Line(8, -9, 20, -30, 10),
        False,
    ),
    Case(
        "round-end touch on a corner, steep side",
        Box(0, 0, 10, 10),
        Line(-9, 8, -30, 20, 10),
        False,
    ),
    Case(
        "round-end hair inside on a corner", Box(0, 0, 10, 10), Line(8 - HAIR, 9, 20, 30, 10), True
    ),
    Case(
        "round-end hair outside on a corner",
        Box(0, 0, 10, 10),
        Line(8 + HAIR, 9, 20, 30, 10),
        False,
    ),
    Case("crossing, both ends outside", Box(0, 0, 10, 10), Line(-20, 0, 20, 0, 2), True),
    Case("crossing, both ends outside, vertical", Box(0, 0, 10, 10), Line(0, -20, 0, 20, 2), True),
    Case(
        "crossing, both ends outside, off the middle",
        Box(0, 0, 10, 10),
        Line(-20, 3, 20, 3, 2),
        True,
    ),
    Case(
        "crossing, both ends outside, diagonal", Box(0, 0, 10, 10), Line(-10, -10, 10, 10, 2), True
    ),
    Case("crossing through one corner only", Box(0, 0, 10, 10), Line(0, 10, 10, 0, 2), True),
    Case("diagonal cutting the corner", Box(0, 0, 10, 10), Line(0, 11, 11, 0, 2), True),
    Case("diagonal clear of the corner", Box(0, 0, 10, 10), Line(0, 12, 12, 0, 2), False),
    Case("segment along an edge", Box(0, 0, 10, 10), Line(-3, -5, 3, -5, 2), True),
    Case("end on an edge", Box(0, 0, 10, 10), Line(5, 0, 20, 0, 2), True),
    Case("end on a corner", Box(0, 0, 10, 10), Line(5, 5, 20, 20, 2), True),
    Case("meets only when extended", Box(0, 0, 10, 10), Line(10, 0, 20, 0, 2), False),
    Case("beside the box, same axis", Box(0, 0, 10, 10), Line(10, -20, 10, 20, 2), False),
    Case("one end inside the box", Box(0, 0, 10, 10), Line(0, 0, 20, 0, 2), True),
    Case("line inside the box", Box(0, 0, 10, 10), Line(-2, -2, 2, 2, 2), True),
    Case("box inside the line's width", Box(0, 0, 10, 10), Line(-20, 0, 20, 0, 30), True),
    Case("box inside a round end", Box(0, 0, 10, 10), Line(0, 0, 0, 0, 40), True),
    Case("both ends on one point: touch", Box(0, 0, 10, 10), Line(6, 0, 6, 0, 2), False),
    Case(
        "both ends on one point: hair inside",
        Box(0, 0, 10, 10),
        Line(6 - HAIR, 0, 6 - HAIR, 0, 2),
        True,
    ),
    Case(
        "both ends on one point: 3-4-5 corner touch", Box(0, 0, 10, 10), Line(8, 9, 8, 9, 10), False
    ),
    Case(
        "both ends on one point: 3-4-5 corner hair inside",
        Box(0, 0, 10, 10),
        Line(8 - HAIR, 9, 8 - HAIR, 9, 10),
        True,
    ),
    Case("both ends on one point: inside the box", Box(0, 0, 10, 10), Line(1, 1, 1, 1, 2), True),
    Case("both ends on one point: same center", Box(3, 4, 2, 2), Line(3, 4, 3, 4, 2), True),
    Case("far apart", Box(0, 0, 10, 10), Line(100, 100, 110, 100, 2), False),
    Case("far apart on one axis", Box(0, 0, 10, 10), Line(0, 1000, 10, 1000, 2), False),
)

TABLES: dict[frozenset[type], tuple[Case, ...]] = {
    frozenset({Circle}): CIRCLE_CIRCLE,
    frozenset({Box}): BOX_BOX,
    frozenset({Circle, Box}): CIRCLE_BOX,
    frozenset({Line}): LINE_LINE,
    frozenset({Circle, Line}): CIRCLE_LINE,
    frozenset({Box, Line}): BOX_LINE,
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
    if isinstance(shape, Line):
        return Line(shape.ax + dx, shape.ay + dy, shape.bx + dx, shape.by + dy, shape.thickness)
    return Box(shape.cx + dx, shape.cy + dy, shape.w, shape.h)


def anchor(shape: Shape) -> tuple[float, float]:
    """Return a point of `shape`: its center, or a line's end A."""
    if isinstance(shape, Line):
        return shape.ax, shape.ay
    return shape.cx, shape.cy


def point_line(circle: Circle) -> Line:
    """Return the line whose two ends are the circle's center, as thick as the circle is wide."""
    return Line(circle.cx, circle.cy, circle.cx, circle.cy, 2 * circle.r)


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
        Line(-5000, -5000, 5000, -5000, 2),
        Circle(anchor(case.a)[0] + 3000, anchor(case.a)[1], 2),
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


def test_growing_a_line_adds_twice_the_margin_to_its_thickness_and_keeps_its_ends() -> None:
    line: Line = Line(1, 2, 3.5, -4, 6)
    for margin in MARGINS:
        assert grow_hitbox((line,), margin) == (Line(1, 2, 3.5, -4, 6 + 2 * margin),)
    mixed: Hitbox = (Circle(0, 0, 3), line, Box(5, 5, 4, 4))
    assert grow_hitbox(mixed, 0.5) == (
        Circle(0, 0, 3.5),
        Line(1, 2, 3.5, -4, 7),
        Box(5, 5, 5, 5),
    )
    # The growth reaches both sides and both ends: a hair inside only after growing.
    near: Hitbox = (Circle(15 + HAIR, 0, 3),)
    flat: Hitbox = (Line(0, 0, 10, 0, 4),)
    assert not overlap_both_ways(flat, near)
    assert overlap_both_ways(grow_hitbox(flat, 2 * HAIR), near)
    assert overlap_both_ways(flat, grow_hitbox(near, 2 * HAIR))


@pytest.mark.parametrize(("case_id", "case"), ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_a_line_with_both_ends_on_one_point_acts_as_a_circle(case_id: str, case: Case) -> None:
    a: Shape = point_line(case.a) if isinstance(case.a, Circle) else case.a
    b: Shape = point_line(case.b) if isinstance(case.b, Circle) else case.b
    if (a, b) == (case.a, case.b):
        return
    assert overlap_both_ways((a,), (b,)) is case.overlaps, case_id
    assert overlap_both_ways((a,), (case.b,)) is case.overlaps, case_id
    assert overlap_both_ways((case.a,), (b,)) is case.overlaps, case_id


def test_every_shape_kind_and_every_pair_of_kinds_has_a_table() -> None:
    kinds: set[type] = set(typing.get_args(collision.Shape))
    assert kinds == {Circle, Box, Line}, "a new shape kind needs its tables and its test updates"
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
        lambda bad: hitboxes_overlap(bad, (Line(0, 0, 5, 5, 2),)),
        lambda bad: hitboxes_overlap((Line(0, 0, 5, 5, 2),), bad),
        lambda bad: hitboxes_overlap(bad, ()),
        lambda bad: hitboxes_overlap((), bad),
        lambda bad: place_hitbox(bad, 1.0, 2.0),
        lambda bad: grow_hitbox(bad, 1.0),
    ],
    ids=[
        "overlap-first",
        "overlap-second",
        "overlap-first-vs-line",
        "overlap-second-vs-line",
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
            cast(Hitbox, (Line(0, 0, 5, 5, 2), bad_shape)),
            cast(Hitbox, (bad_shape, Line(0, 0, 5, 5, 2))),
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


def shape_from_json(raw: dict[str, object]) -> Circle | Box:
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
class ChainFacts:
    """One chain lightning variant as its tuning file states it, in px, before invert."""

    nodes: tuple[tuple[float, float], ...]
    arcs: tuple[tuple[int, int], ...]
    mirror: InvertMirror
    node_size: float
    arc_width: float


@dataclass(frozen=True, slots=True)
class VariantCase:
    """One variant of one drifter type, as its tuning file states it."""

    drifter_type: DrifterType
    variant: str | None
    """None: the type has no tuning file."""

    tuning: DrifterTuning | None
    shapes: tuple[Circle | Box, ...]
    """The hitbox the file lists. Empty for the chain lightning, which has `chain` instead."""

    invert: bool = False
    chain: ChainFacts | None = None
    """Set for a chain lightning variant: its hitbox is built from nodes and arcs."""


def chain_layout(raw: dict[str, object], spacing: float) -> ChainLayout:
    """Return a chain lightning variant's layout in px: the file's node units x `node_spacing`."""
    return ChainLayout(
        nodes=tuple(
            (float(x) * spacing, float(y) * spacing)
            for x, y in cast(list[list[float]], raw["nodes"])
        ),
        arcs=tuple((int(a), int(b)) for a, b in cast(list[list[int]], raw["arcs"])),
        invert_mirror=InvertMirror(str(raw["invert_mirror"])),
    )


def load_chain_cases(data: dict[str, object]) -> list[VariantCase]:
    """Return one case per variant and `invert` value of the chain lightning's tuning file.

    The records are built the way `app.tuning` builds them (contract, Tuning files), here.
    """
    spacing: float = float(cast(float, data["node_spacing"]))
    node_size: float = float(cast(float, data["node_size"]))
    arc_width: float = float(cast(float, data["arc_width"]))
    raw_variants: dict[str, dict[str, object]] = cast(
        dict[str, dict[str, object]], data["variants"]
    )
    layouts: dict[str, ChainLayout] = {
        name: chain_layout(raw, spacing) for name, raw in raw_variants.items()
    }
    variants: dict[str, VariantTuning] = {}
    for name, layout in layouts.items():
        width, height = layout_size(layout.nodes, node_size)
        variants[name] = VariantTuning(
            width=width,
            height=height,
            hitbox=chain_hitbox(layout.nodes, layout.arcs, node_size, arc_width),
            extra=ChainLightningVariantExtra(layout=layout),
        )
    type_extra: ChainLightningTypeExtra = ChainLightningTypeExtra(
        node_size=node_size,
        arc_width=arc_width,
        charge_ticks=int(cast(int, data["charge_ticks"])),
        fire_ticks=int(cast(int, data["fire_ticks"])),
        charge_rays=int(cast(int, data["charge_rays"])),
        ray_length=float(cast(float, data["ray_length"])),
        ray_width=float(cast(float, data["ray_width"])),
        warning_layout=layouts[str(data["entry_warning_icon"])],
    )
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.CHAIN_LIGHTNING: DrifterTypeTuning(
                variants=variants,
                default_variant=str(data["default_variant"]),
                speed_ratio=float(cast(float, data["speed_ratio"])),
                entry_warning_ticks=int(cast(int, data["entry_warning_ticks"])),
                extra=type_extra,
            )
        },
        switches=PlaytestSwitches(),
    )
    return [
        VariantCase(
            DrifterType.CHAIN_LIGHTNING,
            name,
            tuning,
            (),
            invert=invert,
            chain=ChainFacts(
                nodes=layout.nodes,
                arcs=layout.arcs,
                mirror=layout.invert_mirror,
                node_size=node_size,
                arc_width=arc_width,
            ),
        )
        for name, layout in layouts.items()
        for invert in (False, True)
    ]


def circles_and_boxes(hitbox: Hitbox) -> tuple[Circle | Box, ...]:
    """Return `hitbox` with every shape narrowed to a circle or a box (a line fails the test)."""
    narrowed: list[Circle | Box] = []
    for shape in hitbox:
        assert isinstance(shape, Circle | Box), f"unexpected shape {shape} in a fireball hitbox"
        narrowed.append(shape)
    return tuple(narrowed)


def load_fireball_cases(data: dict[str, object]) -> list[VariantCase]:
    """Return one case per variant and `invert` value of the fireball's tuning file.

    The records are built the way `app.tuning` builds them (contract, Tuning files), here: each
    variant's hitbox is `fireball_hitbox` of its `head_width` and the type's `tail_ratio` and
    `angle_degrees`, un-inverted. The case's shapes are the same call with the case's `invert`.
    """
    angle: float = float(cast(float, data["angle_degrees"]))
    ratio: float = float(cast(float, data["tail_ratio"]))
    heads: dict[str, float] = {
        name: float(cast(float, raw["head_width"]))
        for name, raw in cast(dict[str, dict[str, object]], data["variants"]).items()
    }
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.FIREBALL: DrifterTypeTuning(
                variants={
                    name: VariantTuning(
                        width=head,
                        height=head,
                        hitbox=fireball_hitbox(head, ratio, angle, False),
                        extra=None,
                    )
                    for name, head in heads.items()
                },
                default_variant=str(data["default_variant"]),
                speed_ratio=float(cast(float, data["speed_ratio"])),
                entry_warning_ticks=int(cast(int, data["entry_warning_ticks"])),
                extra=FireballTypeExtra(angle_degrees=angle, tail_ratio=ratio),
            )
        },
        switches=PlaytestSwitches(),
    )
    return [
        VariantCase(
            DrifterType.FIREBALL,
            name,
            tuning,
            circles_and_boxes(fireball_hitbox(head, ratio, angle, invert)),
            invert=invert,
        )
        for name, head in heads.items()
        for invert in (False, True)
    ]


def load_variant_cases() -> list[VariantCase]:
    """Return one case per variant of every drifter type, from `game/tuning/drifters/`.

    The chain lightning and the fireball get one case per variant and `invert` value.
    """
    cases: list[VariantCase] = []
    for drifter_type in DrifterType:
        path: Path = DRIFTER_TUNING_DIR / f"{drifter_type.value}.json"
        if not path.is_file():
            cases.append(VariantCase(drifter_type, None, None, ()))
            continue
        data: dict[str, object] = json.loads(path.read_text())
        if drifter_type is DrifterType.CHAIN_LIGHTNING:
            cases.extend(load_chain_cases(data))
            continue
        if drifter_type is DrifterType.FIREBALL:
            cases.extend(load_fireball_cases(data))
            continue
        raw_variants: dict[str, dict[str, object]] = cast(
            dict[str, dict[str, object]], data["variants"]
        )
        variants: dict[str, VariantTuning] = {}
        shapes_by_variant: dict[str, tuple[Circle | Box, ...]] = {}
        for name, raw in raw_variants.items():
            shapes: tuple[Circle | Box, ...] = tuple(
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

SHAPE_CASES: list[VariantCase] = [c for c in VARIANT_CASES if c.chain is None]
"""Types whose tuning file lists a hitbox, and any type with no file (it fails by name)."""

CHAIN_CASES: list[VariantCase] = [c for c in VARIANT_CASES if c.chain is not None]
"""The chain lightning, per variant and `invert` value."""

FIREBALL_CASES: list[VariantCase] = [
    c for c in VARIANT_CASES if c.drifter_type is DrifterType.FIREBALL and c.variant is not None
]
"""The fireball, per variant and `invert` value. Head is `shapes[0]`, tail `shapes[1]`."""


def case_id(case: VariantCase) -> str:
    """Return the test id of a case: the type, the variant, and `-invert` when it is set."""
    return f"{case.drifter_type.value}-{case.variant}" + ("-invert" if case.invert else "")


DIRECTIONS: dict[str, tuple[int, int]] = {
    "from the left": (1, 0),
    "from the right": (-1, 0),
    "from above": (0, 1),
    "from below": (0, -1),
}
"""Where the drifter comes from, as the unit step from the drifter toward the ship."""


def touching_distance(
    shapes: tuple[Circle | Box, ...], toward: tuple[int, int]
) -> tuple[float, bool]:
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
        Placement(case.drifter_type, x=x, y=y, variant=case.variant, invert=case.invert),
        1,
        case.tuning,
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


@pytest.mark.parametrize("case", SHAPE_CASES, ids=[case_id(c) for c in SHAPE_CASES])
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


CLEAR_SLACK: float = 1e-6
"""px. A clear placement is this far past touching, so float error in the layout's irrational
node positions (diagonals, the triangle) can't turn a touch into an overlap."""

INSIDE: float = 0.5
"""px. A hit placement puts the nearest firing shape this far into the ship."""


@dataclass(frozen=True, slots=True)
class Place:
    """Where the chain's center sits, and whether a firing chain overlaps the ship there."""

    name: str
    x: float
    y: float
    hit: bool


def mirrored(facts: ChainFacts, invert: bool) -> tuple[tuple[float, float], ...]:
    """Return the node offsets with `invert` applied, by the file's own `invert_mirror`."""
    if not invert:
        return facts.nodes
    if facts.mirror is InvertMirror.LEFT_RIGHT:
        return tuple((-x, y) for x, y in facts.nodes)
    assert facts.mirror is InvertMirror.TOP_BOTTOM
    return tuple((x, -y) for x, y in facts.nodes)


def chain_places(facts: ChainFacts, invert: bool) -> list[Place]:
    """Return the places that must overlap a firing chain, and the places that must not.

    Hits: the middle of each arc on the ship's center, each node on it, and each of the four sides
    with the chain's nearest edge 0.5 px into the ship. Clear: the same four sides with the nearest
    firing shape just clear of the ship's 32 x 32 square. The nearest edge is worked out from the
    node radius and half the arc width, the file's own numbers.
    """
    nodes: tuple[tuple[float, float], ...] = mirrored(facts, invert)
    places: list[Place] = []
    for index, (a, b) in enumerate(facts.arcs):
        mid_x: float = (nodes[a][0] + nodes[b][0]) / 2
        mid_y: float = (nodes[a][1] + nodes[b][1]) / 2
        places.append(Place(f"middle of arc {index}", SPAWN_X - mid_x, SPAWN_Y - mid_y, True))
    for index, (x, y) in enumerate(nodes):
        places.append(Place(f"node {index}", SPAWN_X - x, SPAWN_Y - y, True))
    # Every round part of the firing set: a node circle, and the round end of each arc.
    disks: list[tuple[float, float, float]] = [(x, y, facts.node_size / 2) for x, y in nodes]
    disks += [
        (nodes[end][0], nodes[end][1], facts.arc_width / 2) for arc in facts.arcs for end in arc
    ]
    foot_row: float = SPAWN_Y + SHIP_H / 2 - FOOT_H / 2
    left = max(disks, key=lambda d: d[0] + d[2])
    right = min(disks, key=lambda d: d[0] - d[2])
    above = max(disks, key=lambda d: d[1] + d[2])
    below = min(disks, key=lambda d: d[1] - d[2])
    for gap, hit, label in ((-INSIDE, True, "inside"), (CLEAR_SLACK, False, "clear")):
        places += [
            Place(
                f"chain left of the ship, {label}",
                SPAWN_X - SHIP_W / 2 - (left[0] + left[2]) - gap,
                foot_row - left[1],
                hit,
            ),
            Place(
                f"chain right of the ship, {label}",
                SPAWN_X + SHIP_W / 2 - (right[0] - right[2]) + gap,
                foot_row - right[1],
                hit,
            ),
            Place(
                f"chain above the ship, {label}",
                SPAWN_X - above[0],
                SPAWN_Y - SHIP_H / 2 - (above[1] + above[2]) - gap,
                hit,
            ),
            Place(
                f"chain below the ship, {label}",
                SPAWN_X - below[0],
                SPAWN_Y + SHIP_H / 2 - (below[1] - below[2]) + gap,
                hit,
            ),
        ]
    return places


def firing_set(facts: ChainFacts, invert: bool, x: float, y: float) -> Hitbox:
    """Return the placed hitbox of a chain with every node on screen: each arc, then each node."""
    nodes: tuple[tuple[float, float], ...] = mirrored(facts, invert)
    lines: Hitbox = tuple(
        Line(nodes[a][0] + x, nodes[a][1] + y, nodes[b][0] + x, nodes[b][1] + y, facts.arc_width)
        for a, b in facts.arcs
    )
    joined: set[int] = {end for arc in facts.arcs for end in arc}
    circles: Hitbox = tuple(
        Circle(nx + x, ny + y, facts.node_size / 2)
        for index, (nx, ny) in enumerate(nodes)
        if index in joined
    )
    return lines + circles


@pytest.mark.parametrize("case", CHAIN_CASES, ids=[case_id(c) for c in CHAIN_CASES])
def test_ship_meets_every_chain_lightning_variant_only_while_it_fires(case: VariantCase) -> None:
    facts: ChainFacts | None = case.chain
    assert facts is not None
    ship: Hitbox = ship_hitbox(spawn())
    ctx: TickContext = TickContext(ship=spawn())
    for place in chain_places(facts, case.invert):
        where: str = f"{place.name} at ({place.x}, {place.y})"
        # In WARNING: it touches nothing, on every state of the warning.
        waiting: Drifter = drifter_at(case, place.x, place.y)
        assert isinstance(waiting, ChainLightning)
        while waiting.phase is Phase.WARNING:
            assert not waiting.is_charging()
            assert not waiting.is_firing()
            assert waiting.current_hitbox() == (), where
            assert not overlap_both_ways(waiting.current_hitbox(), ship), where
            waiting = waiting.update(ctx)
        active: Drifter = waiting
        assert isinstance(active, ChainLightning)
        assert (active.x, active.y) == (place.x, place.y)
        # Charging: the first and last state of the charge touch nothing.
        for tick in (0, active.charge_ticks - 1):
            charging: ChainLightning = replace(active, ticks_in_phase=tick)
            assert charging.is_charging(), where
            assert not charging.is_firing(), where
            assert charging.current_hitbox() == (), where
            assert not overlap_both_ways(charging.current_hitbox(), ship), where
        # Firing: the first and last state of the fire, every node on screen.
        for tick in (active.charge_ticks, active.charge_ticks + active.fire_ticks - 1):
            firing: ChainLightning = replace(active, ticks_in_phase=tick)
            assert firing.is_firing(), where
            assert not firing.is_charging(), where
            assert all(firing.nodes_on_screen()), f"a node is off screen: {where}"
            assert firing.current_hitbox() == firing_set(facts, case.invert, place.x, place.y), (
                where
            )
            assert overlap_both_ways(firing.current_hitbox(), ship) is place.hit, where


@pytest.mark.parametrize("case", FIREBALL_CASES, ids=[case_id(c) for c in FIREBALL_CASES])
def test_ship_meets_the_fireball_tail_alone(case: VariantCase) -> None:
    assert len(case.shapes) == 2
    head, tail = case.shapes
    assert isinstance(head, Circle)
    assert isinstance(tail, Circle)
    ship: Hitbox = ship_hitbox(spawn())
    foot: Box = cast(Box, ship[1])
    foot_bottom: float = foot.cy + foot.h / 2
    # The tail trails the head up and to one side, so the tail alone can reach the ship only from
    # below, or from the side the head flies toward: the right without `invert` (the head is down
    # and to the right of the tail), the left with it.
    outer_x: float = foot.cx - foot.w / 2 if case.invert else foot.cx + foot.w / 2
    outer_sign: float = -1.0 if case.invert else 1.0
    row: float = foot_bottom - INSIDE
    # name, tail center when it overlaps, tail center when just clear
    places: tuple[tuple[str, tuple[float, float], tuple[float, float]], ...] = (
        (
            "below the foot",
            (SPAWN_X, row),
            (SPAWN_X, foot_bottom + tail.r + CLEAR_SLACK),
        ),
        (
            "beside the foot",
            (outer_x - outer_sign * INSIDE, row),
            (outer_x + outer_sign * (tail.r + CLEAR_SLACK), row),
        ),
    )
    for name, hit_at, clear_at in places:
        for (tail_x, tail_y), expect in ((hit_at, True), (clear_at, False)):
            where: str = f"{name}, tail center ({tail_x}, {tail_y})"
            x: float = tail_x - tail.cx
            y: float = tail_y - tail.cy
            active: Drifter = activate(drifter_at(case, x, y))
            assert active.current_hitbox() == place_hitbox(case.shapes, x, y), where
            head_only: Hitbox = place_hitbox((head,), x, y)
            tail_only: Hitbox = place_hitbox((tail,), x, y)
            assert not overlap_both_ways(head_only, ship), f"the head is not clear: {where}"
            assert overlap_both_ways(tail_only, ship) is expect, where
            assert overlap_both_ways(active.current_hitbox(), ship) is expect, where


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
