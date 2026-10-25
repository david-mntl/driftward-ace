"""The graze margin from tuning, the graze state of a new drifter, the graze popup and ring.

Contract: docs/contracts/systems/drifters.md, Rules (shared base: Graze zone, Graze state;
spawner, step 8) and docs/contracts/systems/run.md, Interface (DRA-117: `core/graze.py`
`GrazeRules`, `GrazeRing`, `graze_popup`, `graze_ring`, `step_graze_rings`; `core/popup.py`
`PopupKind`, `kind`), Rules (step 3a, step 5b Pay). Task:
docs/contracts/DRA-117/tasks/DRA-117-06-qa-engineer.md. One test per behavior it lists.
When a graze pays (step 5b) is DRA-117-05 (`test_run_graze.py`).

Like test_drifters.py, the tuning records are built here from the GDD values below, never read
from game/tuning/, and no expected number is imported from the code under test. The popup and the
ring are read two ways: straight from `graze_popup`, `graze_ring`, `step_popups` and
`step_graze_rings`, and out of a run that pays one graze. In the run the ship is put back at rest
on its home spot (320, 240) before every tick, so it hovers, and the rock is moved instead: 6 px
inside the 14 px zone on one tick, 20 px outside it on the next, which pays one graze. The ship's
foot is 32 wide, 12 tall, at the bottom of its 32 x 32 square (04-ship.md, hitbox): its right edge
is 16 px right of the ship's center and its middle row 10 px below it.
"""

import dataclasses
from dataclasses import replace
from itertools import pairwise

import pytest

from core.collision import Box, Circle, Hitbox, Line, Polygon, hitboxes_overlap
from core.drifters.base import (
    Birth,
    Drifter,
    DrifterType,
    GrazeState,
    Phase,
    TickContext,
    born_drifter,
)
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
)
from core.drifters.coin import CoinTypeExtra, CoinVariantExtra
from core.drifters.electric_ball import ElectricBallTypeExtra, ElectricBallVariantExtra
from core.drifters.floating_island import IslandShape, IslandTypeExtra, IslandVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.graze import (
    DEFAULT_GRAZE_POINTS,
    DEFAULT_GRAZE_POPUP_RISE_PER_TICK,
    DEFAULT_GRAZE_POPUP_TICKS,
    DEFAULT_GRAZE_RING_END_DIAMETER,
    DEFAULT_GRAZE_RING_START_DIAMETER,
    DEFAULT_GRAZE_RING_TICKS,
    DEFAULT_GRAZE_RING_WIDTH,
    DEFAULT_GRAZE_RULES,
    GrazeRing,
    GrazeRules,
    graze_popup,
    graze_ring,
    step_graze_rings,
)
from core.popup import PointsPopup, PopupKind, step_popups
from core.run import Run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust
from core.ship import step as ship_step

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

TUNED_MARGINS: tuple[float, ...] = (20.0, 3.5)
"""Margins that are none of the GDD's, to show the spawner hands on what it was given."""

GRAZE_POINTS: int = 25
"""Source: 06-scoring.md, graze_points (locked)."""

GRAZE_POPUP_TICKS: int = 60
GRAZE_POPUP_RISE: float = 0.5
"""States and px a tick. Source: 06-scoring.md, graze_popup (guess)."""

GRAZE_RING_TICKS: int = 15
GRAZE_RING_START: float = 16.0
GRAZE_RING_END: float = 32.0
GRAZE_RING_WIDTH: int = 1
"""Source: 06-scoring.md, graze_ring (guess)."""

INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, invuln_ticks (locked)."""

HOME_X: float = 320.0
HOME_Y: float = 240.0
HOME: Ship = Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

NO_KEY: Thrust = Thrust()

FOOT_HALF_W: float = 16.0
FOOT_ROW_DY: float = 10.0
"""The ship's foot: half its 32 px width, and its middle row below the center (16 - 12 / 2).
Source: 04-ship.md, hitbox (guess)."""

ROCK_RADIUS: float = 14.0
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

IN: float = 6.0
OUT: float = 20.0
"""Gaps, px, between the rock's hitbox and the ship's foot: inside the 14 px zone, and outside."""

WARNING_TICKS: int = 60
SPEED_RATIO: float = 0.375
CHARGE_TICKS: int = 120
FIRE_TICKS: int = 120
PULSE_RADIUS: float = 64.0
BALL_SIZE: float = 16.0
NODE_SPACING: float = 128.0
NODE_SIZE: float = 12.0
ARC_WIDTH: float = 6.0
"""Source: 07-drifters.md and drifters/03-chain-lightning.md, drifters/10-electric-ball.md,
Values (guess)."""

PAIR_NODES: tuple[tuple[float, float], ...] = (
    (-NODE_SPACING / 2, 0.0),
    (NODE_SPACING / 2, 0.0),
)
PAIR_LAYOUT: ChainLayout = ChainLayout(
    nodes=PAIR_NODES, arcs=((0, 1),), invert_mirror=InvertMirror.LEFT_RIGHT
)
"""The chain lightning's flat pair. Source: drifters.md, Rules, Chain lightning, Layout."""

