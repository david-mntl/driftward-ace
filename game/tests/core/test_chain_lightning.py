"""Chain lightning tests, the base hooks it uses, and chain lightnings inside the run.

Contract: docs/contracts/systems/drifters.md, Rules: Chain lightning, The base (Warning copy,
Warning settle, Timers, Re-hit cooldown, Entering, Leaving), Spawner; docs/contracts/systems/run.md,
Rules. Task: docs/contracts/DRA-47/tasks/DRA-47-08-qa-engineer.md. One test per behavior it
lists. The tuning records are built here from the GDD values below, never read from
game/tuning/, and no expected number is imported from the code under test.
"""

import logging
import math
from dataclasses import dataclass, replace
from decimal import Decimal
from itertools import pairwise

import pytest

from core.collision import Box, Circle, Hitbox, Line, Shape, hitboxes_overlap, place_hitbox
from core.drifters.base import (
    Drifter,
    DrifterType,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
    scale_telegraph,
    scale_timer,
)
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightning,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
)
from core.drifters.meteorite import Meteorite
from core.drifters.satellite import Satellite, SatelliteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

SPEED_RATIO: float = 0.375
"""Level 1 speed as a multiple of the top sideways speed. Source: drifters/03-chain-lightning.md,
speed_ratio (guess)."""

LEVEL_ONE_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""px/tick, about 2.4675. Source: drifters/03-chain-lightning.md, speed."""

WARNING_TICKS: int = 60
"""ticks. Source: 07-drifters.md, entry_warning_ticks (guess)."""

SCREEN_W: int = 640
SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

SPACING: float = 128.0
"""px between neighbouring nodes. Source: drifters/03-chain-lightning.md, node_spacing (guess)."""

NODE_SIZE: float = 12.0
"""px. Source: drifters/03-chain-lightning.md, node_size (guess)."""

ARC_WIDTH: float = 6.0
"""px. Source: drifters/03-chain-lightning.md, arc_width (guess)."""

CHARGE_TICKS: int = 120
FIRE_TICKS: int = 120
"""ticks. Source: drifters/03-chain-lightning.md, charge_ticks, fire_ticks (guess)."""

CHARGE_RAYS: int = 4
RAY_LENGTH: float = 6.0
RAY_WIDTH: float = 1.0
"""Source: drifters/03-chain-lightning.md, charge_rays, ray_length (guess); placeholder_look."""

TELEGRAPH_MIN: int = 45
"""ticks. Source: 07-drifters.md, telegraph_min (locked)."""

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
TIMER_MULT: tuple[float, ...] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Hazard speed × and Timer × for Levels 1 to 8. Source: 08-difficulty.md, level table."""

CHARGE_BY_LEVEL: tuple[int, ...] = (120, 113, 107, 102, 98, 93, 89, 84)
"""120 × Timer × rounded up. Source: drifters/03-chain-lightning.md, Values; drifters.md, Rules,
Chain lightning, Values at Level 1."""

REHIT_COOLDOWN: int = 180
REHIT_DIM: float = 0.75
"""Source: 05-lives-and-damage.md, rehit_cooldown, rehit_dim (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

TRIANGLE_HEIGHT_UNITS: float = 0.4330127
"""Half the height of the equilateral triangle layout, in node_spacing units. Source:
drifters.md, Rules, Chain lightning, Layout."""


@dataclass(frozen=True)
class Layout:
    """One layout from the contract's table: units of node_spacing, and the expected size."""

    nodes: tuple[tuple[float, float], ...]
    arcs: tuple[tuple[int, int], ...]
    mirror: str
    width: float
    height: float


DIAG: float = 0.35355339
LONG_DIAG: float = 0.70710678

LAYOUTS: dict[str, Layout] = {
    "pair_flat": Layout(((-0.5, 0.0), (0.5, 0.0)), ((0, 1),), "left_right", 140.0, 12.0),
    "pair_diagonal": Layout(
        ((-DIAG, -DIAG), (DIAG, DIAG)), ((0, 1),), "left_right", 102.50966784, 102.50966784
    ),
    "pair_vertical": Layout(((0.0, -0.5), (0.0, 0.5)), ((0, 1),), "left_right", 12.0, 140.0),
    "trio_line": Layout(
        ((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)), ((0, 1), (1, 2)), "left_right", 268.0, 12.0
    ),
    "trio_diagonal": Layout(
        ((-LONG_DIAG, -LONG_DIAG), (0.0, 0.0), (LONG_DIAG, LONG_DIAG)),
        ((0, 1), (1, 2)),
        "left_right",
        193.01933,
        193.01933,
    ),
    "trio_l": Layout(
        ((-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)), ((0, 1), (1, 2)), "left_right", 140.0, 140.0
    ),
    "trio_triangle": Layout(
        (
            (-0.5, TRIANGLE_HEIGHT_UNITS),
            (0.0, -TRIANGLE_HEIGHT_UNITS),
            (0.5, TRIANGLE_HEIGHT_UNITS),
        ),
        ((0, 1), (1, 2), (2, 0)),
        "top_bottom",
        140.0,
        122.85,
    ),
}
"""The seven layouts. Source: drifters.md, Rules, Chain lightning, Layout (table)."""

TRIANGLE_NODES: tuple[tuple[float, float], ...] = tuple(
    (x * SPACING, y * SPACING) for x, y in LAYOUTS["trio_triangle"].nodes
)
"""The point-up triangle in px, the entry warning's layout. Source: entry_warning_icon (locked)."""


def px_nodes(name: str) -> tuple[tuple[float, float], ...]:
    """A layout's node offsets in px, before invert."""
    return tuple((x * SPACING, y * SPACING) for x, y in LAYOUTS[name].nodes)


def expected_nodes(name: str, invert: bool) -> tuple[tuple[float, float], ...]:
    """A layout's node offsets in px with invert applied, by the layout's own mirror."""
    nodes = px_nodes(name)
    if not invert:
        return nodes
    if LAYOUTS[name].mirror == "left_right":
        return tuple((-x, y) for x, y in nodes)
    return tuple((x, -y) for x, y in nodes)


