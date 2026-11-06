"""The drifter looks rules: which strip draws which drifter, and how fast it plays.

Records only. `app.drifter_looks_tuning` reads `tuning/drifter_looks.json`, checks every field and
builds a `DrifterLooks`; `ui.drifters.sprites` loads the strips it names. A strip is one PNG, all
frames side by side in one row, every frame `frame_w` x `frame_h` px.

Source: 12-art-and-audio.md, rules 9, 10 and 13; the drifter specs' look sections.
"""

import logging
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class StripOrder(Enum):
    """The order a strip's frames play in."""

    LOOP = "loop"
    """Frame 0, 1, 2, ... then round again."""

    RANDOM = "random"
    """A pseudo-random frame each step that never repeats the frame before it."""


@dataclass(frozen=True, slots=True, kw_only=True)
class StripRule:
    """One strip: its file and how it plays."""

    name: str
    """Short name for logs and errors."""

    file: str
    """File name in `assets/sprites/`."""

    frame_w: int
    """Width of one frame, px. The strip's width is a whole number of these."""

    frame_h: int
    """Height of every frame, px. The strip's height."""

    ticks_per_frame: int
    """Game ticks each frame stays, >= 1."""

    order: StripOrder
    """How the frames follow each other."""


@dataclass(frozen=True, slots=True, kw_only=True)
class UfoLooks:
    """The UFO's pool of looks. Each UFO picks one."""

    looks: tuple[StripRule, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class MeteoriteLooks:
    """The meteorite's pool of rock skins. Each rock picks one and is scaled to its variant."""

    looks: tuple[StripRule, ...]

    art_hitbox_width: int
    """Width of the hit circle the art was drawn for, px. A rock scales by its width over this."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanetLooks:
    """The planet's pool of looks, and the code-drawn field rings round it."""

    looks: tuple[StripRule, ...]

    field_ring_color: tuple[int, int, int]
    """Color of every field ring, RGB 0..255."""

    field_ring_width: int
    """Width of every field ring, px, >= 1."""

    field_ring_radius_step: int
    """Px an inner ring's radius is rounded to, >= 1. A bigger step keeps fewer ring images in
    memory; the ring then moves in jumps of this many px."""


@dataclass(frozen=True, slots=True, kw_only=True)
class FireballLooks:
    """The fireball's strip. It is drawn for the big head and scaled down for the small one."""

    strip: StripRule

    art_head_width: int
    """Width of the head in the art, px. A fireball is scaled by head width over this."""

    art_head_center: tuple[int, int]
    """The head's center, px from the top-left of a frame facing down-right (not inverted)."""


@dataclass(frozen=True, slots=True, kw_only=True)
class CoinLooks:
    """One strip per coin variant."""

    common: StripRule
    rare: StripRule


@dataclass(frozen=True, slots=True, kw_only=True)
class ElectricBallLooks:
    """The electric ball: charge strip, fire strip, firing ring, and the code-drawn charge look."""

    charge: StripRule
    """The ball while it charges. Its `ticks_per_frame` is the speed at the start."""

    charge_ticks_per_frame_end: int
    """Ticks per frame when the charge is full. The speed eases from the start value to this."""

    fire: StripRule
    """The ball while the circle fires."""

    ring: StripRule
    """The firing circle, centered, drawn at 2 x pulse radius."""

    ray_color: tuple[int, int, int]
    """Color of the charge rays, RGB 0..255."""

    outline_color: tuple[int, int, int]
    """Color of the charge outline at full level, RGB 0..255."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChainLightningLooks:
    """Chain lightning: a node strip for charge and fire, an arc strip, the code-drawn rays."""

    node_charge: StripRule
    """A node while none of its arcs fires. `ticks_per_frame` is the speed at the start."""

    charge_ticks_per_frame_end: int
    """Ticks per frame when the charge is full."""

    node_fire: StripRule
    """A node while one of its arcs fires."""

    arc: StripRule
    """A firing arc: drawn scaled to the node distance, turned to the arc's angle."""

    ray_color: tuple[int, int, int]
    """Color of the charge rays, RGB 0..255."""


@dataclass(frozen=True, slots=True, kw_only=True)
class FloatingIslandLooks:
    """The ground images an island is cut from. Each island picks one."""

    looks: tuple[str, ...]
    """File names in `assets/sprites/`."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DrifterLooks:
    """Every drifter look value."""

    dim_steps: int
    """Brightness levels a dimmed drifter is drawn at, >= 1. A brightness rounds to a step."""

    ufo: UfoLooks
    meteorite: MeteoriteLooks
    planet: PlanetLooks
    fireball: FireballLooks
    coin: CoinLooks
    electric_ball: ElectricBallLooks
    chain_lightning: ChainLightningLooks
    floating_island: FloatingIslandLooks

    def strips(self) -> tuple[StripRule, ...]:
        """Return every strip rule, each once."""
        electric, chain = self.electric_ball, self.chain_lightning
        return (
            *self.ufo.looks,
            *self.meteorite.looks,
            *self.planet.looks,
            self.fireball.strip,
            self.coin.common,
            self.coin.rare,
            electric.charge,
            electric.fire,
            electric.ring,
            chain.node_charge,
            chain.node_fire,
            chain.arc,
        )
