"""One run of the game: lives, falls, hits, objects, the respawn wait, game over, retry.

`Run` holds the ship, the world scroll, the objects and the lives, and `step_run` advances all
of them one fixed 60 Hz tick. The ship step reports where the ship is (`is_below_floor`), the
objects report where they are and what a touch does; the run decides what a fall or a hit
costs. `add_objects` is the only way an object enters a run. No frame time, no randomness, no
run mode. Stdlib and `core` only.

Source: docs/contracts/systems/run.md, Interface, Rules and Logging.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Final

from core.collision import Hitbox, hitboxes_overlap
from core.levels import level_at
from core.objects.base import GameObject, Phase, TickContext, TouchEffect
from core.objects.spawner import Placement, spawn_object
from core.objects.tuning import ObjectTuning
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

    objects: tuple[GameObject, ...] = ()
    """Objects on the field, oldest first. Source: systems/run.md, Interface (DRA-29)."""

    next_uid: int = 1
    """The uid the next added object gets. Source: systems/run.md, Interface (DRA-29)."""

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


def add_objects(run: Run, placements: Sequence[Placement], tuning: ObjectTuning) -> Run:
    """Spawn each placement in order and append it to the run, each with the next uid.

    Returns `run` unchanged at game over or with no placements. New objects are in WARNING and
    first update on the next `step_run`. Errors from `spawn_object` rise, and the run is not
    changed. Source: systems/run.md, Rules, add_objects.
    """
    if run.game_over or not placements:
        return run
    added: list[GameObject] = []
    for offset, placement in enumerate(placements):
        spawned: GameObject = spawn_object(placement, run.level, tuning)
        added.append(replace(spawned, uid=run.next_uid + offset))
    for obj, placement in zip(added, placements, strict=True):
        level: int = run.level if placement.as_level is None else placement.as_level
        log.debug(
            "object spawn id=%d type=%s variant=%s x=%.2f y=%.2f speed=%.2f level=%d",
            obj.uid,
            obj.object_type.value,
            obj.variant,
            obj.x,
            obj.y,
            obj.speed,
            level,
        )
    return replace(run, objects=run.objects + tuple(added), next_uid=run.next_uid + len(added))


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
    """A playing tick: press, timer, objects, wait, ship, scroll, then a fall or a hit, then drops.

    A hit is tested only when the ship did not fall. Source: systems/run.md, Rules, a playing
    tick, steps 1 to 9.
    """
    press: bool = _is_press(thrust, run.held)
    protected: bool = run.invulnerable
    left: int = max(run.invuln_ticks_left - 1, 0)
    objects: tuple[GameObject, ...] = _update_objects(run)
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
        objects=objects,
        invuln_ticks_left=left,
        waiting=stands,
        held=thrust,
    )
    if is_below_floor(ship):
        return _drop_objects(_apply_fall(stepped, protected, thrust))
    return _drop_objects(_apply_hit(stepped, protected, thrust))


def _update_objects(run: Run) -> tuple[GameObject, ...]:
    """Update every object once with the ship as it was at the start of the tick (step 3).

    Logs each object that turns from WARNING to ACTIVE.
    """
    ctx = TickContext(ship=run.ship)
    updated: tuple[GameObject, ...] = tuple(obj.update(ctx) for obj in run.objects)
    for before, after in zip(run.objects, updated, strict=True):
        if before.phase is Phase.WARNING and after.phase is Phase.ACTIVE:
            log.debug(
                "object active id=%d type=%s x=%.2f y=%.2f",
                after.uid,
                after.object_type.value,
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


def _touches_ship(obj: GameObject, ship_box: Hitbox) -> bool:
    """True when `obj` is ACTIVE, a HIT on touch, able to hit now, and overlaps `ship_box`.

    The object decides whether it can hit again (`may_hit_ship`), not the run.
    """
    return (
        obj.phase is Phase.ACTIVE
        and obj.effect_on_touch() is TouchEffect.HIT
        and obj.may_hit_ship()
        and hitboxes_overlap(obj.current_hitbox(), ship_box)
    )


def _apply_hit(stepped: Run, protected: bool, thrust: Thrust) -> Run:
    """Apply a hit to the run after its ship, scroll and objects stepped (step 7).

    Nothing happens with no touching object, or while protected. Otherwise one life is lost
    whatever the number of touching objects, each gets `hit_ship = True`, and the run is
    invulnerable again or over. The ship and the wait stay as they were.
    Source: 05-lives-and-damage.md, rules 1 and 4; systems/run.md, Rules, step 7.
    """
    ship_box: Hitbox = ship_hitbox(stepped.ship)
    touching: tuple[bool, ...] = tuple(_touches_ship(obj, ship_box) for obj in stepped.objects)
    if protected or not any(touching):
        return stepped
    objects: list[GameObject] = []
    for obj, touched in zip(stepped.objects, touching, strict=True):
        if not touched:
            objects.append(obj)
            continue
        log.debug(
            "object touch id=%d type=%s effect=%s",
            obj.uid,
            obj.object_type.value,
            obj.effect_on_touch().value,
        )
        objects.append(replace(obj, hit_ship=True))
    lives: int = stepped.lives - 1
    log.debug("life lost lives=%d", lives)
    hit = replace(stepped, objects=tuple(objects), lives=lives)
    if lives > 0:
        return replace(hit, invuln_ticks_left=INVULN_TICKS)
    return _end_run(hit, thrust)


def _drop_objects(run: Run) -> Run:
    """Remove every GONE or off-screen object, keeping the order of the rest (step 8).

    Logs each dropped object with its last position.
    """
    kept: list[GameObject] = []
    for obj in run.objects:
        if obj.phase is not Phase.GONE and not obj.is_off_screen():
            kept.append(obj)
            continue
        log.debug(
            "object gone id=%d type=%s x=%.2f y=%.2f",
            obj.uid,
            obj.object_type.value,
            obj.x,
            obj.y,
        )
    if len(kept) == len(run.objects):
        return run
    return replace(run, objects=tuple(kept))


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