def box_size(nodes: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    """The box around every node circle: the spread of the centers plus the node size."""
    xs = [x for x, _ in nodes]
    ys = [y for _, y in nodes]
    return max(xs) - min(xs) + NODE_SIZE, max(ys) - min(ys) + NODE_SIZE


def full_hitbox(
    nodes: tuple[tuple[float, float], ...], arcs: tuple[tuple[int, int], ...]
) -> Hitbox:
    """One line per arc, then one circle per node, as offsets. Source: Rules, Chain lightning."""
    lines: Hitbox = tuple(
        Line(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], ARC_WIDTH) for a, b in arcs
    )
    circles: Hitbox = tuple(Circle(x, y, NODE_SIZE / 2) for x, y in nodes)
    return lines + circles


def make_layout(name: str) -> ChainLayout:
    """The tuning record of a layout, built from the units above."""
    layout = LAYOUTS[name]
    mirror = InvertMirror.LEFT_RIGHT if layout.mirror == "left_right" else InvertMirror.TOP_BOTTOM
    return ChainLayout(nodes=px_nodes(name), arcs=layout.arcs, invert_mirror=mirror)


def make_tuning(
    *,
    hazards: HazardRules | None = None,
    switches: PlaytestSwitches | None = None,
    charge_ticks: int = CHARGE_TICKS,
    fire_ticks: int = FIRE_TICKS,
) -> DrifterTuning:
    """Build the chain lightning, meteorite and satellite tuning from the GDD values above."""
    chain_variants: dict[str, VariantTuning] = {}
    for name, layout in LAYOUTS.items():
        nodes = px_nodes(name)
        width, height = box_size(nodes)
        chain_variants[name] = VariantTuning(
            width=width,
            height=height,
            hitbox=full_hitbox(nodes, layout.arcs),
            extra=ChainLightningVariantExtra(layout=make_layout(name)),
        )
    extra: dict[str, VariantExtra | None] = {"flat": SatelliteVariantExtra(angle_degrees=0.0)}
    satellite_variants: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=36.0, height=12.0, hitbox=(Box(0, 0, 12, 12), Box(0, 0, 36, 6)), extra=value
        )
        for name, value in extra.items()
    }
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.CHAIN_LIGHTNING: DrifterTypeTuning(
                variants=chain_variants,
                default_variant="pair_flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=ChainLightningTypeExtra(
                    node_size=NODE_SIZE,
                    arc_width=ARC_WIDTH,
                    charge_ticks=charge_ticks,
                    fire_ticks=fire_ticks,
                    charge_rays=CHARGE_RAYS,
                    ray_length=RAY_LENGTH,
                    ray_width=RAY_WIDTH,
                    warning_layout=make_layout("trio_triangle"),
                ),
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))},
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            DrifterType.SATELLITE: DrifterTypeTuning(
                variants=satellite_variants,
                default_variant="flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
CTX: TickContext = TickContext(ship=spawn())
LEVELS: range = range(1, 9)


def place(
    variant: str | None = None,
    x: float | None = HOME_X,
    y: float | None = None,
    *,
    invert: bool = False,
    level: int = 1,
    as_level: int | None = None,
    specialty_enabled: bool | None = None,
    tuning: DrifterTuning = TUNING,
) -> ChainLightning:
    """Spawn a chain lightning through the spawner. No y: its box starts above the top edge."""
    placement: Placement = Placement(
        DrifterType.CHAIN_LIGHTNING,
        x,
        y,
        variant=variant,
        as_level=as_level,
        specialty_enabled=specialty_enabled,
        invert=invert,
    )
    drifter: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(drifter, ChainLightning)
    return drifter


def advance[T: Drifter](drifter: T, ticks: int, ctx: TickContext = CTX) -> T:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active(
    variant: str | None = None,
    x: float | None = HOME_X,
    y: float | None = None,
    *,
    invert: bool = False,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
) -> ChainLightning:
    """A chain lightning that has just turned ACTIVE, on its first charging state."""
    chain = advance(place(variant, x, y, invert=invert, level=level, tuning=tuning), WARNING_TICKS)
    assert chain.phase is Phase.ACTIVE
    assert chain.ticks_in_phase == 0
    return chain


def firing_at(
    variant: str,
    x: float,
    y: float,
    *,
    invert: bool = False,
    tuning: DrifterTuning = TUNING,
) -> ChainLightning:
    """An ACTIVE chain lightning put on its first firing state, at the given center."""
    chain = active(variant, invert=invert, tuning=tuning)
    return replace(chain, x=x, y=y, ticks_in_phase=chain.charge_ticks)


def node_on_screen(nx: float, ny: float) -> bool:
    """Whether a node's 12 x 12 square shares area with the screen, worked out here."""
    half = NODE_SIZE / 2
    return nx - half < SCREEN_W and nx + half > 0 and ny - half < SCREEN_H and ny + half > 0


def expected_arcs(chain: ChainLightning) -> tuple[int, ...]:
    """The arcs whose two nodes are both on screen, worked out from the placed node centers."""
    on = [node_on_screen(chain.x + ox, chain.y + oy) for ox, oy in chain.nodes]
    return tuple(i for i, (a, b) in enumerate(chain.arcs) if on[a] and on[b])


def assert_nodes(
    actual: tuple[tuple[float, float], ...], expected: tuple[tuple[float, float], ...]
) -> None:
    """The same node offsets in the same order, numbers equal within 1e-6."""
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected, strict=True):
        assert got == pytest.approx(want, abs=1e-6)


def grown(hitbox: Hitbox, margin: float) -> Hitbox:
    """The lines and circles of a hitbox grown by `margin` on every side, worked out here."""
    result: list[Shape] = []
    for shape in hitbox:
        if isinstance(shape, Line):
            thickness = shape.thickness + 2 * margin
            result.append(Line(shape.ax, shape.ay, shape.bx, shape.by, thickness))
        elif isinstance(shape, Circle):
            result.append(Circle(shape.cx, shape.cy, shape.r + margin))
        else:
            raise AssertionError(f"unexpected shape {shape!r}")
    return tuple(result)


def shape_values(shape: Shape) -> tuple[str, tuple[float, ...]]:
    """A shape's kind and numbers, to compare with a tolerance."""
    if isinstance(shape, Circle):
        return "circle", (shape.cx, shape.cy, shape.r)
    if isinstance(shape, Line):
        return "line", (shape.ax, shape.ay, shape.bx, shape.by, shape.thickness)
    if isinstance(shape, Box):
        return "box", (shape.cx, shape.cy, shape.w, shape.h)
    raise AssertionError(f"unknown shape {shape!r}")


