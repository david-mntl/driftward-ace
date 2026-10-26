"""The coin, the base rules it relies on, its popup, and coins inside the run.

Contract: docs/contracts/systems/drifters.md, Rules: Coin, The base (Parked and moving, Per-tick
facts, Collect, Entering, Leaving), Spawner (step 4, Parked), Diagram (the coin timeline);
docs/contracts/systems/run.md, Rules (steps 3, 3a, 5a, 6, 7, 9, a game-over tick, Score) and
Logging, Diagram (the score and popup timelines); docs/contracts/systems/scroll.md,
`scroll_step_px`. Task: docs/contracts/DRA-62/tasks/DRA-62-06-qa-engineer.md. One test per
behavior it lists (the `scroll_step_px` one is in test_scroll.py). The tuning records are built
here from the GDD values below, never read from game/tuning/, and no expected number is imported
from the code under test.
"""

import logging
import math
from dataclasses import replace
from fractions import Fraction

import pytest

from core.collision import Box, Circle, Hitbox, hitboxes_overlap, place_hitbox
from core.drifters.base import Drifter, DrifterType, Phase, TickContext, TouchEffect
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.popup import PointsPopup
from core.run import Run, add_drifters, next_run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

CRYSTAL_W: int = 12
CRYSTAL_H: int = 20
BODY_H: int = 10
RING_W: int = 22
RING_H: int = 8
"""px. Source: drifters/04-coin.md, Values (guess); drifters.md, Rules, Coin (Values)."""

GLINT: tuple[int, int, int] = (2, 3, 3)
"""Glint side, left, top, px. Source: drifters.md, Rules, Coin (Values)."""

POINTS: dict[str, int] = {"common": 50, "rare": 100}
"""Points by variant. Source: 06-scoring.md, coin_points (common 50 locked, rare 100 guess)."""

POPUP_TICKS: int = 60
"""Source: drifters/04-coin.md, popup (60 ticks, guess)."""

POPUP_RISE: float = 0.5
"""px/tick. Source: scope report DRA-62, Not in GDD (Director approval)."""

SCROLL_SPEED: float = 1.1
"""px/tick at Level 1. Source: 03-world-and-camera.md, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, scroll_start_delay (guess)."""

PX_PER_METER: int = 10
"""Source: 03-world-and-camera.md, px_per_meter (locked)."""

SCREEN_W: int = 640
SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

REHIT_COOLDOWN: int = 180
"""Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

GRAVITY: float = 0.16
FALL_CAP: float = 5.5
"""px/tick². px/tick. Source: 04-ship.md, Values, gravity, fall_cap (guess)."""

LAST_LIFE_DELAY: int = 120
"""Ticks from the death tick to game over. Source: 02-game-flow.md, Values, last_life_delay
(guess)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()
UP = Thrust(up=True)

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

HITBOX = (Box(0.0, 0.0, float(CRYSTAL_W), float(BODY_H)),)
"""The coin's one box, the crystal's middle rectangle. Source: drifters.md, Rules, Coin (Size and
hitbox)."""

ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, 14.0),)
"""The medium meteorite, a hazard to put on the ship beside a coin. Source:
drifters/01-meteorite.md, variants (guess)."""

VARIANTS: tuple[str, ...] = tuple(POINTS)

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""


def meters_after_step(scroll: Scroll) -> int:
    """Whole meters after one more step of a moving scroll, worked out here in whole numbers."""
    distance = (scroll.scrolled_ticks + 1) * Fraction("1.1")
    return math.floor(distance / PX_PER_METER)


def make_tuning(*, switches: PlaytestSwitches | None = None) -> DrifterTuning:
    """Build the coin and meteorite tuning from the GDD values above.

    The coin's records are built the way the contract says `app.tuning` builds them: every variant
    has the crystal's size and the one box, speed_ratio 0.0 and no entry warning.
    """
    type_extra = CoinTypeExtra(
        body_height=BODY_H,
        ring_width=RING_W,
        ring_height=RING_H,
        glint_size=GLINT[0],
        glint_left=GLINT[1],
        glint_top=GLINT[2],
        popup_ticks=POPUP_TICKS,
        popup_rise_per_tick=POPUP_RISE,
    )
    coin_variants: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=CRYSTAL_W,
            height=CRYSTAL_H,
            hitbox=HITBOX,
            extra=CoinVariantExtra(points=points, glint=name == "rare"),
        )
        for name, points in POINTS.items()
    }
    return DrifterTuning(
        drifters={
            DrifterType.COIN: DrifterTypeTuning(
                variants=coin_variants,
                default_variant="common",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=type_extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK_HITBOX)},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )


