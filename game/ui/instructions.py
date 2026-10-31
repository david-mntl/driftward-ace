"""Instructions page: the title, six glass cards, each an icon with a topic and a short caption, and
the footer.

Source: docs/contracts/systems/screens.md, Interface (ui/instructions.py); 10-ui.md,
`instructions_text_and_look`. The view takes the surface and the look and only draws. It never
fills the background, never flips the display, never logs per frame, never catches an error and
never reads the run mode, a key or the focus. The icons are drawn once, at 4 times their size and
scaled down, then kept.
"""

import logging
import math
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from itertools import pairwise
from typing import Final

import pygame

from ui.screen_look import ScreenLook, halo
from ui.screen_rules import RGB

log = logging.getLogger(__name__)

INSTRUCTIONS_TITLE_TEXT: Final[str] = "HOW TO PLAY"
"""Page title. 10-ui.md, instructions_text_and_look."""

INSTRUCTION_SECTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("FLY", "Hold to thrust. Let go and gravity takes you."),
    ("PAUSE", "Press again to go on."),
    ("GRAZE", "Skim a hazard without touching. Score."),
    ("WARNING", "A hazard is coming. Get clear."),
    ("FALL", "Fall off the bottom, lose a life."),
    ("COINS", "Points. The best ones sit near danger."),
)
"""The six (topic, caption) pairs, in card order. 10-ui.md, instructions_text_and_look."""

CARD_COLOR_KEYS: Final[tuple[str, ...]] = (
    "frame_lights",
    "ship_lines_light",
    "graze",
    "last_life",
    "ship_lines",
    "level",
)
"""The palette key that lights each card's topic and icon, in card order. 12-art-and-audio.md,
Screen colors."""

BACK_KEYS: Final[tuple[str, ...]] = ("ENTER", "SPACE")
"""The keys that go back, shown in the footer. 10-ui.md, instructions_text_and_look."""

BACK_WORD: Final[str] = "BACK"
"""The word after the footer's key caps. 10-ui.md, instructions_text_and_look."""

_DESIGN_W: Final[int] = 176
_DESIGN_H: Final[int] = 96
"""The icons' drawing space, the mock-up's 176 x 96. Each icon is scaled to fit its box."""

_SUPERSAMPLE: Final[int] = 4
"""Times larger than its box an icon is drawn, then scaled down, so the lines are smooth."""

_DASH: Final[float] = 4.0
"""Length of a dash and of a gap, in design units."""

_STROKE: Final[float] = 1.6
"""Line width of most icon strokes, design units."""

type Point = tuple[float, float]

_SHIP: Final[tuple[Point, ...]] = (
    (0.50, 0.00),
    (0.62, 0.35),
    (0.70, 0.55),
    (1.00, 0.82),
    (0.92, 0.90),
    (0.66, 0.78),
    (0.58, 0.97),
    (0.50, 0.88),
    (0.42, 0.97),
    (0.34, 0.78),
    (0.08, 0.90),
    (0.00, 0.82),
    (0.30, 0.55),
    (0.38, 0.35),
)
"""The ship's silhouette in a 0..1 box: a long nose, swept blade wings, a split tail."""