def assert_hitbox(actual: Hitbox, expected: Hitbox) -> None:
    """The same shapes in the same order, numbers equal within 1e-6."""
    assert [shape_values(s)[0] for s in actual] == [shape_values(s)[0] for s in expected]
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected, strict=True):
        assert shape_values(got)[1] == pytest.approx(shape_values(want)[1], abs=1e-6)


def test_chain_lightning_defaults_to_pair_flat_needs_x_and_starts_above_the_top() -> None:
    chain = place(None)
    assert chain.variant == "pair_flat"
    assert (chain.width, chain.height) == (140.0, 12.0)
    assert chain.phase is Phase.WARNING
    assert chain.invert is False
    for variant in LAYOUTS:
        for invert in (False, True):
            with pytest.raises(ValueError, match="x") as missing:
                place(variant, None, invert=invert)
            assert "chain_lightning placement needs x" in str(missing.value)
            with pytest.raises(ValueError, match="needs x"):
                place(variant, None, 100.0, invert=invert)
    # No y: the bottom of its box on the top edge, fully above it.
    for variant in LAYOUTS:
        for invert in (False, True):
            started = place(variant, 200.0, invert=invert)
            assert started.x == 200.0
            assert started.y == -started.height / 2
            assert started.y + started.height / 2 == 0.0
            assert not started.is_partly_on_screen()
    # A y the placement sets is kept, including 0 and a negative one.
    for y in (0.0, 123.5, -300.0, 600.0):
        assert place("trio_l", 320.0, y).y == y
    # A specialty switched on raises; off and unset are fine. invert is accepted.
    with pytest.raises(ValueError, match="specialty"):
        place(specialty_enabled=True)
    with pytest.raises(ValueError, match="chain_lightning has no specialty"):
        place("trio_triangle", invert=True, specialty_enabled=True)
    for switch in (False, None):
        assert place(specialty_enabled=switch).specialty is None
    for variant in LAYOUTS:
        assert place(variant, invert=True).invert is True
        assert place(variant, invert=False).invert is False
    assert chain.effect_on_touch() is TouchEffect.HIT


@pytest.mark.parametrize("name", list(LAYOUTS))
def test_every_layout_and_its_invert(name: str) -> None:
    layout = LAYOUTS[name]
    for invert in (False, True):
        chain = place(name, invert=invert)
        want = expected_nodes(name, invert)
        assert_nodes(chain.nodes, want)
        assert chain.arcs == layout.arcs
        assert chain.node_size == NODE_SIZE
        assert chain.arc_width == ARC_WIDTH
        # Neighbouring nodes are node_spacing apart, whatever invert did.
        for a, b in chain.arcs:
            gap = math.dist(chain.nodes[a], chain.nodes[b])
            assert gap == pytest.approx(SPACING, rel=1e-6)
        # The box around the node circles is centered on the chain and as the Layout table says.
        xs = [x for x, _ in chain.nodes]
        ys = [y for _, y in chain.nodes]
        assert min(xs) + max(xs) == pytest.approx(0.0, abs=1e-6)
        assert min(ys) + max(ys) == pytest.approx(0.0, abs=1e-6)
        assert chain.width == pytest.approx(layout.width, abs=0.01)
        assert chain.height == pytest.approx(layout.height, abs=0.01)
        assert (max(xs) - min(xs) + NODE_SIZE, max(ys) - min(ys) + NODE_SIZE) == pytest.approx(
            (chain.width, chain.height), abs=1e-6
        )
        assert_hitbox(chain.hitbox, full_hitbox(want, layout.arcs))
    plain = place(name).nodes
    flipped = place(name, invert=True).nodes
    if name in ("pair_flat", "pair_vertical", "trio_line"):
        # Symmetric: the same positions, whatever the order they are listed in.
        assert_nodes(tuple(sorted(flipped)), tuple(sorted(plain)))
    elif name == "trio_triangle":
        # Upside down: x kept, y negated, so the point is down.
        assert_nodes(flipped, tuple((x, -y) for x, y in plain))
        assert min(y for _, y in plain) < 0 < max(y for _, y in plain)
        assert [y for _, y in plain][1] < 0
        assert [y for _, y in flipped][1] > 0
    else:
        # Mirrored left to right: y kept, x negated.
        assert_nodes(flipped, tuple((-x, y) for x, y in plain))
        assert flipped != plain


def test_diagonals_and_the_l_have_the_left_node_highest_and_the_triangle_points_up() -> None:
    diagonal = place("pair_diagonal").nodes
    assert diagonal[0][0] < diagonal[1][0]
    assert diagonal[0][1] < diagonal[1][1]
    trio = place("trio_diagonal").nodes
    assert trio[0][1] < trio[1][1] < trio[2][1]
    letter = place("trio_l").nodes
    # Top, corner, right: the corner is below the top node and left of the right one.
    assert letter[0][1] < letter[1][1]
    assert letter[0][0] == letter[1][0] < letter[2][0]
    assert letter[1][1] == letter[2][1]
    triangle = place("trio_triangle").nodes
    assert triangle[1][1] < triangle[0][1] == triangle[2][1]


def test_the_cycle_charges_then_fires_and_keeps_cycling_while_it_falls() -> None:
    chain = place("pair_flat")
    cycle = CHARGE_TICKS + FIRE_TICKS
    # Neither charging nor firing through the whole warning.
    for count in range(WARNING_TICKS):
        assert chain.phase is Phase.WARNING
        assert chain.ticks_in_phase == count
        assert not chain.is_charging()
        assert not chain.is_firing()
        assert chain.firing_arcs() == ()
        assert chain.charge_ray_count() == 0
        chain = chain.update(CTX)
    assert chain.phase is Phase.ACTIVE
    # Charging on exactly charge_ticks states from the one it appears on, then firing on the
    # next fire_ticks, then charging again, for three cycles.
    states: list[ChainLightning] = [chain]
    for _ in range(3 * cycle - 1):
        states.append(states[-1].update(CTX))
    for index, state in enumerate(states):
        assert state.phase is Phase.ACTIVE
        assert state.ticks_in_phase == index
        in_charge = index % cycle < CHARGE_TICKS
        assert state.is_charging() is in_charge, index
        assert state.is_firing() is (not in_charge), index
    runs: list[tuple[bool, int]] = []
    for state in states:
        if not runs or runs[-1][0] != state.is_charging():
            runs.append((state.is_charging(), 0))
        runs[-1] = (runs[-1][0], runs[-1][1] + 1)
    assert runs == [(True, 120), (False, 120)] * 3
    # It falls the whole time: the same step every update, whatever the phase of the cycle.
    for before, after in pairwise(states):
        assert after.y - before.y == pytest.approx(LEVEL_ONE_SPEED)
        assert after.x == before.x
    # Neither at GONE.
    gone = replace(states[10], phase=Phase.GONE)
    assert not gone.is_charging()
    assert not gone.is_firing()
    assert gone.update(CTX) == gone
    # The contract's timeline: fires on state T+180, the 120th ACTIVE state.
    assert states[119].is_charging()
    assert states[120].is_firing()
    assert states[239].is_firing()
    assert states[240].is_charging()
    assert states[0].y == pytest.approx(-6.0)
    assert states[30].y == pytest.approx(68.03, abs=0.01)
    assert states[120].y == pytest.approx(290.10, abs=0.01)


