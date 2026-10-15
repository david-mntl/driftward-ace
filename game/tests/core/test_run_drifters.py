"""Drifters inside the run: how they enter, when they hit, one hit per hazard, when they leave.

Contract: docs/contracts/systems/run.md, Rules. Task:
docs/contracts/DRA-29/tasks/DRA-29-08-qa-engineer.md. One test per behavior it lists.
The tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test.
"""

import logging
from dataclasses import replace

import pytest

from core.collision import Circle, hitboxes_overlap, place_hitbox
from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import Run, add_drifters, start_run, step_run
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

SPEED_RATIO: float = 0.75
"""Fixed test value for the speed rule, not the live tuning file."""

WARNING_TICKS: int = 30
"""Fixed test value for the warning length, not the live tuning file."""

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


def make_tuning() -> DrifterTuning:
    """Build the meteorite tuning from the GDD values above."""
    variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=width, height=width, hitbox=(Circle(0, 0, radius),))
        for name, (width, radius) in SIZES.items()
    }
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=variants,
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            )
        },
        switches=PlaytestSwitches(),
    )


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
    hit_ship: bool = False,
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
        hit_ship=hit_ship,
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


def test_a_warning_never_hits_and_ends_after_the_30th_step() -> None:
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
        assert not only(state).hit_ship
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
    assert only(after).hit_ship
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
    assert only(run).hit_ship
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
        assert not only(run).hit_ship, tick
        assert run.invuln_ticks_left == INVULN_TICKS - 1 - tick
        run = hold_ship(run)

    assert not run.invulnerable
    assert hitboxes_overlap(only(run).current_hitbox(), ship_hitbox(step_run(run, NO_KEY).ship))

    # Still overlapping when the timer is out: it hits now.
    run = step_run(run, NO_KEY)
    assert run.lives == LIVES_START - 1
    assert only(run).hit_ship
    assert run.invuln_ticks_left == INVULN_TICKS


def test_a_meteorite_hits_once() -> None:
    speed: float = 0.5
    start: Meteorite = rock(speed=speed)
    assert start.may_hit_ship()
    run: Run = step_run(run_with(start), NO_KEY)
    assert run.lives == LIVES_START - 1
    assert only(run).hit_ship
    assert not only(run).may_hit_ship()
    assert only(run).y == pytest.approx(HOME_Y + speed)

    # The rock keeps falling and stays on the field while it overlaps the ship, through
    # the invulnerability and 15 ticks past its end.
    for tick in range(INVULN_TICKS + 15):
        run = hold_ship(run)
        run = step_run(run, NO_KEY)
        assert run.lives == LIVES_START - 1, tick
        assert only(run).uid == 1
        assert only(run).hit_ship
        assert only(run).y == pytest.approx(HOME_Y + speed * (tick + 2))
        if tick >= INVULN_TICKS:
            assert not run.invulnerable
            assert hitboxes_overlap(only(run).current_hitbox(), ship_hitbox(run.ship))
    assert not run.game_over


def test_two_meteorites_on_one_tick_cost_one_life() -> None:
    far: Meteorite = rock(x=50.0, y=100.0)
    run: Run = step_run(run_with(rock(x=312.0), rock(x=328.0, y=244.0), far), NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert [drifter.hit_ship for drifter in run.drifters] == [True, True, False]
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
    assert not only(after).hit_ship
    assert only(after).phase is Phase.ACTIVE


def test_a_hit_on_the_last_life_ends_the_run() -> None:
    speed: float = 0.5
    before: Run = run_with(rock(speed=speed), lives=1)
    expected: Run = step_run(replace(before, drifters=()), NO_KEY)

    over: Run = step_run(before, NO_KEY)

    assert over.lives == 0
    assert over.game_over
    assert not over.invulnerable
    assert not over.waiting
    assert over.ship == expected.ship
    assert over.ship != spawn()
    assert only(over).hit_ship
    assert only(over).y == pytest.approx(HOME_Y + speed)

    # Everything freezes on the next ticks. Drifters don't move, and nothing is added.
    run: Run = over
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
    assert only(run).hit_ship
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
    assert not only(run).hit_ship
    assert not run.game_over

    # On the last life the fall ends the run, still with no hit recorded.
    over: Run = step_run(run_with(under, ship=fell, lives=1), NO_KEY)
    assert over.game_over
    assert over.lives == 0
    assert not only(over).hit_ship


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


def test_a_retry_starts_with_no_drifters() -> None:
    over: Run = step_run(run_with(rock(), rock(x=50.0, y=100.0), lives=1), NO_KEY)
    assert over.game_over
    assert len(over.drifters) == 2
    assert over.next_uid == 3

    armed: Run = step_run(over, NO_KEY)
    assert armed.drifters == over.drifters
    run: Run = step_run(armed, Thrust(up=True))

    assert not run.game_over
    assert run.drifters == ()
    assert run.next_uid == 1
    assert run == replace(start_run(), held=Thrust(up=True))

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
    for _ in range(150):
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
    for _ in range(100):
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
    for _ in range(100):
        run = hold_ship(step_run(run, NO_KEY))
        if run.drifters:
            assert not only(run).hit_ship
    through: list[str] = lines(caplog)
    assert run.drifters == ()
    assert run.lives == LIVES_START
    assert [line.split(" ")[0] for line in through] == ["invulnerable", "drifter"]
    assert through[1].startswith("drifter gone id=1 ")
