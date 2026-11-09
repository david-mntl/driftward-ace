"""The demo flight's look: the coin, the popup and the ship, the arrow keys the script holds, the
caption, the skip hint, and the fades at the end of the demo and the start of the run after it.

The four arrow key caps sit as an inverted T at the bottom center of the play area. A held key
lights up and sinks a little by its glow (`Demo.glow`, eased). The caption sits above the keys and
fades in, rising, whenever it changes. In the last `start_ticks` the start word takes its place,
fading in and shrinking to size. The skip hint sits in the top-right corner. Colors
and the font come from the screens' look; every size and timing from DemoLook
(tuning/demo.json). It only draws: it never logs per frame and never reads a key.

Source: docs/contracts/systems/demo.md; 10-ui.md, demo_look.
"""

import logging
import math
from dataclasses import dataclass
from typing import Final

import pygame

from core.demo import ARROWS, Demo, DemoRules, step_at
from ui.drifters.registry import render_drifter
from ui.popup_view import draw_points_popup
from ui.screen_look import ScreenLook
from ui.screen_rules import RGB
from ui.ship_view import ShipLook, draw_ship

log = logging.getLogger(__name__)

SKIP_KEYS: Final[tuple[str, ...]] = ("ENTER", "SPACE")
"""The keys that skip the demo, shown in the skip hint. 02-game-flow.md, confirm_keys."""

KEY_LAYOUT: Final[tuple[tuple[str, int, int], ...]] = (
    ("UP", 0, 0),
    ("LEFT", -1, 1),
    ("DOWN", 0, 1),
    ("RIGHT", 1, 1),
)
"""Each key cap's label, column (-1..1) and row (0 top, 1 bottom): an inverted T."""

_ALPHA_STEP: Final[int] = 16
"""Text alpha is rounded to a multiple of this, so a fade makes few cached text pictures."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DemoLook:
    """Sizes and timings of the demo's overlay, px and ticks. From tuning/demo.json, look."""

    key_size: int
    """A key cap's side, px."""

    key_gap: int
    """Space between key caps, px."""

    key_radius: int
    """A key cap's corner radius, px."""

    key_bottom: int
    """Gap from the play area's bottom edge to the bottom row of keys, px."""

    arrow_size: int
    """Half the arrow's width on a key cap, px."""

    press_depth: int
    """How far a held key sinks, px."""

    idle_fill_alpha: int
    """A key cap's fill when not held, 0..255."""

    idle_border_alpha: int
    """A key cap's border when not held, 0..255."""

    lit_fill_alpha: int
    """A key cap's fill when held, 0..255."""

    caption_role: str
    """The screens' text role of the caption."""

    caption_gap: int
    """Gap from the caption's bottom to the top row of keys, px."""

    caption_fade_ticks: int
    """Ticks a new caption takes to fade in, at least 1."""

    caption_rise: int
    """How far a new caption rises while it fades in, px."""

    skip_margin: int
    """Gap from the play area's top and right edges to the skip hint, px."""

    skip_word: str
    """The word after the skip keys."""

    fade_in_ticks: int
    """Ticks the run after the demo takes to fade in from black, at least 0."""

    coin_ring_radius: int
    """The pulsing ring round the waiting coin: its middle radius, px. 0: no ring."""

    coin_ring_pulse: int
    """How far the ring's radius swings either way, px."""

    coin_ring_period_ticks: int
    """Ticks of one pulse, at least 1."""

    coin_ring_alpha: int
    """The ring's alpha at its brightest, 0..255."""

    start_text: str
    """The word that shows in the last `start_ticks` of the demo, as the run is about to start."""

    start_role: str
    """The screens' text role of the start word."""

    start_ticks: int
    """The last ticks of the demo in which the start word shows instead of the caption, at
    least 0. 0: no start word."""

    start_pop_ticks: int
    """Ticks the start word takes to fade in and shrink to its size, at least 1."""

    start_scale: float
    """How big the start word starts, times its size, at least 1. It shrinks to 1."""

    start_y: int
    """The start word's center, px from the play area's top edge."""