def test_the_cycle_at_level_8_uses_the_shorter_charge_and_the_same_fire() -> None:
    chain = active(level=8)
    assert chain.charge_ticks == 84
    assert chain.fire_ticks == FIRE_TICKS
    for index in range(2 * (84 + FIRE_TICKS)):
        in_charge = index % (84 + FIRE_TICKS) < 84
        assert chain.is_charging() is in_charge, index
        assert chain.is_firing() is (not in_charge), index
        chain = chain.update(CTX)


def ray_counts(chain: ChainLightning) -> list[int]:
    """Rays per node on each charging state of a chain that has just turned ACTIVE."""
    counts: list[int] = []
    for _ in range(chain.charge_ticks):
        assert chain.is_charging()
        counts.append(chain.charge_ray_count())
        chain = chain.update(CTX)
    assert chain.is_firing()
    return counts


def test_rays_grow_one_per_step_up_to_charge_rays_and_follow_the_shorter_charge() -> None:
    def expected(charge: int, boundaries: tuple[int, ...]) -> list[int]:
        return [sum(1 for b in boundaries if t >= b) for t in range(charge)]

    # Level 1: 1 ray on cycle ticks 0 to 29, 2 on 30 to 59, 3 on 60 to 89, 4 on 90 to 119.
    level_one = ray_counts(active())
    assert level_one == expected(120, (0, 30, 60, 90))
    # Level 8, 84 ticks: a new ray every 21 ticks, and all four on the last step.
    level_eight = ray_counts(active(level=8))
    assert level_eight == expected(84, (0, 21, 42, 63))
    assert level_eight[-1] == CHARGE_RAYS
    # A charge held at telegraph_min (45): the steps follow it and the last one shows all rays.
    held = ray_counts(active(tuning=make_tuning(charge_ticks=30)))
    assert held == expected(45, (0, 12, 23, 34))
    assert held[-1] == CHARGE_RAYS
    for counts in (level_one, level_eight, held):
        assert max(counts) == CHARGE_RAYS
        assert counts == sorted(counts)
    # None while firing, and none in the warning.
    chain = active()
    for _ in range(CHARGE_TICKS + FIRE_TICKS):
        if chain.is_firing():
            assert chain.charge_ray_count() == 0
        chain = chain.update(CTX)
    assert place().charge_ray_count() == 0
    assert advance(place(), WARNING_TICKS - 1).charge_ray_count() == 0


def test_the_charge_scales_with_the_timer_and_never_goes_below_telegraph_min() -> None:
    assert [place(level=level).charge_ticks for level in LEVELS] == list(CHARGE_BY_LEVEL)
    assert [place(as_level=level).charge_ticks for level in LEVELS] == list(CHARGE_BY_LEVEL)
    # The fire never changes with the level.
    assert {place(level=level).fire_ticks for level in LEVELS} == {FIRE_TICKS}
    # Speed is the Level 1 speed times the level's hazard speed.
    for level in LEVELS:
        assert place(level=level).speed == pytest.approx(LEVEL_ONE_SPEED * HAZARD_SPEED[level - 1])
    # The warning is never scaled.
    assert {place(level=level).warning_ticks for level in LEVELS} == {WARNING_TICKS}
    # A tuning charge already below telegraph_min is raised to it, at every level.
    short = make_tuning(charge_ticks=30)
    assert [place(level=level, tuning=short).charge_ticks for level in LEVELS] == [45] * 8
    # A telegraph_min set in HazardRules is the floor.
    floor_100 = make_tuning(hazards=HazardRules(telegraph_min_ticks=100))
    assert [place(level=level, tuning=floor_100).charge_ticks for level in LEVELS] == [
        120,
        113,
        107,
        102,
        100,
        100,
        100,
        100,
    ]
    floor_0 = make_tuning(hazards=HazardRules(telegraph_min_ticks=0))
    assert [place(level=level, tuning=floor_0).charge_ticks for level in LEVELS] == list(
        CHARGE_BY_LEVEL
    )
    # timer_scaling off: the Level 1 charge at every level, the floor still holds.
    no_timer = make_tuning(switches=PlaytestSwitches(timer_scaling=False))
    assert {place(level=level, tuning=no_timer).charge_ticks for level in LEVELS} == {120}
    assert place(as_level=8, tuning=no_timer).charge_ticks == 120
    both = make_tuning(charge_ticks=30, switches=PlaytestSwitches(timer_scaling=False))
    assert {place(level=level, tuning=both).charge_ticks for level in LEVELS} == {45}
    # hazard_speed_scaling off: the Level 1 speed at every level, the charge still scales.
    no_speed = make_tuning(switches=PlaytestSwitches(hazard_speed_scaling=False))
    for level in LEVELS:
        slow = place(level=level, tuning=no_speed)
        assert slow.speed == pytest.approx(LEVEL_ONE_SPEED)
        assert slow.charge_ticks == CHARGE_BY_LEVEL[level - 1]
    # A placement's level beats the run's.
    assert place(level=1, as_level=8).charge_ticks == 84
    assert place(level=8, as_level=1).charge_ticks == 120


def test_scale_timer_rounds_up_and_never_adds_a_tick_to_a_whole_product() -> None:
    for ticks in range(1, 301):
        for mult in TIMER_MULT:
            exact = Decimal(ticks) * Decimal(str(mult))
            want = int(exact.to_integral_value(rounding="ROUND_CEILING"))
            assert scale_timer(ticks, mult) == want, (ticks, mult)
    assert scale_timer(120, 0.85) == 102
    assert scale_timer(120, 0.7) == 84
    assert scale_timer(100, 0.7) == 70
    assert scale_timer(120, 0.94) == 113
    assert scale_timer(120, 1.0) == 120
    # A telegraph is never below its minimum.
    assert scale_telegraph(120, 0.7, 45) == 84
    assert scale_telegraph(120, 0.7, 100) == 100
    assert scale_telegraph(30, 1.0, 45) == 45
    assert scale_telegraph(60, 0.7, 45) == 45
    assert scale_telegraph(120, 1.0, 0) == 120