def draw_instructions(surface: pygame.Surface, look: ScreenLook) -> None:
    """Draw the title, the rulers, the six cards and the footer onto ``surface``. Units: px.

    The title sits at the top of the head band. The cards fill the window between the head band and
    the footer band inside the margins, ``columns`` to a row, ``gap`` apart. In a card the icon is
    on the left and the topic and caption are a block centered on the right. The footer's key caps
    and word are centered in the footer band. Needs ``pygame.font`` initialized.
    """
    rules = look.rules.instructions
    width, height = surface.get_size()
    look.blit_rulers(surface)
    look.blit_text(
        surface,
        INSTRUCTIONS_TITLE_TEXT,
        "title",
        look.palette["plating"],
        {"midtop": (width // 2, rules.margin_top)},
    )
    for index, rect in enumerate(card_rects(look, surface.get_size())):
        _draw_card(surface, look, index, rect)
    foot_centery: int = height - rules.margin_bottom - rules.foot_h // 2
    look.blit_keys(surface, BACK_KEYS, BACK_WORD, {"center": (width // 2, foot_centery)})


def card_rects(look: ScreenLook, size: tuple[int, int]) -> list[pygame.Rect]:
    """Return the six card rects for a window of ``size``, in card order, px.

    The grid fills the space between the head band and the footer band inside the side margins.
    Cards are as wide and tall as the grid allows, the leftover pixels going to the margin.
    """
    rules = look.rules.instructions
    width, height = size
    top: int = rules.margin_top + rules.head_h
    bottom: int = height - rules.margin_bottom - rules.foot_h
    columns: int = rules.columns
    rows: int = math.ceil(len(INSTRUCTION_SECTIONS) / columns)
    card_w: int = (width - 2 * rules.margin_x - (columns - 1) * rules.gap) // columns
    card_h: int = (bottom - top - (rows - 1) * rules.gap) // rows
    return [
        pygame.Rect(
            rules.margin_x + (index % columns) * (card_w + rules.gap),
            top + (index // columns) * (card_h + rules.gap),
            card_w,
            card_h,
        )
        for index in range(len(INSTRUCTION_SECTIONS))
    ]


def icon_rect(look: ScreenLook, card: pygame.Rect) -> pygame.Rect:
    """Return where a card's icon sits inside ``card``: its left, centered across the height."""
    rules = look.rules.instructions
    top: int = max(rules.pad_y, (card.height - rules.icon_h) // 2)
    return pygame.Rect(card.left + rules.pad_x, card.top + top, rules.icon_w, rules.icon_h)


def _draw_card(surface: pygame.Surface, look: ScreenLook, index: int, card: pygame.Rect) -> None:
    """Draw one card: the glass, the icon, and the topic and caption beside it."""
    rules = look.rules.instructions
    title, caption = INSTRUCTION_SECTIONS[index]
    color: RGB = look.palette[CARD_COLOR_KEYS[index]]
    look.glass(surface, card, rules.blur)
    icon, pad = _icon(look, index)
    box: pygame.Rect = icon_rect(look, card)
    surface.blit(icon, (box.left - pad, box.top - pad))
    text_left: int = box.right + rules.text_gap
    lines: tuple[str, ...] = _wrap(look, caption, card.right - rules.pad_x - text_left)
    title_h: int = look.text_size(title, "card_title")[1]
    line_h: int = look.text_size(caption, "card_text")[1]
    block: int = title_h + rules.caption_gap + len(lines) * line_h
    top: int = card.centery - block // 2
    look.blit_text(surface, title, "card_title", color, {"topleft": (text_left, top)})
    top += title_h + rules.caption_gap
    for line in lines:
        look.blit_text(
            surface,
            line,
            "card_text",
            look.palette["plating"],
            {"topleft": (text_left, top)},
            glow=False,
            alpha=rules.caption_alpha,
        )
        top += line_h


@cache
def _wrap(look: ScreenLook, text: str, width: int) -> tuple[str, ...]:
    """Split ``text`` into lines no wider than ``width`` px at the caption size, breaking at spaces.

    A single word wider than ``width`` stays on a line of its own.
    """
    lines: list[str] = []
    current: str = ""
    for word in text.split(" "):
        trial: str = f"{current} {word}" if current else word
        if current and look.text_size(trial, "card_text")[0] > width:
            lines.append(current)
            current = word
        else:
            current = trial
    lines.append(current)
    return tuple(lines)


@cache
def _icon(look: ScreenLook, index: int) -> tuple[pygame.Surface, int]:
    """Return card ``index``'s icon with its soft glow, and the margin the glow adds, px.

    Drawn once at ``_SUPERSAMPLE`` times its box and scaled down, then the labels are set on it
    at the final size, then it gets its glow.
    """
    rules = look.rules.instructions
    scale: float = min(rules.icon_w / _DESIGN_W, rules.icon_h / _DESIGN_H)
    big: pygame.Surface = pygame.Surface(
        (rules.icon_w * _SUPERSAMPLE, rules.icon_h * _SUPERSAMPLE), pygame.SRCALPHA
    )
    canvas: _Canvas = _Canvas(
        big,
        scale * _SUPERSAMPLE,
        (
            (rules.icon_w * _SUPERSAMPLE - _DESIGN_W * scale * _SUPERSAMPLE) / 2,
            (rules.icon_h * _SUPERSAMPLE - _DESIGN_H * scale * _SUPERSAMPLE) / 2,
        ),
        look.palette,
    )
    labels: list[tuple[str, str, RGB, Point]] = _DRAWERS[index](canvas)
    small: pygame.Surface = pygame.transform.smoothscale(big, (rules.icon_w, rules.icon_h))
    for string, role, color, (x, y) in labels:
        center: tuple[int, int] = (
            round((canvas.offset[0] + x * canvas.scale) / _SUPERSAMPLE),
            round((canvas.offset[1] + y * canvas.scale) / _SUPERSAMPLE),
        )
        look.blit_text(small, string, role, color, {"center": center}, glow=False)
    glow = look.rules.glow
    return halo(small, glow.icon_radius, glow.icon_strength), 2 * glow.icon_radius


class _Canvas:
    """A supersampled surface with drawing in the 176 x 96 design space. Strokes are round."""

    def __init__(
        self,
        surface: pygame.Surface,
        scale: float,
        offset: Point,
        palette: Mapping[str, RGB],
    ) -> None:
        self.surface: pygame.Surface = surface
        self.scale: float = scale
        self.offset: Point = offset
        self.palette: Mapping[str, RGB] = palette
        self.key_color: str = "frame_lights"
        """The palette key the current icon's lines use. Set by each drawer."""

    def color(self, key: str) -> RGB:
        """Return the palette color ``key``."""
        return self.palette[key]

    def pt(self, x: float, y: float) -> tuple[float, float]:
        """Return the pixel of design point (x, y)."""
        return (self.offset[0] + x * self.scale, self.offset[1] + y * self.scale)

    def _layer(self, color: RGB, alpha: float) -> tuple[pygame.Surface, tuple[int, int, int, int]]:
        """Return the surface to draw on and the RGBA: a clear layer when translucent."""
        rgba: tuple[int, int, int, int] = (*color, round(255 * alpha))
        if alpha >= 1.0:
            return self.surface, rgba
        return pygame.Surface(self.surface.get_size(), pygame.SRCALPHA), rgba

    def _flush(self, layer: pygame.Surface) -> None:
        """Blend a translucent layer onto the canvas."""
        if layer is not self.surface:
            self.surface.blit(layer, (0, 0))

    def line(
        self,
        points: Sequence[Point],
        color: RGB,
        width: float = _STROKE,
        alpha: float = 1.0,
    ) -> None:
        """Draw a polyline through design ``points``, round at every end and joint."""
        layer, rgba = self._layer(color, alpha)
        pixels: list[tuple[float, float]] = [self.pt(x, y) for x, y in points]
        thick: int = max(round(width * self.scale), 1)
        for start, end in pairwise(pixels):
            pygame.draw.line(layer, rgba, start, end, thick)
        for pixel in pixels:
            pygame.draw.circle(layer, rgba, pixel, thick / 2)
        self._flush(layer)

    def dashed(
        self, points: Sequence[Point], color: RGB, width: float = _STROKE, alpha: float = 1.0
    ) -> None:
        """Draw a polyline as dashes, ``_DASH`` long with ``_DASH`` gaps, along ``points``."""
        layer, rgba = self._layer(color, alpha)
        thick: int = max(round(width * self.scale), 1)
        travelled: float = 0.0
        for (x0, y0), (x1, y1) in pairwise(points):
            length: float = math.hypot(x1 - x0, y1 - y0)
            pos: float = 0.0
            while pos < length:
                on: bool = int((travelled + pos) // _DASH) % 2 == 0
                step: float = min(_DASH - (travelled + pos) % _DASH, length - pos)
                if on:
                    a: float = pos / length
                    b: float = (pos + step) / length
                    pygame.draw.line(
                        layer,
                        rgba,
                        self.pt(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a),
                        self.pt(x0 + (x1 - x0) * b, y0 + (y1 - y0) * b),
                        thick,
                    )
                pos += step
            travelled += length
        self._flush(layer)

    def polygon(
        self,
        points: Sequence[Point],
        fill: RGB | None = None,
        outline: RGB | None = None,
        fill_alpha: float = 1.0,
        width: float = _STROKE,
    ) -> None:
        """Draw a closed polygon through design ``points``, filled and/or outlined."""
        if fill is not None:
            layer, rgba = self._layer(fill, fill_alpha)
            pygame.draw.polygon(layer, rgba, [self.pt(x, y) for x, y in points])
            self._flush(layer)
        if outline is not None:
            self.line([*points, points[0]], outline, width)

    def circle(
        self,
        center: Point,
        radius: float,
        fill: RGB | None = None,
        outline: RGB | None = None,
        width: float = _STROKE,
        alpha: float = 1.0,
    ) -> None:
        """Draw a circle at design ``center``, filled and/or outlined."""
        pixel: tuple[float, float] = self.pt(*center)
        thick: int = max(round(width * self.scale), 1)
        if fill is not None:
            layer, rgba = self._layer(fill, alpha)
            pygame.draw.circle(layer, rgba, pixel, radius * self.scale)
            self._flush(layer)
        if outline is not None:
            layer, rgba = self._layer(outline, alpha)
            pygame.draw.circle(layer, rgba, pixel, radius * self.scale, thick)
            self._flush(layer)

    def dashed_circle(self, center: Point, radius: float, color: RGB, alpha: float = 1.0) -> None:
        """Draw a circle of dashes."""
        steps: int = max(int(2 * math.pi * radius / 2), 12)
        points: list[Point] = [
            (
                center[0] + radius * math.cos(2 * math.pi * i / steps),
                center[1] + radius * math.sin(2 * math.pi * i / steps),
            )
            for i in range(steps + 1)
        ]
        self.dashed(points, color, alpha=alpha)

    def key(self, rect: tuple[float, float, float, float], hot: bool) -> None:
        """Draw a key cap, cyan: faint fill and border, a lit fill and border when ``hot``."""
        x, y, w, h = rect
        cyan: RGB = self.color("frame_lights")
        layer, rgba = self._layer(cyan, 0.32 if hot else 0.09)
        body: pygame.Rect = pygame.Rect(self.pt(x, y), (w * self.scale, h * self.scale))
        pygame.draw.rect(layer, rgba, body, border_radius=round(5 * self.scale))
        self._flush(layer)
        layer, rgba = self._layer(cyan, 1.0 if hot else 0.55)
        pygame.draw.rect(
            layer, rgba, body, max(round(1.4 * self.scale), 1), border_radius=round(5 * self.scale)
        )
        self._flush(layer)

    def arrow(self, center: Point, degrees: float) -> None:
        """Draw the arrow of a key cap at design ``center``, pointing up at 0, turned clockwise."""
        angle: float = math.radians(degrees)

        def turn(x: float, y: float) -> Point:
            return (
                center[0] + x * math.cos(angle) - y * math.sin(angle),
                center[1] + x * math.sin(angle) + y * math.cos(angle),
            )

        color: RGB = _lighten(self.color("frame_lights"), 0.1)
        self.line([turn(-5, 2), turn(0, -4), turn(5, 2)], color, 1.8)
        self.line([turn(0, -4), turn(0, 7)], color, 1.8)

    def ship(self, x: float, y: float, w: float, h: float) -> None:
        """Draw the ship: pale plating, a cyan outline and a cyan cockpit, in the box x, y, w, h."""
        points: list[Point] = [(x + px * w, y + py * h) for px, py in _SHIP]
        plating: RGB = _mix(self.color("plating"), self.color("panel_body"), 0.7)
        self.polygon(points, fill=plating, outline=self.color("frame_lights"), width=1.2)
        self.circle((x + 0.5 * w, y + 0.34 * h), 0.05 * w + 1.0, fill=self.color("frame_lights"))

    def heart(self, x: float, y: float, scale: float) -> None:
        """Draw a solid heart whose box starts at design (x, y); ``scale`` is against 24 units."""
        points: list[Point] = []
        for i in range(48):
            t: float = 2 * math.pi * i / 48
            hx: float = 16 * math.sin(t) ** 3
            hy: float = -(
                13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            )
            points.append(
                (x + (1 + (hx + 16) / 32 * 22) * scale, y + (4.5 + (hy + 12) / 29 * 16.5) * scale)
            )
        self.polygon(points, fill=self.color("hearts"))

    def star(self, x: float, y: float, arm: float) -> None:
        """Draw a four-point sparkle at design (x, y), ``arm`` units long, in the card's color."""
        inner: float = arm * 0.3
        points: list[Point] = [
            (x, y - arm),
            (x + inner, y - inner),
            (x + arm, y),
            (x + inner, y + inner),
            (x, y + arm),
            (x - inner, y + inner),
            (x - arm, y),
            (x - inner, y - inner),
        ]
        self.polygon(points, fill=self.color(self.key_color))


def _mix(a: RGB, b: RGB, share: float) -> RGB:
    """Return ``a`` mixed with ``b``: ``share`` of ``a``, the rest ``b``."""
    return (
        round(a[0] * share + b[0] * (1 - share)),
        round(a[1] * share + b[1] * (1 - share)),
        round(a[2] * share + b[2] * (1 - share)),
    )


def _lighten(color: RGB, share: float) -> RGB:
    """Return ``color`` with ``share`` of white mixed in."""
    return _mix((255, 255, 255), color, share)


type Label = tuple[str, str, RGB, Point]
"""A label set on an icon after it is scaled down: text, font role, color, design center."""


def _draw_fly(c: _Canvas) -> list[Label]:
    """FLY: the four arrow keys with up lit, the ship with a flame, a dashed curve with a head."""
    c.key_color = "frame_lights"
    k: RGB = c.color("frame_lights")
    for rect, degrees, hot in (
        ((30, 18, 26, 26), 0, True),
        ((2, 48, 26, 26), 270, False),
        ((30, 48, 26, 26), 180, False),
        ((58, 48, 26, 26), 90, False),
    ):
        c.key(rect, hot)
        c.arrow((rect[0] + 13, rect[1] + 13), degrees)
    c.ship(104, 22, 30, 40)
    warn: RGB = c.color("last_life")
    c.polygon([(114, 63), (119, 78), (124, 63)], fill=warn)
    c.polygon([(116, 63), (119, 72), (122, 63)], fill=(255, 255, 255), fill_alpha=0.85)
    c.dashed([_bezier((136, 30), (148, 6), (172, 10), (171, 52), i / 24) for i in range(25)], k)
    c.line([(166, 46), (171, 55), (176, 46)], k)
    return []


def _draw_pause(c: _Canvas) -> list[Label]:
    """PAUSE: the ENTER and SPACE keys, then a pause sign turning into a play sign."""
    k: RGB = c.color("ship_lines_light")
    c.key_color = "ship_lines_light"
    c.key((2, 14, 56, 26), True)
    c.key((2, 56, 56, 26), True)
    c.line([(62, 27), (70, 27), (70, 69), (62, 69)], k)
    c.line([(70, 48), (80, 48)], k)
    c.circle((100, 48), 17, outline=k)
    c.polygon([(94, 40), (98.5, 40), (98.5, 56), (94, 56)], fill=k)
    c.polygon([(102, 40), (106.5, 40), (106.5, 56), (102, 56)], fill=k)
    c.line([(120, 43), (132, 43)], k)
    c.line([(127, 38), (132, 43)], k)
    c.line([(132, 53), (120, 53)], k)
    c.line([(125, 58), (120, 53)], k)
    c.circle((152, 48), 17, outline=k)
    c.polygon([(148, 40), (160, 48), (148, 56)], fill=k)
    cyan: RGB = c.color("frame_lights")
    return [("ENTER", "key", cyan, (30, 27)), ("SPACE", "key", cyan, (30, 69))]


def _draw_graze(c: _Canvas) -> list[Label]:
    """GRAZE: a rock with a dashed ring round it, the ship skimming past, ``+25`` and a sparkle."""
    k: RGB = c.color("graze")
    c.key_color = "graze"
    light: RGB = c.color("ship_lines_light")
    c.dashed_circle((62, 48), 44, k, alpha=0.8)
    rock: list[Point] = [
        (40, 40),
        (50, 22),
        (72, 18),
        (90, 32),
        (92, 56),
        (76, 76),
        (48, 76),
        (36, 60),
    ]
    c.polygon(rock, fill=_mix(light, c.color("panel_body"), 0.22), outline=light)
    c.ship(100, 22, 27, 36)
    c.dashed([(113, 62), (113, 92)], k, alpha=0.7)
    c.star(150, 47, 7)
    return [("+25", "row", k, (146, 30))]


def _draw_warning(c: _Canvas) -> list[Label]:
    """WARNING: one plain warning sign, a triangle with a mark, and chevrons pointing down."""
    k: RGB = c.color("last_life")
    c.key_color = "last_life"
    c.dashed([(0, 6), (176, 6)], k, alpha=0.55)
    c.polygon([(88, 12), (108, 46), (68, 46)], fill=k, fill_alpha=0.26, outline=k)
    c.line([(88, 23), (88, 35)], k, 2.6)
    c.circle((88, 40.5), 1.9, fill=k)
    c.dashed([(70, 54), (70, 94)], k, alpha=0.6)
    c.dashed([(106, 54), (106, 94)], k, alpha=0.6)
    for top, alpha in ((62, 1.0), (73, 0.65), (84, 0.35)):
        c.line([(80, top), (88, top + 6), (96, top)], k, alpha=alpha)
    return []


def _draw_fall(c: _Canvas) -> list[Label]:
    """FALL: the ship over the floor line, an arrow down to a broken heart, ``-1``."""
    k: RGB = c.color("ship_lines")
    c.key_color = "ship_lines"
    for x, top, bottom in ((22, 6, 18), (36, 2, 16), (50, 6, 18)):
        c.line([(x, top), (x, bottom)], k, alpha=0.45)
    c.ship(20, 26, 32, 42)
    floor: RGB = c.color("panel_body")
    c.polygon([(0, 64), (176, 64), (176, 96), (0, 96)], fill=floor, fill_alpha=0.5)
    c.dashed([(0, 64), (176, 64)], k)
    c.line([(66, 46), (88, 46)], k)
    c.line([(82, 40), (88, 46), (82, 52)], k)
    c.heart(98, 26, 1.7)
    c.line([(118, 28), (112, 40), (120, 44), (113, 56)], floor, 3)
    return [("−1", "row", k, (150, 46))]


def _draw_coins(c: _Canvas) -> list[Label]:
    """COINS: a rock with coins near it, ``+50`` and a sparkle."""
    k: RGB = c.color("level")
    c.key_color = "level"
    light: RGB = c.color("ship_lines_light")
    rock: list[Point] = [(14, 48), (22, 30), (42, 24), (58, 38), (60, 60), (44, 76), (22, 72)]
    c.polygon(rock, fill=_mix(light, c.color("panel_body"), 0.22), outline=light)
    c.dashed_circle((38, 50), 40, light, alpha=0.45)
    body: RGB = _mix(k, c.color("panel_body"), 0.28)
    for center, outer, inner in (((86, 30), 13, 8.5), ((112, 58), 13, 8.5), ((78, 68), 10, 6)):
        c.circle(center, outer, fill=body, outline=k, width=1.8)
        c.circle(center, inner, outline=k, width=1.0, alpha=0.6)
    for cx, cy in ((86, 30), (112, 58)):
        c.polygon([(cx, cy - 6), (cx + 4, cy), (cx, cy + 6), (cx - 4, cy)], fill=k)
    c.star(154, 59, 6)
    return [("+50", "row", k, (146, 34))]


_DRAWERS: Final[tuple[Callable[[_Canvas], list[Label]], ...]] = (
    _draw_fly,
    _draw_pause,
    _draw_graze,
    _draw_warning,
    _draw_fall,
    _draw_coins,
)
"""Each card's icon drawer, in card order."""


def _bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """Return the point at ``t`` (0..1) on the cubic curve through the four control points."""
    u: float = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )
