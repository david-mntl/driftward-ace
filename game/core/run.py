"""One run of the game: lives, falls, hits, drifters, the respawn wait, game over, retry.

`Run` holds the ship, the world scroll, the drifters and the lives, and `step_run` advances all
of them one fixed 60 Hz tick. The ship step reports where the ship is (`is_below_floor`), the
drifters report where they are and what a touch does; the run decides what a fall or a hit
costs. `add_drifters` is the only way a drifter enters a run. No frame time, no randomness, no
run mode. Stdlib and `core` only.

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
from core.levels import level_at
from core.scroll import Scroll, start_scroll, step_scroll
from core.ship import Ship, Thrust, is_below_floor, ship_hitbox, spawn, step

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


@dataclass(frozen=True, slots=True)
class Run:
    """One run's state after a tick."""

    ship: Ship
    """The ship (core.ship)."""

    scroll: Scroll
    """The world scroll and distance (core.scroll)."""

    lives: int = LIVES_START
    """Lives left, 0 to LIVES_START. 0 only in game over."""

    invuln_ticks_left: int = 0
    """Ticks of invulnerability still to come. 0 means not invulnerable."""

    waiting: bool = False
    """The ship stands at the respawn point until an arrow press."""

    game_over: bool = False
    """The Game Over box shows and everything is frozen."""

    held: Thrust = field(default_factory=Thrust)
    """The arrow keys held on the last tick, to tell a press from a hold."""

    retry_armed: bool = False
    """Game over only: every arrow has been released since the box appeared."""

    drifters: tuple[Drifter, ...] = ()
    """Drifters on the field, oldest first. Source: systems/run.md, Interface (DRA-29)."""

    next_uid: int = 1
    """The uid the next added drifter gets. Source: systems/run.md, Interface (DRA-29)."""

    @property
    def invulnerable(self) -> bool:
        """True while invulnerability has ticks left. Source: 05-lives-and-damage.md, rule 2.4."""
        return self.invuln_ticks_left > 0

    @property
    def ship_visible(self) -> bool:
        """True when the ship is drawn this frame.

        Always True when not invulnerable. While invulnerable it blinks, starting visible,
        one swap every BLINK_SWAP_TICKS. Source: 05-lives-and-damage.md, invuln_blink (locked);
        scope report DRA-23, blink.
        """
        if not self.invulnerable:
            return True
        elapsed: int = INVULN_TICKS - self.invuln_ticks_left
        return (elapsed // BLINK_SWAP_TICKS) % 2 == 0

    @property
    def level(self) -> int:
        """The level of the run, 1 to 8, from the meters. Source: 08-difficulty.md, rule 1."""
        return level_at(self.scroll.meters)


def start_run() -> Run:
    """Return a new run: the ship at spawn, the scroll at tick 0, every other field default.

    Source: 02-game-flow.md, rule 3; systems/run.md, Interface.
    """
    return Run(ship=spawn(), scroll=start_scroll())


def add_drifters(run: Run, placements: Sequence[Placement], tuning: DrifterTuning) -> Run:
    """Spawn each placement in order and append it to the run, each with the next uid.

    Returns `run` unchanged at game over or with no placements. New drifters are in WARNING and
    first update on the next `step_run`. Errors from `spawn_drifter` rise, and the run is not
    changed. Source: systems/run.md, Rules, add_drifters.
    """
    if run.game_over or not placements:
        return run
    added: list[Drifter] = []
    for offset, placement in enumerate(placements):
        spawned: Drifter = spawn_drifter(placement, run.level, tuning)
        added.append(replace(spawned, uid=run.next_uid + offset))
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


def step_run(run: Run, thrust: Thrust) -> Run:
    """Advance the run one fixed 60 Hz tick and return the new run. Never mutates the input.

    Pure apart from event logging on `core.run`. Same run and thrust in, same run out.
    Source: systems/run.md, Rules; 15-tech-constraints.md, rule 2.
    """
    if run.game_over:
        return _step_game_over(run, thrust)
    return _step_playing(run, thrust)


def _arrows(thrust: Thrust) -> tuple[bool, bool, bool, bool]:
    """Return the four arrow states (up, down, left, right)."""
    return thrust.up, thrust.down, thrust.left, thrust.right


def _any_arrow(thrust: Thrust) -> bool:
    """True when at least one arrow is held."""
    return any(_arrows(thrust))


def _is_press(thrust: Thrust, held: Thrust) -> bool:
    """True when an arrow is held now that was not held on the last tick.

    Source: 05-lives-and-damage.md, rule 2.5 ("until the first arrow key press").
    """
    pairs = zip(_arrows(thrust), _arrows(held), strict=True)
    return any(now and not before for now, before in pairs)


def _step_playing(run: Run, thrust: Thrust) -> Run:
    """A playing tick: press, timer, drifters, wait, ship, scroll, fall or hit, cooldowns, drops.

    A hit is tested only when the ship did not fall. Source: systems/run.md, Rules, a playing
    tick, steps 1 to 10.
    """
    press: bool = _is_press(thrust, run.held)
    protected: bool = run.invulnerable
    left: int = max(run.invuln_ticks_left - 1, 0)
    drifters: tuple[Drifter, ...] = _update_drifters(run)
    ended_wait: bool = run.waiting and press
    if ended_wait:
        log.debug("respawn wait end")
    stands: bool = run.waiting and not press
    ship: Ship = run.ship if stands else step(run.ship, thrust)
    scroll: Scroll = step_scroll(run.scroll)
    if run.invuln_ticks_left == 1:
        log.debug("invulnerable end")
    stepped = replace(
        run,
        ship=ship,
        scroll=scroll,
        drifters=drifters,
        invuln_ticks_left=left,
        waiting=stands,
        held=thrust,
    )
    if is_below_floor(ship):
        outcome: Run = _apply_fall(stepped, protected, thrust)
    else:
        outcome = _apply_hit(stepped, protected, thrust)
    return _drop_drifters(_cool_down(outcome, stepped.drifters))


def _update_drifters(run: Run) -> tuple[Drifter, ...]:
    """Update every drifter once with the ship as it was at the start of the tick (step 3).

    Each updated drifter is then marked entered when it is on screen. Logs each drifter that
    turns from WARNING to ACTIVE.
    """
    ctx = TickContext(ship=run.ship)
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


def _apply_fall(stepped: Run, protected: bool, thrust: Thrust) -> Run:
    """Apply a fall to the run after its ship and scroll stepped.

    A protected fall respawns the ship with no wait and no life lost. An unprotected fall
    costs a life and respawns it waiting with fresh invulnerability, or ends the run on the
    last life.
    Source: 05-lives-and-damage.md, rules 2.1 to 2.6 and 5; systems/run.md, Rules, step 6.
    """
    fell = stepped.ship
    if protected:
        _log_respawn(fell, waits=False)
        return replace(stepped, ship=spawn(), waiting=False)
    lives: int = stepped.lives - 1
    log.debug("life lost lives=%d", lives)
    if lives > 0:
        _log_respawn(fell, waits=True)
        return replace(
            stepped, lives=lives, ship=spawn(), waiting=True, invuln_ticks_left=INVULN_TICKS
        )
    return _end_run(stepped, thrust)


def _end_run(stepped: Run, thrust: Thrust) -> Run:
    """Return the run in game over with 0 lives. The ship stays where it is.

    Source: 05-lives-and-damage.md, rule 5; systems/run.md, Rules, steps 6.3 and 7.5.
    """
    log.info("game over meters=%d", stepped.scroll.meters)
    return replace(
        stepped,
        lives=0,
        game_over=True,
        invuln_ticks_left=0,
        waiting=False,
        retry_armed=not _any_arrow(thrust),
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


def _apply_hit(stepped: Run, protected: bool, thrust: Thrust) -> Run:
    """Apply a hit to the run after its ship, scroll and drifters stepped (step 7).

    Nothing happens with no touching drifter, or while protected. Otherwise one life is lost
    whatever the number of touching drifters, each starts its re-hit cooldown, and the run is
    invulnerable again or over. The ship and the wait stay as they were.
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
    return _end_run(hit, thrust)


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


def _log_respawn(fell_from: Ship, *, waits: bool) -> None:
    """Log a respawn with the position the ship fell from and whether it waits."""
    log.debug("respawn from x=%.2f y=%.2f wait=%s", fell_from.x, fell_from.y, waits)


def _step_game_over(run: Run, thrust: Thrust) -> Run:
    """A game-over tick: everything frozen, until every arrow is released and one is pressed.

    The retry press does not thrust: the new run is exactly `start_run()`.
    Source: 02-game-flow.md, rules 5 and 6; 91-decision-log.md, rows 30 and 31.
    """
    if not _any_arrow(thrust):
        return replace(run, retry_armed=True, held=thrust)
    if run.retry_armed:
        log.info("new run")
        return replace(start_run(), held=thrust)
    return replace(run, held=thrust)