def test_an_arc_fires_only_while_both_its_nodes_are_on_screen() -> None:
    # (variant, x, y, arcs that fire). A node is on screen while any part of its 12 px square is.
    cases: list[tuple[str, float, float, tuple[int, ...]]] = [
        ("pair_flat", 320.0, 240.0, (0,)),
        ("trio_line", 320.0, 240.0, (0, 1)),
        # Left node's right edge on the left wall: off. Any part inside: on.
        ("trio_line", 122.0, 240.0, (1,)),
        ("trio_line", 122.01, 240.0, (0, 1)),
        ("trio_line", 518.0, 240.0, (0,)),
        ("trio_line", 517.99, 240.0, (0, 1)),
        # Above the top edge and past the floor.
        ("pair_vertical", 320.0, 58.0, ()),
        ("pair_vertical", 320.0, 58.01, (0,)),
        ("pair_vertical", 320.0, 422.0, ()),
        ("pair_vertical", 320.0, 421.99, (0,)),
        ("trio_l", 320.0, 0.0, (1,)),
        ("trio_l", 320.0, 430.0, ()),
        ("trio_diagonal", 320.0, 400.0, (0,)),
        ("trio_diagonal", 320.0, -40.0, ()),
        ("trio_diagonal", 320.0, -5.0, (1,)),
        ("trio_triangle", 320.0, 40.0, (2,)),
        ("trio_triangle", 320.0, 430.0, (0, 1, 2)),
        ("trio_triangle", 320.0, 440.0, ()),
    ]
    for variant, x, y, arcs in cases:
        chain = firing_at(variant, x, y)
        assert chain.firing_arcs() == arcs, (variant, x, y)
        assert chain.firing_arcs() == expected_arcs(chain), (variant, x, y)
    # Charging and warning: nothing, wherever the nodes are.
    on_screen = replace(firing_at("trio_line", 320.0, 240.0), ticks_in_phase=5)
    assert on_screen.is_charging()
    assert on_screen.firing_arcs() == ()
    assert place("trio_line", 320.0, 240.0).firing_arcs() == ()


def test_an_arc_stops_on_the_first_state_one_of_its_nodes_leaves() -> None:
    # A long fire, so one firing phase covers the whole fall from above the top to below the floor.
    tuning = make_tuning(fire_ticks=1000)
    for variant, invert in (("pair_vertical", False), ("trio_l", True), ("trio_triangle", False)):
        chain = firing_at(variant, 320.0, -200.0, invert=invert, tuning=tuning)
        seen: list[tuple[int, ...]] = []
        for _ in range(300):
            assert chain.is_firing()
            assert chain.firing_arcs() == expected_arcs(chain)
            seen.append(chain.firing_arcs())
            chain = chain.update(CTX)
        assert seen[0] == ()
        assert seen[-1] == ()
        assert max(len(arcs) for arcs in seen) > 0
        # None fires before it enters, none comes back once its nodes have left: each arc is on
        # for one unbroken stretch of states.
        for arc in range(len(chain.arcs)):
            flags = [arc in arcs for arcs in seen]
            first = flags.index(True)
            last = len(flags) - 1 - flags[::-1].index(True)
            assert all(flags[first : last + 1]), (variant, arc)
    # The two vertical nodes: the bottom one leaves first, and the arc stops on that very state.
    chain = firing_at("pair_vertical", 320.0, 400.0, tuning=tuning)
    previous = chain
    while chain.firing_arcs():
        previous = chain
        chain = chain.update(CTX)
    assert previous.firing_arcs() == (0,)
    assert chain.y + 64 - NODE_SIZE / 2 >= SCREEN_H
    assert previous.y + 64 - NODE_SIZE / 2 < SCREEN_H
    assert chain.current_hitbox() == ()


def test_the_hitbox_is_empty_until_an_arc_fires_and_then_the_arcs_and_their_nodes() -> None:
    # Nothing while warning, nothing on any charging state, nothing at GONE.
    chain = place("trio_triangle", HOME_X, HOME_Y)
    for _ in range(WARNING_TICKS):
        assert chain.current_hitbox() == ()
        assert chain.graze_zone() == ()
        chain = chain.update(CTX)
    for _ in range(CHARGE_TICKS):
        assert chain.is_charging()
        assert chain.current_hitbox() == ()
        assert chain.graze_zone() == ()
        chain = chain.update(CTX)
    assert chain.is_firing()
    assert replace(chain, phase=Phase.GONE).current_hitbox() == ()
    # Every variant and invert, all nodes on screen: one line per arc, one circle per node.
    for name, layout in LAYOUTS.items():
        for invert in (False, True):
            firing = firing_at(name, HOME_X, HOME_Y, invert=invert)
            nodes = expected_nodes(name, invert)
            want = place_hitbox(full_hitbox(nodes, layout.arcs), HOME_X, HOME_Y)
            assert len(want) == len(layout.arcs) + len(nodes)
            assert_hitbox(firing.current_hitbox(), want)
            # The graze zone exists only while an arc fires: each shape grown by 14 on every side.
            assert_hitbox(firing.graze_zone(), grown(want, GRAZE_MARGIN))
            assert replace(firing, ticks_in_phase=0).graze_zone() == ()
    # A node whose arcs are all off is not in the hitbox; the others keep theirs.
    left_off = firing_at("trio_line", 122.0, HOME_Y)
    assert left_off.firing_arcs() == (1,)
    assert_hitbox(
        left_off.current_hitbox(),
        (
            Line(122.0, HOME_Y, 250.0, HOME_Y, ARC_WIDTH),
            Circle(122.0, HOME_Y, NODE_SIZE / 2),
            Circle(250.0, HOME_Y, NODE_SIZE / 2),
        ),
    )
    top_off = firing_at("trio_l", 320.0, 0.0)
    assert top_off.firing_arcs() == (1,)
    assert_hitbox(
        top_off.current_hitbox(),
        (
            Line(256.0, 64.0, 384.0, 64.0, ARC_WIDTH),
            Circle(256.0, 64.0, NODE_SIZE / 2),
            Circle(384.0, 64.0, NODE_SIZE / 2),
        ),
    )
    triangle_top = firing_at("trio_triangle", 320.0, 40.0)
    assert triangle_top.firing_arcs() == (2,)
    low = 40.0 + TRIANGLE_NODES[0][1]
    assert_hitbox(
        triangle_top.current_hitbox(),
        (
            Line(384.0, low, 256.0, low, ARC_WIDTH),
            Circle(256.0, low, NODE_SIZE / 2),
            Circle(384.0, low, NODE_SIZE / 2),
        ),
    )
    # No arc on screen: nothing at all, though the phase is firing.
    none_left = firing_at("trio_l", 320.0, 430.0)
    assert none_left.is_firing()
    assert none_left.current_hitbox() == ()
    assert none_left.graze_zone() == ()