CIRCLE_R: float = 14.0
BOX_W: float = 30.0
BOX_H: float = 20.0
LINE_HALF: float = 20.0
LINE_THICKNESS: float = 6.0
TRIANGLE: tuple[tuple[float, float], ...] = ((-20.0, -15.0), (20.0, 15.0), (-20.0, 15.0))
"""One hitbox of each shape kind, in px from the center. The values are test values, not the
game's: only the grow rule is under test (06-scoring.md, Rules, 3)."""

SHAPE_HITBOX: dict[str, Hitbox] = {
    "circle": (Circle(0.0, 0.0, CIRCLE_R),),
    "box": (Box(0.0, 0.0, BOX_W, BOX_H),),
    "line": (Line(-LINE_HALF, 0.0, LINE_HALF, 0.0, LINE_THICKNESS),),
    "polygon": (Polygon(TRIANGLE),),
}

CTX: TickContext = TickContext(ship=HOME)

CUSTOM_RULES: GrazeRules = GrazeRules(
    points=40,
    popup_ticks=7,
    popup_rise_per_tick=1.5,
    ring_ticks=4,
    ring_start_diameter=10.0,
    ring_end_diameter=20.0,
    ring_width=3,
)
"""Values that are none of the GDD's."""

ONE_TICK_RULES: GrazeRules = GrazeRules(
    points=0,
    popup_ticks=1,
    popup_rise_per_tick=0.0,
    ring_ticks=1,
    ring_start_diameter=12.0,
    ring_end_diameter=48.0,
    ring_width=2,
)
"""The shortest legal popup and ring: each shows on one state."""

LONG_RULES: GrazeRules = GrazeRules(
    points=1000,
    popup_ticks=90,
    popup_rise_per_tick=0.25,
    ring_ticks=30,
    ring_start_diameter=8.0,
    ring_end_diameter=72.0,
    ring_width=1,
)
"""A longer popup and a bigger ring than the GDD's."""

ALL_RULES: tuple[GrazeRules, ...] = (GrazeRules(), CUSTOM_RULES, ONE_TICK_RULES, LONG_RULES)

STILL: Scroll = Scroll()
"""A scroll at tick 0: the world stands still for the first 30 ticks, and then moves."""

SPEEDS: dict[DrifterType, float | None] = {
    DrifterType.METEORITE: 0.0,
    DrifterType.CHAIN_LIGHTNING: 0.0,
    DrifterType.ELECTRIC_BALL: 0.0,
    DrifterType.COIN: None,
    DrifterType.FLOATING_ISLAND: None,
}
"""A hazard is held still so two hundred ticks keep it in play; a coin and an island are parked."""


