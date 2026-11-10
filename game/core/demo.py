"""The demo flight: a short scripted flight before the first run of a page load.

A script of steps flies the ship with the real `core.ship.step`, so the demo shows the real drift.
A step holds set arrows, or stands still (as the ship does while it waits to respawn), or flies by
the autopilot: it taps the arrows itself, as a player would, to reach a spot and hover there. One
coin waits where the ship will be at the end of the coin step, worked out by flying the script
once ahead, so the ship always collects it whatever the ship's values. The world does not scroll:
the coin stays put. Each arrow's glow on screen eases toward held or free over `key_fade_ticks`.
Stdlib and core only, no frame time, no randomness.

Source: docs/contracts/systems/demo.md; 02-game-flow.md, rule 5a.
"""

import logging
from dataclasses import dataclass, field, replace
from typing import Final

from core.collision import Hitbox, hitboxes_overlap
from core.drifters.base import Drifter, DrifterType, Phase, TickContext, TouchEffect
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.levels import FIRST_LEVEL
from core.popup import PointsPopup, step_popups
from core.ship import Ship, Thrust, ship_hitbox, spawn, step
from core.sound_cue import SoundCue

log = logging.getLogger(__name__)

ARROWS: Final[tuple[str, ...]] = ("up", "down", "left", "right")
"""The arrows, in the order of `Demo.glow`."""

type Spot = tuple[float, float]
"""A point in the play area, screen px, y down."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DemoStep:
    """One step of the script: how the ship flies, for how long, and its caption."""

    keys: Thrust
    """The arrows held through the step. None when it stands or flies by the autopilot."""

    ticks: int
    """How long the step lasts, ticks, at least 1."""

    caption: str | None
    """The caption shown from this step on. None: the last caption stays."""

    stand: bool = False
    """True: the ship stands still through the step, as it does while it waits to respawn."""

    pilot_to: Spot | None = None
    """Set: the autopilot taps the arrows to fly to this spot and hover there."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PilotRules:
    """How the autopilot taps the arrows. Speeds px/tick, distances px."""

    gain: float
    """Speed wanted per px of distance to the spot, per tick. Bigger flies in harder."""

    max_speed: float
    """Fastest speed the autopilot asks for, up or down, px/tick. Sideways it allows 1.5 times."""

    band: float
    """How far the speed may stray from the wanted one before a key goes down or up, px/tick.
    Bigger gives longer, calmer taps and a little more bob."""

    near_px: float
    """Sideways distance to the spot within which, with sideways speed under `near_speed`, no
    side key is tapped: drag settles the rest."""

    near_speed: float
    """See `near_px`, px/tick."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DemoRules:
    """The demo's script, its coin and its timing, from tuning/demo.json."""

    steps: tuple[DemoStep, ...]
    """The script, in order. At least one step."""

    coin_step: int
    """Index of the step at whose last tick the ship reaches the coin."""

    coin_type: DrifterType
    """The drifter type of the coin: a pickup, collected on touch."""

    coin_variant: str
    """The coin's variant name in its type's tuning."""

    fade_out_ticks: int
    """The last ticks of the demo, in which the play area fades to black, at least 0."""

    pilot: PilotRules
    """How the autopilot flies."""

    key_fade_ticks: int
    """Ticks an arrow's glow takes to go from free to held or back, at least 1."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Demo:
    """The demo after a tick."""

    rules: DemoRules
    ship: Ship
    coin: Drifter | None
    """The coin until it is collected, then None."""

    popups: tuple[PointsPopup, ...] = ()
    tick: int = 0
    """Ticks played so far."""

    held: Thrust = field(default_factory=Thrust)
    """The arrows the last tick held. None before the first tick."""

    stood: bool = False
    """True when the last tick stood (before the first tick: the first step stands)."""

    glow: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    """Each arrow's glow on screen, 0..1, in ARROWS order."""

    sound_cues: tuple[SoundCue, ...] = ()
    """The sounds of the last tick."""

    points: int = 0
    """Points the collected coin paid, for the HUD's score while the demo shows."""

    @property
    def total_ticks(self) -> int:
        """The demo's whole length, ticks."""
        return sum(demo_step.ticks for demo_step in self.rules.steps)

    @property
    def done(self) -> bool:
        """True once every step has played."""
        return self.tick >= self.total_ticks

    @property
    def step_index(self) -> int:
        """Index of the step the next tick plays. The last step once done."""
        return step_at(self.rules, self.tick)[0]

    @property
    def ticks_in_step(self) -> int:
        """Ticks the current step has played."""
        return step_at(self.rules, self.tick)[1]

    @property
    def ticks_left(self) -> int:
        """Ticks still to play."""
        return max(self.total_ticks - self.tick, 0)

    @property
    def caption(self) -> str | None:
        """The caption shown now: the last one set by this step or an earlier one."""
        return caption_at(self.rules, self.step_index)

    @property
    def fade(self) -> float:
        """How dark the play area is, 0..1: 0 until the last `fade_out_ticks`, then up to 1."""
        fade_ticks: int = self.rules.fade_out_ticks
        if fade_ticks <= 0:
            return 0.0
        return min(max(1.0 - self.ticks_left / fade_ticks, 0.0), 1.0)