def draw_demo(
    surface: pygame.Surface,
    demo: Demo,
    rules: DemoLook,
    look: ScreenLook,
    ship_look: ShipLook,
    tick: int,
) -> None:
    """Draw the demo over the play area's background and starfield, on `surface`.

    The coin, the ship (flames for the held keys, none while standing), the popups over it (in a
    run they sit behind the ship; here the ship can sit on the coin's spot and would hide its
    points), the keys, the caption (the start word instead in the last `start_ticks`) and the skip
    hint, then the black of the end fade. `tick` steps the flame flicker.
    """
    if demo.coin is not None:
        _draw_coin_ring(surface, (demo.coin.x, demo.coin.y), demo.tick, rules, look)
        render_drifter(surface, demo.coin)
    draw_ship(surface, demo.ship, None if demo.stood else demo.held, tick, ship_look)
    for popup in demo.popups:
        draw_points_popup(surface, popup)
    top: int = _draw_keys(surface, demo, rules, look)
    if starting(demo, rules):
        _draw_start(surface, demo, rules, look)
    else:
        _draw_caption(surface, demo, rules, look, top)
    look.blit_keys(
        surface,
        SKIP_KEYS,
        rules.skip_word,
        {"topright": (surface.get_width() - rules.skip_margin, rules.skip_margin)},
    )
    _darken(surface, demo.fade)


def draw_fade_in(surface: pygame.Surface, run_ticks: int, rules: DemoLook) -> None:
    """Darken `surface` for the first `fade_in_ticks` of the run after the demo, black to clear."""
    if rules.fade_in_ticks <= 0 or run_ticks >= rules.fade_in_ticks:
        return
    _darken(surface, 1.0 - run_ticks / rules.fade_in_ticks)


def starting(demo: Demo, rules: DemoLook) -> bool:
    """True in the last `start_ticks` of the demo, while the start word shows."""
    return rules.start_ticks > 0 and demo.ticks_left <= rules.start_ticks


def key_light(demo: Demo, name: str) -> float:
    """How lit key `name` (UP, DOWN, LEFT or RIGHT) is now, 0..1: its glow, eased."""
    return _ease(demo.glow[ARROWS.index(name.lower())])


def caption_age(rules: DemoRules, tick: int) -> int:
    """Ticks since the caption shown after `tick` demo ticks was set."""
    index, into = step_at(rules, tick)
    age: int = into
    for earlier in range(index, 0, -1):
        if rules.steps[earlier].caption is not None:
            return age
        age += rules.steps[earlier - 1].ticks
    return age


def _ease(t: float) -> float:
    """Smoothstep of t in 0..1."""
    return t * t * (3.0 - 2.0 * t)