def make_tuning(hazards: HazardRules | None = None) -> DrifterTuning:
    """Build the tuning of every drifter the tests below place, from the values above.

    The meteorite has one variant of each shape kind and the medium circle; `hazards` None
    leaves the field out, so the tuning holds the default hazard rules.
    """
    variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=40.0, height=40.0, hitbox=hitbox)
        for name, hitbox in SHAPE_HITBOX.items()
    }
    variants["medium"] = VariantTuning(
        width=28.0, height=28.0, hitbox=(Circle(0.0, 0.0, ROCK_RADIUS),)
    )
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=variants,
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            DrifterType.COIN: DrifterTypeTuning(
                variants={
                    "common": VariantTuning(
                        width=12,
                        height=20,
                        hitbox=(Box(0.0, 0.0, 12.0, 10.0),),
                        extra=CoinVariantExtra(points=50, glint=False),
                    )
                },
                default_variant="common",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=CoinTypeExtra(
                    body_height=10,
                    ring_width=22,
                    ring_height=8,
                    glint_size=2,
                    glint_left=3,
                    glint_top=3,
                    popup_ticks=60,
                    popup_rise_per_tick=0.5,
                ),
            ),
            DrifterType.FLOATING_ISLAND: DrifterTypeTuning(
                variants={
                    "box": VariantTuning(
                        width=120.0,
                        height=120.0,
                        hitbox=(Box(0.0, 0.0, 120.0, 120.0),),
                        extra=IslandVariantExtra(shape=IslandShape.RECTANGLE),
                    )
                },
                default_variant="box",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=IslandTypeExtra(arm=40.0),
            ),
            DrifterType.CHAIN_LIGHTNING: DrifterTypeTuning(
                variants={
                    "pair_flat": VariantTuning(
                        width=NODE_SPACING + NODE_SIZE,
                        height=NODE_SIZE,
                        hitbox=(
                            Line(PAIR_NODES[0][0], 0.0, PAIR_NODES[1][0], 0.0, ARC_WIDTH),
                            Circle(PAIR_NODES[0][0], 0.0, NODE_SIZE / 2),
                            Circle(PAIR_NODES[1][0], 0.0, NODE_SIZE / 2),
                        ),
                        extra=ChainLightningVariantExtra(layout=PAIR_LAYOUT),
                    )
                },
                default_variant="pair_flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=ChainLightningTypeExtra(
                    node_size=NODE_SIZE,
                    arc_width=ARC_WIDTH,
                    charge_ticks=CHARGE_TICKS,
                    fire_ticks=FIRE_TICKS,
                    charge_rays=4,
                    ray_length=6.0,
                    ray_width=1.0,
                    warning_layout=PAIR_LAYOUT,
                ),
            ),
            DrifterType.ELECTRIC_BALL: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=BALL_SIZE,
                        height=BALL_SIZE,
                        hitbox=(Circle(0.0, 0.0, PULSE_RADIUS),),
                        extra=ElectricBallVariantExtra(pulse_radius=PULSE_RADIUS),
                    )
                },
                default_variant="standard",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=ElectricBallTypeExtra(
                    charge_ticks=CHARGE_TICKS,
                    fire_ticks=FIRE_TICKS,
                    charge_rays=4,
                    ray_length=6.0,
                    ray_width=1.0,
                    outline_width=1.0,
                    rim_width=2.0,
                    fill_opacity=0.35,
                ),
            ),
        },
        switches=PlaytestSwitches(),
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


def tuning_with(margin: float | None) -> DrifterTuning:
    """The tuning with the hazards' margin set, or with `hazards` left out for None."""
    if margin is None:
        return make_tuning()
    return make_tuning(HazardRules(graze_margin=margin))


MARGINS: tuple[float | None, ...] = (None, *TUNED_MARGINS)
"""None: the default hazard rules. The expected margin then is `GRAZE_MARGIN`."""


def expected_margin(margin: float | None) -> float:
    """The margin a drifter must carry for a tuning built with `margin`."""
    return GRAZE_MARGIN if margin is None else margin


def spawn(
    drifter_type: DrifterType,
    tuning: DrifterTuning,
    *,
    x: float = 300.0,
    y: float = 200.0,
    variant: str | None = None,
    level: int = 1,
    as_level: int | None = None,
) -> Drifter:
    """Spawn a drifter through the spawner, held still when it is a hazard."""
    placement: Placement = Placement(
        drifter_type, x, y, variant=variant, speed=SPEEDS[drifter_type], as_level=as_level
    )
    return spawn_drifter(placement, level, tuning)


def advance(drifter: Drifter, ticks: int, ctx: TickContext = CTX) -> Drifter:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active_rock(tuning: DrifterTuning, variant: str, level: int = 1) -> Drifter:
    """A meteorite of `variant` on its first ACTIVE state, moving at its own speed."""
    rock: Drifter = spawn_drifter(
        Placement(DrifterType.METEORITE, 300.0, 100.0, variant=variant), level, tuning
    )
    rock = advance(rock, WARNING_TICKS)
    assert rock.phase is Phase.ACTIVE
    return rock


def expected_zone(name: str, x: float, y: float, margin: float) -> Hitbox:
    """The graze zone of the test shape `name` at (x, y): each shape grown by `margin`.

    Written from 06-scoring.md, Rules, 3 and `grow_hitbox`'s contract: a circle's radius grows
    by it, a box's sides by twice it, a line's thickness by twice it (ends stay), and a polygon
    is itself then one line per edge, of thickness twice the margin.
    """
    if name == "circle":
        return (Circle(x, y, CIRCLE_R + margin),)
    if name == "box":
        return (Box(x, y, BOX_W + 2 * margin, BOX_H + 2 * margin),)
    if name == "line":
        return (Line(-LINE_HALF + x, y, LINE_HALF + x, y, LINE_THICKNESS + 2 * margin),)
    assert name == "polygon"
    points: tuple[tuple[float, float], ...] = tuple((px + x, py + y) for px, py in TRIANGLE)
    edges: tuple[Hitbox, ...] = tuple(
        (Line(a[0], a[1], b[0], b[1], 2 * margin),)
        for a, b in zip(points, points[1:] + points[:1], strict=True)
    )
    return (Polygon(points), *(shape for edge in edges for shape in edge))


