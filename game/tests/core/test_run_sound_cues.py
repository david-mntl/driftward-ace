"""The sound cues a run lists for each stepped tick: coin, graze, hit, their order, and when none.

Contract: docs/contracts/systems/run.md, Interface (DRA-158: the sound cues), Rules (Sound cues,
steps 5a, 5b, 6 and 7, The last life, A last-life tick); docs/contracts/systems/game-flow.md,
Rules (`run_stepped`).
Task: docs/contracts/DRA-158/tasks/DRA-158-02-qa-engineer.md. One test per behavior it lists.

The tuning records are built here from the GDD values below, never read from game/tuning/, and no
expected number is imported from the code under test. The ship is put back at rest on its home
spot before a tick that needs it (a ship held still), and a hazard is moved instead, by the gap
between its hitbox and the ship's foot (16 px right of the ship's center, 10 px below it). A gap
above 14 is outside the graze zone, a gap from 0 to 14 is inside it, a gap below 0 is a touch. A
hazard that "leaves" the zone is built with `graze_state` INSIDE and put outside: it pays on that
tick. A fall is a ship whose next step puts its top edge on the floor.
"""

from dataclasses import replace

import pytest

from core.collision import Box, Circle, Hitbox
from core.drifters.base import Drifter, DrifterType, GrazeState, Phase
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.game_flow import GameFlow, Screen, TickInput, start_flow, step_flow
from core.run import Run, next_run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust
from core.sound_cue import SoundCue

LIVES_START: int = 5
INVULN_TICKS: int = 60
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

COIN_POINTS: int = 50
"""Source: drifters/04-coin.md, Values (common coin)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""

FALL_X: float = 200.0
"""Where the falling ship is, left of the field's center."""

FELL_Y: float = AT_FLOOR_Y + FALL_CAP
"""The falling ship's center after its step: its top edge on the floor."""

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

FOOT_HALF_W: float = 16.0
FOOT_ROW_DY: float = 10.0
"""The ship's foot: half its 32 px width, and its middle row below the center (16 - 12 / 2).
Source: 04-ship.md, hitbox (guess)."""

ROCK_RADIUS: float = 14.0
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

IN: float = 6.0
OUT: float = 20.0
"""Gaps, px, between a hazard's hitbox and the ship's foot: inside the zone, outside it (the zone
reaches 14 px, graze_margin, locked in 06-scoring.md)."""

LAST_LIFE_DELAY: int = 120
"""Ticks from the death tick to game over. Source: 02-game-flow.md, Values, last_life_delay
(guess)."""

SPEED_RATIO: float = 0.375
WARNING_TICKS: int = 60
"""Source: the hazards' speed_ratio (guess) and 07-drifters.md, entry_warning_ticks (guess)."""

NO_KEY = Thrust()
HOME: Ship = Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)
FALLING: Ship = Ship(x=FALL_X, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)

STILL: Scroll = Scroll()
"""A scroll at tick 0: the world stands still for the first 30 ticks, so a parked coin stays where
it is put."""

ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, ROCK_RADIUS),)
COIN_HITBOX: Hitbox = (Box(0.0, 0.0, 12.0, 10.0),)


def make_tuning() -> DrifterTuning:
    """Build the tuning of the two drifters the tests place, from the GDD values above.

    The meteorite's medium variant and the coin's common one, the way `app.tuning` builds them.
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
                        extra=CoinVariantExtra(points=COIN_POINTS, glint=False),
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
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = make_tuning()


def rock(x: float, y: float) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, 100.0, 100.0), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0, x=x, y=y)


def coin(x: float, y: float) -> Coin:
    """A common coin, ACTIVE from birth."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.COIN, x, y), 1, TUNING)
    assert isinstance(spawned, Coin)
    return spawned


def rock_at_gap(gap: float, *, left: bool = False) -> Meteorite:
    """A still rock whose hitbox is `gap` px from the home ship's foot, right or left of it."""
    sign: float = -1.0 if left else 1.0
    return rock(HOME_X + sign * (FOOT_HALF_W + ROCK_RADIUS + gap), HOME_Y + FOOT_ROW_DY)


def leaving(drifter: Meteorite) -> Meteorite:
    """The rock as if the ship had been inside its zone on the last tick."""
    return replace(drifter, graze_state=GrazeState.INSIDE)


