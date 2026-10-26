"""The graze rule inside the run: step 5b, the score, the last life, game over, a new run, the log.

Contract: docs/contracts/systems/run.md, Diagram (the two graze state tables), Interface
(DRA-117: `core/graze.py` `check_grazes`, `GrazeCheck`, `GrazeRules`; `core/run.py`), Rules (step
5b, a last-life tick, a game-over tick, Score, Other rules, Logging);
docs/design/gdd/06-scoring.md, Rules 3 to 8.
Task: docs/contracts/DRA-117/tasks/DRA-117-05-qa-engineer.md. One test per behavior it lists.
The graze margin from tuning and the popup's and the ring's own state over time are DRA-117-06.

The tuning records are built here from the GDD values below, never read from game/tuning/, and no
expected number is imported from the code under test. The ship is put back at rest on its home
spot before every tick (a ship held still, so it flies and hovers) and the hazard is moved
instead, by the gap between its hitbox and the ship's foot. The ship's foot is 32 wide, 12 tall,
at the bottom of its 32 x 32 square (04-ship.md, hitbox), so the foot's right edge is 16 px right
of the ship's center and its middle row 10 px below it. A gap above 14 is outside the zone, a gap
from 0 to 14 is inside it without touching, and a gap below 0 is a touch.
"""

import copy
import logging
from collections.abc import Sequence
from dataclasses import replace

import pytest

from core.collision import Box, Circle, Hitbox, Line
from core.drifters.base import Drifter, DrifterType, GrazeState, Phase, TickContext
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightning,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
)
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.electric_ball import (
    ElectricBall,
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
)
from core.drifters.floating_island import (
    FloatingIsland,
    IslandShape,
    IslandTypeExtra,
    IslandVariantExtra,
)
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.graze import (
    DEFAULT_GRAZE_RULES,
    GrazeCheck,
    GrazeRules,
    check_grazes,
)
from core.popup import PointsPopup, PopupKind
from core.run import Run, next_run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, start_waves

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

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

REHIT_COOLDOWN: int = 180
"""Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

PX_PER_METER: int = 10
SCROLL_SPEED_TENTHS: int = 11
SCROLL_START_DELAY: int = 30
"""Source: 03-world-and-camera.md, px_per_meter (locked), scroll_base 1.1 px (guess) and
scroll_start_delay (guess)."""

SCREEN_W: float = 640.0
SCREEN_H: float = 480.0
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

FOOT_HALF_W: float = 16.0
FOOT_ROW_DY: float = 10.0
"""The ship's foot: half its 32 px width, and its middle row below the center (16 - 12 / 2).
Source: 04-ship.md, hitbox (guess)."""

ROCK_RADIUS: float = 14.0
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

CHARGE_TICKS: int = 120
FIRE_TICKS: int = 120
"""Source: drifters/03-chain-lightning.md and drifters/10-electric-ball.md, Values (guess)."""

PULSE_RADIUS: float = 64.0
BALL_SIZE: float = 16.0
"""px. Source: drifters/10-electric-ball.md, ball_size, pulse_radius (guess)."""

NODE_SPACING: float = 128.0
NODE_SIZE: float = 12.0
ARC_WIDTH: float = 6.0
"""px. Source: drifters/03-chain-lightning.md, node_spacing, node_size, arc_width (guess)."""

WARNING_TICKS: int = 60
"""ticks. Source: 07-drifters.md, entry_warning_ticks (guess)."""

SPEED_RATIO: float = 0.375
"""Source: the hazards' speed_ratio (guess)."""

RUN_LOGGER = "core.run"
GRAZE_LOGGER = "core.graze"
"""Logger names. Source: systems/run.md, Logging, and Interface (core/graze.py logs nothing)."""

NO_KEY = Thrust()
UP = Thrust(up=True)

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

HOME: Ship = Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)

IN: float = 6.0
OUT: float = 20.0
TOUCH: float = -4.0
"""Gaps, px, between a hazard's hitbox and the ship's foot: inside the zone, outside it (the zone
reaches 14), and 4 px into the hitbox."""

STILL: Scroll = Scroll()
"""A scroll at tick 0: the world stands still for the first 30 ticks, so a parked coin or island
stays where it is put and the meters are 0."""

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""

ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, ROCK_RADIUS),)
COIN_HITBOX: Hitbox = (Box(0.0, 0.0, 12.0, 10.0),)
BOX_ISLAND_SIZE: float = 120.0
"""The box island, 120 x 120. Source: drifters/05-floating-islands.md, Values (guess)."""

CTX: TickContext = TickContext(ship=HOME)

PAIR_NODES: tuple[tuple[float, float], ...] = (
    (-NODE_SPACING / 2, 0.0),
    (NODE_SPACING / 2, 0.0),
)
"""The chain lightning's flat pair, in px. Source: drifters.md, Rules, Chain lightning, Layout."""

PAIR_LAYOUT: ChainLayout = ChainLayout(
    nodes=PAIR_NODES, arcs=((0, 1),), invert_mirror=InvertMirror.LEFT_RIGHT
)

LAST_LIFE_DELAY: int = 120
"""Ticks from the death tick to game over. Source: 02-game-flow.md, Values, last_life_delay
(guess)."""

CUSTOM_RULES: GrazeRules = GrazeRules(
    points=40,
    popup_ticks=7,
    popup_rise_per_tick=1.5,
    ring_ticks=4,
    ring_start_diameter=10.0,
    ring_end_diameter=20.0,
    ring_width=3,
)
"""Values that are none of the GDD's, to show the run pays and shows what it was given."""