@pytest.mark.parametrize("margin", MARGINS)
def test_the_spawner_hands_every_drifter_the_hazards_graze_margin(margin: float | None) -> None:
    tuning: DrifterTuning = tuning_with(margin)
    wanted: float = expected_margin(margin)
    # Every drifter type gets it at birth, the pickup and the blocker too (their zone is ()).
    for drifter_type in SPEEDS:
        born: Drifter = spawn(drifter_type, tuning)
        assert born.graze_margin == wanted, drifter_type
    for name in SHAPE_HITBOX:
        assert active_rock(tuning, name).graze_margin == wanted, name
    # The same through the base's own builder: the field is carried from the birth, and a
    # birth that leaves it out gets the default.
    birth: Birth = Birth(
        x=300.0,
        y=100.0,
        variant="medium",
        width=28.0,
        height=28.0,
        hitbox=SHAPE_HITBOX["circle"],
        speed=1.0,
        warning_ticks=WARNING_TICKS,
        timer_mult=1.0,
        specialty_enabled=None,
        invert=False,
        variant_extra=None,
        rehit_cooldown_ticks=180,
        rehit_dim=0.75,
        type_extra=None,
        telegraph_min_ticks=0,
    )
    assert born_drifter(Meteorite, birth).graze_margin == GRAZE_MARGIN
    assert born_drifter(Meteorite, replace(birth, graze_margin=9.0)).graze_margin == 9.0


@pytest.mark.parametrize("margin", MARGINS)
@pytest.mark.parametrize("name", list(SHAPE_HITBOX))
def test_a_hazards_graze_zone_is_its_hitbox_grown_by_the_margin_for_every_shape_kind(
    name: str, margin: float | None
) -> None:
    tuning: DrifterTuning = tuning_with(margin)
    wanted: float = expected_margin(margin)
    rock: Drifter = spawn_drifter(
        Placement(DrifterType.METEORITE, 300.0, 100.0, variant=name), 1, tuning
    )
    # In the warning there is no hitbox and no zone.
    for _ in range(WARNING_TICKS):
        assert rock.graze_zone() == ()
        rock = rock.update(CTX)
    # Then, as it moves, the zone is the shapes grown, at every position, the margin the same.
    for _ in range(40):
        assert rock.current_hitbox() == place_expected_hitbox(name, rock.x, rock.y)
        assert rock.graze_zone() == expected_zone(name, rock.x, rock.y, wanted)
        assert rock.graze_margin == wanted
        rock = rock.update(CTX)
    assert rock.y > 100.0


def place_expected_hitbox(name: str, x: float, y: float) -> Hitbox:
    """The test shape `name` moved to (x, y), written out."""
    if name == "circle":
        return (Circle(x, y, CIRCLE_R),)
    if name == "box":
        return (Box(x, y, BOX_W, BOX_H),)
    if name == "line":
        return (Line(-LINE_HALF + x, y, LINE_HALF + x, y, LINE_THICKNESS),)
    assert name == "polygon"
    return (Polygon(tuple((px + x, py + y) for px, py in TRIANGLE)),)


@pytest.mark.parametrize("margin", MARGINS)
def test_the_zone_reaches_the_margin_and_no_further_from_each_shape(margin: float | None) -> None:
    """A probe box 1 px wide put just inside the margin overlaps the zone, just outside it not.

    It measures the distance from the hitbox's own edge, so it does not lean on the zone's
    construction. Each probe is put on the middle of a side: the circle's right, the box's
    right, the line's end, the polygon's base (the triangle's flat bottom edge).
    """
    tuning: DrifterTuning = tuning_with(margin)
    wanted: float = expected_margin(margin)
    x: float = 300.0
    y: float = 100.0
    # Edge position of each shape, then the probe's center that far from it.
    sides: dict[str, tuple[float, float, float, float]] = {
        # (edge x, edge y, step x, step y) with the step pointing away from the shape
        "circle": (x + CIRCLE_R, y, 1.0, 0.0),
        "box": (x + BOX_W / 2, y, 1.0, 0.0),
        "line": (x + LINE_HALF + LINE_THICKNESS / 2, y, 1.0, 0.0),
        "polygon": (x, y + 15.0, 0.0, 1.0),
    }
    for name, (edge_x, edge_y, step_x, step_y) in sides.items():
        rock: Drifter = replace(active_rock(tuning, name), x=x, y=y)
        zone: Hitbox = rock.graze_zone()
        inside: Hitbox = (
            Box(edge_x + step_x * (wanted - 1.0), edge_y + step_y * (wanted - 1.0), 1.0, 1.0),
        )
        outside: Hitbox = (
            Box(edge_x + step_x * (wanted + 1.0), edge_y + step_y * (wanted + 1.0), 1.0, 1.0),
        )
        assert hitboxes_overlap(zone, inside), name
        assert not hitboxes_overlap(zone, outside), name