def run_of(
    *drifters: Drifter,
    ship: Ship = HOME,
    lives: int = LIVES_START,
    invuln_ticks_left: int = 0,
    waiting: bool = False,
) -> Run:
    """A run on a still scroll with the drifters numbered from 1, in order."""
    numbered: tuple[Drifter, ...] = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return replace(
        start_run(),
        ship=ship,
        scroll=STILL,
        lives=lives,
        invuln_ticks_left=invuln_ticks_left,
        waiting=waiting,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def hit_run(*drifters: Drifter, lives: int = LIVES_START, **fields: object) -> Run:
    """A ship at home with a still rock on it: the next tick is a hit, unless protected."""
    return run_of(rock(HOME_X, HOME_Y), *drifters, lives=lives, **fields)  # type: ignore[arg-type]


def fall_run(*drifters: Drifter, lives: int = LIVES_START, **fields: object) -> Run:
    """A ship that falls past the floor on the next tick with no key."""
    return run_of(*drifters, ship=FALLING, lives=lives, **fields)  # type: ignore[arg-type]


def death_run(how: str) -> Run:
    """A one-life run, the next tick of which loses it, by a `touch` or a `fall`.

    The tick also collects a coin and pays a graze, so its cues are COIN, GRAZE, HIT.
    """
    if how == "touch":
        return hit_run(coin(HOME_X, HOME_Y), leaving(rock_at_gap(OUT)), lives=1)
    assert how == "fall"
    return fall_run(coin(FALL_X, FELL_Y), leaving(rock(100.0, 100.0)), lives=1)


def play(run: Run, ticks: int) -> list[Run]:
    """The run after the tick it was given, then after each of `ticks` more, with no key."""
    states: list[Run] = [step_run(run, NO_KEY)]
    for _ in range(ticks):
        states.append(step_run(states[-1], NO_KEY))
    return states


def test_a_collected_coin_gives_one_coin_on_that_tick_and_nothing_on_the_next() -> None:
    run = run_of(coin(HOME_X, HOME_Y))
    first = step_run(run, NO_KEY)
    assert first.coin_points == COIN_POINTS
    assert first.sound_cues == (SoundCue.COIN,)
    second = step_run(first, NO_KEY)
    assert second.coin_points == COIN_POINTS
    assert second.sound_cues == ()


def test_one_paid_graze_gives_one_graze_and_two_paid_on_one_tick_give_two() -> None:
    # A real pass: inside the zone on tick 1, outside on tick 2.
    entered = step_run(run_of(rock_at_gap(IN)), NO_KEY)
    assert entered.drifters[0].graze_state is GrazeState.INSIDE
    assert entered.grazes == 0
    assert entered.sound_cues == ()
    outside = rock_at_gap(OUT)
    moved = replace(entered.drifters[0], x=outside.x, y=outside.y)
    one = step_run(replace(entered, ship=HOME, drifters=(moved,)), NO_KEY)
    assert one.grazes == 1
    assert one.sound_cues == (SoundCue.GRAZE,)
    assert step_run(one, NO_KEY).sound_cues == ()
    # Two hazards leaving their zones on one tick, one on each side.
    both = run_of(leaving(rock_at_gap(OUT)), leaving(rock_at_gap(OUT, left=True)))
    two = step_run(both, NO_KEY)
    assert two.grazes == 2
    assert two.sound_cues == (SoundCue.GRAZE, SoundCue.GRAZE)


def test_an_unprotected_touch_gives_one_hit_and_two_touching_hazards_still_give_one() -> None:
    one = step_run(hit_run(), NO_KEY)
    assert one.lives == LIVES_START - 1
    assert one.sound_cues == (SoundCue.HIT,)
    both = step_run(hit_run(rock(HOME_X + 6.0, HOME_Y)), NO_KEY)
    assert all(d.rehit_ticks_left > 0 for d in both.drifters)
    assert both.lives == LIVES_START - 1
    assert both.sound_cues == (SoundCue.HIT,)


def test_an_unprotected_fall_to_a_life_left_gives_one_hit() -> None:
    fell = step_run(fall_run(), NO_KEY)
    assert fell.lives == LIVES_START - 1
    assert fell.last_life is False
    assert fell.sound_cues == (SoundCue.HIT,)


@pytest.mark.parametrize("how", ["fall", "touch"])
def test_a_protected_fall_and_a_touch_while_protected_give_no_cue(how: str) -> None:
    for left in (1, INVULN_TICKS):
        run = (fall_run if how == "fall" else hit_run)(invuln_ticks_left=left)
        stepped = step_run(run, NO_KEY)
        assert stepped.lives == LIVES_START
        assert stepped.sound_cues == ()


@pytest.mark.parametrize("how", ["touch", "fall"])
def test_a_tick_with_a_coin_a_graze_and_a_life_lost_gives_coin_graze_hit_in_that_order(
    how: str,
) -> None:
    run = hit_run if how == "touch" else fall_run
    if how == "touch":
        run_before = run(coin(HOME_X, HOME_Y), leaving(rock_at_gap(OUT)))
    else:
        run_before = run(coin(FALL_X, FELL_Y), leaving(rock(100.0, 100.0)))
    stepped = step_run(run_before, NO_KEY)
    assert stepped.lives == LIVES_START - 1
    assert stepped.coin_points == COIN_POINTS
    assert stepped.grazes == 1
    assert stepped.sound_cues == (SoundCue.COIN, SoundCue.GRAZE, SoundCue.HIT)


@pytest.mark.parametrize("how", ["touch", "fall"])
def test_the_tick_that_loses_the_last_life_gives_its_hit_and_game_over_after_its_coin_and_graze(
    how: str,
) -> None:
    quiet = step_run(death_run(how), NO_KEY)
    assert quiet.lives == 0
    assert quiet.last_life is True
    assert quiet.coin_points == COIN_POINTS
    assert quiet.grazes == 1
    assert quiet.sound_cues == (SoundCue.COIN, SoundCue.GRAZE, SoundCue.HIT, SoundCue.GAME_OVER)
    # The same tick with nothing to collect or graze: the HIT, then GAME_OVER.
    bare = step_run(hit_run(lives=1) if how == "touch" else fall_run(lives=1), NO_KEY)
    assert bare.lives == 0
    assert bare.sound_cues == (SoundCue.HIT, SoundCue.GAME_OVER)


@pytest.mark.parametrize("how", ["touch", "fall"])
def test_last_life_ticks_after_it_and_a_game_over_tick_give_no_cue(how: str) -> None:
    states = play(death_run(how), LAST_LIFE_DELAY)
    assert states[0].sound_cues[-2:] == (SoundCue.HIT, SoundCue.GAME_OVER)
    assert states[-1].game_over is True
    over_index = next(i for i, s in enumerate(states) if s.game_over)
    assert over_index == LAST_LIFE_DELAY
    for state in states[1:]:
        assert state.sound_cues == ()
    # A coin, a graze and a hazard on the ship during the last life still give none.
    ship = states[0].ship
    parked = (
        replace(coin(ship.x, ship.y), uid=90),
        replace(leaving(rock(ship.x, ship.y)), uid=91),
    )
    busy = replace(states[1], drifters=states[1].drifters + parked)
    assert busy.last_life is True
    after = step_run(busy, NO_KEY)
    assert after.sound_cues == ()
    assert after.coin_points == busy.coin_points
    assert after.lives == 0
    # A game-over tick, stepped again, holding cues it did not make, gives none.
    over = states[-1]
    stale = replace(over, sound_cues=(SoundCue.COIN, SoundCue.HIT))
    assert step_run(stale, NO_KEY).sound_cues == ()
    assert step_run(stale, Thrust(up=True)).sound_cues == ()


def test_a_quiet_tick_after_a_tick_with_cues_gives_none_a_cue_is_never_carried_over() -> None:
    cued = step_run(hit_run(coin(HOME_X, HOME_Y)), NO_KEY)
    assert cued.sound_cues == (SoundCue.COIN, SoundCue.HIT)
    # Protected now, so the rock on the ship costs nothing and nothing else happens.
    quiet = step_run(replace(cued, ship=HOME), NO_KEY)
    assert quiet.invuln_ticks_left > 0
    assert quiet.sound_cues == ()
    # A run handed in with cues it did not make: its next tick lists only its own.
    stale = replace(quiet, sound_cues=(SoundCue.GRAZE, SoundCue.HIT))
    assert step_run(stale, NO_KEY).sound_cues == ()
    owed = replace(run_of(coin(HOME_X, HOME_Y)), sound_cues=(SoundCue.HIT,))
    assert step_run(owed, NO_KEY).sound_cues == (SoundCue.COIN,)


def test_start_run_and_next_run_give_no_cue() -> None:
    assert start_run().sound_cues == ()
    finished = play(death_run("touch"), LAST_LIFE_DELAY)[-1]
    stale = replace(finished, sound_cues=(SoundCue.COIN, SoundCue.GRAZE, SoundCue.HIT))
    assert next_run(stale).sound_cues == ()
    cued = step_run(hit_run(coin(HOME_X, HOME_Y)), NO_KEY)
    assert cued.sound_cues != ()
    assert next_run(cued).sound_cues == ()


def test_a_paused_tick_leaves_run_stepped_false_with_the_cues_still_in_the_run() -> None:
    cued = step_run(hit_run(coin(HOME_X, HOME_Y)), NO_KEY)
    cues = (SoundCue.COIN, SoundCue.HIT)
    assert cued.sound_cues == cues
    playing: GameFlow = replace(
        start_flow(cued), screen=Screen.PLAYING, confirm_held=False, arrows_held=NO_KEY
    )
    stepped = step_flow(playing, TickInput(thrust=NO_KEY))
    assert stepped.run_stepped is True
    assert stepped.run.sound_cues == ()
    # Back to a run holding cues from its last stepped tick; pause it by a focus loss.
    paused = step_flow(playing, TickInput(focus_lost=True))
    assert paused.screen is Screen.PAUSED
    assert paused.run_stepped is False
    assert paused.run.sound_cues == cues
    # Paused ticks, with arrows held: the run is not stepped and still holds the cues.
    held = step_flow(paused, TickInput(thrust=Thrust(up=True)))
    assert held.screen is Screen.PAUSED
    assert held.run_stepped is False
    assert held.run.sound_cues == cues
    idle = step_flow(held, TickInput())
    assert idle.run_stepped is False
    assert idle.run.sound_cues == cues
    # The resume tick steps nothing either.
    resumed = step_flow(idle, TickInput(confirm=True))
    assert resumed.screen is Screen.PLAYING
    assert resumed.run_stepped is False
    assert resumed.run.sound_cues == cues
    # The first tick that steps the run again lists its own cues.
    again = step_flow(resumed, TickInput(confirm=True))
    assert again.run_stepped is True
    assert again.run.sound_cues == ()
