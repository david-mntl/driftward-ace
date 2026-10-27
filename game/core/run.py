"""One run of the game: lives, falls, hits, drifters, the respawn wait, last life, game over.

`Run` holds the ship, the world scroll, the drifters and the lives, and `step_run` advances all
of them one fixed 60 Hz tick. The ship step reports where the ship is (`is_below_floor`), the
drifters report where they are and what a touch does; the run decides what a fall or a hit
costs. On the last life the ship bursts and the world runs on until game over. `add_drifters`
is the only way a drifter enters a run, `next_run` the only way a run follows another. No frame
time, no randomness, no run mode. Stdlib and `core` only.

Source: docs/contracts/systems/run.md, Interface, Rules and Logging.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Final

from core.collision import Hitbox, hitboxes_overlap
from core.drifters.base import Drifter, Phase, TickContext, TouchEffect
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.graze import (
    DEFAULT_GRAZE_RULES,
    GrazeCheck,
    GrazeRing,
    GrazeRules,
    check_grazes,
    graze_popup,
    graze_ring,
    step_graze_rings,
)
from core.last_life import DEFAULT_LAST_LIFE_RULES, Burst, LastLifeRules, start_burst, step_burst
from core.levels import FIRST_LEVEL
from core.popup import PointsPopup, step_popups
from core.scroll import Scroll, scroll_step_px, start_scroll, step_scroll
from core.ship import (
    NO_GROUND,
    GravityWell,
    Ground,
    Ship,
    Thrust,
    block_ship,
    is_below_floor,
    ship_hitbox,
    spawn,
    spawn_clear,
    step,
)
from core.waves import WaveRun, next_run_waves, step_waves
from core.world import SCREEN_H

log = logging.getLogger(__name__)

LIVES_START: Final[int] = 3
"""Lives at the start of a run. Source: 05-lives-and-damage.md, lives_start (locked)."""

INVULN_TICKS: Final[int] = 30
"""Ticks of invulnerability after a respawn. Source: 05-lives-and-damage.md, invuln_ticks
(locked)."""

BLINK_SWAP_TICKS: Final[int] = 6
"""Ticks between one visible/hidden swap of the blink. Source: scope report DRA-23, blink:
one swap every 0.1 s, approved in chat, not in the GDD (05-lives-and-damage.md, blink_period
is TBD, LD-04). 0.1 s x 60 ticks/s (15-tech-constraints.md, tick_rate, locked) = 6 ticks."""

RESPAWN_WAIT_LIMIT: Final[int | None] = None
"""Longest respawn wait, ticks. None means no limit. Nothing reads it in DRA-23.
Source: 05-lives-and-damage.md, rule 2.5: the wait has no time limit."""

POINTS_PER_METER: Final[int] = 1
"""Points for each whole meter flown. Source: 06-scoring.md, points_per_meter (locked)."""


@dataclass(frozen=True, slots=True)
class Run:
    """One run's state after a tick."""

    ship: Ship
    """The ship (core.ship)."""

    scroll: Scroll
    """The world scroll and distance (core.scroll)."""

    lives: int = LIVES_START
    """Lives left, 0 to LIVES_START. 0 only from the last life on (DRA-125)."""

    invuln_ticks_left: int = 0
    """Ticks of invulnerability still to come. 0 means not invulnerable."""

    waiting: bool = False
    """The ship stands at the respawn point until an arrow press."""

    game_over: bool = False
    """The last-life delay has ended: the run is over and everything is frozen (DRA-125)."""

    held: Thrust = field(default_factory=Thrust)
    """The arrow keys held on the last tick, to tell a press from a hold."""

    drifters: tuple[Drifter, ...] = ()
    """Drifters on the field, oldest first. Source: systems/run.md, Interface (DRA-29)."""

    next_uid: int = 1
    """The uid the next added drifter gets. Source: systems/run.md, Interface (DRA-29)."""

    coin_points: int = 0
    """Points from coins this run, >= 0. Step 5a adds to it. Source: systems/run.md, Score."""

    popups: tuple[PointsPopup, ...] = ()
    """Points popups on screen, oldest first. Source: systems/run.md, Interface (DRA-62)."""

    waves: WaveRun | None = None
    """The run's waves (core.waves). None: no waves play. Source: systems/run.md, Interface
    (DRA-76)."""

    grazes: int = 0
    """Grazes paid this run, at least 0. Only step 5b adds to it. Source: systems/run.md,
    Interface (DRA-117)."""

    graze_rings: tuple[GrazeRing, ...] = ()
    """Graze rings on screen, oldest first. Source: systems/run.md, Interface (DRA-117)."""

    graze_rules: GrazeRules = DEFAULT_GRAZE_RULES
    """The graze values, from the app. A new run keeps them. Source: systems/run.md, Interface
    (DRA-117)."""

    burst: Burst | None = None
    """The last life's burst, from the tick lives reach 0. None before. Source: systems/run.md,
    Interface (DRA-125)."""

    final_score: int | None = None
    """The score on the tick lives reach 0. None before. Source: systems/run.md, Interface
    (DRA-125)."""

    last_life_rules: LastLifeRules = DEFAULT_LAST_LIFE_RULES
    """The last-life values, from the app. A new run keeps them. Source: systems/run.md,
    Interface (DRA-125)."""

    final_level: int | None = None
    """The level on the tick lives reach 0, going into its waves step. None before. Source:
    systems/run.md, Interface (DRA-126)."""

    @property
    def last_life(self) -> bool:
        """True from the tick lives reach 0 until game over: the world runs on without the ship.

        Source: systems/run.md, Interface (DRA-125).
        """
        return self.burst is not None and not self.game_over

    @property
    def score(self) -> int:
        """The run's score in whole points: meters flown times POINTS_PER_METER, plus coin points,
        plus the grazes times the graze points.

        Once the last life is lost it is `final_score`, frozen while the scroll runs on. Source:
        systems/run.md, Rules, Score; 06-scoring.md, Summary and rules 1 and 2; 02-game-flow.md,
        rule 8.
        """
        if self.final_score is not None:
            return self.final_score
        graze_points: int = self.grazes * self.graze_rules.points
        return self.scroll.meters * POINTS_PER_METER + self.coin_points + graze_points

    @property
    def invulnerable(self) -> bool:
        """True while invulnerability has ticks left. Source: 05-lives-and-damage.md, rule 2.4."""
        return self.invuln_ticks_left > 0

    @property
    def ship_visible(self) -> bool:
        """True when the ship is drawn this frame.

        Always False once the ship has burst (the last life, never rebuilt). Otherwise True when
        not invulnerable. While invulnerable it blinks, starting visible, one swap every
        BLINK_SWAP_TICKS. Source: 05-lives-and-damage.md, invuln_blink (locked), rule 5; scope
        report DRA-23, blink.
        """
        if self.burst is not None:
            return False
        if not self.invulnerable:
            return True
        elapsed: int = INVULN_TICKS - self.invuln_ticks_left
        return (elapsed // BLINK_SWAP_TICKS) % 2 == 0

    @property
    def level(self) -> int:
        """The level of the run, 1 to 8: its waves' level, or FIRST_LEVEL with no waves.

        Source: 08-difficulty.md, rule 1; systems/run.md, Interface (DRA-76).
        """
        if self.waves is None:
            return FIRST_LEVEL
        return self.waves.level

    @property
    def level_reached(self) -> int:
        """The level the run reached, FIRST_LEVEL to LEVEL_COUNT: `final_level` once the last life
        is lost, else `level`.

        Source: systems/run.md, Interface (DRA-126); 11-save-data.md, Edge cases.
        """
        if self.final_level is not None:
            return self.final_level
        return self.level

    @property
    def wave_spawns_due(self) -> tuple[Placement, ...]:
        """The placements that came due on the last tick, or () with no waves.

        The app hands them to `add_drifters`. Source: systems/run.md, Interface (DRA-76).
        """
        if self.waves is None:
            return ()
        return self.waves.spawns_due


def start_run(
    waves: WaveRun | None = None,
    graze_rules: GrazeRules = DEFAULT_GRAZE_RULES,
    last_life_rules: LastLifeRules = DEFAULT_LAST_LIFE_RULES,
) -> Run:
    """Return a new run: the ship at spawn, the scroll at tick 0, every other field default.

    No drifters, next_uid 1, coin_points 0, grazes 0 (so the score is 0), no popups, no graze
    rings, no burst and no final score. `waves` is the run's wave state from
    `core.waves.start_waves`, or None for a run with no waves. `graze_rules` and
    `last_life_rules` are kept in the run for its whole life and by `next_run`.

    Source: 02-game-flow.md, rule 3; systems/run.md, Interface.
    """
    return Run(
        ship=spawn(),
        scroll=start_scroll(),
        waves=waves,
        graze_rules=graze_rules,
        last_life_rules=last_life_rules,
    )


def next_run(run: Run) -> Run:
    """Return a fresh run after `run`: Wave 0 again at Level 1, the graze and last-life values kept.

    Logs INFO `new run` first, then builds `start_run` with the next waves (a new seed for the
    picks) or None when `run` has none. Any run state may be given. Source: systems/run.md, Rules,
    next_run; 02-game-flow.md, rules 5 and 11.
    """
    log.info("new run")
    return start_run(_next_waves(run.waves), run.graze_rules, run.last_life_rules)


def hold_arrows(run: Run, thrust: Thrust) -> Run:
    """Return the run with `held = thrust` and nothing else changed. Pure, no logging.

    The game flow calls it on paused ticks, so an arrow pressed during a pause is not a press
    when play resumes. Source: systems/run.md, Rules, hold_arrows.
    """
    return replace(run, held=thrust)


def add_drifters(run: Run, placements: Sequence[Placement], tuning: DrifterTuning) -> Run:
    """Spawn each placement in order and append it to the run, each with the next uid.

    Returns `run` unchanged at game over or with no placements; the last life still takes them.
    New drifters are in WARNING and
    first update on the next `step_run`. Errors from `spawn_drifter` rise, and the run is not
    changed. Each one settles its entry warning from the ship as it is now. Source: systems/run.md,
    Rules, add_drifters.
    """
    if run.game_over or not placements:
        return run
    added: list[Drifter] = []
    for offset, placement in enumerate(placements):
        spawned: Drifter = spawn_drifter(placement, run.level, tuning)
        numbered: Drifter = replace(spawned, uid=run.next_uid + offset)
        added.append(numbered.settle_warning(TickContext(ship=run.ship)))
    for drifter, placement in zip(added, placements, strict=True):
        level: int = run.level if placement.as_level is None else placement.as_level
        log.debug(
            "drifter spawn id=%d type=%s variant=%s x=%.2f y=%.2f speed=%.2f level=%d",
            drifter.uid,
            drifter.drifter_type.value,
            drifter.variant,
            drifter.x,
            drifter.y,
            drifter.speed,
            level,
        )
    return replace(run, drifters=run.drifters + tuple(added), next_uid=run.next_uid + len(added))


def island_ground(drifters: Sequence[Drifter], scroll_step_px: float) -> Ground:
    """Return the ground the ship can't enter: the shapes of every ACTIVE BLOCK drifter, joined.

    The ground moves down by `scroll_step_px` (px/tick), the step the islands just moved by.
    NO_GROUND when no drifter blocks. Pure, no logging. Source: systems/run.md, Interface.
    """
    shapes: Hitbox = tuple(
        shape
        for drifter in drifters
        if drifter.phase is Phase.ACTIVE and drifter.effect_on_touch() is TouchEffect.BLOCK
        for shape in drifter.current_hitbox()
    )
    if not shapes:
        return NO_GROUND
    return Ground(hitbox=shapes, velocity_x=0.0, velocity_y=scroll_step_px)


def gravity_wells(drifters: Sequence[Drifter]) -> tuple[GravityWell, ...]:
    """Return the gravity field of every drifter that has one now, in drifter order.

    A field comes from `Drifter.gravity_well()`, which is None in WARNING and for every drifter
    without one. () when there is none. Pure, no logging. Source: systems/run.md, Interface.
    """
    return tuple(well for drifter in drifters if (well := drifter.gravity_well()) is not None)


def step_run(run: Run, thrust: Thrust) -> Run:
    """Advance the run one fixed 60 Hz tick and return the new run. Never mutates the input.

    Pure apart from event logging on `core.run`. Same run and thrust in, same run out.
    Source: systems/run.md, Rules; 15-tech-constraints.md, rule 2.
    """
    if run.game_over:
        return hold_arrows(run, thrust)
    if run.burst is not None:
        return _step_last_life(run, run.burst, thrust)
    return _step_playing(run, thrust)


def _arrows(thrust: Thrust) -> tuple[bool, bool, bool, bool]:
    """Return the four arrow states (up, down, left, right)."""
    return thrust.up, thrust.down, thrust.left, thrust.right


def _is_press(thrust: Thrust, held: Thrust) -> bool:
    """True when an arrow is held now that was not held on the last tick.

    Source: 05-lives-and-damage.md, rule 2.5 ("until the first arrow key press").
    """
    pairs = zip(_arrows(thrust), _arrows(held), strict=True)
    return any(now and not before for now, before in pairs)


def _step_playing(run: Run, thrust: Thrust) -> Run:
    """A playing tick: press, timer, drifters, popups and rings, ground and wells, ship, scroll,
    collect, graze, fall or hit, cooldowns, drops, waves.

    The tick that loses the last life runs in full. A hit is tested only when the ship did not
    fall. The level is read once, going into the tick.
    Source: systems/run.md, Rules, a playing tick, steps 1 to 10 with 3a, 5a, 5b and 9a.
    """
    press: bool = _is_press(thrust, run.held)
    protected: bool = run.invulnerable
    left: int = max(run.invuln_ticks_left - 1, 0)
    scroll_px: float = scroll_step_px(run.scroll, run.level)
    drifters: tuple[Drifter, ...] = _update_drifters(run, scroll_px)
    ended_wait: bool = run.waiting and press
    if ended_wait:
        log.debug("respawn wait end")
    stands: bool = run.waiting and not press
    ground: Ground = island_ground(drifters, scroll_px)
    wells: tuple[GravityWell, ...] = gravity_wells(drifters)
    ship: Ship = block_ship(run.ship, ground) if stands else step(run.ship, thrust, ground, wells)
    scroll: Scroll = step_scroll(run.scroll, run.level)
    if run.invuln_ticks_left == 1:
        log.debug("invulnerable end")
    stepped = replace(
        run,
        ship=ship,
        scroll=scroll,
        drifters=drifters,
        popups=step_popups(run.popups),
        graze_rings=step_graze_rings(run.graze_rings),
        invuln_ticks_left=left,
        waiting=stands,
        held=thrust,
    )
    collected: Run = stepped if stands else _apply_collect(stepped)
    grazed: Run = _apply_graze(collected, may_pay=not protected and not stands)
    if is_below_floor(ship):
        outcome: Run = _apply_fall(grazed, protected, ground)
    else:
        outcome = _apply_hit(grazed, protected)
    return _step_run_waves(_drop_drifters(_cool_down(outcome, grazed.drifters)))


def _update_drifters(run: Run, scroll_px: float) -> tuple[Drifter, ...]:
    """Update every drifter once with the ship as it was at the start of the tick (step 3).

    `scroll_px` is how far the world scrolls this tick, px. Each updated drifter is then marked
    entered when it is on screen. Logs each drifter that turns from WARNING to ACTIVE.
    """
    ctx = TickContext(ship=run.ship, scroll_step_px=scroll_px)
    updated: tuple[Drifter, ...] = tuple(
        drifter.update(ctx).mark_entered() for drifter in run.drifters
    )
    for before, after in zip(run.drifters, updated, strict=True):
        if before.phase is Phase.WARNING and after.phase is Phase.ACTIVE:
            log.debug(
                "drifter active id=%d type=%s x=%.2f y=%.2f",
                after.uid,
                after.drifter_type.value,
                after.x,
                after.y,
            )
    return updated


def _collects(drifter: Drifter, ship_box: Hitbox) -> bool:
    """True when `drifter` is ACTIVE, a COLLECT on touch, and overlaps `ship_box`."""
    return (
        drifter.phase is Phase.ACTIVE
        and drifter.effect_on_touch() is TouchEffect.COLLECT
        and hitboxes_overlap(drifter.current_hitbox(), ship_box)
    )


def _apply_collect(stepped: Run) -> Run:
    """Collect every pickup the ship overlaps after its step (step 5a).

    Each one adds its points to the coin points, adds its popup (when it has one) after the
    popups step 3a kept, and turns GONE so step 9 drops it. Protection plays no part. Nothing else
    changes. Source: systems/run.md, Rules, step 5a.
    """
    ship_box: Hitbox = ship_hitbox(stepped.ship)
    collecting: tuple[bool, ...] = tuple(
        _collects(drifter, ship_box) for drifter in stepped.drifters
    )
    if not any(collecting):
        return stepped
    drifters: list[Drifter] = []
    popups: list[PointsPopup] = []
    points: int = 0
    for drifter, collected in zip(stepped.drifters, collecting, strict=True):
        if not collected:
            drifters.append(drifter)
            continue
        log.debug(
            "drifter touch id=%d type=%s effect=%s",
            drifter.uid,
            drifter.drifter_type.value,
            drifter.effect_on_touch().value,
        )
        points += drifter.collect_points()
        popup: PointsPopup | None = drifter.collect_popup()
        if popup is not None:
            popups.append(popup)
        drifters.append(replace(drifter, phase=Phase.GONE))
    return replace(
        stepped,
        drifters=tuple(drifters),
        coin_points=stepped.coin_points + points,
        popups=stepped.popups + tuple(popups),
    )


def _apply_graze(stepped: Run, *, may_pay: bool) -> Run:
    """Follow the ship through every hazard's graze zone and pay the exits (step 5b).

    `may_pay` is False when the ship was protected going into the tick or stands in the respawn
    wait. Each paid graze adds one to `grazes`, a graze popup after the popups steps 3a and 5a
    left, a graze ring after the rings step 3a kept, and one log line. Nothing else changes.
    Source: systems/run.md, Rules, step 5b.
    """
    check: GrazeCheck = check_grazes(stepped.drifters, ship_hitbox(stepped.ship), may_pay)
    for drifter in check.paid:
        log.debug("drifter graze id=%d type=%s", drifter.uid, drifter.drifter_type.value)
    paid: int = len(check.paid)
    rules: GrazeRules = stepped.graze_rules
    return replace(
        stepped,
        drifters=check.drifters,
        grazes=stepped.grazes + paid,
        popups=stepped.popups + (graze_popup(rules, stepped.ship),) * paid,
        graze_rings=stepped.graze_rings + (graze_ring(rules),) * paid,
    )


def _apply_fall(stepped: Run, protected: bool, ground: Ground) -> Run:
    """Apply a fall to the run after its ship and scroll stepped.

    A protected fall respawns the ship with no wait and no life lost. An unprotected fall
    costs a life and respawns it waiting with fresh invulnerability, or starts the last life with
    the burst on the bottom edge, where the ship left the screen. The respawn spot is the one
    nearest the respawn point that `ground` doesn't hold.
    Source: 05-lives-and-damage.md, rules 2.1 to 2.7 and 5; systems/run.md, Rules, step 6.
    """
    fell = stepped.ship
    if protected:
        _log_respawn(fell, waits=False)
        return replace(stepped, ship=_respawn_ship(ground), waiting=False)
    lives: int = stepped.lives - 1
    log.debug("life lost lives=%d", lives)
    if lives > 0:
        _log_respawn(fell, waits=True)
        return replace(
            stepped,
            lives=lives,
            ship=_respawn_ship(ground),
            waiting=True,
            invuln_ticks_left=INVULN_TICKS,
        )
    return _start_last_life(stepped, fell.x, SCREEN_H)


def _start_last_life(stepped: Run, burst_x: float, burst_y: float) -> Run:
    """Return the run on the tick lives reach 0: 0 lives, the score kept, the burst started.

    `final_score` is the score so far this tick, the coin and graze of this tick included.
    `final_level` is the level the tick was flown at: the waves step that may raise it comes
    later in the tick. The ship stays where it is, the run is not over, and the tick goes on with
    steps 8 to 10.
    Source: 05-lives-and-damage.md, rule 5; systems/run.md, Rules, The last life.
    """
    final: int = stepped.score
    log.info("last life score=%d", final)
    return replace(
        stepped,
        lives=0,
        invuln_ticks_left=0,
        waiting=False,
        final_score=final,
        final_level=stepped.level,
        burst=start_burst(stepped.last_life_rules, burst_x, burst_y),
    )


def _touches_ship(drifter: Drifter, ship_box: Hitbox) -> bool:
    """True when `drifter` is ACTIVE, a HIT on touch, able to hit now, and overlaps `ship_box`.

    The drifter decides whether it can hit again (`may_hit_ship`), not the run.
    """
    return (
        drifter.phase is Phase.ACTIVE
        and drifter.effect_on_touch() is TouchEffect.HIT
        and drifter.may_hit_ship()
        and hitboxes_overlap(drifter.current_hitbox(), ship_box)
    )


def _apply_hit(stepped: Run, protected: bool) -> Run:
    """Apply a hit to the run after its ship, scroll and drifters stepped (step 7).

    Nothing happens with no touching drifter, or while protected. Otherwise one life is lost
    whatever the number of touching drifters, each starts its re-hit cooldown, and the run is
    invulnerable again or on its last life, with the burst at the ship's center. The ship and the
    wait stay as they were.
    Source: 05-lives-and-damage.md, rules 1 and 4; systems/run.md, Rules, step 7.
    """
    ship_box: Hitbox = ship_hitbox(stepped.ship)
    touching: tuple[bool, ...] = tuple(
        _touches_ship(drifter, ship_box) for drifter in stepped.drifters
    )
    if protected or not any(touching):
        return stepped
    drifters: list[Drifter] = []
    for drifter, touched in zip(stepped.drifters, touching, strict=True):
        if not touched:
            drifters.append(drifter)
            continue
        log.debug(
            "drifter touch id=%d type=%s effect=%s",
            drifter.uid,
            drifter.drifter_type.value,
            drifter.effect_on_touch().value,
        )
        drifters.append(replace(drifter, rehit_ticks_left=drifter.rehit_cooldown_ticks))
    lives: int = stepped.lives - 1
    log.debug("life lost lives=%d", lives)
    hit = replace(stepped, drifters=tuple(drifters), lives=lives)
    if lives > 0:
        return replace(hit, invuln_ticks_left=INVULN_TICKS)
    return _start_last_life(hit, hit.ship.x, hit.ship.y)


def _cool_down(run: Run, before_hit: tuple[Drifter, ...]) -> Run:
    """Count every running re-hit cooldown down by 1, except one that started this tick (step 8).

    `before_hit` is the drifters as they went into step 7, in the same order as `run.drifters`.
    A cooldown that started this tick was 0 going in, so only drifters that were above 0 count
    down. Source: systems/run.md, Rules, step 8.
    """
    if not any(was.rehit_ticks_left > 0 for was in before_hit):
        return run
    drifters: tuple[Drifter, ...] = tuple(
        replace(now, rehit_ticks_left=now.rehit_ticks_left - 1) if was.rehit_ticks_left > 0 else now
        for was, now in zip(before_hit, run.drifters, strict=True)
    )
    return replace(run, drifters=drifters)


def _drop_drifters(run: Run) -> Run:
    """Remove every GONE or off-screen drifter, keeping the order of the rest (step 9).

    Logs each dropped drifter with its last position.
    """
    kept: list[Drifter] = []
    for drifter in run.drifters:
        if drifter.phase is not Phase.GONE and not drifter.is_off_screen():
            kept.append(drifter)
            continue
        log.debug(
            "drifter gone id=%d type=%s x=%.2f y=%.2f",
            drifter.uid,
            drifter.drifter_type.value,
            drifter.x,
            drifter.y,
        )
    if len(kept) == len(run.drifters):
        return run
    return replace(run, drifters=tuple(kept))


def _step_run_waves(run: Run) -> Run:
    """Step the run's waves with this tick's scroll distance (step 9a). No waves: unchanged.

    Source: systems/run.md, Rules, step 9a.
    """
    if run.waves is None:
        return run
    return replace(run, waves=step_waves(run.waves, run.scroll.distance_px))


def _respawn_ship(ground: Ground) -> Ship:
    """Return the respawn ship clear of `ground`. Logs when the spot moved off the respawn point."""
    ship: Ship = spawn_clear(ground)
    if ship.y != spawn().y:
        log.debug("respawn clear of island y=%.2f", ship.y)
    return ship


def _log_respawn(fell_from: Ship, *, waits: bool) -> None:
    """Log a respawn with the position the ship fell from and whether it waits."""
    log.debug("respawn from x=%.2f y=%.2f wait=%s", fell_from.x, fell_from.y, waits)


def _step_last_life(run: Run, burst: Burst, thrust: Thrust) -> Run:
    """A last-life tick: the world runs on without the ship, the burst a tick older.

    Drifters, popups, graze rings and scroll step as on a playing tick; there is no ship step, no
    collect, graze, fall or hit, so the score stays frozen. Cooldowns, drops and waves follow,
    and when the burst is finished the run is over. Source: systems/run.md, Rules, A last-life
    tick.
    """
    scroll_px: float = scroll_step_px(run.scroll, run.level)
    drifters: tuple[Drifter, ...] = _update_drifters(run, scroll_px)
    stepped = replace(
        run,
        scroll=step_scroll(run.scroll, run.level),
        drifters=drifters,
        popups=step_popups(run.popups),
        graze_rings=step_graze_rings(run.graze_rings),
        burst=step_burst(burst),
        held=thrust,
    )
    return _end_last_life(_step_run_waves(_drop_drifters(_cool_down(stepped, drifters))))


def _end_last_life(run: Run) -> Run:
    """Return the run in game over once its burst is finished, else unchanged. Logs INFO.

    Source: systems/run.md, Rules, A last-life tick, step 7.
    """
    if run.burst is None or not run.burst.finished:
        return run
    log.info("game over score=%d", run.score)
    return replace(run, game_over=True)


def _next_waves(waves: WaveRun | None) -> WaveRun | None:
    """Return the waves of the next run: restarted from `waves`, or None when the run has none."""
    if waves is None:
        return None
    return next_run_waves(waves)