def test_the_graze_zone_never_changes_with_the_level() -> None:
    for margin in MARGINS:
        wanted: float = expected_margin(margin)
        flat: DrifterTuning = tuning_with(margin)
        off: DrifterTuning = replace(
            flat, switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
        )
        for name in SHAPE_HITBOX:
            for tuning in (flat, off):
                for level in range(1, 9):
                    for rock in (
                        active_rock(tuning, name, level),
                        advance(
                            spawn_drifter(
                                Placement(
                                    DrifterType.METEORITE,
                                    300.0,
                                    100.0,
                                    variant=name,
                                    as_level=level,
                                    speed=0.0,
                                ),
                                1,
                                tuning,
                            ),
                            WARNING_TICKS,
                        ),
                    ):
                        assert rock.graze_margin == wanted, (name, level)
                        placed: Drifter = replace(rock, x=300.0, y=100.0)
                        assert placed.graze_zone() == expected_zone(name, 300.0, 100.0, wanted)
        # The other hazards: the chain lightning's arc and nodes while it fires, the ball's circle.
        for level in range(1, 9):
            chain: Drifter = spawn(DrifterType.CHAIN_LIGHTNING, flat, level=level)
            ball: Drifter = spawn(DrifterType.ELECTRIC_BALL, flat, level=level)
            assert chain.graze_margin == wanted
            assert ball.graze_margin == wanted


@pytest.mark.parametrize("margin", MARGINS)
def test_the_chain_lightning_and_the_electric_ball_grow_their_shapes_by_the_margin_while_firing(
    margin: float | None,
) -> None:
    tuning: DrifterTuning = tuning_with(margin)
    wanted: float = expected_margin(margin)
    chain: Drifter = advance(spawn(DrifterType.CHAIN_LIGHTNING, tuning), WARNING_TICKS)
    ball: Drifter = advance(spawn(DrifterType.ELECTRIC_BALL, tuning), WARNING_TICKS)
    assert chain.phase is Phase.ACTIVE
    assert ball.phase is Phase.ACTIVE
    # Charging: no hitbox, so no zone.
    assert chain.graze_zone() == ()
    assert ball.graze_zone() == ()
    fire_chain: Drifter = replace(chain, ticks_in_phase=CHARGE_TICKS)
    fire_ball: Drifter = replace(ball, ticks_in_phase=CHARGE_TICKS)
    x: float = fire_chain.x
    y: float = fire_chain.y
    assert fire_chain.graze_zone() == (
        Line(x + PAIR_NODES[0][0], y, x + PAIR_NODES[1][0], y, ARC_WIDTH + 2 * wanted),
        Circle(x + PAIR_NODES[0][0], y, NODE_SIZE / 2 + wanted),
        Circle(x + PAIR_NODES[1][0], y, NODE_SIZE / 2 + wanted),
    )
    assert fire_ball.graze_zone() == (Circle(fire_ball.x, fire_ball.y, PULSE_RADIUS + wanted),)


@pytest.mark.parametrize("margin", MARGINS)
def test_every_new_drifter_is_outside_and_an_update_carries_the_graze_state_over(
    margin: float | None,
) -> None:
    tuning: DrifterTuning = tuning_with(margin)
    ctx: TickContext = TickContext(ship=HOME, scroll_step_px=1.1)
    for drifter_type in SPEEDS:
        born: Drifter = spawn(drifter_type, tuning)
        assert born.graze_state is GrazeState.OUTSIDE, drifter_type
        for level in (1, 8):
            assert spawn(drifter_type, tuning, level=level).graze_state is GrazeState.OUTSIDE
        # Whatever the run set on it stays through every update: the warning, the switch to
        # ACTIVE, two whole cycles of the chain lightning and the ball.
        for state in GrazeState:
            drifter: Drifter = replace(born, graze_state=state)
            for tick in range(2 * (WARNING_TICKS + CHARGE_TICKS + FIRE_TICKS) + 5):
                drifter = drifter.update(ctx)
                assert drifter.graze_state is state, (drifter_type, state, tick)
    for name in SHAPE_HITBOX:
        assert active_rock(tuning, name).graze_state is GrazeState.OUTSIDE
        # The base's builder starts it OUTSIDE too.
        rock: Drifter = spawn_drifter(
            Placement(DrifterType.METEORITE, 300.0, 100.0, variant=name), 1, tuning
        )
        assert rock.graze_state is GrazeState.OUTSIDE