TUNING: DrifterTuning = make_tuning()
NO_SCALING: DrifterTuning = make_tuning(
    switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
)


def coin(
    variant: str | None = None,
    x: float | None = HOME_X,
    y: float | None = HOME_Y,
    *,
    as_level: int | None = None,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
) -> Coin:
    """Spawn a coin through the spawner. y None: the top edge."""
    placement = Placement(DrifterType.COIN, x, y, variant=variant, as_level=as_level)
    spawned: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(spawned, Coin)
    return spawned


def rock(x: float, y: float) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def run_of(
    ship: Ship,
    *drifters: Drifter,
    lives: int = LIVES_START,
    coin_points: int = 0,
    waiting: bool = False,
    invuln_ticks_left: int = 0,
    popups: tuple[PointsPopup, ...] = (),
) -> Run:
    """A moving-scroll run with the drifters numbered from 1, in order, and the ship where given."""
    numbered = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return Run(
        ship=ship,
        scroll=SCROLLING,
        lives=lives,
        coin_points=coin_points,
        waiting=waiting,
        invuln_ticks_left=invuln_ticks_left,
        popups=popups,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def lines_starting(caplog: pytest.LogCaptureFixture, prefix: str) -> list[str]:
    """The lines the run logged that start with `prefix`."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == RUN_LOGGER and r.getMessage().startswith(prefix)
    ]


def run_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line the run logged, in order."""
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def coins_of(run: Run) -> list[Coin]:
    """The coins on the field, in order."""
    return [d for d in run.drifters if isinstance(d, Coin)]


def test_a_coin_is_born_active_with_no_warning_at_its_x_or_a_set_spot() -> None:
    for variant in VARIANTS:
        top = coin(variant, 320.0, None)
        assert top.phase is Phase.ACTIVE, variant
        assert top.ticks_in_phase == 0
        assert (top.x, top.y) == (320.0, -CRYSTAL_H / 2)
        assert top.variant == variant
        assert (top.width, top.height) == (CRYSTAL_W, CRYSTAL_H)
        assert top.warning_ticks == 0
        assert top.speed == 0.0
        assert not top.has_entered
        assert top.uid == 0
        assert top.specialty is None
        assert top.rehit_ticks_left == 0
        assert top.points == POINTS[variant]
        assert top.glint is (variant == "rare")
        assert (top.body_height, top.ring_width, top.ring_height) == (BODY_H, RING_W, RING_H)
        assert (top.glint_size, top.glint_left, top.glint_top) == GLINT
        assert (top.popup_ticks, top.popup_rise_per_tick) == (POPUP_TICKS, POPUP_RISE)
        # Its hitbox is there on the state it is born on: there is no WARNING state to wait out.
        assert top.current_hitbox() == place_hitbox(HITBOX, 320.0, -CRYSTAL_H / 2)
        # Its first update keeps it ACTIVE.
        first = top.update(TickContext(ship=spawn()))
        assert first.phase is Phase.ACTIVE
        assert first.ticks_in_phase == 1
        # A set spot is kept.
        spot = coin(variant, 440.0, 210.0)
        assert (spot.x, spot.y) == (440.0, 210.0)
        assert spot.phase is Phase.ACTIVE
        assert spot.current_hitbox() == place_hitbox(HITBOX, 440.0, 210.0)
    # No variant given: common, the default. An x of 0 is an x.
    assert coin(None).variant == "common"
    assert coin(None, 0.0, None).x == 0.0
    # Added to a run, it is ACTIVE at once, with its uid, and logs no `drifter active` later.
    added = add_drifters(start_run(), [Placement(DrifterType.COIN, x=320.0)], TUNING)
    assert len(added.drifters) == 1
    assert added.drifters[0].phase is Phase.ACTIVE
    assert added.drifters[0].uid == 1
    assert added.drifters[0].current_hitbox() != ()
    # A placement without x is refused, with or without y; the run is left as it was.
    for placement in (Placement(DrifterType.COIN), Placement(DrifterType.COIN, y=100.0)):
        with pytest.raises(ValueError, match="coin placement needs x"):
            spawn_drifter(placement, 1, TUNING)
        with pytest.raises(ValueError, match="coin placement needs x"):
            add_drifters(start_run(), [placement], TUNING)


def test_a_coin_moves_only_by_the_scroll_step_at_every_level_and_with_the_switches_off() -> None:
    steps = [0.0, 0.0, 1.1, 1.1, 3.7, 0.0, 1.1, 1.1]
    ships = [spawn(), resting(0.0, 0.0), resting(500.0, 400.0), resting(318.0, 100.0)]
    for variant in VARIANTS:
        for tuning in (TUNING, NO_SCALING):
            for level in (1, 8):
                where = (variant, tuning is NO_SCALING, level)
                moving = coin(variant, 123.0, 50.0, as_level=level, tuning=tuning)
                assert moving.speed == 0.0, where
                y = 50.0
                for index, step in enumerate(steps * 3):
                    ship = ships[index % len(ships)]
                    moving = moving.update(TickContext(ship=ship, scroll_step_px=step))
                    y += step
                    assert moving.y == pytest.approx(y, abs=1e-9), (where, index)
                    assert moving.x == 123.0
                    assert moving.ticks_in_phase == index + 1
                    assert moving.phase is Phase.ACTIVE
                # A TickContext built with the ship alone is a world standing still.
                still = moving.update(TickContext(ship=spawn()))
                assert still.y == moving.y
                assert still.x == moving.x
    # In a run: still on the states after ticks 1 to 30, first moves on tick 31, then 1.1 a tick.
    paths: list[list[float]] = []
    for tuning, level in ((TUNING, 1), (TUNING, 8), (NO_SCALING, 8)):
        run = add_drifters(
            start_run(), [Placement(DrifterType.COIN, x=100.0, as_level=level)], tuning
        )
        path: list[float] = []
        for tick in range(1, 71):
            run = step_run(replace(run, ship=resting(HOME_X, HOME_Y)), NO_KEY)
            (only,) = coins_of(run)
            assert only.x == 100.0
            path.append(only.y)
            if tick <= SCROLL_START_DELAY:
                assert only.y == -CRYSTAL_H / 2, tick
            else:
                expected = -CRYSTAL_H / 2 + (tick - SCROLL_START_DELAY) * SCROLL_SPEED
                assert only.y == pytest.approx(expected, abs=1e-9), tick
            assert only.speed == 0.0
        paths.append(path)
    assert paths[0] == paths[1] == paths[2]
    assert paths[0][30] == pytest.approx(-CRYSTAL_H / 2 + SCROLL_SPEED, abs=1e-9)


def test_the_spawner_gives_a_coin_no_speed_and_refuses_a_speed_an_invert_and_a_specialty() -> None:
    for variant in VARIANTS:
        for level in (1, 8):
            for tuning in (TUNING, NO_SCALING):
                spawned = coin(variant, 200.0, None, as_level=level, tuning=tuning)
                assert spawned.speed == 0.0, (variant, level)
    # A speed is refused whatever it is, at any level; the run is left as it was.
    for speed in (0.0, 1.0, 4.5):
        placement = Placement(DrifterType.COIN, x=200.0, speed=speed)
        with pytest.raises(ValueError, match="coin has no speed"):
            spawn_drifter(placement, 1, TUNING)
        with pytest.raises(ValueError, match="coin has no speed"):
            spawn_drifter(replace(placement, as_level=8), 1, TUNING)
        run = start_run()
        with pytest.raises(ValueError, match="coin has no speed"):
            add_drifters(run, [placement], TUNING)
        assert run.drifters == ()
    with pytest.raises(ValueError, match="coin has no invert"):
        spawn_drifter(Placement(DrifterType.COIN, x=200.0, invert=True), 1, TUNING)
    with pytest.raises(ValueError, match="coin has no specialty"):
        spawn_drifter(Placement(DrifterType.COIN, x=200.0, specialty_enabled=True), 1, TUNING)
    # A switch left off or unset is no switch.
    for off in (False, None):
        placement = Placement(DrifterType.COIN, x=200.0, specialty_enabled=off)
        assert spawn_drifter(placement, 1, TUNING).specialty is None


def test_a_coins_touch_is_a_collect_it_has_no_graze_zone_and_it_is_never_dimmed() -> None:
    hazard = rock(HOME_X, HOME_Y)
    assert hazard.effect_on_touch() is TouchEffect.HIT
    assert hazard.graze_zone() != ()
    # The base pays nothing and shows nothing; only the coin does.
    assert hazard.collect_points() == 0
    assert hazard.collect_popup() is None
    for variant in VARIANTS:
        for spot in ((HOME_X, HOME_Y), (100.0, 100.0)):
            piece = coin(variant, *spot)
            assert piece.effect_on_touch() is TouchEffect.COLLECT
            assert piece.effect_on_touch() is not TouchEffect.HIT
            assert piece.graze_zone() == ()
            assert piece.brightness() == 1.0
            assert piece.may_hit_ship()
            assert piece.collect_points() == POINTS[variant]
    # On the ship, a coin still has no graze zone.
    overlapping = coin("common", HOME_X, HOME_Y)
    assert hitboxes_overlap(overlapping.current_hitbox(), ship_hitbox(spawn()))
    assert overlapping.graze_zone() == ()
    # A hit elsewhere on the field never starts a cooldown on a coin or dims it.
    far = coin("rare", 100.0, 100.0)
    run = run_of(resting(HOME_X, HOME_Y), far, rock(HOME_X, HOME_Y))
    for after in range(1, 6):
        run = step_run(replace(run, ship=resting(HOME_X, HOME_Y)), NO_KEY)
        (still_there,) = coins_of(run)
        assert still_there.rehit_ticks_left == 0, after
        assert still_there.brightness() == 1.0, after
    assert run.lives == LIVES_START - 1
    assert run.drifters[1].rehit_ticks_left > 0


def test_a_coin_is_judged_on_its_crystals_box_and_its_rings_box_in_and_out() -> None:
    piece = coin("common", 320.0, 200.0)
    assert piece.drawn_parts() == (Box(320.0, 200.0, 12.0, 20.0), Box(320.0, 200.0, 22.0, 8.0))

    def entered(x: float, y: float) -> Coin:
        return replace(coin("common", x, y), has_entered=True)

    # Entering: partly on screen means a box shares area; touching from outside does not count.
    assert not coin("common", 320.0, -10.0).is_partly_on_screen()
    assert coin("common", 320.0, -9.9).is_partly_on_screen()
    assert not coin("common", -11.0, 200.0).is_partly_on_screen()
    assert coin("common", -10.9, 200.0).is_partly_on_screen()  # the ring alone is in
    assert not coin("common", 651.0, 200.0).is_partly_on_screen()
    assert coin("common", 650.9, 200.0).is_partly_on_screen()
    assert not coin("common", 320.0, 490.0 + 14.0).is_partly_on_screen()
    # Leaving: once entered, every box fully past a side or the floor; never at the top.
    assert not entered(320.0, -500.0).is_off_screen()
    assert not entered(320.0, 489.9).is_off_screen()  # the crystal's top edge is at 479.9
    assert entered(320.0, 490.0).is_off_screen()  # crystal top 480, ring top 486
    assert not entered(-6.0, 200.0).is_off_screen()  # crystal right edge 0, ring's at 5
    assert not entered(-10.9, 200.0).is_off_screen()
    assert entered(-11.0, 200.0).is_off_screen()  # ring right edge 0 too
    assert not entered(646.0, 200.0).is_off_screen()  # crystal left edge 640, ring's at 635
    assert not entered(650.9, 200.0).is_off_screen()
    assert entered(651.0, 200.0).is_off_screen()
    # Never before it entered, wherever it is.
    assert not coin("common", 320.0, 900.0).is_off_screen()
    assert not replace(
        coin("common", 320.0, 900.0), has_entered=True, phase=Phase.GONE
    ).is_off_screen()


@pytest.mark.smoke
def test_the_coin_timeline_holds_in_the_run_from_the_top_and_from_a_spot_on_screen(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    parked = resting(HOME_X, HOME_Y)
    # From the top at x 100 (clear of the ship), the world already scrolling when it is added.
    run = add_drifters(
        replace(start_run(), scroll=SCROLLING), [Placement(DrifterType.COIN, x=100.0)], TUNING
    )
    (start,) = coins_of(run)
    assert (start.y, start.has_entered) == (-10.0, False)
    assert not start.is_partly_on_screen()
    for n in range(1, 455):
        run = step_run(replace(run, ship=parked), NO_KEY)
        (piece,) = coins_of(run)
        assert piece.phase is Phase.ACTIVE
        assert piece.y == pytest.approx(-10.0 + n * SCROLL_SPEED, abs=1e-6), n
        assert piece.has_entered, n
        assert piece.current_hitbox() == place_hitbox(HITBOX, 100.0, piece.y)
        assert lines_starting(caplog, "drifter gone") == [], n
    assert piece.y == pytest.approx(489.40, abs=1e-6)
    assert piece.y - CRYSTAL_H / 2 == pytest.approx(479.40, abs=1e-6)  # still on screen
    run = step_run(replace(run, ship=parked), NO_KEY)
    assert run.drifters == ()
    assert run.lives == LIVES_START
    assert run.coin_points == 0
    assert run.popups == ()
    assert lines_starting(caplog, "drifter gone") == [
        "drifter gone id=1 type=coin x=100.00 y=490.50"
    ]
    # Placed at (440, 210): on screen at once, enters on its first update, dropped on n = 255.
    run = add_drifters(
        replace(start_run(), scroll=SCROLLING), [Placement(DrifterType.COIN, 440.0, 210.0)], TUNING
    )
    (spot,) = coins_of(run)
    assert spot.is_partly_on_screen()
    assert not spot.has_entered
    for n in range(1, 255):
        run = step_run(replace(run, ship=parked), NO_KEY)
        (piece,) = coins_of(run)
        assert piece.has_entered, n
        assert piece.y == pytest.approx(210.0 + n * SCROLL_SPEED, abs=1e-6), n
    assert piece.y == pytest.approx(489.40, abs=1e-6)
    run = step_run(replace(run, ship=parked), NO_KEY)
    assert run.drifters == ()
    assert (
        lines_starting(caplog, "drifter gone")[-1]
        == "drifter gone id=1 type=coin x=440.00 y=490.50"
    )


def test_a_coin_the_ship_touches_pays_its_points_is_gone_and_leaves_a_popup_at_its_center() -> None:
    for variant in VARIANTS:
        for already in (0, 7):
            piece = coin(variant, HOME_X, HOME_Y)
            run = run_of(resting(HOME_X, HOME_Y), piece, coin_points=already)
            meters = meters_after_step(run.scroll)
            run = step_run(run, NO_KEY)
            where = (variant, already)
            assert run.coin_points == already + POINTS[variant], where
            assert run.score == meters + already + POINTS[variant], where
            assert run.drifters == (), where
            # The popup is at the coin's center on this tick: where the scroll moved it to.
            moved_y = HOME_Y + SCROLL_SPEED
            (popup,) = run.popups
            assert popup.age_ticks == 0
            assert popup.x == HOME_X
            assert popup.start_y == pytest.approx(moved_y, abs=1e-9), where
            assert popup.y == popup.start_y
            assert popup.points == POINTS[variant]
            assert (popup.lifetime_ticks, popup.rise_per_tick) == (POPUP_TICKS, POPUP_RISE)
            # Nothing else changes: no life, no protection, no wait, no game over.
            assert run.lives == LIVES_START
            assert run.invuln_ticks_left == 0
            assert not run.waiting
            assert not run.game_over
    # Before the scroll starts the coin stands still, and the popup is at its spot.
    run = replace(run_of(resting(HOME_X, HOME_Y), coin("rare")), scroll=Scroll())
    run = step_run(run, NO_KEY)
    assert run.coin_points == POINTS["rare"]
    assert run.popups[0].start_y == HOME_Y
    # Edge contact is no touch: the coin's left edge on the bar's right edge. A hair inside is one.
    bar = ship_hitbox(resting(HOME_X, HOME_Y + GRAVITY))[0]
    assert isinstance(bar, Box)
    edge_x = bar.cx + bar.w / 2 + CRYSTAL_W / 2
    for x, collected in ((edge_x, False), (edge_x - 0.01, True), (edge_x + 0.01, False)):
        near = run_of(resting(HOME_X, HOME_Y), coin("common", x, 220.0 - SCROLL_SPEED))
        near = step_run(near, NO_KEY)
        assert (near.coin_points == POINTS["common"]) is collected, x
        assert len(coins_of(near)) == (0 if collected else 1)
        assert len(near.popups) == (1 if collected else 0)


def test_an_invulnerable_ship_collects() -> None:
    for left in (INVULN_TICKS, 5, 1):
        run = run_of(resting(HOME_X, HOME_Y), coin("rare"), invuln_ticks_left=left, lives=2)
        run = step_run(run, NO_KEY)
        assert run.coin_points == POINTS["rare"], left
        assert run.drifters == ()
        assert len(run.popups) == 1
        assert run.invuln_ticks_left == left - 1
        assert run.lives == 2


def test_a_ship_in_the_respawn_wait_collects_nothing_until_a_press_ends_the_wait() -> None:
    for invuln in (0, INVULN_TICKS):
        standing = resting(HOME_X, HOME_Y)
        run = run_of(standing, coin("common"), waiting=True, invuln_ticks_left=invuln, lives=2)
        assert hitboxes_overlap(run.drifters[0].current_hitbox(), ship_hitbox(standing))
        for waited in range(1, 4):
            run = step_run(run, NO_KEY)
            (piece,) = coins_of(run)
            where = (invuln, waited)
            assert run.coin_points == 0, where
            assert run.popups == ()
            assert run.waiting
            assert run.ship == standing
            assert piece.phase is Phase.ACTIVE
            assert piece.y == pytest.approx(HOME_Y + waited * SCROLL_SPEED, abs=1e-9), where
        # The press ends the wait: the ship moves and collects the coin it overlaps.
        before = run
        run = step_run(run, UP)
        assert not run.waiting
        assert run.ship != standing
        assert run.coin_points == POINTS["common"]
        assert run.drifters == ()
        (popup,) = run.popups
        assert popup.start_y == pytest.approx(before.drifters[0].y + SCROLL_SPEED, abs=1e-9)
        assert popup.age_ticks == 0
    # A coin that has gone by while the ship waits stays lost: nothing is paid later.
    run = run_of(resting(HOME_X, HOME_Y), coin("common", HOME_X, 100.0), waiting=True)
    for _ in range(300):
        run = step_run(run, NO_KEY)
    assert run.coin_points == 0
    assert run.popups == ()


def test_a_coin_and_a_hazard_touched_on_one_tick_the_coin_pays_and_the_hit_costs_a_life(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    run = run_of(resting(HOME_X, HOME_Y), coin("rare"), rock(HOME_X, HOME_Y))
    run = step_run(run, NO_KEY)
    assert run.coin_points == POINTS["rare"]
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over
    assert len(run.popups) == 1
    # The coin is dropped; the hazard stays, with its cooldown started. Only the hit costs a life.
    assert [d.drifter_type for d in run.drifters] == [DrifterType.METEORITE]
    assert run.drifters[0].rehit_ticks_left == REHIT_COOLDOWN
    assert run_lines(caplog) == [
        "drifter touch id=1 type=coin effect=collect",
        "drifter touch id=2 type=meteorite effect=hit",
        f"life lost lives={LIVES_START - 1}",
        f"drifter gone id=1 type=coin x={HOME_X:.2f} y={HOME_Y + SCROLL_SPEED:.2f}",
    ]
    # The same tick with the order of the two drifters swapped pays the same.
    swapped = step_run(run_of(resting(HOME_X, HOME_Y), rock(HOME_X, HOME_Y), coin("rare")), NO_KEY)
    assert swapped.coin_points == POINTS["rare"]
    assert swapped.lives == LIVES_START - 1


def fall_ship() -> Ship:
    """A ship that falls below the floor on its next step, at the fall cap."""
    return Ship(x=HOME_X, y=495.0, vx=0.0, vy=FALL_CAP)


def test_a_coin_touched_on_a_fall_tick_pays_the_fall_costs_its_life_and_no_hit_is_tested(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    fell_to = 495.0 + FALL_CAP
    for protected in (False, True):
        caplog.clear()
        # The coin ends the tick at 488.9: on the ship's bar, which then hangs at 500.5.
        piece = coin("common", HOME_X, 487.8)
        hazard = rock(HOME_X, fell_to)
        run = run_of(
            fall_ship(),
            piece,
            hazard,
            invuln_ticks_left=INVULN_TICKS if protected else 0,
        )
        assert hitboxes_overlap(hazard.current_hitbox(), ship_hitbox(replace(run.ship, y=fell_to)))
        run = step_run(run, NO_KEY)
        assert run.coin_points == POINTS["common"], protected
        assert len(run.popups) == 1
        assert run.popups[0].start_y == pytest.approx(487.8 + SCROLL_SPEED, abs=1e-9)
        assert coins_of(run) == []
        assert run.ship == spawn()
        assert run.drifters[0].rehit_ticks_left == 0, "no hit is tested on a fall tick"
        lines = run_lines(caplog)
        assert lines[0] == "drifter touch id=1 type=coin effect=collect"
        assert not any("effect=hit" in line for line in lines)
        if protected:
            assert run.lives == LIVES_START
            assert not run.waiting
        else:
            assert run.lives == LIVES_START - 1
            assert run.waiting
            assert run.invuln_ticks_left == INVULN_TICKS
            assert lines[1] == f"life lost lives={LIVES_START - 1}"
        assert lines[-1].startswith("drifter gone id=1 type=coin")


def test_a_coin_paid_on_the_last_lifes_tick_is_in_the_frozen_final_score_and_a_new_run_clears_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    scenarios = {
        "fall": run_of(fall_ship(), coin("rare", HOME_X, 487.8), lives=1, coin_points=50),
        "hit": run_of(
            resting(HOME_X, HOME_Y), coin("rare"), rock(HOME_X, HOME_Y), lives=1, coin_points=50
        ),
    }
    for name, run in scenarios.items():
        meters = meters_after_step(run.scroll)
        last = step_run(run, NO_KEY)
        assert last.last_life, name
        assert not last.game_over
        assert last.lives == 0
        assert last.coin_points == 50 + POINTS["rare"], name
        assert last.score == meters + 50 + POINTS["rare"], name
        assert last.final_score == last.score
        assert len(last.popups) == 1
        # The last life: the score and the coin points stay, the popup ages with the world.
        frozen = last
        for k in range(1, 6):
            frozen = step_run(frozen, NO_KEY)
            assert frozen.last_life
            assert frozen.score == last.score
            assert frozen.coin_points == last.coin_points
            assert [p.age_ticks for p in frozen.popups] == [k]
        # An arrow held on the death tick or after it changes nothing either.
        held_last = step_run(run, UP)
        assert held_last.last_life
        assert step_run(held_last, UP).score == held_last.score
        assert step_run(held_last, UP).popups == step_run(held_last, NO_KEY).popups
        # Game over: the score is still the final score, and everything freezes.
        over = last
        for _ in range(LAST_LIFE_DELAY):
            over = step_run(over, NO_KEY)
        assert over.game_over, name
        assert over.score == last.score
        assert over.coin_points == last.coin_points
        assert over.scroll.meters > last.scroll.meters
        again = step_run(over, NO_KEY)
        assert again.score == over.score
        assert again.popups == over.popups
        # A new run: no coin points, no popups.
        fresh = next_run(over)
        assert not fresh.game_over, name
        assert fresh.coin_points == 0, name
        assert fresh.score == 0
        assert fresh.popups == ()
        assert fresh.drifters == ()
    assert lines_starting(caplog, "last life") != []
    assert lines_starting(caplog, "game over") != []


def test_two_coins_touched_on_one_tick_both_pay_with_their_popups_in_drifter_order(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    older = PointsPopup(
        x=50.0,
        start_y=300.0,
        points=50,
        lifetime_ticks=POPUP_TICKS,
        rise_per_tick=POPUP_RISE,
        age_ticks=5,
    )
    first = coin("rare", HOME_X - 8.0, HOME_Y)
    second = coin("common", HOME_X + 8.0, HOME_Y)
    run = run_of(resting(HOME_X, HOME_Y), first, second, popups=(older,))
    run = step_run(run, NO_KEY)
    assert run.coin_points == POINTS["rare"] + POINTS["common"]
    assert run.drifters == ()
    # The popup the earlier tick left comes first (one tick older), then one per coin, in order.
    assert [p.points for p in run.popups] == [50, 100, 50]
    assert run.popups[0].age_ticks == 6
    assert [p.x for p in run.popups[1:]] == [HOME_X - 8.0, HOME_X + 8.0]
    assert [p.age_ticks for p in run.popups[1:]] == [0, 0]
    assert lines_starting(caplog, "drifter touch") == [
        "drifter touch id=1 type=coin effect=collect",
        "drifter touch id=2 type=coin effect=collect",
    ]
    gone = lines_starting(caplog, "drifter gone")
    assert [line.split()[2] for line in gone] == ["id=1", "id=2"]
    # Two coins, one in reach and one not: only the one touched pays.
    apart = run_of(
        resting(HOME_X, HOME_Y), coin("common", HOME_X, HOME_Y), coin("rare", 100.0, 100.0)
    )
    apart = step_run(apart, NO_KEY)
    assert apart.coin_points == POINTS["common"]
    assert [c.variant for c in coins_of(apart)] == ["rare"]


def test_a_popup_rises_for_its_lifetime_ages_through_the_last_life_and_is_gone_in_a_new_run() -> (
    None
):
    run = run_of(resting(HOME_X, HOME_Y), coin("rare", HOME_X, HOME_Y))
    away = resting(100.0, 400.0)
    run = step_run(run, NO_KEY)
    (born,) = run.popups
    center_x, center_y = born.x, born.start_y
    assert (born.age_ticks, born.y) == (0, center_y)
    assert center_x == HOME_X
    # It shows on exactly 60 states: the tick it appears and the 59 after it.
    for k in range(1, POPUP_TICKS):
        run = step_run(replace(run, ship=away), NO_KEY)
        (popup,) = run.popups
        assert popup.age_ticks == k
        assert popup.x == center_x, k
        assert popup.y == pytest.approx(center_y - POPUP_RISE * k, abs=1e-9), k
        assert popup.points == POINTS["rare"]
    assert run.popups[0].y == pytest.approx(center_y - 29.5, abs=1e-9)
    # The scroll never moved it: the scroll was moving the whole time.
    assert run.scroll.scrolled_ticks == 70 + POPUP_TICKS
    run = step_run(replace(run, ship=away), NO_KEY)
    assert run.popups == ()
    # It ages on a wait tick and on a protected tick too.
    old = PointsPopup(x=10.0, start_y=100.0, points=50, lifetime_ticks=3, rise_per_tick=POPUP_RISE)
    waiting = run_of(resting(HOME_X, HOME_Y), waiting=True, popups=(old,), invuln_ticks_left=2)
    for age in (1, 2):
        waiting = step_run(waiting, NO_KEY)
        assert waiting.popups[0].age_ticks == age
    assert step_run(waiting, NO_KEY).popups == ()
    # The last life: the world runs on, so a popup keeps aging and goes when it ends. The tick
    # the last life starts ages it once.
    last_life = run_of(fall_ship(), lives=1, popups=(old,))
    last = step_run(last_life, NO_KEY)
    assert last.last_life
    assert [p.age_ticks for p in last.popups] == [1]
    last = step_run(last, NO_KEY)
    assert [p.age_ticks for p in last.popups] == [2]
    assert step_run(last, NO_KEY).popups == ()
    # A long popup is still on screen at game over, and frozen there like everything else.
    long_popup = PointsPopup(
        x=10.0, start_y=100.0, points=50, lifetime_ticks=500, rise_per_tick=POPUP_RISE
    )
    over = step_run(run_of(fall_ship(), lives=1, popups=(long_popup,)), NO_KEY)
    for _ in range(LAST_LIFE_DELAY):
        over = step_run(over, NO_KEY)
    assert over.game_over
    assert [p.age_ticks for p in over.popups] == [LAST_LIFE_DELAY + 1]
    for held in (NO_KEY, NO_KEY, NO_KEY):
        over = step_run(over, held)
        assert over.game_over
        assert over.popups == (replace(long_popup, age_ticks=LAST_LIFE_DELAY + 1),)
    # A new run starts with none.
    fresh = next_run(over)
    assert not fresh.game_over
    assert fresh.popups == ()
    assert fresh.drifters == ()


def test_a_collected_coin_logs_spawn_touch_and_gone_a_missed_one_spawn_and_gone_and_nothing_else(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    # Collected: added, then taken on the tick the ship touches it.
    run = add_drifters(
        replace(start_run(), ship=resting(HOME_X, HOME_Y), scroll=SCROLLING),
        [Placement(DrifterType.COIN, HOME_X, HOME_Y)],
        TUNING,
    )
    assert run_lines(caplog) == [
        f"drifter spawn id=1 type=coin variant=common x={HOME_X:.2f} y={HOME_Y:.2f} "
        "speed=0.00 level=1"
    ]
    caplog.clear()
    run = step_run(run, NO_KEY)
    assert run.coin_points == POINTS["common"]
    assert run_lines(caplog) == [
        "drifter touch id=1 type=coin effect=collect",
        f"drifter gone id=1 type=coin x={HOME_X:.2f} y={HOME_Y + SCROLL_SPEED:.2f}",
    ]
    # Missed: it falls past the floor and is dropped, with no touch.
    caplog.clear()
    parked = resting(HOME_X, HOME_Y)
    run = add_drifters(
        replace(start_run(), scroll=SCROLLING), [Placement(DrifterType.COIN, x=100.0)], TUNING
    )
    for _ in range(455):
        run = step_run(replace(run, ship=parked), NO_KEY)
    assert run.drifters == ()
    assert run_lines(caplog) == [
        "drifter spawn id=1 type=coin variant=common x=100.00 y=-10.00 speed=0.00 level=1",
        "drifter gone id=1 type=coin x=100.00 y=490.50",
    ]
    # No line, from any logger, names a coin's activation, the score or the points.
    for record in caplog.records:
        message = record.getMessage().lower()
        assert "drifter active" not in message
        assert "score" not in message
        assert "point" not in message
        assert "popup" not in message