def run_with_ship(ship: Ship, *placements: Placement, tuning: DrifterTuning = TUNING) -> Run:
    """A fresh run with the ship put where the test wants it, and the placements added."""
    return add_drifters(replace(start_run(), ship=ship), list(placements), tuning)


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def warning_node_of(chain: Drifter) -> int | None:
    """The settled warning node of a chain lightning."""
    assert isinstance(chain, ChainLightning)
    return chain.warning_node


def test_the_warning_sits_above_the_node_nearest_the_ship_and_stays_put() -> None:
    # (variant, x, y, ship x, ship y, node index, warning center). The warning is 24 wide.
    cases: list[tuple[str, float, float | None, float, float, int, tuple[float, float]]] = [
        ("pair_flat", 320.0, None, 100.0, 300.0, 0, (256.0, 12.0)),
        ("pair_flat", 320.0, None, 500.0, 300.0, 1, (384.0, 12.0)),
        # A tie in distance: the left node.
        ("pair_flat", 320.0, None, 320.0, 240.0, 0, (256.0, 12.0)),
        # A tie in distance and in x: the lower index, the upper node.
        ("pair_vertical", 320.0, 240.0, 320.0, 240.0, 0, (320.0, 176.0)),
        ("trio_line", 320.0, None, 330.0, 0.0, 1, (320.0, 12.0)),
        ("trio_line", 320.0, None, 5.0, 400.0, 0, (192.0, 12.0)),
        ("trio_line", 320.0, None, 630.0, 400.0, 2, (448.0, 12.0)),
        # The center is clamped by half the 24 px warning, on both axes.
        ("pair_flat", 30.0, None, 10.0, 300.0, 0, (12.0, 12.0)),
        ("pair_flat", 620.0, None, 630.0, 300.0, 1, (628.0, 12.0)),
        ("pair_flat", 320.0, 470.0, 256.0, 470.0, 0, (256.0, 468.0)),
        ("pair_flat", 20.0, 470.0, 5.0, 470.0, 0, (12.0, 468.0)),
        # Wide chains and narrow ones are clamped the same, not by their own size.
        ("pair_vertical", 20.0, 240.0, 20.0, 5.0, 0, (20.0, 176.0)),
        ("pair_vertical", 620.0, 240.0, 620.0, 470.0, 1, (620.0, 304.0)),
    ]
    for variant, x, y, ship_x, ship_y, index, center in cases:
        run = run_with_ship(
            resting(ship_x, ship_y), Placement(DrifterType.CHAIN_LIGHTNING, x, y, variant=variant)
        )
        chain = run.drifters[0]
        assert warning_node_of(chain) == index, (variant, x, ship_x, ship_y)
        assert chain.warning_center() == pytest.approx(center, abs=1e-6), (variant, x, y)
        assert chain.warning_copy().width == pytest.approx(140.0)
    # An inverted chain warns above its mirrored node.
    inverted = run_with_ship(
        resting(0.0, 300.0),
        Placement(DrifterType.CHAIN_LIGHTNING, 320.0, 240.0, variant="pair_diagonal", invert=True),
    ).drifters[0]
    offset = DIAG * SPACING
    assert warning_node_of(inverted) == 1
    assert inverted.warning_center() == pytest.approx((320.0 - offset, 240.0 + offset), abs=1e-6)
    # It stays put for the whole warning, whatever the ship does, and settling changes nothing
    # else about the chain.
    start = run_with_ship(
        resting(100.0, 100.0), Placement(DrifterType.CHAIN_LIGHTNING, 320.0, variant="pair_flat")
    )
    born = start.drifters[0]
    assert isinstance(born, ChainLightning)
    unsettled = place("pair_flat")
    assert replace(born, uid=0, warning_node=None) == unsettled
    assert born.uid == 1
    assert born.warning_center() == (256.0, 12.0)
    run = start
    for _ in range(WARNING_TICKS - 1):
        run = step_run(run, Thrust(right=True))
        chain = run.drifters[0]
        assert chain.phase is Phase.WARNING
        assert chain.warning_center() == (256.0, 12.0)
        assert warning_node_of(chain) == 0
        assert (chain.x, chain.y) == (320.0, -6.0)
    run = step_run(run, Thrust(right=True))
    assert run.drifters[0].phase is Phase.ACTIVE


def test_the_warning_copy_is_the_point_up_triangle_for_every_variant_and_invert() -> None:
    nodes = tuple(TRIANGLE_NODES)
    width, height = box_size(nodes)
    for name in LAYOUTS:
        for invert in (False, True):
            chain = place(name, 300.0, 200.0, invert=invert)
            copy = chain.warning_copy()
            assert isinstance(copy, ChainLightning)
            assert_nodes(copy.nodes, nodes)
            assert copy.arcs == LAYOUTS["trio_triangle"].arcs
            assert copy.nodes[1][1] < copy.nodes[0][1] == copy.nodes[2][1]
            assert (copy.width, copy.height) == pytest.approx((width, height), abs=1e-6)
            assert (copy.width, copy.height) == pytest.approx((140.0, 122.85), abs=0.01)
            # Only the look differs: same place, same phase, same cooldown, same node size.
            assert (copy.x, copy.y, copy.phase, copy.node_size) == (
                300.0,
                200.0,
                Phase.WARNING,
                12.0,
            )
            assert copy.invert is invert
            assert copy.current_hitbox() == ()
            # The owner is not changed by asking.
            assert_nodes(chain.nodes, expected_nodes(name, invert))
            assert chain.warning_tilt_degrees() == 0.0
    # Whatever the chain: a spot 12 px or more from the wall is not moved.
    narrow = place("pair_vertical", 20.0, 100.0)
    assert narrow.width == NODE_SIZE
    assert narrow.warning_center() == (20.0, 100.0)
    # A chain built without add_drifters warns above its own center, clamped.
    assert place("pair_flat").warning_center() == (HOME_X, 12.0)
    assert place("trio_l", 20.0, 100.0).warning_center() == (20.0, 100.0)
    assert place("trio_l", 620.0, 900.0).warning_center() == (620.0, 468.0)
    assert place("pair_flat", 320.0, 240.0).warning_node is None
    assert place("pair_flat", 320.0, 240.0).warning_center() == (320.0, 240.0)


