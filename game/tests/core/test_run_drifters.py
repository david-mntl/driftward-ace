"""Drifters inside the run: how they enter, when they hit, the re-hit cooldown, when they leave.

Contract: docs/contracts/systems/run.md, Rules. Tasks:
docs/contracts/DRA-29/tasks/DRA-29-08-qa-engineer.md and
docs/contracts/DRA-39/tasks/DRA-39-07-qa-engineer.md. One test per behavior they list.
The tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test.
"""

import logging
from dataclasses import replace

import pytest

from core.collision import Box, Circle, hitboxes_overlap, place_hitbox
from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.meteorite import Meteorite
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.spawner import Placement
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, next_run, start_run, step_run
from core.scroll import Scroll, start_scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

LIVES_START: int = 3
"""Source: 05-lives-and-damage.md, Values, lives_start (locked)."""

INVULN_TICKS: int = 30
"""Ticks. Source: 05-lives-and-damage.md, Values, invuln_ticks (locked)."""

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

GRAVITY: float = 0.16
"""px/tick². Source: 04-ship.md, Values, gravity (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

SCREEN_W: int = 640
"""px. Source: 03-world-and-camera.md, Values, screen_w (guess)."""

SPEED_RATIO: float = 0.375
"""Level 1 speed as a multiple of the top sideways speed, meteorite and satellite alike.
Source: drifters/01-meteorite.md and drifters/02-satellite.md, speed_ratio (guess)."""

WARNING_TICKS: int = 60
"""ticks. Source: 07-drifters.md, entry_warning_ticks (guess)."""

LAST_LIFE_DELAY: int = 120
"""Ticks from the death tick to game over. Source: 02-game-flow.md, Values, last_life_delay
(guess)."""

REHIT_COOLDOWN: int = 180
"""ticks. Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

REHIT_DIM: float = 0.75
"""× brightness. Source: 05-lives-and-damage.md, rehit_dim (guess)."""

SMALL_COOLDOWN: int = 4
"""A small cooldown set through the tuning, to test a value that is not the default."""

SATELLITE_W: float = 36.0
SATELLITE_H: float = 12.0
"""px. Source: drifters/02-satellite.md, size (guess)."""

SATELLITE_BOXES = (Box(0, 0, 12, 12), Box(0, 0, 36, 6))
"""Body, then panel bar, both centered. Source: drifters/02-satellite.md, hitbox (guess)."""

SATELLITE_DROP_TICKS: int = 274
"""Active ticks until a flat Level 1 satellite is dropped past the right wall. Source:
docs/contracts/systems/drifters.md, Diagram, Satellite timeline."""

METEORITE_DROP_TICKS: int = 206
"""Active ticks until a medium Level 1 meteorite is dropped below the floor. Source:
docs/contracts/systems/drifters.md, Diagram, Meteorite timeline."""

MEDIUM_SIZE: float = 28.0
"""Visible width and height of a medium meteorite, px. Source: drifters/01-meteorite.md,
variants (guess)."""

MEDIUM_RADIUS: float = 14.0
"""Hitbox radius of a medium meteorite, px. Source: drifters/01-meteorite.md, variants (guess)."""

SIZES: dict[str, tuple[float, float]] = {
    "small": (20, 10),
    "medium": (MEDIUM_SIZE, MEDIUM_RADIUS),
    "big": (40, 20),
}
"""Variant name to (width, hitbox radius), px. Source: drifters/01-meteorite.md, variants
(guess)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""


def make_tuning(*, hazards: HazardRules | None = None) -> DrifterTuning:
    """Build the meteorite and satellite tuning from the GDD values above."""
    variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=width, height=width, hitbox=(Circle(0, 0, radius),))
        for name, (width, radius) in SIZES.items()
    }
    satellite: dict[str, VariantTuning] = {
        "flat": VariantTuning(
            width=SATELLITE_W,
            height=SATELLITE_H,
            hitbox=SATELLITE_BOXES,
            extra=SatelliteVariantExtra(angle_degrees=0.0),
        )
    }
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=variants,
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            DrifterType.SATELLITE: DrifterTypeTuning(
                variants=satellite,
                default_variant="flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches(),
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
LEVEL_1_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""Level 1 meteorite speed, px/tick (hazard speed x 1.00 at Level 1). Source: 08-difficulty.md,
level table (locked); drifters/01-meteorite.md, speed_ratio."""