def step_at(rules: DemoRules, tick: int) -> tuple[int, int]:
    """Return (step index, ticks into it) for `tick` ticks played. Past the end: the last step."""
    start: int = 0
    for index, demo_step in enumerate(rules.steps):
        if tick < start + demo_step.ticks:
            return index, tick - start
        start += demo_step.ticks
    last: int = len(rules.steps) - 1
    return last, rules.steps[last].ticks


def caption_at(rules: DemoRules, index: int) -> str | None:
    """Return the caption shown during step `index`: its own, or the last earlier one set."""
    for demo_step in reversed(rules.steps[: index + 1]):
        if demo_step.caption is not None:
            return demo_step.caption
    return None


def check_demo_rules(rules: DemoRules) -> None:
    """Raise ValueError when the script can't play: no steps, a step under 1 tick, a step that
    both stands and flies, a coin step out of range, or a timing below its floor."""
    if not rules.steps:
        raise ValueError("demo has no steps")
    for index, demo_step in enumerate(rules.steps):
        if demo_step.ticks < 1:
            raise ValueError(f"demo step {index} lasts under 1 tick")
        flies: bool = demo_step.keys != Thrust() or demo_step.pilot_to is not None
        if demo_step.stand and flies:
            raise ValueError(f"demo step {index} stands, so it can hold no keys and fly nowhere")
        if demo_step.keys != Thrust() and demo_step.pilot_to is not None:
            raise ValueError(f"demo step {index} holds keys and flies by the autopilot")
    if not 0 <= rules.coin_step < len(rules.steps):
        raise ValueError(f"demo coin_step {rules.coin_step} is not a step")
    if rules.fade_out_ticks < 0:
        raise ValueError("demo fade_out_ticks is below 0")
    if rules.key_fade_ticks < 1:
        raise ValueError("demo key_fade_ticks is below 1")


def autopilot(ship: Ship, spot: Spot, held: Thrust, rules: PilotRules) -> Thrust:
    """Return the arrows to hold this tick to fly the ship to `spot` and hover there.

    Each axis wants a speed toward the spot, bigger the farther it is, up to `max_speed`. A key
    goes down when the speed strays past the wanted one by `band` and comes up once it strays
    `band` the other way, so taps are a few ticks long. Up brakes a fall and holds the hover
    against gravity; down brakes a climb only when it is well past the wanted speed.
    """
    target_x, target_y = spot
    top: float = rules.max_speed
    want_vy: float = min(max((target_y - ship.y) * rules.gain, -top), top)
    want_vx: float = min(max((target_x - ship.x) * rules.gain, -1.5 * top), 1.5 * top)
    up: bool = ship.vy > want_vy + (-rules.band if held.up else rules.band)
    down: bool = not up and ship.vy < want_vy - 3 * rules.band
    near: bool = abs(target_x - ship.x) < rules.near_px and abs(ship.vx) < rules.near_speed
    right: bool = not near and ship.vx < want_vx - (-rules.band if held.right else rules.band)
    left: bool = (
        not near and not right and ship.vx > want_vx + (-rules.band if held.left else rules.band)
    )
    return Thrust(up=up, down=down, left=left, right=right)


