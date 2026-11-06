"""The chain lightning look: node strips, firing arcs scaled and turned to fit, code-drawn rays.

Source: docs/contracts/systems/drifters.md, Presentation, Chain lightning;
drifters/03-chain-lightning.md, look; 12-art-and-audio.md, rules 9 and 13. A node plays the fire
strip while one of its arcs fires (`firing_arcs()`), else the charge strip, whose frames speed up
as the charge fills. Each firing arc is the arc strip stretched to the real distance between its
two nodes and turned to the arc's angle, its centerline on the line joining the node centers.
Frames count game ticks, offset by uid. Arcs are cached per length and angle. It only draws.
"""

import logging
import math
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.chain_lightning import (
    ChainLightning,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    Point,
    mirrored_nodes,
)
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import ChainLightningLooks, StripRule
from ui.drifters.rays import blit_centered, rays_image
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, eased_frame, installed_sprites, scaled_size, strip_frame

log = logging.getLogger(__name__)

FULL_TURN_DEGREES: Final[int] = 360
"""Whole degrees in a turn: an arc's angle is kept in `0 .. 359`."""

_ARC_SALT: Final[int] = 101
"""Added to the uid once per arc index, so two arcs of one chain don't crackle together."""


@register_view(DrifterType.CHAIN_LIGHTNING)
def render_chain_lightning(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the firing arcs, then the nodes, then the charge rays, around `center`.

    Scaled by `scale`; colors are times `brightness`. Raises TypeError when `drifter` is not a
    ChainLightning.
    """
    if not isinstance(drifter, ChainLightning):
        raise TypeError("render_chain_lightning draws a ChainLightning")
    sprites: Sprites = installed_sprites()
    level: int = sprites.level(brightness)
    nodes: tuple[Point, ...] = tuple(
        (center[0] + ox * scale, center[1] + oy * scale) for ox, oy in drifter.nodes
    )
    firing: tuple[int, ...] = drifter.firing_arcs()
    _draw_arcs(surface, sprites, drifter, nodes, firing, scale, level)
    _draw_nodes(surface, sprites, drifter, nodes, firing, scale, level)
    _draw_rays(surface, sprites, drifter, nodes, scale, level)


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build the node strips, every arc of every layout (both ways round), and the rays."""
    looks: ChainLightningLooks = sprites.looks.chain_lightning
    for level in sprites.warm_levels:
        for rule in (looks.node_charge, looks.node_fire):
            for index in range(sprites.count(rule)):
                sprites.image(rule, index, level)
    chain = tuning.drifters.get(DrifterType.CHAIN_LIGHTNING)
    if chain is None or not isinstance(chain.extra, ChainLightningTypeExtra):
        return
    extra: ChainLightningTypeExtra = chain.extra
    for variant in chain.variants.values():
        if not isinstance(variant.extra, ChainLightningVariantExtra):
            continue
        for invert in (False, True):
            nodes: tuple[Point, ...] = mirrored_nodes(variant.extra.layout, invert)
            for a, b in variant.extra.layout.arcs:
                for level in sprites.warm_levels:
                    for index in range(sprites.count(looks.arc)):
                        _arc_image(sprites, nodes[a], nodes[b], index, 1.0, level)
    for level in sprites.warm_levels:
        for count in range(1, extra.charge_rays + 1):
            _rays(
                sprites,
                (count, extra.charge_rays),
                (extra.node_size, extra.ray_length, extra.ray_width),
                1.0,
                level,
            )


def _draw_arcs(
    surface: pygame.Surface,
    sprites: Sprites,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    firing: tuple[int, ...],
    scale: float,
    level: int,
) -> None:
    """Blit the arc strip's frame over every arc that fires now, joining its two node centers."""
    rule: StripRule = sprites.looks.chain_lightning.arc
    count: int = sprites.count(rule)
    for arc_index in firing:
        a, b = chain.arcs[arc_index]
        frame: int = strip_frame(
            rule, sprites.seed(chain.uid) + arc_index * _ARC_SALT, chain.ticks_in_phase, count
        )
        image: pygame.Surface = _arc_image(sprites, nodes[a], nodes[b], frame, scale, level)
        middle: tuple[int, int] = (
            round((nodes[a][0] + nodes[b][0]) / 2),
            round((nodes[a][1] + nodes[b][1]) / 2),
        )
        surface.blit(image, image.get_rect(center=middle))


def _arc_image(
    sprites: Sprites, start: Point, end: Point, frame: int, scale: float, level: int
) -> pygame.Surface:
    """Return arc frame `frame` stretched to the distance start-end and turned to its angle.

    The frame's left edge is `start` and its right edge `end`; its middle row is the line between
    them. The length is rounded to px and the angle to whole degrees counterclockwise on screen
    (y is down, so dy flips), so the cache holds one image per layout arc.
    """
    rule: StripRule = sprites.looks.chain_lightning.arc
    dx: float = end[0] - start[0]
    dy: float = end[1] - start[1]
    length: int = max(1, round(math.hypot(dx, dy)))
    height: int = max(1, round(rule.frame_h * scale))
    angle: int = round(math.degrees(math.atan2(-dy, dx))) % FULL_TURN_DEGREES
    return sprites.image(rule, frame, level, size=(length, height), angle=angle)


def _draw_nodes(
    surface: pygame.Surface,
    sprites: Sprites,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    firing: tuple[int, ...],
    scale: float,
    level: int,
) -> None:
    """Blit a node frame at every node: the fire strip if one of its arcs fires, else the charge."""
    looks: ChainLightningLooks = sprites.looks.chain_lightning
    burning: set[int] = {node for arc_index in firing for node in chain.arcs[arc_index]}
    charge: int = eased_frame(
        looks.node_charge,
        looks.charge_ticks_per_frame_end,
        sprites.seed(chain.uid),
        chain.cycle_tick(),
        chain.charge_ticks,
        sprites.count(looks.node_charge),
    )
    fire: int = strip_frame(
        looks.node_fire,
        sprites.seed(chain.uid),
        chain.ticks_in_phase,
        sprites.count(looks.node_fire),
    )
    for number, (x, y) in enumerate(nodes):
        rule: StripRule = looks.node_fire if number in burning else looks.node_charge
        image: pygame.Surface = sprites.image(
            rule,
            fire if number in burning else charge,
            level,
            size=scaled_size(rule, scale),
        )
        surface.blit(image, image.get_rect(center=(round(x), round(y))))


def _draw_rays(
    surface: pygame.Surface,
    sprites: Sprites,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    scale: float,
    level: int,
) -> None:
    """Blit the charge rays around every node: `charge_ray_count()` of them, evenly spread."""
    count: int = chain.charge_ray_count()
    if count == 0:
        return
    image: pygame.Surface = _rays(
        sprites,
        (count, chain.charge_rays),
        (chain.node_size, chain.ray_length, chain.ray_width),
        scale,
        level,
    )
    for x, y in nodes:
        blit_centered(surface, image, (round(x), round(y)))


def _rays(
    sprites: Sprites,
    counts: tuple[int, int],
    node: tuple[float, float, float],
    scale: float,
    level: int,
) -> pygame.Surface:
    """Return the image of `counts` = (rays shown, most rays) round a node of `node` = (size, ray
    length, ray width), px, in the ray color at `level`."""
    return rays_image(
        sprites,
        count=counts[0],
        total=counts[1],
        edge=node[0] / 2,
        length=node[1],
        width=node[2],
        scale=scale,
        color=sprites.shade(sprites.looks.chain_lightning.ray_color, level),
    )
