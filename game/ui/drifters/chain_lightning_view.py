"""The placeholder chain lightning look: cyan nodes, a firing band per arc, charge rays.

Source: docs/contracts/systems/drifters.md, Presentation, Chain lightning;
drifters/03-chain-lightning.md, placeholder_look (guess). It only draws.
"""

import logging
import math
from typing import Final

import pygame

from core.collision import Line
from core.drifters.base import Drifter, DrifterType
from core.drifters.chain_lightning import ChainLightning, Point
from ui.drifters.registry import dim_color, register_view
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

CHAIN_NODE_COLOR: Final[tuple[int, int, int]] = (0, 220, 255)
"""Node color, RGB. Source: drifters/03-chain-lightning.md, placeholder_look (guess)."""

CHAIN_RAY_COLOR: Final[tuple[int, int, int]] = (120, 200, 255)
"""Charge ray color, RGB. Source: drifters/03-chain-lightning.md, placeholder_look (guess)."""

CHAIN_ARC_COLOR: Final[tuple[int, int, int]] = (220, 240, 255)
"""Firing arc band color, RGB. Source: drifters/03-chain-lightning.md, placeholder_look (guess)."""

FIRST_RAY_DEGREES: Final[float] = 45.0
"""Angle of the first ray, degrees counterclockwise on screen from pointing right.

Source: drifters/03-chain-lightning.md, ray_length (guess).
"""

FULL_TURN_DEGREES: Final[float] = 360.0
"""Degrees in a full turn, to spread the rays evenly."""


@register_view(DrifterType.CHAIN_LIGHTNING)
def render_chain_lightning(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the firing bands, then the nodes, then the charge rays, around `center`.

    Colors are times `brightness`. Raises TypeError when `drifter` is not a ChainLightning.
    """
    if not isinstance(drifter, ChainLightning):
        raise TypeError("render_chain_lightning draws a ChainLightning")
    nodes: tuple[Point, ...] = tuple(
        (center[0] + ox * scale, center[1] + oy * scale) for ox, oy in drifter.nodes
    )
    _draw_arcs(surface, drifter, nodes, scale, brightness)
    _draw_nodes(surface, drifter, nodes, scale, brightness)
    _draw_rays(surface, drifter, nodes, scale, brightness)


def _draw_arcs(
    surface: pygame.Surface,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    scale: float,
    brightness: float,
) -> None:
    """Fill a band between the two nodes of every arc that fires now."""
    color: tuple[int, int, int] = dim_color(CHAIN_ARC_COLOR, brightness)
    for index in chain.firing_arcs():
        (ax, ay), (bx, by) = (nodes[node] for node in chain.arcs[index])
        draw_shape(surface, color, Line(ax, ay, bx, by, chain.arc_width * scale))


def _draw_nodes(
    surface: pygame.Surface,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    scale: float,
    brightness: float,
) -> None:
    """Fill a disc of diameter `node_size` at every node, firing or not."""
    color: tuple[int, int, int] = dim_color(CHAIN_NODE_COLOR, brightness)
    radius: int = round(chain.node_size * scale / 2)
    for x, y in nodes:
        pygame.draw.circle(surface, color, (round(x), round(y)), radius)


def _draw_rays(
    surface: pygame.Surface,
    chain: ChainLightning,
    nodes: tuple[Point, ...],
    scale: float,
    brightness: float,
) -> None:
    """Draw the charge rays around every node: `charge_ray_count()` of them, evenly spread."""
    count: int = chain.charge_ray_count()
    color: tuple[int, int, int] = dim_color(CHAIN_RAY_COLOR, brightness)
    width: int = max(1, round(chain.ray_width * scale))
    edge: float = chain.node_size / 2 * scale
    tip: float = (chain.node_size / 2 + chain.ray_length) * scale
    for k in range(count):
        angle: float = math.radians(FIRST_RAY_DEGREES + k * FULL_TURN_DEGREES / chain.charge_rays)
        dx: float = math.cos(angle)
        dy: float = -math.sin(angle)
        for x, y in nodes:
            start: tuple[float, float] = (x + dx * edge, y + dy * edge)
            end: tuple[float, float] = (x + dx * tip, y + dy * tip)
            pygame.draw.line(surface, color, start, end, width)
