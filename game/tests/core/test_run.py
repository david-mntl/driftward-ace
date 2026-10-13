"""Run tests: lives, falls, the respawn wait, invulnerability, game over, retry.

Contract: docs/contracts/systems/run.md, Rules.
Task: docs/contracts/DRA-23/tasks/DRA-23-04-qa-engineer.md. One test per behavior it lists.
Every expected number comes from the GDD values below, never from the code under test.
"""

import logging
from dataclasses import replace

import pytest

from core.run import Run, start_run, step_run
from core.scroll import Scroll, start_scroll
from core.ship import Ship, Thrust, spawn, step

LIVES_START: int = 3
"""Source: 05-lives-and-damage.md, Values, lives_start (locked)."""

INVULN_TICKS: int = 30
"""Ticks. Source: 05-lives-and-damage.md, Values, invuln_ticks (locked)."""

BLINK_SWAP_TICKS: int = 6
"""Ticks. Source: scope report DRA-23, blink (one swap every 0.1 s, approved by the Director in
chat, not in the GDD) x 60 ticks/s (15-tech-constraints.md, tick_rate, locked)."""

START_X: float = 320.0
"""Source: 05-lives-and-damage.md, Values, fall_respawn (locked); 03-world-and-camera.md,
ship_start."""

START_Y: float = 240.0
"""Source: 05-lives-and-damage.md, Values, fall_respawn (locked); 03-world-and-camera.md,
ship_start."""

GRAVITY: float = 0.16
"""px/tick². Source: 04-ship.md, Values, gravity (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, Values, scroll_start_delay (guess)."""

NO_KEY = Thrust()
RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""


def _falling_ship() -> Ship:
    """A ship whose next tick with no key ends with its top edge at y 480 (a fall)."""
    return Ship(x=100.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)


def _falling_run(
    lives: int = LIVES_START,
    invuln_ticks_left: int = 0,
    held: Thrust = NO_KEY,
    scroll: Scroll | None = None,
) -> Run:
    """A run whose ship falls past the floor on the next tick with no key."""
    return Run(
        ship=_falling_ship(),
        scroll=scroll if scroll is not None else Scroll(ticks=200, scrolled_ticks=170),
        lives=lives,
        invuln_ticks_left=invuln_ticks_left,
        held=held,
    )


def _advance(run: Run, thrust: Thrust, ticks: int) -> Run:
    """Step the run the given number of ticks with the same keys."""
    for _ in range(ticks):
        run = step_run(run, thrust)
    return run


def _states_after_respawn(press_at: int | None, count: int) -> list[Run]:
    """The respawn state, then `count` more states. One up press at tick `press_at`, if given."""
    run = step_run(_falling_run(), NO_KEY)
    states = [run]
    for tick in range(1, count + 1):
        pressed = press_at is not None and tick == press_at
        run = step_run(run, Thrust(up=True) if pressed else NO_KEY)
        states.append(run)
    return states


def _top_edge(ship: Ship) -> float:
    return ship.y - SHIP_H / 2


def _assert_fresh_run(run: Run) -> None:
    """The state of a run that has just started."""
    assert run.lives == LIVES_START
    assert run.ship == spawn()
    assert run.scroll == start_scroll()
    assert not run.invulnerable
    assert not run.waiting
    assert not run.game_over


def _lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def _count(lines: list[str], prefix: str) -> int:
    return sum(1 for line in lines if line.startswith(prefix))


def test_run_starts_with_three_lives_at_spawn() -> None:
    run = start_run()

    _assert_fresh_run(run)
    assert (run.ship.x, run.ship.y, run.ship.vx, run.ship.vy) == pytest.approx(
        (START_X, START_Y, 0.0, 0.0)
    )
    assert run.scroll.ticks == 0
    assert run.scroll.scrolled_ticks == 0


def test_unprotected_fall_costs_a_life_and_respawns_waiting() -> None:
    before = _falling_run()
    assert not before.invulnerable

    run = step_run(before, NO_KEY)

    assert run.lives == LIVES_START - 1
    assert run.ship == spawn()
    assert (run.ship.x, run.ship.y, run.ship.vx, run.ship.vy) == pytest.approx(
        (START_X, START_Y, 0.0, 0.0)
    )
    assert run.waiting
    assert run.invulnerable
    assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over