def at_gap(drifter: Drifter, gap: float) -> Drifter:
    """The rock moved so its hitbox is `gap` px from the ship's foot on the right, home spot.

    The row is the foot's middle one. A gap from 0 to 14 is inside the zone.
    """
    return replace(
        drifter,
        x=HOME_X + FOOT_HALF_W + ROCK_RADIUS + gap,
        y=HOME_Y + FOOT_ROW_DY,
    )


def still_rock(tuning: DrifterTuning) -> Drifter:
    """A medium meteorite that stands still, ACTIVE, with the uid the run's list gives it."""
    spawned: Drifter = spawn_drifter(
        Placement(DrifterType.METEORITE, 100.0, 100.0, speed=0.0), 1, tuning
    )
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, uid=1)


def run_of(*drifters: Drifter, rules: GrazeRules | None = None) -> Run:
    """A run on a still scroll with the drifters numbered from 1, the ship at home."""
    base: Run = start_run() if rules is None else start_run(graze_rules=rules)
    numbered: tuple[Drifter, ...] = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return replace(base, ship=HOME, scroll=STILL, drifters=numbered, next_uid=len(numbered) + 1)


def tick_at(run: Run, gap: float) -> Run:
    """Put the ship at home at rest and the first drifter at `gap`, then step one tick."""
    moved: tuple[Drifter, ...] = (at_gap(run.drifters[0], gap), *run.drifters[1:])
    return step_run(replace(run, ship=HOME, drifters=moved), NO_KEY)


def paid_run(rules: GrazeRules | None = None) -> Run:
    """The run on the state after the tick that pays one graze: inside the zone, then outside."""
    run: Run = run_of(still_rock(make_tuning()), rules=rules)
    run = tick_at(run, IN)
    assert run.grazes == 0
    assert run.drifters[0].graze_state is GrazeState.INSIDE
    run = tick_at(run, OUT)
    assert run.grazes == 1
    assert run.drifters[0].graze_state is GrazeState.SPENT
    return run


def hold(run: Run, *, waiting: bool = False, protected: bool = False) -> Run:
    """One more tick with the ship put back at home and the rock where it is.

    `waiting` stands the ship in the respawn wait, `protected` makes it invulnerable going in.
    """
    return step_run(
        replace(
            run,
            ship=HOME,
            waiting=waiting,
            invuln_ticks_left=INVULN_TICKS if protected else 0,
        ),
        NO_KEY,
    )


def graze_popups(run: Run) -> list[PointsPopup]:
    """The popups of kind GRAZE the run holds, oldest first."""
    return [popup for popup in run.popups if popup.kind is PopupKind.GRAZE]


def rules_id(rules: GrazeRules) -> str:
    """A short id for a parametrized test."""
    return f"points{rules.points}-popup{rules.popup_ticks}-ring{rules.ring_ticks}"


def check_popup_over_time(
    popups_by_state: list[list[PointsPopup]], rules: GrazeRules, x: float, y: float
) -> None:
    """The states after the paying tick: each popup state is age k, same x, y rising, then none.

    `popups_by_state[0]` is the state after the paying tick (age 0).
    """
    shown: int = 0
    for age, popups in enumerate(popups_by_state):
        if age < rules.popup_ticks:
            assert len(popups) == 1, age
            popup: PointsPopup = popups[0]
            assert popup.kind is PopupKind.GRAZE
            assert popup.points == rules.points
            assert popup.age_ticks == age
            assert popup.lifetime_ticks == rules.popup_ticks
            assert popup.x == x
            assert popup.y == pytest.approx(y - age * rules.popup_rise_per_tick)
            shown += 1
        else:
            assert popups == [], age
    assert shown == rules.popup_ticks