def test_the_meteorite_and_the_satellite_come_back_unchanged_from_settle_warning() -> None:
    meteorite = spawn_drifter(Placement(DrifterType.METEORITE, 300.0), 1, TUNING)
    satellite = spawn_drifter(Placement(DrifterType.SATELLITE, None, 300.0), 1, TUNING)
    assert isinstance(meteorite, Meteorite)
    assert isinstance(satellite, Satellite)
    for obj in (meteorite, satellite, advance(meteorite, WARNING_TICKS), advance(satellite, 70)):
        for ship in (spawn(), resting(0.0, 0.0), resting(300.0, 300.0)):
            assert obj.settle_warning(TickContext(ship=ship)) == obj
        assert obj.warning_copy() == obj
    # Through add_drifters they are exactly what the spawner built, with a uid.
    run = run_with_ship(
        resting(300.0, 300.0),
        Placement(DrifterType.METEORITE, 300.0),
        Placement(DrifterType.SATELLITE, None, 300.0),
    )
    assert run.drifters == (replace(meteorite, uid=1), replace(satellite, uid=2))
    assert run.next_uid == 3


def entering_run(chain: ChainLightning, *, ship: Ship) -> Run:
    """A run holding one chain lightning, uid 1."""
    return Run(
        ship=ship,
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        drifters=(replace(chain, uid=1),),
        next_uid=2,
    )


def test_it_is_dropped_once_every_node_is_fully_below_the_floor() -> None:
    for name in LAYOUTS:
        for invert in (False, True):
            # When the lowest-reaching node's top edge reaches the floor, worked out here.
            nodes = expected_nodes(name, invert)
            height = box_size(nodes)[1]
            y = -height / 2
            active_ticks = 0
            while min(y + oy for _, oy in nodes) - NODE_SIZE / 2 < SCREEN_H:
                y += LEVEL_ONE_SPEED
                active_ticks += 1
            ship = resting(20.0, 20.0)
            run = run_with_ship(
                ship, Placement(DrifterType.CHAIN_LIGHTNING, 500.0, variant=name, invert=invert)
            )
            for step in range(1, WARNING_TICKS + active_ticks):
                run = step_run(replace(run, ship=ship), NO_KEY)
                assert len(run.drifters) == 1, (name, invert, step)
            assert run.drifters[0].phase is Phase.ACTIVE
            # The next tick is the one where every node is fully below the floor.
            run = step_run(replace(run, ship=ship), NO_KEY)
            assert run.drifters == (), (name, invert)
            assert run.lives == LIVES_START
    # A chain that is ACTIVE but has never been on screen is never dropped, wherever it is.
    far = place("pair_flat", 320.0, 900.0)
    waiting = entering_run(advance(far, WARNING_TICKS), ship=resting(20.0, 20.0))
    assert not waiting.drifters[0].has_entered
    for _ in range(50):
        waiting = step_run(replace(waiting, ship=resting(20.0, 20.0)), NO_KEY)
        assert len(waiting.drifters) == 1
        assert not waiting.drifters[0].has_entered


def touch_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """The `drifter touch` lines the run logged."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == RUN_LOGGER and r.getMessage().startswith("drifter touch")
    ]


def chain_run(
    *,
    variant: str = "pair_flat",
    ticks_in_phase: int = 0,
    speed: float = 0.0,
    y: float = HOME_Y,
    invuln: int = 0,
    tuning: DrifterTuning = TUNING,
) -> Run:
    """A run with one ACTIVE chain lightning at (320, y), that has entered, over the ship."""
    chain = replace(
        place(variant, HOME_X, y, tuning=tuning),
        uid=1,
        phase=Phase.ACTIVE,
        ticks_in_phase=ticks_in_phase,
        speed=speed,
        has_entered=True,
    )
    return Run(
        ship=resting(HOME_X, HOME_Y),
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        invuln_ticks_left=invuln,
        drifters=(chain,),
        next_uid=2,
    )


def chain_of(run: Run) -> ChainLightning:
    """The single chain lightning on the field."""
    assert len(run.drifters) == 1
    chain = run.drifters[0]
    assert isinstance(chain, ChainLightning)
    return chain


def tick(run: Run, ship: Ship | None = None, *, clear_invuln: bool = True) -> Run:
    """One tick with the ship put back first, and invulnerability cleared so only the cooldown
    can stop a hit."""
    run = replace(run, ship=resting(HOME_X, HOME_Y) if ship is None else ship)
    return step_run(replace(run, invuln_ticks_left=0) if clear_invuln else run, NO_KEY)


NODE_ONLY_SHIP: Ship = resting(245.5, HOME_Y)
"""Next to the left node of a pair_flat at (320, 240): the node at (256, 240) is reached by the
ship's foot, the arc is not (checked in the test)."""