@pytest.mark.smoke
def test_wait_holds_the_ship_and_the_scroll_keeps_going() -> None:
    run = step_run(_falling_run(scroll=start_scroll()), NO_KEY)
    ticks = 1
    assert run.waiting
    assert run.scroll.scrolled_ticks == max(0, ticks - SCROLL_START_DELAY)

    for _ in range(600):
        before = run.scroll.scrolled_ticks
        run = step_run(run, NO_KEY)
        ticks += 1
        assert run.waiting
        assert run.ship == spawn()
        assert run.lives == LIVES_START - 1
        assert run.scroll.ticks == ticks
        assert run.scroll.scrolled_ticks == max(0, ticks - SCROLL_START_DELAY)
        if ticks > SCROLL_START_DELAY:
            assert run.scroll.scrolled_ticks == before + 1


def test_the_press_that_ends_the_wait_also_thrusts() -> None:
    waiting = step_run(_falling_run(), NO_KEY)
    assert waiting.waiting

    for thrust in (Thrust(up=True), Thrust(right=True), Thrust(left=True, down=True)):
        run = step_run(waiting, thrust)

        assert not run.waiting
        assert run.ship == step(spawn(), thrust)
        assert run.lives == LIVES_START - 1


def test_a_held_arrow_does_not_end_the_wait() -> None:
    right = Thrust(right=True)

    # Held since before the fall.
    held_before = step_run(_falling_run(held=right), right)
    # Pressed on the very tick of the fall.
    pressed_on_fall = step_run(_falling_run(), right)

    for run in (held_before, pressed_on_fall):
        assert run.waiting
        assert run.ship == spawn()
        for _ in range(120):
            run = step_run(run, right)
            assert run.waiting
            assert run.ship == spawn()

        run = step_run(run, NO_KEY)
        assert run.waiting
        assert run.ship == spawn()

        run = step_run(run, right)
        assert not run.waiting
        assert run.ship == step(spawn(), right)


@pytest.mark.parametrize("press_at", [None, 10, 29, 30])
def test_invulnerability_lasts_30_ticks_wait_or_no_wait(press_at: int | None) -> None:
    states = _states_after_respawn(press_at, INVULN_TICKS + 10)

    for index, run in enumerate(states):
        assert run.invulnerable == (index < INVULN_TICKS), index
    assert states[0].waiting
    if press_at is not None:
        assert not states[press_at].waiting


def test_blink_swaps_every_six_ticks_then_stays_visible() -> None:
    for press_at in (None, 10):
        states = _states_after_respawn(press_at, INVULN_TICKS + 12)
        visible = [run.ship_visible for run in states]

        block = BLINK_SWAP_TICKS
        expected = (
            [True] * block
            + [False] * block
            + [True] * block
            + [False] * block
            + [True] * block
            + [True] * (len(states) - 5 * block)
        )
        assert visible == expected


def test_a_fall_while_invulnerable_costs_no_life() -> None:
    for left in (INVULN_TICKS, 17, 2, 1):
        before = _falling_run(lives=2, invuln_ticks_left=left)
        assert before.invulnerable

        run = step_run(before, NO_KEY)

        assert run.lives == 2
        assert run.ship == spawn()
        assert not run.waiting
        assert not run.game_over
        assert run.invuln_ticks_left == left - 1
        assert run.invulnerable == (left > 1)


def test_losing_the_last_life_ends_the_run() -> None:
    run = step_run(_falling_run(lives=1), NO_KEY)

    assert run.lives == 0
    assert run.game_over
    assert not run.waiting
    assert not run.invulnerable
    assert _top_edge(run.ship) >= SCREEN_H
    assert run.ship != spawn()


@pytest.mark.smoke
def test_game_over_freezes_everything() -> None:
    over = step_run(_falling_run(lives=1), NO_KEY)
    assert over.game_over

    run = over
    for _ in range(300):
        run = step_run(run, NO_KEY)
        assert run.game_over
        assert run.ship == over.ship
        assert run.scroll == over.scroll
        assert run.lives == 0