@pytest.mark.parametrize("rules", ALL_RULES, ids=rules_id)
def test_a_graze_popup_is_of_kind_graze_shows_the_points_rises_and_is_gone_after(
    rules: GrazeRules,
) -> None:
    # Straight from the functions, on a ship that is nowhere near home.
    ship: Ship = Ship(x=123.5, y=301.25, vx=2.0, vy=-1.0)
    popup: PointsPopup = graze_popup(rules, ship)
    assert popup.kind is PopupKind.GRAZE
    assert popup.x == 123.5
    assert popup.start_y == 301.25
    assert popup.y == 301.25
    assert popup.points == rules.points
    assert popup.lifetime_ticks == rules.popup_ticks
    assert popup.rise_per_tick == rules.popup_rise_per_tick
    assert popup.age_ticks == 0
    states: list[list[PointsPopup]] = [[popup]]
    shown: tuple[PointsPopup, ...] = (popup,)
    for _ in range(rules.popup_ticks + 2):
        shown = step_popups(shown)
        states.append(list(shown))
    check_popup_over_time(states, rules, 123.5, 301.25)

    # Inside a run: it appears on the paying tick at the ship's center after the ship's move.
    paying: Run = paid_run(rules)
    moved: Ship = ship_step(HOME, NO_KEY)
    assert moved.y != HOME_Y
    assert paying.ship == moved
    first: PointsPopup = graze_popups(paying)[0]
    assert (first.x, first.start_y) == (moved.x, moved.y)
    assert first.age_ticks == 0
    run_states: list[list[PointsPopup]] = [graze_popups(paying)]
    run: Run = paying
    for _ in range(rules.popup_ticks + 2):
        run = hold(run)
        assert run.grazes == 1
        run_states.append(graze_popups(run))
    check_popup_over_time(run_states, rules, moved.x, moved.y)


def test_a_coin_popup_keeps_kind_coin_beside_a_graze_popup() -> None:
    # A popup built the old way is a coin's.
    plain: PointsPopup = PointsPopup(
        x=1.0, start_y=2.0, points=50, lifetime_ticks=60, rise_per_tick=0.5
    )
    assert plain.kind is PopupKind.COIN
    assert step_popups((plain,))[0].kind is PopupKind.COIN
    tuning: DrifterTuning = make_tuning()
    # The tick a rock pays and a coin is collected at once: coin popup first, then the graze one.
    run: Run = run_of(still_rock(tuning))
    run = tick_at(run, IN)
    coin: Drifter = spawn_drifter(Placement(DrifterType.COIN, HOME_X, HOME_Y), 1, tuning)
    run = replace(run, drifters=(*run.drifters, replace(coin, uid=2)), next_uid=3)
    run = tick_at(run, OUT)
    assert run.grazes == 1
    assert run.coin_points == 50
    assert [popup.kind for popup in run.popups] == [PopupKind.COIN, PopupKind.GRAZE]
    assert [popup.points for popup in run.popups] == [50, GRAZE_POINTS]
    # Every popup keeps its kind while it ages, and both are gone after 60 states.
    for age in range(1, GRAZE_POPUP_TICKS):
        run = hold(run)
        assert [popup.kind for popup in run.popups] == [PopupKind.COIN, PopupKind.GRAZE], age
        assert [popup.age_ticks for popup in run.popups] == [age, age]
    run = hold(run)
    assert run.popups == ()


def check_ring_state(ring: GrazeRing, rules: GrazeRules, age: int) -> None:
    """A ring that shows on the state at `age`: its size and opacity on the even step."""
    assert ring.age_ticks == age
    assert ring.line_width == rules.ring_width
    assert ring.lifetime_ticks == rules.ring_ticks
    step: float = (rules.ring_end_diameter - rules.ring_start_diameter) / rules.ring_ticks
    assert ring.diameter == pytest.approx(rules.ring_start_diameter + step * age)
    assert ring.opacity == pytest.approx(1.0 - age / rules.ring_ticks)
    assert ring.opacity > 0.0


@pytest.mark.parametrize("rules", ALL_RULES, ids=rules_id)
def test_a_graze_ring_starts_full_grows_and_fades_evenly_and_is_gone_after(
    rules: GrazeRules,
) -> None:
    ring: GrazeRing = graze_ring(rules)
    assert ring.age_ticks == 0
    assert ring.start_diameter == rules.ring_start_diameter
    assert ring.end_diameter == rules.ring_end_diameter
    assert ring.line_width == rules.ring_width
    assert ring.lifetime_ticks == rules.ring_ticks
    assert ring.diameter == rules.ring_start_diameter
    assert ring.opacity == 1.0
    # Straight from `step_graze_rings`: shows on exactly `ring_ticks` states, even steps.
    rings: tuple[GrazeRing, ...] = (ring,)
    sizes: list[float] = []
    fades: list[float] = []
    shown: int = 0
    for age in range(rules.ring_ticks + 2):
        if age < rules.ring_ticks:
            assert len(rings) == 1, age
            check_ring_state(rings[0], rules, age)
            sizes.append(rings[0].diameter)
            fades.append(rings[0].opacity)
            shown += 1
        else:
            assert rings == (), age
        rings = step_graze_rings(rings)
    assert shown == rules.ring_ticks
    for before, after in pairwise(sizes):
        assert after - before == pytest.approx(
            (rules.ring_end_diameter - rules.ring_start_diameter) / rules.ring_ticks
        )
    for before, after in pairwise(fades):
        assert after - before == pytest.approx(-1.0 / rules.ring_ticks)

    # Inside a run: one ring on the paying tick at age 0, then the same states, gone after.
    run: Run = paid_run(rules)
    for age in range(rules.ring_ticks + 2):
        if age < rules.ring_ticks:
            assert len(run.graze_rings) == 1, age
            check_ring_state(run.graze_rings[0], rules, age)
        else:
            assert run.graze_rings == (), age
        run = hold(run)
    assert run.grazes == 1