def test_in_the_run_a_charge_never_hits_and_a_firing_arc_hits_once_then_the_chain_cools(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    run = chain_run()
    assert not run.invulnerable
    # Charging over the ship: 119 ticks, states 1 to 119 of the charge, none of them a hit.
    for index in range(1, CHARGE_TICKS):
        run = tick(run)
        assert chain_of(run).is_charging(), index
        assert run.lives == LIVES_START, index
        assert chain_of(run).rehit_ticks_left == 0
        assert chain_of(run).brightness() == 1.0
        assert not run.invulnerable
    assert touch_lines(caplog) == []
    # The first firing tick: the arc is on the ship. One life, one log line, the cooldown starts.
    run = tick(run)
    assert chain_of(run).is_firing()
    assert hitboxes_overlap(chain_of(run).current_hitbox(), ship_hitbox(run.ship))
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN
    assert chain_of(run).brightness() == REHIT_DIM
    assert touch_lines(caplog) == ["drifter touch id=1 type=chain_lightning effect=hit"]
    hit_state = chain_of(run)
    # The cooldown: no hit on the next 180 ticks, dim on exactly 180 states, even with the ship
    # in the arc and the node and invulnerability cleared. The chain keeps cycling.
    for after in range(1, REHIT_COOLDOWN + 1):
        run = tick(run)
        chain = chain_of(run)
        assert run.lives == LIVES_START - 1, after
        assert chain.ticks_in_phase == hit_state.ticks_in_phase + after
        assert chain.phase is Phase.ACTIVE
        assert chain.rehit_ticks_left == REHIT_COOLDOWN - after
        assert chain.brightness() == (REHIT_DIM if after < REHIT_COOLDOWN else 1.0), after
        if after == FIRE_TICKS - 1:
            assert chain.is_firing()
        if after == FIRE_TICKS:
            assert chain.is_charging()
    assert len(touch_lines(caplog)) == 1
    # It is charging again when the cooldown ends. The next firing state hits again.
    assert chain_of(run).is_charging()
    for _ in range(CHARGE_TICKS + FIRE_TICKS + CHARGE_TICKS - 1 - chain_of(run).ticks_in_phase):
        run = tick(run)
        assert chain_of(run).is_charging()
        assert run.lives == LIVES_START - 1
    assert chain_of(run).ticks_in_phase == 2 * CHARGE_TICKS + FIRE_TICKS - 1
    run = tick(run)
    assert chain_of(run).is_firing()
    assert run.lives == LIVES_START - 2
    assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN
    assert len(touch_lines(caplog)) == 2


def test_in_the_run_the_chain_keeps_falling_while_it_cools() -> None:
    run = chain_run(
        speed=LEVEL_ONE_SPEED, y=HOME_Y - LEVEL_ONE_SPEED, ticks_in_phase=CHARGE_TICKS - 1
    )
    start_y = chain_of(run).y
    run = tick(run)
    assert chain_of(run).is_firing()
    assert chain_of(run).y == pytest.approx(start_y + LEVEL_ONE_SPEED)
    assert run.lives == LIVES_START - 1
    hit_y = chain_of(run).y
    for after in range(1, 40):
        run = tick(run)
        chain = chain_of(run)
        assert chain.y == pytest.approx(hit_y + after * LEVEL_ONE_SPEED)
        assert chain.ticks_in_phase == CHARGE_TICKS + after
        assert chain.rehit_ticks_left == REHIT_COOLDOWN - after
        assert chain.brightness() == REHIT_DIM
        assert chain.is_firing()
        assert run.lives == LIVES_START - 1


def test_in_the_run_the_whole_chain_cools_together_and_hits_again_on_the_first_tick_after() -> None:
    # A fire long enough to be still on when the cooldown ends.
    tuning = make_tuning(fire_ticks=1000)
    run = chain_run(ticks_in_phase=CHARGE_TICKS - 1, tuning=tuning)
    run = tick(run)
    assert run.lives == LIVES_START - 1
    assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN
    # During the cooldown the ship moves from the arc to the node alone: still no hit. The node
    # is part of the same hazard.
    node_hitbox = place_hitbox((Circle(0, 0, NODE_SIZE / 2),), 256.0, HOME_Y)
    arc_hitbox = place_hitbox((Line(0, 0, 128.0, 0, ARC_WIDTH),), 256.0, HOME_Y)
    node_ship = step_run(replace(run, ship=NODE_ONLY_SHIP, invuln_ticks_left=0), NO_KEY).ship
    assert hitboxes_overlap(node_hitbox, ship_hitbox(node_ship))
    assert not hitboxes_overlap(arc_hitbox, ship_hitbox(node_ship))
    for after in range(1, REHIT_COOLDOWN + 1):
        run = tick(run, NODE_ONLY_SHIP if after % 2 else None)
        assert run.lives == LIVES_START - 1, after
        assert chain_of(run).is_firing()
        assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN - after
    assert chain_of(run).rehit_ticks_left == 0
    assert chain_of(run).brightness() == 1.0
    # The tick after: it hits again, and its cooldown starts again.
    run = tick(run)
    assert run.lives == LIVES_START - 2
    assert run.invuln_ticks_left == INVULN_TICKS
    assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN
    assert chain_of(run).brightness() == REHIT_DIM


def test_in_the_run_a_node_hits_only_while_an_arc_fires(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    # Charging: the node is not a hit.
    run = chain_run(ticks_in_phase=0)
    for _ in range(CHARGE_TICKS - 1):
        run = tick(run, NODE_ONLY_SHIP)
        assert run.lives == LIVES_START
    assert chain_of(run).is_charging()
    assert touch_lines(caplog) == []
    # The first firing tick: the node, with its arc firing, is a hit.
    run = tick(run, NODE_ONLY_SHIP)
    assert chain_of(run).is_firing()
    assert not hitboxes_overlap(
        place_hitbox((Line(0, 0, 128.0, 0, ARC_WIDTH),), 256.0, HOME_Y), ship_hitbox(run.ship)
    )
    assert hitboxes_overlap(chain_of(run).current_hitbox(), ship_hitbox(run.ship))
    assert run.lives == LIVES_START - 1
    assert touch_lines(caplog) == ["drifter touch id=1 type=chain_lightning effect=hit"]


def test_in_the_run_an_invulnerable_touch_is_no_hit_and_starts_no_cooldown(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    tuning = make_tuning(fire_ticks=1000)
    run = chain_run(ticks_in_phase=CHARGE_TICKS, invuln=INVULN_TICKS, tuning=tuning)
    assert chain_of(run).is_firing()
    for left in range(INVULN_TICKS - 1, -1, -1):
        run = tick(run, clear_invuln=False)
        assert run.lives == LIVES_START
        assert run.invuln_ticks_left == left
        assert chain_of(run).is_firing()
        assert hitboxes_overlap(chain_of(run).current_hitbox(), ship_hitbox(run.ship))
        assert chain_of(run).rehit_ticks_left == 0
        assert chain_of(run).brightness() == 1.0
    assert touch_lines(caplog) == []
    # Still in the arc when the timer is out: it hits on the first unprotected tick.
    run = tick(run, clear_invuln=False)
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert chain_of(run).rehit_ticks_left == REHIT_COOLDOWN
    assert len(touch_lines(caplog)) == 1