def make_tuning() -> DrifterTuning:
    """Build the tuning of every drifter the tests below place, from the GDD values above.

    The meteorite's medium variant, the coin's common one, the island's box, the chain
    lightning's flat pair and the electric ball, each the way `app.tuning` builds it.
    """
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK_HITBOX)},
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            DrifterType.COIN: DrifterTypeTuning(
                variants={
                    "common": VariantTuning(
                        width=12,
                        height=20,
                        hitbox=COIN_HITBOX,
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
                        width=BOX_ISLAND_SIZE,
                        height=BOX_ISLAND_SIZE,
                        hitbox=(Box(0.0, 0.0, BOX_ISLAND_SIZE, BOX_ISLAND_SIZE),),
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
                            Line(
                                PAIR_NODES[0][0],
                                0.0,
                                PAIR_NODES[1][0],
                                0.0,
                                ARC_WIDTH,
                            ),
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


TUNING: DrifterTuning = make_tuning()


def rock(x: float = 0.0, y: float = 0.0) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, 100.0, 100.0), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0, x=x, y=y)


def coin(x: float, y: float) -> Coin:
    """A common coin, ACTIVE from birth."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.COIN, x, y), 1, TUNING)
    assert isinstance(spawned, Coin)
    return spawned


def island(x: float, y: float) -> FloatingIsland:
    """A box island, ACTIVE from birth."""
    spawned: Drifter = spawn_drifter(
        Placement(DrifterType.FLOATING_ISLAND, x, y, variant="box"), 1, TUNING
    )
    assert isinstance(spawned, FloatingIsland)
    return spawned


def advance[T: Drifter](drifter: T, ticks: int) -> T:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(CTX)
    return drifter


def ball(x: float, y: float, cycle_tick: int) -> ElectricBall:
    """A ball held still at (x, y), ACTIVE, with `ticks_in_phase` at `cycle_tick`."""
    spawned: Drifter = spawn_drifter(
        Placement(DrifterType.ELECTRIC_BALL, x, y, speed=0.0), 1, TUNING
    )
    assert isinstance(spawned, ElectricBall)
    active: ElectricBall = advance(spawned, WARNING_TICKS)
    assert active.phase is Phase.ACTIVE
    return replace(active, ticks_in_phase=cycle_tick)


def chain(x: float, y: float, cycle_tick: int) -> ChainLightning:
    """A flat chain lightning pair held still at (x, y), ACTIVE, at `cycle_tick`."""
    spawned: Drifter = spawn_drifter(
        Placement(DrifterType.CHAIN_LIGHTNING, x, y, speed=0.0), 1, TUNING
    )
    assert isinstance(spawned, ChainLightning)
    active: ChainLightning = advance(spawned, WARNING_TICKS)
    assert active.phase is Phase.ACTIVE
    return replace(active, ticks_in_phase=cycle_tick)


def run_of(
    *drifters: Drifter,
    ship: Ship = HOME,
    lives: int = LIVES_START,
    waiting: bool = False,
    invuln_ticks_left: int = 0,
    coin_points: int = 0,
    scroll: Scroll = STILL,
    rules: GrazeRules | None = None,
) -> Run:
    """A run on the given scroll with the drifters numbered from 1, in order."""
    base: Run = start_run() if rules is None else start_run(graze_rules=rules)
    numbered = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return replace(
        base,
        ship=ship,
        scroll=scroll,
        lives=lives,
        waiting=waiting,
        invuln_ticks_left=invuln_ticks_left,
        coin_points=coin_points,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def at_gap(drifter: Drifter, gap: float, *, left: bool = False) -> Drifter:
    """The rock moved so its hitbox is `gap` px from the ship's foot (home spot), right or left.

    The row is the foot's middle one. A gap from 0 to 14 is inside the zone, below 0 a touch.
    """
    sign: float = -1.0 if left else 1.0
    return replace(
        drifter,
        x=HOME_X + sign * (FOOT_HALF_W + ROCK_RADIUS + gap),
        y=HOME_Y + FOOT_ROW_DY,
    )


def step_at(
    run: Run,
    gap: float,
    *,
    thrust: Thrust = NO_KEY,
    index: int = 0,
    left: bool = False,
) -> Run:
    """Put the ship back at home at rest, the drifter at `index` at `gap`, and step one tick."""
    moved: list[Drifter] = list(run.drifters)
    moved[index] = at_gap(moved[index], gap, left=left)
    return step_run(replace(run, ship=HOME, drifters=tuple(moved)), thrust)


def walk(run: Run, gaps: Sequence[float], *, thrust: Thrust = NO_KEY) -> list[Run]:
    """Step once per gap with the first drifter there; the run after each tick."""
    states: list[Run] = []
    for gap in gaps:
        run = step_at(run, gap, thrust=thrust)
        states.append(run)
    return states


def graze_state(run: Run, index: int = 0) -> GrazeState:
    """The graze state of the drifter at `index` in the run."""
    return run.drifters[index].graze_state


def paid(states: Sequence[Run]) -> list[int]:
    """The grazes after each tick."""
    return [state.grazes for state in states]


def grazes_of(caplog: pytest.LogCaptureFixture) -> list[str]:
    """The `drifter graze` messages logged, in order."""
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith("drifter graze")]


def test_a_hazard_passed_beside_pays_one_graze_on_the_tick_the_ship_leaves_its_zone() -> None:
    run = run_of(rock())
    states = walk(run, [OUT, OUT, IN, IN, IN, OUT, OUT])
    assert paid(states) == [0, 0, 0, 0, 0, 1, 1]
    assert [graze_state(s) for s in states] == [
        GrazeState.OUTSIDE,
        GrazeState.OUTSIDE,
        GrazeState.INSIDE,
        GrazeState.INSIDE,
        GrazeState.INSIDE,
        GrazeState.SPENT,
        GrazeState.SPENT,
    ]
    # Nothing pays on the tick it entered, and nothing is shown before the exit.
    for state in states[:5]:
        assert state.popups == ()
        assert state.graze_rings == ()
        assert state.score == 0
    # The exit tick: one graze, one graze popup at the ship's center, one ring, and nothing else.
    exit_tick = states[5]
    assert exit_tick.grazes == 1
    assert exit_tick.score == GRAZE_POINTS
    assert len(exit_tick.popups) == 1
    popup: PointsPopup = exit_tick.popups[0]
    assert popup.kind is PopupKind.GRAZE
    assert popup.points == GRAZE_POINTS
    assert (popup.x, popup.start_y) == (exit_tick.ship.x, exit_tick.ship.y)
    assert popup.age_ticks == 0
    assert popup.lifetime_ticks == GRAZE_POPUP_TICKS
    assert popup.rise_per_tick == GRAZE_POPUP_RISE
    assert len(exit_tick.graze_rings) == 1
    ring = exit_tick.graze_rings[0]
    assert ring.age_ticks == 0
    assert (ring.start_diameter, ring.end_diameter) == (GRAZE_RING_START, GRAZE_RING_END)
    assert (ring.line_width, ring.lifetime_ticks) == (GRAZE_RING_WIDTH, GRAZE_RING_TICKS)
    assert exit_tick.lives == LIVES_START
    assert exit_tick.invuln_ticks_left == 0
    assert exit_tick.drifters[0].rehit_ticks_left == 0
    # The popup and the ring then age on their own and the count stays.
    after = states[6]
    assert after.popups[0].age_ticks == 1
    assert after.graze_rings[0].age_ticks == 1
    assert after.grazes == 1


def test_entering_and_leaving_the_same_hazards_zone_again_pays_nothing_more() -> None:
    states = walk(run_of(rock()), [IN, OUT, IN, OUT, IN, IN, OUT, OUT])
    assert paid(states) == [0, 1, 1, 1, 1, 1, 1, 1]
    assert [graze_state(s) for s in states[1:]] == [GrazeState.SPENT] * 7
    for state in states[1:]:
        assert len(state.popups) == 1
        assert len(state.graze_rings) == 1
        assert state.score == GRAZE_POINTS


def test_a_hit_a_pass_through_while_invulnerable_and_a_touch_in_the_wait_never_pay() -> None:
    # A hit: inside, then a touch that costs a life, then out, and in and out again once the
    # protection and the cooldown are over. Nothing pays before the hit or after it.
    states = walk(run_of(rock()), [IN, IN, TOUCH])
    assert paid(states) == [0, 0, 0]
    assert states[2].lives == LIVES_START - 1
    assert states[2].drifters[0].rehit_ticks_left == REHIT_COOLDOWN
    assert graze_state(states[2]) is GrazeState.SPENT
    run = states[2]
    for gap in [IN, OUT, IN, OUT]:
        run = step_at(run, gap)
        assert run.grazes == 0
    for _ in range(INVULN_TICKS + REHIT_COOLDOWN + 5):
        run = step_at(run, OUT)
    assert run.invuln_ticks_left == 0
    assert run.drifters[0].rehit_ticks_left == 0
    for gap in [IN, IN, OUT, IN, OUT]:
        run = step_at(run, gap)
        assert run.grazes == 0
        assert graze_state(run) is GrazeState.SPENT
    assert run.popups == ()
    assert run.graze_rings == ()
    # Passed through while invulnerable: the touch is no hit, and it still ends the graze for good,
    # even after the protection has run out.
    run = run_of(rock(), invuln_ticks_left=10)
    for gap in [IN, TOUCH, IN, OUT]:
        run = step_at(run, gap)
        assert run.grazes == 0
        assert run.lives == LIVES_START
    assert graze_state(run) is GrazeState.SPENT
    assert run.drifters[0].rehit_ticks_left == 0
    for _ in range(12):
        run = step_at(run, OUT)
    assert run.invuln_ticks_left == 0
    for gap in [IN, OUT, IN, OUT]:
        run = step_at(run, gap)
        assert run.grazes == 0
    # Touched while standing in the respawn wait: the same.
    run = run_of(rock(), waiting=True)
    run = step_at(run, TOUCH)
    assert run.waiting
    assert graze_state(run) is GrazeState.SPENT
    for gap in [IN, OUT]:
        run = step_at(run, gap)
        assert run.grazes == 0
    run = step_at(run, IN, thrust=UP)
    assert not run.waiting
    run = step_at(run, OUT, thrust=UP)
    assert run.grazes == 0
    assert graze_state(run) is GrazeState.SPENT
    # The touch alone, with the ship invulnerable in the wait, is the same.
    run = run_of(rock(), waiting=True, invuln_ticks_left=20)
    for gap in [IN, TOUCH, IN, OUT]:
        run = step_at(run, gap)
    assert run.grazes == 0
    assert graze_state(run) is GrazeState.SPENT


def test_an_exit_on_a_protected_tick_pays_nothing_and_a_later_clean_exit_pays() -> None:
    # Two protected ticks. The exit on the second one is blocked and the hazard goes back to
    # OUTSIDE, so a later clean exit by the same hazard still pays.
    states = walk(run_of(rock(), invuln_ticks_left=2), [IN, OUT])
    assert [s.invuln_ticks_left for s in states] == [1, 0]
    assert paid(states) == [0, 0]
    assert graze_state(states[0]) is GrazeState.INSIDE
    assert graze_state(states[1]) is GrazeState.OUTSIDE
    assert states[1].popups == ()
    assert states[1].graze_rings == ()
    later = walk(states[1], [IN, OUT])
    assert paid(later) == [0, 1]
    assert graze_state(later[0]) is GrazeState.INSIDE
    assert graze_state(later[1]) is GrazeState.SPENT
    # Three protected ticks (3, 2 and 1 left going in). The exit on the third, the last protected
    # one, pays nothing; the same exit one tick later, the first unprotected one, pays.
    last_protected = walk(run_of(rock(), invuln_ticks_left=3), [IN, IN, OUT])
    assert [s.invuln_ticks_left for s in last_protected] == [2, 1, 0]
    assert paid(last_protected) == [0, 0, 0]
    assert graze_state(last_protected[2]) is GrazeState.OUTSIDE
    first_unprotected = walk(run_of(rock(), invuln_ticks_left=3), [IN, IN, IN, OUT])
    assert paid(first_unprotected) == [0, 0, 0, 1]
    assert first_unprotected[3].invuln_ticks_left == 0
    assert graze_state(first_unprotected[3]) is GrazeState.SPENT
    # Not a hit and no cooldown on any of those passes.
    assert first_unprotected[3].drifters[0].rehit_ticks_left == 0
    assert first_unprotected[3].lives == LIVES_START


def test_a_ship_that_entered_while_invulnerable_and_leaves_after_protection_pays() -> None:
    states = walk(run_of(rock(), invuln_ticks_left=3), [IN, IN, IN, IN, IN, OUT])
    assert [s.invuln_ticks_left for s in states] == [2, 1, 0, 0, 0, 0]
    assert [graze_state(s) for s in states[:5]] == [GrazeState.INSIDE] * 5
    assert paid(states) == [0, 0, 0, 0, 0, 1]
    assert graze_state(states[5]) is GrazeState.SPENT
    assert len(states[5].popups) == 1
    assert len(states[5].graze_rings) == 1


def test_an_exit_in_the_respawn_wait_pays_nothing_but_the_press_tick_that_ends_it_pays() -> None:
    # Standing in the wait with the protection already over: the exit pays nothing, the hazard
    # goes back to OUTSIDE, and the ship is still waiting.
    states = walk(run_of(rock(), waiting=True), [IN, IN, OUT])
    assert all(s.waiting for s in states)
    assert all(s.invuln_ticks_left == 0 for s in states)
    assert [graze_state(s) for s in states] == [
        GrazeState.INSIDE,
        GrazeState.INSIDE,
        GrazeState.OUTSIDE,
    ]
    assert paid(states) == [0, 0, 0]
    # More ticks standing, in and out again: still nothing.
    run = states[2]
    for gap in [IN, OUT, OUT]:
        run = step_at(run, gap)
        assert run.waiting
    assert run.grazes == 0
    assert graze_state(run) is GrazeState.OUTSIDE
    # Back inside, still standing, then the press tick that ends the wait with the exit on it.
    run = step_at(run, IN)
    assert graze_state(run) is GrazeState.INSIDE
    assert run.waiting
    pressed = step_at(run, OUT, thrust=UP)
    assert not pressed.waiting
    assert pressed.grazes == 1
    assert graze_state(pressed) is GrazeState.SPENT
    popup = pressed.popups[0]
    assert popup.kind is PopupKind.GRAZE
    assert (popup.x, popup.start_y) == (pressed.ship.x, pressed.ship.y)
    assert len(pressed.graze_rings) == 1
    # A wait that ran out of protection inside the zone and ends with a clean exit on a later
    # flying tick pays too: the exit blocked in the wait left the hazard OUTSIDE, and the press
    # tick took it INSIDE.
    flying = walk(run_of(rock(), waiting=True), [IN, OUT])
    assert paid(flying) == [0, 0]
    again = step_at(flying[1], IN, thrust=UP)
    assert not again.waiting
    assert graze_state(again) is GrazeState.INSIDE
    leaving = step_at(again, OUT)
    assert leaving.grazes == 1
    # The ship held still in the air (flying, hovering) pays: the scenes above put it back at
    # rest every tick and it grazed.
    assert not leaving.waiting


@pytest.mark.parametrize("make", ["chain", "ball"])
def test_a_hazard_that_stops_firing_with_the_ship_in_its_zone_pays_and_never_pays_again(
    make: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    last_firing: int = CHARGE_TICKS + FIRE_TICKS - 2
    foot_right: float = HOME_X + FOOT_HALF_W
    foot_left: float = HOME_X - FOOT_HALF_W
    row: float = HOME_Y + FOOT_ROW_DY
    hazard: Drifter
    charging: Drifter
    type_name: str
    if make == "ball":
        # The circle's left edge is 6 px right of the foot.
        hazard = ball(foot_right + IN + PULSE_RADIUS, row, last_firing)
        type_name = "electric_ball"
        charging = ball(foot_right + IN + PULSE_RADIUS, row, 0)
    else:
        # The right node's right edge is 6 px left of the foot.
        hazard = chain(foot_left - IN - NODE_SIZE / 2 - NODE_SPACING / 2, row, last_firing)
        type_name = "chain_lightning"
        charging = chain(foot_left - IN - NODE_SIZE / 2 - NODE_SPACING / 2, row, 0)
    assert hazard.graze_zone() != ()
    # Charging with the ship beside it: no zone, nothing inside, nothing pays.
    run = run_of(charging)
    for tick in range(CHARGE_TICKS - 1):
        run = step_run(replace(run, ship=HOME), NO_KEY)
        assert run.grazes == 0, tick
        assert graze_state(run) is GrazeState.OUTSIDE, tick
    # Firing on the last firing tick (the ship inside, not touching), then it stops: pays on the
    # tick the zone goes away.
    run = run_of(hazard)
    run = step_run(replace(run, ship=HOME), NO_KEY)
    assert run.drifters[0].graze_zone() != ()
    assert graze_state(run) is GrazeState.INSIDE
    assert run.grazes == 0
    run = step_run(replace(run, ship=HOME), NO_KEY)
    assert run.drifters[0].graze_zone() == ()
    assert run.grazes == 1
    assert run.lives == LIVES_START
    assert graze_state(run) is GrazeState.SPENT
    assert len(run.popups) == 1
    assert grazes_of(caplog) == [f"drifter graze id=1 type={type_name}"]
    # Its next firing, with the ship still in the zone, and the end of that one: nothing more.
    for tick in range(CHARGE_TICKS + FIRE_TICKS + 2):
        run = step_run(replace(run, ship=HOME), NO_KEY)
        assert run.grazes == 1, tick
        assert run.lives == LIVES_START, tick
        assert graze_state(run) is GrazeState.SPENT, tick
    assert len(grazes_of(caplog)) == 1


def test_a_hazard_dropped_off_screen_with_the_ship_in_its_zone_pays_on_the_tick_it_is_dropped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    # The ship stands 8 px from the left wall (foot's left edge at 8). The rock is 7 px from the
    # foot with its right edge 1 px on screen, then 0.5 px past the edge: off screen, dropped.
    ship = Ship(x=24.0, y=HOME_Y, vx=0.0, vy=0.0)
    row = HOME_Y + FOOT_ROW_DY
    run = run_of(rock(-13.0, row), ship=ship)
    run = step_run(replace(run, ship=ship), NO_KEY)
    assert len(run.drifters) == 1
    assert run.drifters[0].has_entered
    assert not run.drifters[0].is_off_screen()
    assert graze_state(run) is GrazeState.INSIDE
    assert run.grazes == 0
    run = step_run(
        replace(run, ship=ship, drifters=(replace(run.drifters[0], x=-14.5),)),
        NO_KEY,
    )
    assert run.drifters == ()
    assert run.grazes == 1
    assert len(run.popups) == 1
    assert len(run.graze_rings) == 1
    messages = [r.getMessage() for r in caplog.records]
    graze_at = next(i for i, m in enumerate(messages) if m.startswith("drifter graze"))
    gone_at = next(i for i, m in enumerate(messages) if m.startswith("drifter gone"))
    assert graze_at < gone_at
    # The same rock leaving with the ship nowhere near its zone pays nothing.
    far = Ship(x=200.0, y=HOME_Y, vx=0.0, vy=0.0)
    run = run_of(rock(-13.0, row), ship=far)
    run = step_run(replace(run, ship=far), NO_KEY)
    run = step_run(replace(run, ship=far, drifters=(replace(run.drifters[0], x=-14.5),)), NO_KEY)
    assert run.drifters == ()
    assert run.grazes == 0


def test_coins_and_floating_islands_never_change_graze_state_and_never_pay() -> None:
    # A coin 6 px from the foot's right edge, then 20 px: moved past the ship and away.
    coin_run = run_of(coin(HOME_X + FOOT_HALF_W + 6.0 + 6.0, HOME_Y + FOOT_ROW_DY))
    island_run = run_of(island(HOME_X + FOOT_HALF_W + 6.0 + BOX_ISLAND_SIZE / 2, HOME_Y))
    for run, half in ((coin_run, 6.0), (island_run, BOX_ISLAND_SIZE / 2)):
        for gap in [OUT, IN, IN, 1.0, OUT, IN, OUT]:
            moved = replace(run.drifters[0], x=HOME_X + FOOT_HALF_W + gap + half)
            run = step_run(replace(run, ship=HOME, drifters=(moved,)), NO_KEY)
            assert run.grazes == 0
            assert run.popups == ()
            assert run.graze_rings == ()
            assert run.score == 0
            assert run.drifters[0].graze_state is GrazeState.OUTSIDE
            assert run.drifters[0].graze_zone() == ()
    # A coin the ship takes pays its points and no graze.
    on_ship = replace(coin_run.drifters[0], x=HOME_X, y=HOME_Y + 4.0)
    taken = step_run(replace(coin_run, ship=HOME, drifters=(on_ship,)), NO_KEY)
    assert taken.coin_points == 50
    assert taken.grazes == 0
    assert taken.popups[0].kind is PopupKind.COIN
    # The same two next to a hazard that does graze: the hazard pays, they add nothing.
    mixed = run_of(
        rock(),
        coin(HOME_X + FOOT_HALF_W + 12.0, HOME_Y + FOOT_ROW_DY),
        island(HOME_X + FOOT_HALF_W + 100.0 + BOX_ISLAND_SIZE / 2, HOME_Y),
    )
    states = walk(mixed, [IN, OUT])
    assert paid(states) == [0, 1]
    assert [d.graze_state for d in states[1].drifters[1:]] == [GrazeState.OUTSIDE] * 2


def test_two_hazards_left_on_one_tick_pay_two_grazes_in_drifter_order(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    first = replace(rock(), uid=5)
    second = replace(rock(), uid=3)
    run = replace(run_of(first, second), drifters=(first, second), next_uid=6)

    def put(gap_right: float, gap_left: float) -> Run:
        placed = (
            at_gap(run.drifters[0], gap_right),
            at_gap(run.drifters[1], gap_left, left=True),
        )
        return step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)

    run = put(IN, IN)
    assert run.grazes == 0
    run = put(OUT, OUT)
    assert run.grazes == 2
    assert run.score == 2 * GRAZE_POINTS
    assert [p.kind for p in run.popups] == [PopupKind.GRAZE, PopupKind.GRAZE]
    assert [p.points for p in run.popups] == [GRAZE_POINTS, GRAZE_POINTS]
    assert {(p.x, p.start_y, p.age_ticks) for p in run.popups} == {(run.ship.x, run.ship.y, 0)}
    assert len(run.graze_rings) == 2
    assert [r.age_ticks for r in run.graze_rings] == [0, 0]
    assert [d.graze_state for d in run.drifters] == [GrazeState.SPENT, GrazeState.SPENT]
    assert grazes_of(caplog) == [
        "drifter graze id=5 type=meteorite",
        "drifter graze id=3 type=meteorite",
    ]


@pytest.mark.parametrize(
    "rules", [None, CUSTOM_RULES, GrazeRules(points=0), GrazeRules(points=1000)]
)
def test_grazes_stack_with_no_cap_and_the_score_is_meters_plus_coins_plus_grazes_times_points(
    rules: GrazeRules | None,
) -> None:
    points = GRAZE_POINTS if rules is None else rules.points
    popup_ticks = GRAZE_POPUP_TICKS if rules is None else rules.popup_ticks
    ring_ticks = GRAZE_RING_TICKS if rules is None else rules.ring_ticks
    rocks = tuple(rock() for _ in range(12))
    run = run_of(*rocks, coin_points=150, scroll=SCROLLING, rules=rules)

    def put(gaps: Sequence[float]) -> Run:
        placed = tuple(at_gap(d, g) for d, g in zip(run.drifters, gaps, strict=True))
        return step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)

    run = put([IN] * 12)
    assert run.grazes == 0
    # Seven leave on one tick, five on the next: twelve grazes, each the full points.
    run = put([OUT] * 7 + [IN] * 5)
    assert run.grazes == 7
    assert run.score == run.scroll.meters + 150 + 7 * points
    run = put([OUT] * 12)
    assert run.grazes == 12
    assert run.score == run.scroll.meters + 150 + 12 * points
    assert run.scroll.meters >= 1
    assert all(p.points == points for p in run.popups if p.kind is PopupKind.GRAZE)
    assert len([p for p in run.popups if p.kind is PopupKind.GRAZE]) == 12
    assert len(run.graze_rings) == 12
    # Every popup and ring is the run's own, not the GDD's, when it was given others.
    if rules is not None:
        assert {p.lifetime_ticks for p in run.popups} == {popup_ticks}
        assert {r.lifetime_ticks for r in run.graze_rings} == {ring_ticks}
        assert {r.line_width for r in run.graze_rings} == {rules.ring_width}
    # Twelve more hazards over the same ground pay too: no cap on the count.
    more = tuple(replace(rock(), uid=100 + i) for i in range(12))
    run = replace(run, drifters=run.drifters + more)
    placed = run.drifters[:12] + tuple(at_gap(d, IN) for d in run.drifters[12:])
    run = step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)
    placed = run.drifters[:12] + tuple(at_gap(d, OUT) for d in run.drifters[12:])
    run = step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)
    assert run.grazes == 24
    assert run.score == run.scroll.meters + 150 + 24 * points


def test_a_graze_and_a_hit_by_another_hazard_on_one_tick_the_graze_pays_then_the_hit_counts(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)

    def scene(lives: int) -> Run:
        run = run_of(rock(), rock(), lives=lives)
        run = replace(
            run,
            drifters=(at_gap(run.drifters[0], IN), at_gap(run.drifters[1], OUT, left=True)),
        )
        run = step_run(replace(run, ship=HOME), NO_KEY)
        assert run.grazes == 0
        placed = (at_gap(run.drifters[0], OUT), at_gap(run.drifters[1], TOUCH, left=True))
        return step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)

    run = scene(LIVES_START)
    assert run.grazes == 1
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over
    assert run.drifters[0].graze_state is GrazeState.SPENT
    assert run.drifters[0].rehit_ticks_left == 0
    assert run.drifters[1].rehit_ticks_left == REHIT_COOLDOWN
    assert len(run.popups) == 1
    assert run.popups[0].kind is PopupKind.GRAZE
    assert run.score == GRAZE_POINTS
    messages = [r.getMessage() for r in caplog.records]
    graze_at = messages.index("drifter graze id=1 type=meteorite")
    touch_at = messages.index("drifter touch id=2 type=meteorite effect=hit")
    life_at = messages.index("life lost lives=2")
    assert graze_at < touch_at < life_at
    # On the last life the hit starts the last life, and the final score has the graze in it.
    caplog.clear()
    last = scene(1)
    assert last.last_life
    assert not last.game_over
    assert last.lives == 0
    assert last.grazes == 1
    assert last.score == GRAZE_POINTS
    assert last.final_score == GRAZE_POINTS
    assert [m for m in (r.getMessage() for r in caplog.records) if m.startswith("last life")] == [
        f"last life score={GRAZE_POINTS}"
    ]
    assert [m for m in (r.getMessage() for r in caplog.records) if m.startswith("game over")] == []


def test_a_graze_on_a_fall_tick_pays_then_the_fall_counts(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    low = Ship(x=HOME_X, y=470.0, vx=0.0, vy=0.0)
    row = low.y + FOOT_ROW_DY
    start = replace(run_of(rock(HOME_X + FOOT_HALF_W + ROCK_RADIUS + IN, row), ship=low), ship=low)
    run = step_run(start, NO_KEY)
    assert graze_state(run) is GrazeState.INSIDE
    assert run.grazes == 0
    # The next step puts the ship's top edge on the floor: a fall. The hazard is out of the zone
    # on that tick, and still on screen.
    falling = Ship(x=HOME_X, y=495.0, vx=0.0, vy=5.5)
    far = replace(run.drifters[0], x=HOME_X + FOOT_HALF_W + ROCK_RADIUS + OUT, y=475.0)
    run = step_run(replace(run, ship=falling, drifters=(far,)), NO_KEY)
    assert run.lives == LIVES_START - 1
    assert run.waiting
    assert run.invuln_ticks_left == INVULN_TICKS
    assert run.grazes == 1
    assert graze_state(run) is GrazeState.SPENT
    # The popup is where the ship was after step 4, before the respawn moved it.
    popup = run.popups[0]
    assert popup.x == HOME_X
    assert popup.start_y > SCREEN_H
    messages = [r.getMessage() for r in caplog.records]
    assert messages.index("drifter graze id=1 type=meteorite") < messages.index("life lost lives=2")


LONG_RULES: GrazeRules = replace(CUSTOM_RULES, popup_ticks=500, ring_ticks=500)
"""A popup and a ring that outlast the last life, to see them frozen at game over."""


def _last_life_run(waves: bool, rules: GrazeRules = CUSTOM_RULES) -> Run:
    """A run whose rock paid a graze on tick 2 and whose second rock starts the last life on
    tick 3 (the state after tick 3). Custom graze values, with or without waves."""
    book = WaveBook(
        waves={
            "w0": Wave(wave_id="w0", length_px=1_000_000.0, kind=WaveKind.FIXED, min_level=None)
        },
        wave_zero_id="w0",
        playlists=tuple(LevelPlaylist() for _ in range(8)),
    )
    base = start_run(start_waves(book, 20261019) if waves else None, rules)
    run = replace(
        base,
        lives=1,
        drifters=(replace(rock(), uid=1), replace(rock(), uid=2)),
        next_uid=3,
    )
    for gaps in ((IN, OUT), (OUT, OUT), (OUT, TOUCH)):
        placed = (at_gap(run.drifters[0], gaps[0]), at_gap(run.drifters[1], gaps[1], left=True))
        run = step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)
    assert run.last_life
    assert not run.game_over
    return run


def _to_game_over(run: Run) -> Run:
    """Step a last-life run, the ship put back at home each tick, until game over."""
    for _ in range(LAST_LIFE_DELAY):
        run = step_run(replace(run, ship=HOME), NO_KEY)
    assert run.game_over
    return run


@pytest.mark.parametrize("waves", [False, True])
def test_the_last_life_pays_no_graze_and_game_over_freezes_the_rings_and_a_new_run_clears_them(
    waves: bool,
) -> None:
    last = _last_life_run(waves)
    assert last.grazes == 1
    assert last.score == CUSTOM_RULES.points
    assert last.final_score == CUSTOM_RULES.points
    assert len(last.graze_rings) == 1
    assert last.graze_rings[0].age_ticks == 1
    assert last.popups[0].age_ticks == 1

    # The last life: a rock that passes beside the ship pays nothing and keeps its graze state,
    # and the score never moves. The popup (7 states) and the ring (4 states) age with the world:
    # the death tick was tick 3, so on tick 4 they are at age 2.
    run = replace(last, drifters=(*last.drifters, replace(rock(), uid=3)), next_uid=4)
    ring_ages: list[list[int]] = []
    popup_ages: list[list[int]] = []
    for gap in (IN, OUT, IN, OUT, OUT, OUT, OUT, OUT):
        run = step_at(run, gap, index=2)
        assert run.grazes == 1
        assert graze_state(run, 2) is GrazeState.OUTSIDE
        assert run.score == last.score
        ring_ages.append([r.age_ticks for r in run.graze_rings])
        popup_ages.append([p.age_ticks for p in run.popups])
    assert ring_ages == [[2], [3], [], [], [], [], [], []]
    assert popup_ages == [[2], [3], [4], [5], [6], [], [], []]

    # Game over with a popup and a ring still on screen: they freeze there like everything else.
    long_last = _last_life_run(waves, LONG_RULES)
    over = _to_game_over(long_last)
    assert over.grazes == 1
    assert over.score == CUSTOM_RULES.points
    assert [r.age_ticks for r in over.graze_rings] == [LAST_LIFE_DELAY + 1]
    assert [p.age_ticks for p in over.popups] == [LAST_LIFE_DELAY + 1]
    # The ticks after: nothing changes, not the rings' or the popups' age, not a rock that now
    # sits inside the zone, not the score. The ship is put in front of a rock to show nothing runs.
    frozen = over
    for _ in range(5):
        frozen = step_run(replace(frozen, ship=HOME), NO_KEY)
        assert frozen.grazes == 1
        assert frozen.graze_rings == over.graze_rings
        assert frozen.popups == over.popups
        assert frozen.drifters == over.drifters
        assert frozen.score == over.score
        assert frozen.scroll == over.scroll
    held = step_run(over, UP)
    assert held.game_over
    assert held.grazes == 1
    assert held.graze_rings == over.graze_rings
    # A new run: no grazes, no rings, no popups, no drifters, score 0, the same graze values.
    fresh = next_run(over)
    assert not fresh.game_over
    assert fresh.grazes == 0
    assert fresh.graze_rings == ()
    assert fresh.popups == ()
    assert fresh.drifters == ()
    assert fresh.score == 0
    assert fresh.graze_rules == LONG_RULES
    assert (fresh.waves is not None) is waves
    # And it pays what it was given: one more graze in the new run.
    new_rock = replace(rock(), uid=1)
    run = replace(fresh, drifters=(new_rock,), next_uid=2)
    states = walk(run, [IN, OUT])
    assert states[1].grazes == 1
    assert states[1].score == LONG_RULES.points
    assert states[1].popups[0].points == LONG_RULES.points
    assert states[1].popups[0].lifetime_ticks == LONG_RULES.popup_ticks
    assert states[1].graze_rings[0].lifetime_ticks == LONG_RULES.ring_ticks


def test_start_run_with_no_graze_values_has_the_gdd_defaults_and_the_old_score() -> None:
    fresh = start_run()
    assert fresh.grazes == 0
    assert fresh.graze_rings == ()
    assert fresh.popups == ()
    assert fresh.score == 0
    rules = fresh.graze_rules
    assert rules == GrazeRules()
    assert rules == DEFAULT_GRAZE_RULES
    assert rules.points == GRAZE_POINTS
    assert (rules.popup_ticks, rules.popup_rise_per_tick) == (GRAZE_POPUP_TICKS, GRAZE_POPUP_RISE)
    assert (rules.ring_ticks, rules.ring_width) == (GRAZE_RING_TICKS, GRAZE_RING_WIDTH)
    assert (rules.ring_start_diameter, rules.ring_end_diameter) == (
        GRAZE_RING_START,
        GRAZE_RING_END,
    )
    assert start_run(graze_rules=CUSTOM_RULES).graze_rules == CUSTOM_RULES
    assert start_run(None, CUSTOM_RULES).graze_rules == CUSTOM_RULES
    # A run flown with a hazard far away and no graze scores the meters alone, whole meters,
    # worked out here: 1.1 px a tick after 30 still ticks, 10 px a meter.
    run = replace(start_run(), drifters=(replace(rock(), uid=1),), next_uid=2)
    for _ in range(200):
        run = step_at(run, 300.0)
    moving_ticks = 200 - SCROLL_START_DELAY
    meters = moving_ticks * SCROLL_SPEED_TENTHS // (PX_PER_METER * 10)
    assert meters == 18
    assert run.grazes == 0
    assert run.coin_points == 0
    assert run.score == meters
    with_coins = replace(run, coin_points=150)
    assert with_coins.score == meters + 150
    assert replace(run, grazes=3).score == meters + 3 * GRAZE_POINTS


def test_a_paid_graze_logs_one_line_after_the_collect_lines_and_before_the_hit_lines(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    caplog.set_level(logging.DEBUG, logger=GRAZE_LOGGER)
    # Quiet passes first: an entry, a touch with protection, a blocked exit, a touch in the wait.
    for run in (
        run_of(rock()),
        run_of(rock(), invuln_ticks_left=6),
        run_of(rock(), waiting=True),
    ):
        for gap in [IN, IN, TOUCH, IN, OUT]:
            run = step_at(run, gap)
    for run, gaps in (
        (run_of(rock(), invuln_ticks_left=2), [IN, OUT]),
        (run_of(rock(), waiting=True), [IN, IN, OUT]),
    ):
        for gap in gaps:
            run = step_at(run, gap)
    assert grazes_of(caplog) == []
    caplog.clear()
    # One tick with a collect, a graze and a hit. The coin is the last one added (id 3), so the
    # order of the lines is the order of the steps, not of the ids.
    run = run_of(rock(), rock())
    placed = (at_gap(run.drifters[0], IN), at_gap(run.drifters[1], OUT, left=True))
    run = step_run(replace(run, ship=HOME, drifters=placed), NO_KEY)
    sweet = replace(coin(HOME_X, HOME_Y + 4.0), uid=3)
    caplog.clear()
    with_coin: tuple[Drifter, ...] = (
        at_gap(run.drifters[0], OUT),
        at_gap(run.drifters[1], TOUCH, left=True),
        sweet,
    )
    run = step_run(replace(run, ship=HOME, drifters=with_coin, next_uid=4), NO_KEY)
    assert run.grazes == 1
    assert run.coin_points == 50
    assert run.lives == LIVES_START - 1
    messages = [r.getMessage() for r in caplog.records]
    run_lines = [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]
    assert messages == run_lines
    assert run_lines == [
        "drifter touch id=3 type=coin effect=collect",
        "drifter graze id=1 type=meteorite",
        "drifter touch id=2 type=meteorite effect=hit",
        "life lost lives=2",
        run_lines[4],
    ]
    assert run_lines[4].startswith("drifter gone id=3 type=coin")
    assert not [r for r in caplog.records if r.name == GRAZE_LOGGER]
    # The score, the count, the popup and the ring log nothing of their own.
    assert not [m for m in messages if "score" in m or "popup" in m or "ring" in m]


def test_check_grazes_never_mutates_its_input_and_the_same_input_gives_the_same_result() -> None:
    inside_exit = replace(rock(HOME_X + FOOT_HALF_W + ROCK_RADIUS + OUT, HOME_Y + FOOT_ROW_DY))
    inside_exit = replace(inside_exit, uid=1, graze_state=GrazeState.INSIDE)
    entering = replace(rock(HOME_X - FOOT_HALF_W - ROCK_RADIUS - IN, HOME_Y + FOOT_ROW_DY), uid=2)
    spent = replace(
        rock(HOME_X + FOOT_HALF_W + ROCK_RADIUS + OUT, HOME_Y + FOOT_ROW_DY),
        uid=3,
        graze_state=GrazeState.SPENT,
    )
    touching = replace(rock(HOME_X, HOME_Y + FOOT_ROW_DY), uid=4, graze_state=GrazeState.INSIDE)
    a_coin = replace(coin(HOME_X + FOOT_HALF_W + 12.0, HOME_Y + FOOT_ROW_DY), uid=5)
    a_wall = replace(island(HOME_X + FOOT_HALF_W + 100.0 + BOX_ISLAND_SIZE / 2, HOME_Y), uid=6)
    second_exit = replace(
        rock(HOME_X - FOOT_HALF_W - ROCK_RADIUS - OUT, HOME_Y + FOOT_ROW_DY),
        uid=7,
        graze_state=GrazeState.INSIDE,
    )
    drifters = (inside_exit, entering, spent, touching, a_coin, a_wall, second_exit)
    before = copy.deepcopy(drifters)
    box = ship_hitbox(HOME)
    for may_pay in (True, False):
        first: GrazeCheck = check_grazes(drifters, box, may_pay)
        second: GrazeCheck = check_grazes(drifters, box, may_pay)
        assert drifters == before
        assert [d.graze_state for d in drifters] == [d.graze_state for d in before]
        assert first == second
        assert [d.uid for d in first.drifters] == [1, 2, 3, 4, 5, 6, 7]
        assert [d.graze_state for d in first.drifters] == [
            GrazeState.SPENT if may_pay else GrazeState.OUTSIDE,
            GrazeState.INSIDE,
            GrazeState.SPENT,
            GrazeState.SPENT,
            GrazeState.OUTSIDE,
            GrazeState.OUTSIDE,
            GrazeState.SPENT if may_pay else GrazeState.OUTSIDE,
        ]
        assert [d.uid for d in first.paid] == ([1, 7] if may_pay else [])
        # The result fed back in, with the ship where it is, pays nothing more.
        again = check_grazes(first.drifters, box, may_pay)
        assert again.paid == ()
        assert [d.graze_state for d in again.drifters] == [d.graze_state for d in first.drifters]
