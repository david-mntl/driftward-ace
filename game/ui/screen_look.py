"""The Glass Cockpit look every screen shares: glass panels, glowing text, key caps and choices.

Source: docs/contracts/systems/screens.md, Interface (`ScreenLook`); 10-ui.md, `screens_look`,
`ui_glow` and `ui_font`; 12-art-and-audio.md, Screen colors. Every color, size and strength comes
from ScreenRules (tuning/screens.json). Glow, panels and text are drawn once and kept: per frame the
views only blit them, and the one live cost is the blur of the picture behind a box. The views
take a ScreenLook and only draw. Imports pygame only.
"""

import logging
import math
from collections.abc import Mapping
from typing import Final

import pygame

from ui.screen_rules import RGB, ScreenRules

log = logging.getLogger(__name__)

ARROW_KEYS: Final[frozenset[str]] = frozenset({"UP", "DOWN", "LEFT", "RIGHT"})
"""Key cap labels drawn as an arrow, not as text. Mono fonts have no arrow glyphs to count on."""

PLAY_SIGN: Final[str] = "PLAY"
"""The word of a key row drawn as a small play triangle, as the pause hint's."""

_CACHE_LIMIT: Final[int] = 512
"""Most text pictures kept. The cache is cleared when it grows past this."""

_ARROW_ANGLES: Final[Mapping[str, int]] = {"UP": 0, "LEFT": 90, "DOWN": 180, "RIGHT": 270}
"""Rotation of the arrow picture, degrees counter-clockwise, from one that points up."""

type Anchor = Mapping[str, tuple[int, int]]
"""A pygame Rect anchor, one entry: ``{"center": (x, y)}``, ``{"midtop": (x, y)}`` and so on."""