@pytest.mark.smoke
def test_a_held_arrow_never_retries() -> None:
    right = Thrust(right=True)
    over = step_run(_falling_run(lives=1, held=right), right)
    assert over.game_over

    run = over
    for _ in range(300):
        run = step_run(run, right)
        assert run.game_over
        assert run.ship == over.ship
        assert run.scroll == over.scroll

    # A second arrow pressed while the first is still held is not a retry.
    both = Thrust(right=True, left=True)
    run = _advance(run, both, 5)
    assert run.game_over
    run = _advance(run, Thrust(left=True), 5)
    assert run.game_over

    # Every arrow released, then one pressed.
    run = step_run(run, NO_KEY)
    assert run.game_over
    run = step_run(run, Thrust(up=True))
    assert not run.game_over
    _assert_fresh_run(run)


def test_retry_has_no_delay_when_released_at_game_over() -> None:
    over = step_run(_falling_run(lives=1), NO_KEY)
    assert over.game_over

    run = step_run(over, Thrust(down=True))

    assert not run.game_over
    _assert_fresh_run(run)


def test_a_new_run_starts_like_the_first() -> None:
    over = step_run(_falling_run(lives=1), NO_KEY)
    run = step_run(over, Thrust(left=True))
    _assert_fresh_run(run)

    next_run = step_run(run, NO_KEY)

    assert next_run.ship.vy == pytest.approx(GRAVITY)
    assert next_run.ship.y == pytest.approx(START_Y + GRAVITY)
    assert next_run.ship.x == pytest.approx(START_X)
    assert next_run.scroll.ticks == 1
    assert next_run.scroll.scrolled_ticks == 0
    assert next_run.lives == LIVES_START
    assert not next_run.invulnerable
    assert not next_run.waiting
    assert not next_run.game_over


def test_events_log_once_on_core_run(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    right = Thrust(right=True)

    # A fall while invulnerable: one respawn line, no life lost.
    step_run(_falling_run(lives=2, invuln_ticks_left=17), NO_KEY)
    lines = _lines(caplog)
    assert _count(lines, "respawn from") == 1
    assert _count(lines, "life lost") == 0
    caplog.clear()

    # A key held through the fall and the wait never logs the end of the wait.
    held = _advance(step_run(_falling_run(held=right), right), right, 10)
    assert held.waiting
    assert _count(_lines(caplog), "respawn wait end") == 0
    caplog.clear()

    # First fall. Then 600 ticks of waiting log only the end of the invulnerability.
    run = step_run(_falling_run(), NO_KEY)
    lines = _lines(caplog)
    assert _count(lines, "life lost") == 1
    assert _count(lines, "respawn from") == 1
    caplog.clear()

    run = _advance(run, NO_KEY, 600)
    assert _lines(caplog) == ["invulnerable end"]
    caplog.clear()

    # The press that ends the wait.
    run = step_run(run, right)
    assert _lines(caplog) == ["respawn wait end"]
    run = _advance(run, NO_KEY, 40)
    caplog.clear()

    # Second fall.
    run = step_run(replace(run, ship=_falling_ship()), NO_KEY)
    lines = _lines(caplog)
    assert run.lives == 1
    assert _count(lines, "life lost") == 1
    assert _count(lines, "respawn from") == 1
    caplog.clear()
    run = _advance(run, NO_KEY, 40)
    assert _lines(caplog) == ["invulnerable end"]
    caplog.clear()
    run = step_run(run, right)
    assert _lines(caplog) == ["respawn wait end"]
    run = _advance(run, NO_KEY, 40)
    caplog.clear()

    # Last life: game over, no respawn line. Frozen ticks log nothing.
    run = step_run(replace(run, ship=_falling_ship()), NO_KEY)
    lines = _lines(caplog)
    assert run.game_over
    assert _count(lines, "life lost") == 1
    assert _count(lines, "game over") == 1
    assert _count(lines, "respawn from") == 0
    caplog.clear()
    run = _advance(run, NO_KEY, 100)
    assert _lines(caplog) == []

    # Retry.
    run = step_run(run, Thrust(up=True))
    assert not run.game_over
    lines = _lines(caplog)
    assert _count(lines, "new run") == 1
    assert len(lines) == 1