def test_step_graze_rings_ages_every_ring_in_order_and_drops_only_the_finished() -> None:
    assert step_graze_rings(()) == ()
    old: GrazeRing = replace(graze_ring(GrazeRules()), age_ticks=GRAZE_RING_TICKS - 1)
    new: GrazeRing = graze_ring(GrazeRules())
    custom: GrazeRing = graze_ring(CUSTOM_RULES)
    aged: tuple[GrazeRing, ...] = step_graze_rings((old, new, custom))
    # The old one reaches its life and goes; the others are one tick older, in order.
    assert aged == (replace(new, age_ticks=1), replace(custom, age_ticks=1))
    assert (old.age_ticks, new.age_ticks) == (GRAZE_RING_TICKS - 1, 0)


@pytest.mark.parametrize("state", ["wait", "protected", "wait and protected"])
@pytest.mark.parametrize("rules", ALL_RULES, ids=rules_id)
def test_rings_and_graze_popups_keep_aging_during_the_respawn_wait_and_on_protected_ticks(
    rules: GrazeRules, state: str
) -> None:
    waiting: bool = "wait" in state
    protected: bool = "protected" in state
    run: Run = paid_run(rules)
    ship_after: Ship = run.ship
    popups: list[list[PointsPopup]] = [graze_popups(run)]
    for age in range(rules.ring_ticks + rules.popup_ticks + 2):
        # The ring's state is the same as with a free ship: age k on the state k ticks later.
        if age < rules.ring_ticks:
            assert len(run.graze_rings) == 1, age
            check_ring_state(run.graze_rings[0], rules, age)
        else:
            assert run.graze_rings == (), age
        run = hold(run, waiting=waiting, protected=protected)
        popups.append(graze_popups(run))
        # Nothing here pays a second time and no life is lost.
        assert run.grazes == 1
        assert run.lives == 3
    # The popup aged and left on the same ticks as with a free ship.
    check_popup_over_time(popups, rules, ship_after.x, ship_after.y)


def test_graze_rules_hold_the_gdd_graze_values() -> None:
    rules: GrazeRules = GrazeRules()
    assert rules.points == GRAZE_POINTS
    assert rules.popup_ticks == GRAZE_POPUP_TICKS
    assert rules.popup_rise_per_tick == GRAZE_POPUP_RISE
    assert rules.ring_ticks == GRAZE_RING_TICKS
    assert rules.ring_start_diameter == GRAZE_RING_START
    assert rules.ring_end_diameter == GRAZE_RING_END
    assert rules.ring_width == GRAZE_RING_WIDTH
    assert rules == DEFAULT_GRAZE_RULES
    assert dataclasses.asdict(rules) == {
        "points": 25,
        "popup_ticks": 60,
        "popup_rise_per_tick": 0.5,
        "ring_ticks": 15,
        "ring_start_diameter": 16.0,
        "ring_end_diameter": 32.0,
        "ring_width": 1,
    }
    # The names of the defaults hold the same values.
    assert DEFAULT_GRAZE_POINTS == GRAZE_POINTS
    assert DEFAULT_GRAZE_POPUP_TICKS == GRAZE_POPUP_TICKS
    assert DEFAULT_GRAZE_POPUP_RISE_PER_TICK == GRAZE_POPUP_RISE
    assert DEFAULT_GRAZE_RING_TICKS == GRAZE_RING_TICKS
    assert DEFAULT_GRAZE_RING_START_DIAMETER == GRAZE_RING_START
    assert DEFAULT_GRAZE_RING_END_DIAMETER == GRAZE_RING_END
    assert DEFAULT_GRAZE_RING_WIDTH == GRAZE_RING_WIDTH
    # A field left out keeps its default, one given is kept, and the rest stay.
    one: GrazeRules = GrazeRules(points=10)
    assert one.points == 10
    assert replace(one, points=GRAZE_POINTS) == rules
    # A run started with no rules pays with the GDD's.
    assert start_run().graze_rules == rules