class ScreenLook:
    """Draws the shared parts of every screen. Needs ``pygame.font`` and a display set."""

    def __init__(self, rules: ScreenRules, fonts: Mapping[str, pygame.font.Font]) -> None:
        self.rules: ScreenRules = rules
        self.palette: Mapping[str, RGB] = rules.palette
        self._fonts: Mapping[str, pygame.font.Font] = fonts
        self._spacing: Mapping[str, float] = {r.name: r.spacing for r in rules.fonts.roles}
        self._texts: dict[tuple[str, str, RGB, bool, int], tuple[pygame.Surface, int]] = {}
        self._sizes: dict[tuple[str, str], tuple[int, int]] = {}
        self._caps: dict[tuple[int, int], pygame.Surface] = {}
        self._panels: dict[tuple[int, int, RGB], tuple[pygame.Surface, int]] = {}
        self._fades: dict[tuple[int, int], pygame.Surface] = {}
        self._rulers: dict[tuple[int, int], pygame.Surface] = {}

    # ---- text -------------------------------------------------------------------------------

    def text_size(self, string: str, role: str) -> tuple[int, int]:
        """Return the width and height of ``string`` in ``role``, px, letter-spacing included."""
        key: tuple[str, str] = (string, role)
        found: tuple[int, int] | None = self._sizes.get(key)
        if found is None:
            font: pygame.font.Font = self._fonts[role]
            gap: int = self._gap(role)
            width: int = sum(font.size(char)[0] for char in string) + gap * max(len(string) - 1, 0)
            found = (width, font.get_height())
            if len(self._sizes) >= _CACHE_LIMIT:
                self._sizes.clear()
            self._sizes[key] = found
        return found

    def blit_text(
        self,
        surface: pygame.Surface,
        string: str,
        role: str,
        color: RGB,
        anchor: Anchor,
        glow: bool = True,
        alpha: int = 255,
    ) -> pygame.Rect:
        """Draw ``string`` and return its rect (the text alone, without the glow round it).

        ``anchor`` is one Rect anchor, such as ``{"center": (x, y)}``. ``glow`` puts the soft glow
        behind it. ``alpha`` (0..255) dims it.
        """
        image, pad = self._text(string, role, color, glow, alpha)
        core: pygame.Rect = pygame.Rect(
            (0, 0), (image.get_width() - 2 * pad, image.get_height() - 2 * pad)
        )
        for name, point in anchor.items():
            setattr(core, name, point)
        surface.blit(image, (core.left - pad, core.top - pad))
        return core

    def _text(
        self, string: str, role: str, color: RGB, glow: bool, alpha: int
    ) -> tuple[pygame.Surface, int]:
        """Return the picture of ``string`` and the margin the glow adds on every side, px."""
        key: tuple[str, str, RGB, bool, int] = (string, role, color, glow, alpha)
        found: tuple[pygame.Surface, int] | None = self._texts.get(key)
        if found is not None:
            return found
        if len(self._texts) >= _CACHE_LIMIT:
            self._texts.clear()
        flat: pygame.Surface = self._spaced(string, role, color)
        pad: int = 0
        if glow and self.rules.glow.text_strength > 0:
            radius: int = self.rules.glow.text_radius
            flat, pad = halo(flat, radius, self.rules.glow.text_strength), 2 * radius
        if alpha < 255:
            flat = flat.copy()
            flat.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        self._texts[key] = (flat, pad)
        return flat, pad

    def _spaced(self, string: str, role: str, color: RGB) -> pygame.Surface:
        """Render ``string`` one character at a time, the role's letter-spacing between them."""
        font: pygame.font.Font = self._fonts[role]
        width, height = self.text_size(string, role)
        image: pygame.Surface = pygame.Surface((max(width, 1), height), pygame.SRCALPHA)
        gap: int = self._gap(role)
        left: int = 0
        for char in string:
            if char != " ":
                image.blit(font.render(char, True, color), (left, 0))
            left += font.size(char)[0] + gap
        return image

    def _gap(self, role: str) -> int:
        """Return the px between two characters of ``role``: its spacing in em times its size."""
        return round(self._spacing[role] * self._fonts[role].get_height())

    # ---- panels -----------------------------------------------------------------------------

    def glass(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        blur: bool,
        color: RGB | None = None,
    ) -> None:
        """Draw a see-through glass panel over ``rect``: the blurred picture behind it, the dark
        fill with its scan lines, then the border, the four corner brackets and their glow.

        ``color`` is the border's and brackets' color, the palette's ``frame_lights`` when left
        out. ``blur`` is off for a screen whose background moves, to keep the frame rate.
        """
        if blur:
            self.blur_behind(surface, rect)
        line: RGB = color if color is not None else self.palette["frame_lights"]
        image, margin = self._panel(rect.width, rect.height, line)
        surface.blit(image, (rect.left - margin, rect.top - margin))

    def blur_behind(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Blur the part of ``surface`` inside ``rect``: made ``glass.blur_down`` times smaller and
        scaled back up. Does nothing when ``blur_down`` is 1."""
        factor: int = self.rules.glass.blur_down
        area: pygame.Rect = rect.clip(surface.get_rect())
        if factor <= 1 or area.width < 2 or area.height < 2:
            return
        small_size: tuple[int, int] = (max(area.width // factor, 1), max(area.height // factor, 1))
        small: pygame.Surface = pygame.transform.smoothscale(
            surface.subsurface(area).copy(), small_size
        )
        surface.blit(pygame.transform.smoothscale(small, area.size), area.topleft)

    def _panel(self, width: int, height: int, line: RGB) -> tuple[pygame.Surface, int]:
        """Return the baked panel picture and the margin it has round the rect, px."""
        key: tuple[int, int, RGB] = (width, height, line)
        found: tuple[pygame.Surface, int] | None = self._panels.get(key)
        if found is not None:
            return found
        glass, glow = self.rules.glass, self.rules.glow
        reach: int = 2 * glow.box_radius if glow.box_strength > 0 else 0
        margin: int = reach + glass.bracket_out + glass.bracket_w
        size: tuple[int, int] = (width + 2 * margin, height + 2 * margin)
        lines: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        body: pygame.Rect = pygame.Rect(margin, margin, width, height)
        pygame.draw.rect(lines, (*line, glass.border_alpha), body, glass.border_w)
        self._brackets(lines, body, line)
        picture: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        if glow.box_strength > 0:
            picture.blit(_blur(lines, glow.box_radius, glow.box_strength), (0, 0))
        fill: pygame.Surface = pygame.Surface(body.size, pygame.SRCALPHA)
        fill.fill((*self.palette["panel_body"], glass.fill_alpha))
        for row in range(0, height, glass.scan_pitch):
            fill.fill(
                (*line, glass.scan_alpha), pygame.Rect(0, row + glass.scan_pitch - 1, width, 1)
            )
        picture.blit(fill, body.topleft)
        picture.blit(lines, (0, 0))
        self._panels[key] = (picture, margin)
        return picture, margin

    def _brackets(self, image: pygame.Surface, body: pygame.Rect, line: RGB) -> None:
        """Draw the four corner brackets, ``bracket_out`` px outside ``body``'s edge."""
        glass = self.rules.glass
        out, length, thick = glass.bracket_out, glass.bracket_len, glass.bracket_w
        left, top = body.left - out, body.top - out
        right, bottom = body.right + out, body.bottom + out
        for x, step_x in ((left, 1), (right, -1)):
            for y, step_y in ((top, 1), (bottom, -1)):
                horizontal: pygame.Rect = pygame.Rect(0, 0, length, thick)
                vertical: pygame.Rect = pygame.Rect(0, 0, thick, length)
                horizontal.left = x if step_x > 0 else x - length
                horizontal.top = y if step_y > 0 else y - thick
                vertical.left = x if step_x > 0 else x - thick
                vertical.top = y if step_y > 0 else y - length
                image.fill(line, horizontal)
                image.fill(line, vertical)

    # ---- key caps ---------------------------------------------------------------------------

    def keycap_width(self, label: str) -> int:
        """Return the width of one key cap, px: its text and padding, at least ``min_w``."""
        caps = self.rules.keycap
        if label in ARROW_KEYS:
            return caps.min_w
        return max(caps.min_w, self.text_size(label, "key")[0] + 2 * caps.pad_x)

    def keys_size(self, keys: tuple[str, ...], word: str | None) -> tuple[int, int]:
        """Return the width and height of a row of key caps and the short word after them, px."""
        caps = self.rules.keycap
        width: int = sum(self.keycap_width(k) for k in keys) + caps.gap * (len(keys) - 1)
        if word is not None:
            width += caps.hint_gap + self._word_width(word)
        return width, caps.h

    def _word_width(self, word: str) -> int:
        """Return the width of the word after the key caps, px. The play sign is a triangle."""
        return self.rules.keycap.play_w if word == PLAY_SIGN else self.text_size(word, "hint")[0]

    def blit_keys(
        self,
        surface: pygame.Surface,
        keys: tuple[str, ...],
        word: str | None,
        anchor: Anchor,
        alpha: int = 255,
    ) -> pygame.Rect:
        """Draw a row of key caps and, after them, ``word`` in the hint font. Return its rect.

        A key named in ``ARROW_KEYS`` is drawn as an arrow, and ``PLAY_SIGN`` as a play triangle.
        """
        caps = self.rules.keycap
        row: pygame.Rect = pygame.Rect((0, 0), self.keys_size(keys, word))
        for name, point in anchor.items():
            setattr(row, name, point)
        left: int = row.left
        for label in keys:
            cap: pygame.Rect = pygame.Rect(left, row.top, self.keycap_width(label), caps.h)
            self._keycap(surface, label, cap, alpha)
            left = cap.right + caps.gap
        if word is not None:
            hint_left: int = left - caps.gap + caps.hint_gap
            plating: RGB = self.palette["plating"]
            if word == PLAY_SIGN:
                _play_triangle(
                    surface, (hint_left + caps.play_w // 2, row.centery), plating, caps.play_w
                )
            else:
                anchor_word: Anchor = {"midleft": (hint_left, row.centery)}
                self.blit_text(
                    surface, word, "hint", plating, anchor_word, False, min(alpha, caps.word_alpha)
                )
        return row

    def _keycap(self, surface: pygame.Surface, label: str, cap: pygame.Rect, alpha: int) -> None:
        """Draw one key cap: a faint cyan fill, a thin cyan border, the label in cyan."""
        cyan: RGB = self.palette["frame_lights"]
        surface.blit(self._cap_image(cap.size, alpha), cap.topleft)
        if label in ARROW_KEYS:
            self._blit_arrow(surface, label, cap.center, cyan)
        else:
            self.blit_text(
                surface, label, "key", cyan, {"center": cap.center}, glow=False, alpha=alpha
            )

    def _cap_image(self, size: tuple[int, int], alpha: int) -> pygame.Surface:
        """Return a key cap's body at ``size``, dimmed to ``alpha`` (0..255): drawn once, kept."""
        key: tuple[int, int] = (size[0], alpha)
        found: pygame.Surface | None = self._caps.get(key)
        if found is not None:
            return found
        caps = self.rules.keycap
        cyan: RGB = self.palette["frame_lights"]
        image: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        body: pygame.Rect = image.get_rect()
        pygame.draw.rect(image, (*cyan, caps.fill_alpha), body, border_radius=caps.radius)
        pygame.draw.rect(image, (*cyan, caps.border_alpha), body, 1, border_radius=caps.radius)
        if alpha < 255:
            image.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        self._caps[key] = image
        return image

    def _blit_arrow(
        self, surface: pygame.Surface, name: str, center: tuple[int, int], color: RGB
    ) -> None:
        """Draw a small solid triangle pointing ``name`` at ``center``."""
        size: int = self.rules.keycap.arrow_size
        up: list[tuple[int, int]] = [(0, -size), (size, size), (-size, size)]
        angle: float = math.radians(_ARROW_ANGLES[name])
        points: list[tuple[float, float]] = [
            (
                center[0] + x * math.cos(angle) + y * math.sin(angle),
                center[1] - x * math.sin(angle) + y * math.cos(angle),
            )
            for x, y in up
        ]
        pygame.draw.polygon(surface, color, points)

    # ---- choices ----------------------------------------------------------------------------

    def blit_choice(
        self,
        surface: pygame.Surface,
        label: str,
        rect: pygame.Rect,
        role: str,
        state: str,
    ) -> None:
        """Draw a choice (RETRY, MENU, a menu item) centered in ``rect``.

        ``state`` is ``selected`` (lit, framed by brackets over a cyan fade), ``dim`` (not
        selected) or ``off`` (can't be picked yet).
        """
        choice = self.rules.choice
        plating: RGB = self.palette["plating"]
        if state == "selected":
            surface.blit(self._fade(rect.width, rect.height), rect.topleft)
            cyan: RGB = self.palette["frame_lights"]
            for glyph, anchor in (
                ("[", {"midleft": (rect.left + choice.bracket_inset, rect.centery)}),
                ("]", {"midright": (rect.right - choice.bracket_inset, rect.centery)}),
            ):
                self.blit_text(surface, glyph, role, cyan, anchor)
            self.blit_text(surface, label, role, plating, {"center": rect.center})
            return
        alpha: int = choice.dim_alpha if state == "dim" else choice.off_alpha
        self.blit_text(
            surface, label, role, plating, {"center": rect.center}, glow=False, alpha=alpha
        )

    def _fade(self, width: int, height: int) -> pygame.Surface:
        """Return a selected choice's backdrop: cyan, clear at both ends, brightest mid-way."""
        key: tuple[int, int] = (width, height)
        found: pygame.Surface | None = self._fades.get(key)
        if found is not None:
            return found
        image: pygame.Surface = pygame.Surface(key, pygame.SRCALPHA)
        cyan: RGB = self.palette["frame_lights"]
        peak: int = self.rules.choice.fade_alpha
        for column in range(width):
            share: float = 1.0 - abs(2.0 * (column + 0.5) / width - 1.0)
            image.fill((*cyan, round(peak * share)), pygame.Rect(column, 0, 1, height))
        self._fades[key] = image
        return image

    # ---- page parts -------------------------------------------------------------------------

    def blit_rulers(self, surface: pygame.Surface) -> None:
        """Draw the tick marks down both sides of a full-window page, when ``rulers.enabled``."""
        rulers = self.rules.rulers
        if not rulers.enabled:
            return
        size: tuple[int, int] = surface.get_size()
        image: pygame.Surface | None = self._rulers.get(size)
        if image is None:
            image = self._build_rulers(size)
            self._rulers[size] = image
        surface.blit(image, (0, 0))

    def _build_rulers(self, size: tuple[int, int]) -> pygame.Surface:
        """Bake both rulers: short ticks, a long one every ``major_pitch``. Right mirrors left."""
        rulers = self.rules.rulers
        cyan: RGB = self.palette["frame_lights"]
        image: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        top: int = rulers.inset_y
        for offset in range(0, size[1] - 2 * rulers.inset_y, rulers.minor_pitch):
            major: bool = offset % rulers.major_pitch == 0
            length: int = rulers.w if major else rulers.minor_w
            color: tuple[int, int, int, int] = (
                *cyan,
                rulers.major_alpha if major else rulers.minor_alpha,
            )
            image.fill(color, pygame.Rect(rulers.inset_x, top + offset, length, 1))
            image.fill(
                color, pygame.Rect(size[0] - rulers.inset_x - length, top + offset, length, 1)
            )
        return image


def halo(image: pygame.Surface, radius: int, strength: float) -> pygame.Surface:
    """Return ``image`` with a soft glow of its own colors behind it, on a surface ``2 * radius``
    larger on every side. ``strength`` is 0..1. Needs a per-pixel alpha surface.
    """
    pad: int = 2 * radius
    width, height = image.get_size()
    base: pygame.Surface = pygame.Surface((width + 2 * pad, height + 2 * pad), pygame.SRCALPHA)
    base.blit(image, (pad, pad))
    glow: pygame.Surface = _blur(base, radius, strength)
    glow.blit(base, (0, 0))
    return glow


def _blur(image: pygame.Surface, radius: int, strength: float) -> pygame.Surface:
    """Return a blurred copy of ``image``, its alpha scaled by ``strength``: made smaller by about
    ``radius`` and scaled back up, twice for a softer edge."""
    factor: int = max(radius // 2, 1)
    width, height = image.get_size()
    blurred: pygame.Surface = image
    for divisor in (factor, factor * 2):
        small: tuple[int, int] = (max(width // divisor, 1), max(height // divisor, 1))
        blurred = pygame.transform.smoothscale(
            pygame.transform.smoothscale(blurred, small), (width, height)
        )
    out: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA)
    out.blit(blurred, (0, 0))
    out.blit(blurred, (0, 0))
    out.fill((255, 255, 255, round(255 * strength)), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _play_triangle(
    surface: pygame.Surface, center: tuple[int, int], color: RGB, width: int
) -> None:
    """Draw a small solid triangle ``width`` px wide pointing right, centered on ``center``."""
    x, y = center
    half: int = width // 2
    pygame.draw.polygon(surface, color, [(x - half, y - 4), (x + half, y), (x - half, y + 4)])