def rock(
    x: float = HOME_X,
    y: float = HOME_Y,
    *,
    speed: float = 0.0,
    phase: Phase = Phase.ACTIVE,
    uid: int = 1,
    ticks_in_phase: int = 0,
    rehit_ticks_left: int = 0,
    rehit_cooldown_ticks: int = REHIT_COOLDOWN,
) -> Meteorite:
    """A medium meteorite built directly. ACTIVE with speed 0 stays where it is put."""
    return Meteorite(
        uid=uid,
        x=x,
        y=y,
        variant="medium",
        width=MEDIUM_SIZE,
        height=MEDIUM_SIZE,
        speed=speed,
        hitbox=(Circle(0, 0, MEDIUM_RADIUS),),
        warning_ticks=WARNING_TICKS,
        phase=phase,
        ticks_in_phase=ticks_in_phase,
        rehit_ticks_left=rehit_ticks_left,
        rehit_cooldown_ticks=rehit_cooldown_ticks,
        rehit_dim=REHIT_DIM,
    )


def home_ship() -> Ship:
    """A resting ship at the test position."""
    return Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)


def run_with(
    *drifters: Drifter,
    ship: Ship | None = None,
    lives: int = LIVES_START,
    invuln_ticks_left: int = 0,
    waiting: bool = False,
    game_over: bool = False,
) -> Run:
    """A run with the given drifters, uids set in order from 1, the ship at home by default."""
    numbered: tuple[Drifter, ...] = tuple(
        replace(drifter, uid=index + 1) for index, drifter in enumerate(drifters)
    )
    return Run(
        ship=home_ship() if ship is None else ship,
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        lives=lives,
        invuln_ticks_left=invuln_ticks_left,
        waiting=waiting,
        game_over=game_over,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def hold_ship(run: Run) -> Run:
    """Put the ship back at home, so a test can keep it under a falling drifter."""
    return replace(run, ship=home_ship())


def only(run: Run) -> Drifter:
    """The single drifter on the field."""
    assert len(run.drifters) == 1
    return run.drifters[0]


def lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def count(log_lines: list[str], prefix: str) -> int:
    return sum(1 for line in log_lines if line.startswith(prefix))


def test_add_drifters_spawns_in_order_with_uids() -> None:
    run: Run = start_run()
    placements: list[Placement] = [
        Placement(DrifterType.METEORITE, 100.0, y=50.0, variant="small"),
        Placement(DrifterType.METEORITE, 200.0, y=60.0),
        Placement(DrifterType.METEORITE, 300.0, y=70.0, variant="big"),
    ]

    added: Run = add_drifters(run, placements, TUNING)

    assert [drifter.uid for drifter in added.drifters] == [1, 2, 3]
    assert [drifter.x for drifter in added.drifters] == [100.0, 200.0, 300.0]
    assert [drifter.y for drifter in added.drifters] == [50.0, 60.0, 70.0]
    assert [drifter.variant for drifter in added.drifters] == ["small", "medium", "big"]
    assert added.next_uid == 4
    for drifter in added.drifters:
        assert drifter.phase is Phase.WARNING
        assert drifter.ticks_in_phase == 0
        assert drifter.speed == pytest.approx(LEVEL_1_SPEED)
        assert drifter.warning_ticks == WARNING_TICKS
    # Nothing else in the run changes, and the input run is not touched.
    assert replace(added, drifters=(), next_uid=1) == run
    assert run.drifters == ()
    assert run.next_uid == 1

    # A second call appends after the first, and the uids carry on.
    more: Run = add_drifters(added, [Placement(DrifterType.METEORITE, 400.0, y=80.0)], TUNING)
    assert [drifter.uid for drifter in more.drifters] == [1, 2, 3, 4]
    assert more.drifters[:3] == added.drifters
    assert more.next_uid == 5

    # No placements, or a run at game over: the run comes back unchanged.
    assert add_drifters(run, [], TUNING) == run
    assert add_drifters(added, [], TUNING) == added
    over: Run = run_with(game_over=True)
    assert add_drifters(over, placements, TUNING) == over
    assert over.drifters == ()
    assert over.next_uid == 1


def test_a_warning_never_hits_and_ends_after_its_last_step() -> None:
    run: Run = add_drifters(
        start_run(), [Placement(DrifterType.METEORITE, HOME_X, y=HOME_Y)], TUNING
    )
    states: list[Run] = [run]
    for _ in range(WARNING_TICKS - 1):
        run = step_run(run, NO_KEY)
        states.append(run)

    # The birth state and the 29 states after it show the warning.
    assert len(states) == WARNING_TICKS
    for state in states:
        assert only(state).phase is Phase.WARNING
        assert state.lives == LIVES_START
        assert not state.invulnerable
        assert only(state).rehit_ticks_left == 0
    assert only(states[0]).ticks_in_phase == 0
    # The ship is right on the placed rock for the first ticks: still no hit.
    first: Run = states[1]
    footprint = place_hitbox((Circle(0, 0, MEDIUM_RADIUS),), HOME_X, HOME_Y)
    assert hitboxes_overlap(footprint, ship_hitbox(first.ship))

    run = step_run(run, NO_KEY)
    assert only(run).phase is Phase.ACTIVE
    assert only(run).ticks_in_phase == 0

    # A warning that ends on a tick where it overlaps the ship hits on that very tick.
    ending: Run = run_with(rock(phase=Phase.WARNING, ticks_in_phase=WARNING_TICKS - 1))
    after: Run = step_run(ending, NO_KEY)
    assert only(after).phase is Phase.ACTIVE
    assert only(after).rehit_ticks_left == REHIT_COOLDOWN
    assert after.lives == LIVES_START - 1


def test_a_hit_costs_a_life_and_starts_invulnerability() -> None:
    before: Run = run_with(rock())
    assert not before.invulnerable
    # The ship's tick with no drifter at all.
    expected: Run = step_run(replace(before, drifters=()), NO_KEY)

    run: Run = step_run(before, NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.invulnerable
    assert run.invuln_ticks_left == INVULN_TICKS
    assert only(run).rehit_ticks_left == REHIT_COOLDOWN
    assert only(run).phase is Phase.ACTIVE
    assert not run.game_over
    assert not run.waiting
    # No stun, no bounce: the ship is exactly where a tick with no drifter puts it.
    assert run.ship == expected.ship
    assert (run.ship.x, run.ship.y, run.ship.vx, run.ship.vy) == pytest.approx(
        (HOME_X, HOME_Y + GRAVITY, 0.0, GRAVITY)
    )
    assert run.scroll == expected.scroll


def test_an_invulnerable_ship_takes_no_hit_until_it_ends() -> None:
    run: Run = run_with(rock(), invuln_ticks_left=INVULN_TICKS)
    assert run.invulnerable

    for tick in range(INVULN_TICKS):
        run = step_run(run, NO_KEY)
        assert run.lives == LIVES_START, tick
        assert only(run).rehit_ticks_left == 0, tick
        assert run.invuln_ticks_left == INVULN_TICKS - 1 - tick
        run = hold_ship(run)

    assert not run.invulnerable
    assert hitboxes_overlap(only(run).current_hitbox(), ship_hitbox(step_run(run, NO_KEY).ship))

    # Still overlapping when the timer is out: it hits now.
    run = step_run(run, NO_KEY)
    assert run.lives == LIVES_START - 1
    assert only(run).rehit_ticks_left == REHIT_COOLDOWN
    assert run.invuln_ticks_left == INVULN_TICKS


def test_a_hit_starts_the_cooldown_and_the_drifter_keeps_moving() -> None:
    speed: float = 0.5
    start: Meteorite = rock(speed=speed)
    assert start.may_hit_ship()
    assert start.rehit_ticks_left == 0
    run: Run = step_run(run_with(start), NO_KEY)

    assert run.lives == LIVES_START - 1
    assert only(run).rehit_ticks_left == REHIT_COOLDOWN
    assert not only(run).may_hit_ship()
    assert only(run).y == pytest.approx(HOME_Y + speed)

    # The rock keeps falling and stays on the field while it overlaps the ship, through the
    # invulnerability and 15 ticks past its end. The cooldown runs down one a tick and no
    # second life is lost.
    for tick in range(INVULN_TICKS + 15):
        run = hold_ship(run)
        run = step_run(run, NO_KEY)
        assert run.lives == LIVES_START - 1, tick
        assert only(run).uid == 1
        assert only(run).rehit_ticks_left == REHIT_COOLDOWN - 1 - tick
        assert only(run).y == pytest.approx(HOME_Y + speed * (tick + 2))
        if tick >= INVULN_TICKS:
            assert not run.invulnerable
            assert hitboxes_overlap(only(run).current_hitbox(), ship_hitbox(run.ship))
    assert not run.game_over


@pytest.mark.parametrize("cooldown", [REHIT_COOLDOWN, SMALL_COOLDOWN])
def test_a_hazard_cannot_hit_for_its_cooldown_and_hits_again_after(cooldown: int) -> None:
    run: Run = step_run(run_with(rock(rehit_cooldown_ticks=cooldown)), NO_KEY)
    assert run.lives == LIVES_START - 1
    assert only(run).rehit_ticks_left == cooldown

    # Invulnerability is cleared before every tick, so only the cooldown can stop a hit. The
    # rock overlaps the ship on every tick.
    for tick in range(1, cooldown + 1):
        run = hold_ship(replace(run, invuln_ticks_left=0))
        assert hitboxes_overlap(only(run).current_hitbox(), ship_hitbox(step_run(run, NO_KEY).ship))
        run = step_run(run, NO_KEY)
        assert run.lives == LIVES_START - 1, tick
        assert not run.invulnerable, tick
        assert only(run).rehit_ticks_left == cooldown - tick, tick
        assert only(run).may_hit_ship() == (tick == cooldown)

    assert only(run).rehit_ticks_left == 0
    assert only(run).may_hit_ship()

    # The tick after: it hits, and its cooldown starts again.
    run = step_run(hold_ship(replace(run, invuln_ticks_left=0)), NO_KEY)
    assert run.lives == LIVES_START - 2
    assert run.invuln_ticks_left == INVULN_TICKS
    assert only(run).rehit_ticks_left == cooldown
    assert only(run).uid == 1


def test_a_cooling_hazard_is_dim_for_exactly_its_cooldown() -> None:
    run: Run = step_run(run_with(rock()), NO_KEY)
    states: list[Run] = [run]
    for _ in range(REHIT_COOLDOWN):
        run = step_run(hold_ship(replace(run, invuln_ticks_left=0)), NO_KEY)
        states.append(run)

    # states[0] is the state after the hit, states[k] the state after the k-th tick after it.
    assert len(states) == REHIT_COOLDOWN + 1
    for k, state in enumerate(states[:REHIT_COOLDOWN]):
        assert only(state).brightness() == REHIT_DIM, k
    assert only(states[REHIT_COOLDOWN - 1]).rehit_ticks_left == 1
    assert only(states[REHIT_COOLDOWN]).rehit_ticks_left == 0
    assert only(states[REHIT_COOLDOWN]).brightness() == 1.0
    assert only(states[0]).brightness() == REHIT_DIM
    assert rock().brightness() == 1.0


def test_another_hazard_hits_when_invulnerability_ends_and_the_first_count_goes_on() -> None:
    # B shows its warning while A hits, and turns ACTIVE on the 30th tick, with the ship still
    # protected. It touches the ship from then on and hits when invulnerability ends.
    first: Meteorite = rock()
    second: Meteorite = rock(phase=Phase.WARNING, ticks_in_phase=WARNING_TICKS - INVULN_TICKS)
    run: Run = step_run(run_with(first, second), NO_KEY)
    assert run.lives == LIVES_START - 1
    assert run.drifters[0].rehit_ticks_left == REHIT_COOLDOWN
    assert run.drifters[1].phase is Phase.WARNING

    # Ticks T+1 to T+30 are protected. B turns ACTIVE on T+29 and touches on T+29 and T+30:
    # no hit, so no cooldown starts, and A counts down 179 to 150.
    for tick in range(1, INVULN_TICKS + 1):
        run = step_run(hold_ship(run), NO_KEY)
        assert run.lives == LIVES_START - 1, tick
        assert run.drifters[0].rehit_ticks_left == REHIT_COOLDOWN - tick
        assert run.drifters[1].rehit_ticks_left == 0, tick
    assert run.drifters[1].phase is Phase.ACTIVE
    assert not run.invulnerable
    assert hitboxes_overlap(run.drifters[1].current_hitbox(), ship_hitbox(run.ship))

    # Tick T+31: B hits. Only B's cooldown starts, and A's count goes on from 150.
    run = step_run(hold_ship(run), NO_KEY)
    assert run.lives == LIVES_START - 2
    assert run.invuln_ticks_left == INVULN_TICKS
    assert run.drifters[1].rehit_ticks_left == REHIT_COOLDOWN
    assert run.drifters[0].rehit_ticks_left == REHIT_COOLDOWN - (INVULN_TICKS + 1)

    # A is not restarted by B's hit and runs out on its own schedule.
    for _ in range(REHIT_COOLDOWN - (INVULN_TICKS + 1)):
        run = step_run(hold_ship(run), NO_KEY)
    assert run.drifters[0].rehit_ticks_left == 0
    assert run.drifters[1].rehit_ticks_left == INVULN_TICKS + 1


def test_a_cooldown_counts_on_every_playing_tick_and_freezes_at_game_over() -> None:
    cooling: int = 100

    # A protected tick: a touching rock starts no cooldown, a cooling one counts down.
    touched: Run = step_run(run_with(rock(), invuln_ticks_left=INVULN_TICKS), NO_KEY)
    assert touched.lives == LIVES_START
    assert only(touched).rehit_ticks_left == 0
    counted: Run = step_run(
        run_with(rock(x=50.0, y=100.0, rehit_ticks_left=cooling), invuln_ticks_left=10), NO_KEY
    )
    assert only(counted).rehit_ticks_left == cooling - 1

    # During the respawn wait, with no press.
    waited: Run = step_run(
        run_with(rock(x=50.0, y=100.0, rehit_ticks_left=cooling), ship=spawn(), waiting=True),
        NO_KEY,
    )
    assert waited.waiting
    assert only(waited).rehit_ticks_left == cooling - 1

    # On a tick with a fall.
    fell: Ship = Ship(x=100.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)
    dropped: Run = step_run(
        run_with(rock(x=50.0, y=100.0, rehit_ticks_left=cooling), ship=fell), NO_KEY
    )
    assert dropped.ship == spawn()
    assert dropped.lives == LIVES_START - 1
    assert only(dropped).rehit_ticks_left == cooling - 1

    # On the tick the last life starts: the hit's drifter starts at the full cooldown, the other
    # counts down. The last life's ticks count them down too, until game over freezes them.
    last: Run = step_run(
        run_with(rock(), rock(x=50.0, y=100.0, rehit_ticks_left=cooling), lives=1), NO_KEY
    )
    assert last.last_life
    assert [drifter.rehit_ticks_left for drifter in last.drifters] == [REHIT_COOLDOWN, cooling - 1]
    run: Run = last
    for tick in range(1, LAST_LIFE_DELAY + 1):
        run = step_run(run, NO_KEY)
        assert [drifter.rehit_ticks_left for drifter in run.drifters] == [
            REHIT_COOLDOWN - tick,
            max(cooling - 1 - tick, 0),
        ]
    over: Run = run
    assert over.game_over
    assert [drifter.rehit_ticks_left for drifter in over.drifters] == [
        REHIT_COOLDOWN - LAST_LIFE_DELAY,
        0,
    ]
    for _ in range(100):
        run = step_run(run, NO_KEY)
        assert run.drifters == over.drifters

    # A new run starts with no drifters, and so no cooldown.
    fresh: Run = next_run(run)
    assert not fresh.game_over
    assert fresh.drifters == ()


def satellite_placement(
    x: float | None = None, y: float = 300.0, *, invert: bool = False, speed: float | None = None
) -> Placement:
    """A flat satellite placement. At y 300 and with no x, no ship held at home can touch it."""
    return Placement(DrifterType.SATELLITE, x, y, invert=invert, speed=speed)


def test_a_satellite_outside_the_wall_is_kept_until_it_has_entered_then_dropped() -> None:
    step: float = SPEED_RATIO * TOP_SIDE_SPEED
    run: Run = add_drifters(start_run(), [satellite_placement()], TUNING)
    assert only(run).x == -SATELLITE_W / 2
    assert only(run).y == 300.0
    assert only(run).phase is Phase.WARNING

    # The warning shows on the birth state and the 59 states after it.
    for _ in range(WARNING_TICKS - 1):
        run = hold_ship(step_run(run, NO_KEY))
        assert only(run).phase is Phase.WARNING

    # The first ACTIVE state: still at x -18, its right edge on the left wall. It is not
    # dropped, and has not entered.
    run = hold_ship(step_run(run, NO_KEY))
    assert only(run).phase is Phase.ACTIVE
    assert only(run).ticks_in_phase == 0
    assert only(run).x == pytest.approx(-SATELLITE_W / 2)
    assert only(run).x + SATELLITE_W / 2 <= 0
    assert not only(run).has_entered

    # Its next tick: it is partly on screen, so it has entered.
    run = hold_ship(step_run(run, NO_KEY))
    assert only(run).x == pytest.approx(-SATELLITE_W / 2 + step)
    assert only(run).has_entered
    assert only(run).uid == 1

    # Dropped on the state after its 274th active tick, and not one tick earlier.
    for n in range(2, SATELLITE_DROP_TICKS):
        run = hold_ship(step_run(run, NO_KEY))
        assert len(run.drifters) == 1, n
        assert only(run).x == pytest.approx(-SATELLITE_W / 2 + n * step), n
        assert only(run).x - SATELLITE_W / 2 < SCREEN_W, n
    assert only(run).ticks_in_phase == SATELLITE_DROP_TICKS - 1
    run = hold_ship(step_run(run, NO_KEY))
    assert run.drifters == ()
    assert run.next_uid == 2
    assert run.lives == LIVES_START


def test_a_drifter_that_never_enters_is_never_dropped_and_a_meteorite_still_is() -> None:
    # The satellite starts outside the left wall and flies left, away from the screen.
    run: Run = add_drifters(
        start_run(),
        [
            satellite_placement(-SATELLITE_W / 2, invert=True),
            Placement(DrifterType.METEORITE, 100.0),
        ],
        TUNING,
    )
    step: float = SPEED_RATIO * TOP_SIDE_SPEED
    for _ in range(WARNING_TICKS):
        run = hold_ship(step_run(run, NO_KEY))
    assert [drifter.phase for drifter in run.drifters] == [Phase.ACTIVE, Phase.ACTIVE]

    # The meteorite is present after 205 active ticks and gone after the 206th.
    for _ in range(METEORITE_DROP_TICKS - 1):
        run = hold_ship(step_run(run, NO_KEY))
    assert [drifter.uid for drifter in run.drifters] == [1, 2]
    run = hold_ship(step_run(run, NO_KEY))
    assert [drifter.uid for drifter in run.drifters] == [1]

    # The satellite is never dropped: not now, and not 600 ticks later, far off screen.
    for _ in range(600):
        run = hold_ship(step_run(run, NO_KEY))
    assert [drifter.uid for drifter in run.drifters] == [1]
    assert not only(run).has_entered
    n: int = METEORITE_DROP_TICKS + 600
    assert only(run).x == pytest.approx(-SATELLITE_W / 2 - n * step)
    assert run.lives == LIVES_START
    assert not run.game_over


def test_a_satellite_life_logs_spawn_active_gone_and_one_touch_per_hit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)

    # A satellite that crosses the field untouched: three lines, in order.
    run: Run = add_drifters(start_run(), [satellite_placement()], TUNING)
    for _ in range(WARNING_TICKS + SATELLITE_DROP_TICKS):
        run = hold_ship(step_run(run, NO_KEY))
    seen: list[str] = lines(caplog)
    assert run.drifters == ()
    assert [line.split(" ")[1] for line in seen] == ["spawn", "active", "gone"]
    assert seen[0].startswith("drifter spawn id=1 type=satellite variant=flat x=-18.00 y=300.00")
    assert seen[1].startswith("drifter active id=1 type=satellite ")
    assert seen[2].startswith("drifter gone id=1 type=satellite ")
    caplog.clear()

    # A slow one that rests on the ship hits twice, 181 ticks apart: two touch lines between
    # active and gone, and nothing else about it.
    run = add_drifters(start_run(), [satellite_placement(HOME_X - 60.0, HOME_Y, speed=0.2)], TUNING)
    ticks: int = 0
    while run.drifters and ticks < 4000:
        run = hold_ship(step_run(run, NO_KEY))
        ticks += 1
    assert run.drifters == ()
    drifter_lines: list[str] = [line for line in lines(caplog) if line.startswith("drifter ")]
    assert [line.split(" ")[1] for line in drifter_lines] == [
        "spawn",
        "active",
        "touch",
        "touch",
        "gone",
    ]
    assert drifter_lines[2] == "drifter touch id=1 type=satellite effect=hit"
    assert drifter_lines[3] == "drifter touch id=1 type=satellite effect=hit"
    assert count(lines(caplog), "life lost") == 2
    assert run.lives == LIVES_START - 2


def test_two_meteorites_on_one_tick_cost_one_life() -> None:
    far: Meteorite = rock(x=50.0, y=100.0)
    run: Run = step_run(run_with(rock(x=312.0), rock(x=328.0, y=244.0), far), NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert [drifter.rehit_ticks_left for drifter in run.drifters] == [
        REHIT_COOLDOWN,
        REHIT_COOLDOWN,
        0,
    ]
    assert len(run.drifters) == 3
    assert not run.game_over


def test_a_graze_zone_overlap_is_not_a_hit() -> None:
    beside: Meteorite = rock(x=345.0, y=232.0)
    run: Run = run_with(beside)
    after: Run = step_run(run, NO_KEY)
    # Setup: the zone reaches the ship, the hitbox doesn't.
    assert hitboxes_overlap(beside.graze_zone(), ship_hitbox(after.ship))
    assert not hitboxes_overlap(beside.current_hitbox(), ship_hitbox(after.ship))

    assert after.lives == LIVES_START
    assert not after.invulnerable
    assert only(after).rehit_ticks_left == 0
    assert only(after).phase is Phase.ACTIVE


def test_a_hit_on_the_last_life_starts_the_last_life() -> None:
    speed: float = 0.5
    before: Run = run_with(rock(speed=speed), lives=1)
    expected: Run = step_run(replace(before, drifters=()), NO_KEY)

    last: Run = step_run(before, NO_KEY)

    assert last.lives == 0
    assert last.last_life
    assert not last.game_over
    assert not last.invulnerable
    assert not last.waiting
    assert last.ship == expected.ship
    assert last.ship != spawn()
    assert only(last).rehit_ticks_left == REHIT_COOLDOWN
    assert only(last).y == pytest.approx(HOME_Y + speed)

    # The last life's ticks: the drifter keeps falling, the ship stays, and drifters are added.
    run: Run = last
    for tick in range(1, LAST_LIFE_DELAY + 1):
        run = step_run(run, NO_KEY)
        assert only(run).y == pytest.approx(HOME_Y + speed * (tick + 1))
        assert run.ship == last.ship
        assert run.lives == 0
    added: Run = add_drifters(last, [Placement(DrifterType.METEORITE, 10.0)], TUNING)
    assert len(added.drifters) == 2
    assert added.next_uid == last.next_uid + 1
    over: Run = run
    assert over.game_over

    # Everything freezes on the next ticks. Drifters don't move, and nothing is added.
    for _ in range(100):
        run = step_run(run, NO_KEY)
        assert run.game_over
        assert run.drifters == over.drifters
        assert run.ship == over.ship
        assert run.scroll == over.scroll
        assert run.lives == 0
        assert add_drifters(run, [Placement(DrifterType.METEORITE, 10.0)], TUNING) == run
        assert run.next_uid == over.next_uid


def test_a_hit_during_the_respawn_wait_keeps_the_wait() -> None:
    before: Run = run_with(rock(), ship=spawn(), waiting=True)
    assert not before.invulnerable

    run: Run = step_run(before, NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert only(run).rehit_ticks_left == REHIT_COOLDOWN
    assert run.waiting
    assert run.ship == spawn()
    assert not run.game_over

    # The wait goes on until a press, and that press ends it as it always does.
    run = step_run(run, NO_KEY)
    assert run.waiting
    assert run.ship == spawn()
    run = step_run(run, Thrust(right=True))
    assert not run.waiting
    assert run.lives == LIVES_START - 1


def test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall() -> None:
    fell: Ship = Ship(x=100.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)
    # Under the floor line at the end of the tick: the ship's bar spans 480 to 512.
    under: Meteorite = rock(x=100.0, y=SCREEN_H + 5.0)

    run: Run = step_run(run_with(under, ship=fell), NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.ship == spawn()
    assert run.waiting
    assert run.invuln_ticks_left == INVULN_TICKS
    assert only(run).rehit_ticks_left == 0
    assert not run.game_over

    # On the last life the fall starts the last life, still with no hit recorded.
    last: Run = step_run(run_with(under, ship=fell, lives=1), NO_KEY)
    assert last.last_life
    assert last.lives == 0
    assert only(last).rehit_ticks_left == 0


def test_an_drifter_is_dropped_when_its_top_edge_reaches_the_floor() -> None:
    speed: float = 2.0
    start_y: float = SCREEN_H + MEDIUM_SIZE / 2 - 4 * speed
    run: Run = run_with(rock(x=100.0, y=start_y, speed=speed))

    for tick in range(1, 4):
        run = hold_ship(step_run(run, NO_KEY))
        assert only(run).y - MEDIUM_SIZE / 2 < SCREEN_H, tick
        assert only(run).y == pytest.approx(start_y + speed * tick)

    run = step_run(run, NO_KEY)
    assert run.drifters == ()
    assert run.next_uid == 2

    # Above the top of the screen, a drifter is never dropped.
    high: Run = run_with(rock(x=100.0, y=-200.0, speed=0.0))
    for _ in range(300):
        high = hold_ship(step_run(high, NO_KEY))
        assert len(high.drifters) == 1
    assert only(high).y == -200.0
    falling: Run = run_with(rock(x=100.0, y=-MEDIUM_SIZE * 3, speed=LEVEL_1_SPEED))
    for _ in range(20):
        falling = hold_ship(step_run(falling, NO_KEY))
        assert len(falling.drifters) == 1


def test_a_new_run_starts_with_no_drifters() -> None:
    last: Run = step_run(run_with(rock(), rock(x=50.0, y=100.0), lives=1), NO_KEY)
    assert last.last_life
    assert len(last.drifters) == 2
    assert last.next_uid == 3
    over: Run = last
    for _ in range(LAST_LIFE_DELAY):
        over = step_run(over, NO_KEY)
    assert over.game_over
    assert [d.uid for d in over.drifters] == [1, 2]

    run: Run = next_run(over)

    assert not run.game_over
    assert run.drifters == ()
    assert run.next_uid == 1
    assert run == start_run()

    # The first drifter of the new run is uid 1 again.
    again: Run = add_drifters(run, [Placement(DrifterType.METEORITE, 10.0)], TUNING)
    assert [drifter.uid for drifter in again.drifters] == [1]
    assert again.scroll == start_scroll()


def test_drifter_events_log_once_on_core_run(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)

    # A meteorite that never hits logs exactly three lines.
    run: Run = start_run()
    run = add_drifters(run, [Placement(DrifterType.METEORITE, 100.0)], TUNING)
    assert len(lines(caplog)) == 1
    assert lines(caplog)[0].startswith("drifter spawn id=1 type=meteorite variant=medium")
    for _ in range(WARNING_TICKS + METEORITE_DROP_TICKS):
        run = hold_ship(step_run(run, NO_KEY))
    seen: list[str] = lines(caplog)
    assert run.drifters == ()
    assert len(seen) == 3
    assert seen[0].startswith("drifter spawn id=1 ")
    assert seen[1].startswith("drifter active id=1 type=meteorite ")
    assert seen[2].startswith("drifter gone id=1 type=meteorite ")
    caplog.clear()

    # Two meteorites placed on the ship: one hit, two touch lines, one life lost. They then
    # fall through the invulnerable ship and log nothing more until they are dropped.
    run = start_run()
    run = add_drifters(
        run,
        [
            Placement(DrifterType.METEORITE, HOME_X - 5.0, y=HOME_Y),
            Placement(DrifterType.METEORITE, HOME_X + 5.0, y=HOME_Y),
        ],
        TUNING,
    )
    assert count(lines(caplog), "drifter spawn") == 2
    caplog.clear()
    for _ in range(WARNING_TICKS - 1):
        run = hold_ship(step_run(run, NO_KEY))
    assert lines(caplog) == []
    run = hold_ship(step_run(run, NO_KEY))
    hit_lines: list[str] = lines(caplog)
    assert run.lives == LIVES_START - 1
    assert [line.split(" ")[1] for line in hit_lines] == [
        "active",
        "active",
        "touch",
        "touch",
        "lost",
    ]
    assert hit_lines[2] == "drifter touch id=1 type=meteorite effect=hit"
    assert hit_lines[3] == "drifter touch id=2 type=meteorite effect=hit"
    assert hit_lines[4] == "life lost lives=2"
    caplog.clear()
    for _ in range(150):
        run = hold_ship(step_run(run, NO_KEY))
    later: list[str] = lines(caplog)
    assert run.drifters == ()
    assert count(later, "drifter touch") == 0
    assert count(later, "life lost") == 0
    assert count(later, "invulnerable end") == 1
    assert count(later, "drifter gone") == 2
    assert len(later) == 3
    caplog.clear()

    # A meteorite passing through an invulnerable ship logs nothing until it is dropped.
    run = run_with(rock(y=HOME_Y - 10.0, speed=LEVEL_1_SPEED), invuln_ticks_left=INVULN_TICKS)
    for _ in range(150):
        run = hold_ship(step_run(run, NO_KEY))
        if run.drifters:
            assert only(run).rehit_ticks_left == 0
    through: list[str] = lines(caplog)
    assert run.drifters == ()
    assert run.lives == LIVES_START
    assert [line.split(" ")[0] for line in through] == ["invulnerable", "drifter"]
    assert through[1].startswith("drifter gone id=1 ")
