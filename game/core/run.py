"""One run of the game: lives, falls, the respawn wait, invulnerability, game over, retry.

`Run` holds the ship, the world scroll and the lives, and `step_run` advances all of them one
fixed 60 Hz tick. The ship step reports where the ship is (`is_below_floor`); the run decides
what a fall costs. No frame time, no randomness, no run mode. Stdlib, `core.ship` and
`core.scroll` only.

Source: docs/contracts/systems/run.md, Interface, Rules and Logging.
"""

import logging
from dataclasses import dataclass, replace
from typing import Final

from core.scroll import Scroll, start_scroll, step_scroll
from core.ship import Ship, Thrust, is_below_floor, spawn, step

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

    held: Thrust = Thrust()
    """The arrow keys held on the last tick, to tell a press from a hold."""

    retry_armed: bool = False
    """Game over only: every arrow has been released since the box appeared."""

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


def start_run() -> Run:
    """Return a new run: the ship at spawn, the scroll at tick 0, every other field default.

    Source: 02-game-flow.md, rule 3; systems/run.md, Interface.
    """
    return Run(ship=spawn(), scroll=start_scroll())


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
    """Steps 1 to 6 of a playing tick: press, timer, wait, ship, scroll, fall.

    Source: systems/run.md, Rules, a playing tick.
    """
    press: bool = _is_press(thrust, run.held)
    protected: bool = run.invulnerable
    left: int = max(run.invuln_ticks_left - 1, 0)
    ended_wait: bool = run.waiting and press
    if ended_wait:
        log.debug("respawn wait end")
    stands: bool = run.waiting and not press
    ship: Ship = run.ship if stands else step(run.ship, thrust)
    scroll: Scroll = step_scroll(run.scroll)
    if run.invuln_ticks_left == 1:
        log.debug("invulnerable end")
    stepped = replace(
        run, ship=ship, scroll=scroll, invuln_ticks_left=left, waiting=stands, held=thrust
    )
    if not is_below_floor(ship):
        return stepped
    return _apply_fall(stepped, protected, thrust)


def _apply_fall(stepped: Run, protected: bool, thrust: Thrust) -> Run:
    """Apply a fall to the run after its ship and scroll stepped.

    A protected fall respawns the ship with no wait and no life lost. An unprotected fall
    costs a life and respawns it waiting with fresh invulnerability, or ends the run on the
    last life.
    Source: 05-lives-and-damage.md, rules 2.1 to 2.6 and 5; systems/run.md, Rules, step 5.
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
    log.info("game over meters=%d", stepped.scroll.meters)
    return replace(
        stepped,
        lives=0,
        game_over=True,
        invuln_ticks_left=0,
        waiting=False,
        retry_armed=not _any_arrow(thrust),
    )


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