def _fly(demo_step: DemoStep, ship: Ship, held: Thrust, pilot: PilotRules) -> tuple[Ship, Thrust]:
    """Play one tick of `demo_step`: return the ship after it and the arrows held."""
    if demo_step.stand:
        return ship, Thrust()
    keys: Thrust = demo_step.keys
    if demo_step.pilot_to is not None:
        keys = autopilot(ship, demo_step.pilot_to, held, pilot)
    return step(ship, keys), keys


def coin_spot(rules: DemoRules) -> Spot:
    """Return where the ship's center is at the last tick of the coin step, screen px."""
    ship: Ship = spawn()
    held: Thrust = Thrust()
    for demo_step in rules.steps[: rules.coin_step + 1]:
        for _ in range(demo_step.ticks):
            ship, held = _fly(demo_step, ship, held, rules.pilot)
    return ship.x, ship.y


def start_demo(rules: DemoRules, tuning: DrifterTuning) -> Demo:
    """Return the demo before its first tick: the ship at spawn, the coin at `coin_spot`.

    Raises ValueError from `check_demo_rules`, what `spawn_drifter` raises for the coin, or
    when the coin is not an ACTIVE pickup collected on touch.
    """
    check_demo_rules(rules)
    x, y = coin_spot(rules)
    coin: Drifter = spawn_drifter(
        Placement(rules.coin_type, x=x, y=y, variant=rules.coin_variant), FIRST_LEVEL, tuning
    )
    if coin.phase is not Phase.ACTIVE or coin.effect_on_touch() is not TouchEffect.COLLECT:
        raise ValueError(f"demo coin type '{rules.coin_type.value}' is not a pickup")
    log.debug("demo ready ticks=%d coin x=%.2f y=%.2f", sum(s.ticks for s in rules.steps), x, y)
    return Demo(rules=rules, ship=spawn(), coin=replace(coin, uid=1), stood=rules.steps[0].stand)


def step_demo(demo: Demo) -> Demo:
    """Advance the demo one 60 Hz tick and return it. Never mutates the input.

    The ship flies the current step. The arrows' glow moves one `key_fade_ticks` share toward
    the arrows held. The coin stays put and animates. When the ship's hitbox overlaps the coin's,
    the coin goes, its popup starts and the coin sound plays. A done demo is returned as is.
    """
    if demo.done:
        return demo
    demo_step: DemoStep = demo.rules.steps[demo.step_index]
    ship, held = _fly(demo_step, demo.ship, demo.held, demo.rules.pilot)
    popups: tuple[PointsPopup, ...] = step_popups(demo.popups)
    coin: Drifter | None = demo.coin
    cues: tuple[SoundCue, ...] = ()
    points: int = demo.points
    if coin is not None:
        coin = coin.update(TickContext(ship=demo.ship, scroll_step_px=0.0))
        if _touches(coin, ship_hitbox(ship)):
            log.debug("demo coin collected tick=%d", demo.tick + 1)
            popup: PointsPopup | None = coin.collect_popup()
            popups = popups + (() if popup is None else (popup,))
            cues = (SoundCue.COIN,)
            points += coin.collect_points()
            coin = None
    return replace(
        demo,
        ship=ship,
        coin=coin,
        popups=popups,
        tick=demo.tick + 1,
        held=held,
        stood=demo_step.stand,
        glow=_glow(demo.glow, held, demo.rules.key_fade_ticks),
        sound_cues=cues,
        points=points,
    )


def _glow(
    glow: tuple[float, float, float, float], held: Thrust, fade_ticks: int
) -> tuple[float, float, float, float]:
    """Move each arrow's glow one 1/`fade_ticks` share toward 1 when held, else toward 0."""
    share: float = 1.0 / fade_ticks
    up, down, left, right = (
        min(value + share, 1.0) if getattr(held, arrow) else max(value - share, 0.0)
        for value, arrow in zip(glow, ARROWS, strict=True)
    )
    return (up, down, left, right)


def _touches(coin: Drifter, ship_box: Hitbox) -> bool:
    """True when the coin is ACTIVE and its hitbox overlaps the ship's."""
    return coin.phase is Phase.ACTIVE and hitboxes_overlap(coin.current_hitbox(), ship_box)