def _draw_keys(surface: pygame.Surface, demo: Demo, rules: DemoLook, look: ScreenLook) -> int:
    """Draw the four key caps as an inverted T. Return the top of the top row, px."""
    size: int = rules.key_size
    pitch: int = size + rules.key_gap
    bottom: int = surface.get_height() - rules.key_bottom
    top: int = bottom - 2 * size - rules.key_gap
    centerx: int = surface.get_width() // 2
    for name, column, row in KEY_LAYOUT:
        light: float = key_light(demo, name)
        cap: pygame.Rect = pygame.Rect(0, 0, size, size)
        cap.center = (centerx + column * pitch, top + size // 2 + row * pitch)
        cap.move_ip(0, round(rules.press_depth * light))
        _draw_cap(surface, cap, name, light, rules, look)
    return top


def _draw_cap(
    surface: pygame.Surface,
    cap: pygame.Rect,
    name: str,
    light: float,
    rules: DemoLook,
    look: ScreenLook,
) -> None:
    """Draw one key cap lit by `light` (0..1): a cyan fill and border, the arrow dark when lit."""
    cyan: RGB = look.palette["frame_lights"]
    dark: RGB = look.palette["panel_body"]
    fill: int = round(
        rules.idle_fill_alpha + (rules.lit_fill_alpha - rules.idle_fill_alpha) * light
    )
    border: int = round(rules.idle_border_alpha + (255 - rules.idle_border_alpha) * light)
    image: pygame.Surface = pygame.Surface(cap.size, pygame.SRCALPHA)
    body: pygame.Rect = image.get_rect()
    pygame.draw.rect(image, (*cyan, fill), body, border_radius=rules.key_radius)
    pygame.draw.rect(image, (*cyan, border), body, 1, border_radius=rules.key_radius)
    surface.blit(image, cap.topleft)
    _draw_arrow(surface, name, cap.center, _mix(cyan, dark, light), rules.arrow_size)


def _draw_arrow(
    surface: pygame.Surface, name: str, center: tuple[int, int], color: RGB, size: int
) -> None:
    """Draw a solid triangle `size` px from its center to each edge, pointing `name`."""
    x, y = center
    points: dict[str, list[tuple[int, int]]] = {
        "UP": [(x, y - size), (x + size, y + size), (x - size, y + size)],
        "DOWN": [(x, y + size), (x + size, y - size), (x - size, y - size)],
        "LEFT": [(x - size, y), (x + size, y - size), (x + size, y + size)],
        "RIGHT": [(x + size, y), (x - size, y - size), (x - size, y + size)],
    }
    pygame.draw.polygon(surface, color, points[name])


def _draw_caption(
    surface: pygame.Surface, demo: Demo, rules: DemoLook, look: ScreenLook, keys_top: int
) -> None:
    """Draw the caption centered above the keys, fading in and rising while it is new."""
    caption: str | None = demo.caption
    if caption is None:
        return
    t: float = _ease(
        min(caption_age(demo.rules, demo.tick) / max(rules.caption_fade_ticks, 1), 1.0)
    )
    alpha: int = min(round(255 * t / _ALPHA_STEP) * _ALPHA_STEP, 255)
    if alpha <= 0:
        return
    bottom: int = keys_top - rules.caption_gap + round(rules.caption_rise * (1.0 - t))
    look.blit_text(
        surface,
        caption,
        rules.caption_role,
        look.palette["plating"],
        {"midbottom": (surface.get_width() // 2, bottom)},
        glow=False,
        alpha=alpha,
    )


def _draw_coin_ring(
    surface: pygame.Surface,
    center: tuple[float, float],
    tick: int,
    rules: DemoLook,
    look: ScreenLook,
) -> None:
    """Draw a thin cyan ring round the waiting coin that slowly grows, shrinks and glows."""
    if rules.coin_ring_radius <= 0:
        return
    wave: float = 0.5 - 0.5 * math.cos(2 * math.pi * tick / rules.coin_ring_period_ticks)
    radius: int = round(rules.coin_ring_radius + rules.coin_ring_pulse * (2 * wave - 1))
    alpha: int = round(rules.coin_ring_alpha * (0.45 + 0.55 * wave))
    side: int = 2 * radius + 4
    ring: pygame.Surface = pygame.Surface((side, side), pygame.SRCALPHA)
    cyan: RGB = look.palette["frame_lights"]
    pygame.draw.circle(ring, (*cyan, alpha), (side // 2, side // 2), radius, 1)
    surface.blit(ring, ring.get_rect(center=(round(center[0]), round(center[1]))))


def _draw_start(surface: pygame.Surface, demo: Demo, rules: DemoLook, look: ScreenLook) -> None:
    """Draw the start word centered at `start_y`, fading in and shrinking from `start_scale`."""
    age: int = rules.start_ticks - demo.ticks_left
    t: float = _ease(min(age / max(rules.start_pop_ticks, 1), 1.0))
    width, height = look.text_size(rules.start_text, rules.start_role)
    image: pygame.Surface = pygame.Surface((width + 8, height + 8), pygame.SRCALPHA)
    look.blit_text(
        image,
        rules.start_text,
        rules.start_role,
        look.palette["plating"],
        {"center": image.get_rect().center},
        glow=False,
    )
    scale: float = rules.start_scale + (1.0 - rules.start_scale) * t
    if scale != 1.0:
        image = pygame.transform.smoothscale_by(image, scale)
    image.set_alpha(round(255 * t))
    surface.blit(image, image.get_rect(center=(surface.get_width() // 2, rules.start_y)))


def _darken(surface: pygame.Surface, amount: float) -> None:
    """Darken `surface` in place toward black, `amount` 0 (none) to 1 (fully black).

    A multiply by (1 - amount) is black laid over at that alpha, with no new surface.
    """
    keep: int = round(255 * (1.0 - min(max(amount, 0.0), 1.0)))
    if keep >= 255:
        return
    surface.fill((keep, keep, keep), special_flags=pygame.BLEND_MULT)


def _mix(a: RGB, b: RGB, t: float) -> RGB:
    """Return the color t (0..1) of the way from a to b."""
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )
