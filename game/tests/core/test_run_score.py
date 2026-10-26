"""Run score tests: meters plus coin points, never down, frozen from the last life, 0 when new.

Contract: docs/contracts/systems/run.md, Rules (Score, The last life, a last-life tick, a
game-over tick, `next_run`, Logging) and
docs/contracts/systems/scroll.md, Rules (Distance).
Task: docs/contracts/DRA-61/tasks/DRA-61-04-qa-engineer.md. One test per behavior it lists.
Every expected number comes from the GDD values below, never from the code under test.
"""

import logging
from dataclasses import replace
from itertools import pairwise

import pytest

from core.run import Run, next_run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust

POINTS_PER_METER: int = 1
"""Points for each whole meter. Source: 06-scoring.md, Values, points_per_meter (locked)."""

PX_PER_METER: int = 10
"""px. Source: 03-world-and-camera.md, Values, px_per_meter (locked)."""

SCROLL_PER_TICK_TENTHS: int = 11
"""The scroll speed, 1.1 px/tick, in tenths of a px so the meters are worked out in whole
numbers. Source: 03-world-and-camera.md, Values, scroll_base (guess); 08-difficulty.md,
Level 1 scroll speed x1 (locked)."""

SCROLL_START_DELAY: int = 30
"""Ticks before the world moves. Source: 03-world-and-camera.md, Values, scroll_start_delay
(guess)."""

LIVES_START: int = 3
"""Source: 05-lives-and-damage.md, Values, lives_start (locked)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

NO_KEY = Thrust()
UP = Thrust(up=True)
RUN_LOGGERS = ("core.run", "core.scroll", "core.ship")
"""Every logger a run step writes to. Source: systems/run.md, Logging; scroll.md; ship.md."""

LAST_LIFE_DELAY: int = 120
"""Ticks from the death tick to game over. Source: 02-game-flow.md, Values, last_life_delay
(guess)."""

HOLD_UP_TICKS: int = 150
"""Ticks the scripted pilot holds up after each respawn before it lets the ship fall."""

WAIT_TICKS: int = 90
"""Ticks the scripted pilot leaves the ship standing in the respawn wait."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here falls past the floor on the next tick with no key."""


def _meters_after(ticks: int) -> int:
    """Whole meters flown after `ticks` ticks of an unbroken run: the world moves from tick
    SCROLL_START_DELAY + 1, SCROLL_PER_TICK px each tick, rounded down to a meter."""
    scrolled = max(ticks - SCROLL_START_DELAY, 0)
    return scrolled * SCROLL_PER_TICK_TENTHS // (10 * PX_PER_METER)


def _falling_run(lives: int = LIVES_START, coin_points: int = 0) -> Run:
    """A run whose ship falls past the floor on the next tick with no key."""
    return Run(
        ship=Ship(x=100.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP),
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        lives=lives,
        coin_points=coin_points,
    )


def _scripted_run(coin_points: int = 0) -> list[Run]:
    """A whole run, from play start to game over, through falls, respawn waits and presses.

    The pilot holds up for HOLD_UP_TICKS after each start or respawn press, then lets go and
    the ship falls. It stands in each wait for WAIT_TICKS, then presses up. Returns the state
    after every tick, the start state first. The last state is the game-over state.
    """
    run = replace(start_run(), coin_points=coin_points)
    states = [run]
    flying = 0
    waited = 0
    for _ in range(5000):
        if run.waiting:
            waited += 1
            flying = 0
            thrust = UP if waited > WAIT_TICKS else NO_KEY
        else:
            waited = 0
            flying += 1
            thrust = UP if flying <= HOLD_UP_TICKS else NO_KEY
        run = step_run(run, thrust)
        states.append(run)
        if run.game_over:
            return states
    raise AssertionError("the scripted run never reached game over")


def _death(states: list[Run]) -> int:
    """The index of the state after the tick the last life was lost."""
    return next(i for i, s in enumerate(states) if s.burst is not None)


def _lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name in RUN_LOGGERS]


def test_a_new_run_has_score_0_and_coin_points_0() -> None:
    run = start_run()

    assert run.score == 0
    assert run.coin_points == 0
    assert run.scroll.meters == 0


@pytest.mark.smoke
def test_score_is_the_whole_meters_flown_one_point_a_meter() -> None:
    run = start_run()
    scores = [run.score]
    for _ in range(1000):
        run = step_run(run, UP)
        scores.append(run.score)
        assert run.coin_points == 0

    for ticks, score in enumerate(scores):
        assert score == _meters_after(ticks) * POINTS_PER_METER, f"tick {ticks}"

    # 0 for the first 30 ticks and until 10 px have scrolled: 9 scrolled ticks are 9.9 px,
    # the 10th is 11.0 px, the first meter.
    assert scores[: SCROLL_START_DELAY + 10] == [0] * (SCROLL_START_DELAY + 10)
    assert scores[SCROLL_START_DELAY + 10] == 1
    # After 100 scrolled ticks, 110 px: 11 m (scroll.md, Distance timeline).
    assert scores[SCROLL_START_DELAY + 100] == 11
    assert scores[-1] == 106  # 970 scrolled ticks x 1.1 px = 1067 px, 106 whole meters
    assert all(a <= b for a, b in pairwise(scores))


def test_score_is_the_meters_plus_the_coin_points() -> None:
    for coin_points in (1, 7, 250):
        run = replace(start_run(), coin_points=coin_points)
        assert run.score == coin_points

        for ticks in range(1, 200):
            run = step_run(run, UP)
            assert run.coin_points == coin_points
            assert run.score == _meters_after(ticks) * POINTS_PER_METER + coin_points

    # 170 scrolled ticks x 1.1 px = 187 px: 18 m.
    mid_run = Run(
        ship=start_run().ship,
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        coin_points=5,
    )
    assert mid_run.score == 18 + 5


@pytest.mark.smoke
def test_no_playing_tick_changes_the_coin_points() -> None:
    for coin_points in (0, 12):
        states = _scripted_run(coin_points)
        assert any(s.waiting for s in states), "the run has a respawn wait"
        assert states[-1].lives == 0
        assert states[-1].game_over
        playing = [s for s in states if s.burst is None]
        assert min(s.lives for s in playing) == 1, "the run has falls"
        assert all(s.coin_points == coin_points for s in states)

        # A fall tick on its own.
        assert step_run(_falling_run(coin_points=coin_points), NO_KEY).coin_points == coin_points
        # A last-life fall (the tick the last life starts) and the ticks after it.
        last = step_run(_falling_run(lives=1, coin_points=coin_points), NO_KEY)
        assert last.last_life
        assert last.coin_points == coin_points
        assert step_run(last, NO_KEY).coin_points == coin_points


@pytest.mark.smoke
def test_score_never_goes_down_and_keeps_counting_through_falls_and_waits() -> None:
    states = _scripted_run()
    scores = [s.score for s in states]

    assert all(a <= b for a, b in pairwise(scores))
    # The meters keep counting through every fall, respawn and wait, tick for tick, up to the
    # tick the last life is lost. From then on the score is the frozen final score.
    death = _death(states)
    for ticks, run in enumerate(states):
        assert run.scroll.ticks == ticks
        if ticks <= death:
            assert run.score == _meters_after(ticks) * POINTS_PER_METER, f"tick {ticks}"
        else:
            assert run.score == states[death].score, f"tick {ticks}"

    # A fall happened, and the score still counted up across the wait that followed it.
    fall_ticks = [i for i in range(1, len(states)) if states[i].lives < states[i - 1].lives]
    assert len(fall_ticks) == LIVES_START
    waits = [i for i, s in enumerate(states) if s.waiting]
    assert waits
    first_wait, last_wait = waits[0], waits[-1]
    assert last_wait - first_wait >= WAIT_TICKS - 1
    assert states[last_wait].score > states[first_wait].score
    assert scores[-1] > 0


@pytest.mark.smoke
def test_score_stops_on_the_death_tick_and_stays_through_game_over() -> None:
    states = _scripted_run()
    death = _death(states)
    last = states[death]
    over = states[-1]
    assert over.game_over
    # The death tick runs in full: the score on it is the meters of that tick.
    assert last.score == _meters_after(last.scroll.ticks) * POINTS_PER_METER
    assert last.score > 0
    assert last.final_score == last.score
    # The scroll runs on through the last life, but the score never moves.
    assert over.scroll.ticks == last.scroll.ticks + LAST_LIFE_DELAY
    assert over.scroll.meters > last.scroll.meters
    assert all(s.score == last.score for s in states[death:])

    # Every arrow released: the score never moves.
    run = over
    for _ in range(400):
        run = step_run(run, NO_KEY)
        assert run.game_over
        assert run.score == over.score
        assert run.scroll == over.scroll
        assert run.coin_points == over.coin_points

    # An arrow held since game over: no new run, and the score never moves.
    left = Thrust(left=True)
    run = replace(over, held=left)
    for _ in range(400):
        run = step_run(run, left)
        assert run.game_over
        assert run.score == over.score
        assert run.scroll == over.scroll

    # With coin points, the final score is meters + coin points and stays too.
    paid = _scripted_run(coin_points=40)[-1]
    assert paid.score == over.score + 40
    run = paid
    for _ in range(50):
        run = step_run(run, NO_KEY)
        assert run.score == paid.score


def test_a_new_run_gives_score_0_again() -> None:
    over = _scripted_run()[-1]
    assert over.score > 0

    released = step_run(over, NO_KEY)
    assert released.game_over
    assert released.score == over.score

    run = next_run(released)
    assert not run.game_over
    assert run.score == 0
    assert run.coin_points == 0
    assert run.final_score is None

    # The new run counts from 0 like the first one.
    for ticks in range(1, 200):
        run = step_run(run, UP)
        assert run.score == _meters_after(ticks) * POINTS_PER_METER

    # Coin points do not carry over into a new run.
    paid_over = _scripted_run(coin_points=33)[-1]
    assert paid_over.score == over.score + 33
    fresh = next_run(step_run(paid_over, NO_KEY))
    assert not fresh.game_over
    assert fresh.coin_points == 0
    assert fresh.score == 0


def test_only_the_last_life_and_game_over_lines_name_the_score(
    caplog: pytest.LogCaptureFixture,
) -> None:
    for name in RUN_LOGGERS:
        caplog.set_level(logging.DEBUG, logger=name)

    states = _scripted_run(coin_points=5)
    over = states[-1]
    next_run(step_run(over, NO_KEY))  # the new run
    lines = _lines(caplog)

    assert lines
    named = [line for line in lines if "score" in line.lower()]
    assert named == [f"last life score={over.score}", f"game over score={over.score}"]
    assert not [line for line in lines if "coin" in line.lower()]
    assert not [line for line in lines if line.startswith("game over meters")]
    assert lines.index(named[0]) < lines.index(named[1])
