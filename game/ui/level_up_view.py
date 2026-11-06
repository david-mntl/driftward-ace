"""The level-up banner on the play area, the number's flight over the window and the picture
bump's offset.

Source: docs/contracts/systems/level-up/view.md, Interface and Presentation; rationale.md,
"Everything is drawn from images made once" and "Draw order: behind the world, flight over it".
The view only draws. It never changes the banner, the run or the HUD, and never reads a key or
the run mode. Every picture (digits with gradient and outline, poses, glint frames, LEVEL by
spacing, pips, ring frames, streaks) is made once in ``__init__``. Per frame the view blits
pre-made images, picks one by age, sets a surface alpha and fills rects: no font render, scale,
rotate or new surface.
"""

import logging
import math
from dataclasses import dataclass

import pygame

from core.level_up import LevelUpBanner
from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.world import SCREEN_H, SCREEN_W
from ui.hud import HudView, LevelSlot, Tiles, _ink_tiles
from ui.level_up_motion import (
    band_shares,
    bump_offset,
    fade_share,
    fall_offset,
    fly_position,
    fly_share,
    pose_scales,
)
from ui.level_up_rules import RGB, LevelUpLook

log = logging.getLogger(__name__)

type Point = tuple[int, int]

LABEL_WORD: str = "LEVEL"
"""The word over the number. A fixed word of the HUD and the banner, not a tuning value.
Source: 10-ui.md, `hud_level`; level-up/rationale.md (no schema field for the text)."""

WHITE: RGB = (255, 255, 255)
"""The color a glyph is rendered in before it is tinted. Not a look value."""

FULL_ALPHA: int = 255
"""Opaque, for a surface alpha or a fill."""


@dataclass(frozen=True)
class LevelUpFonts:
    """The two fonts of the banner, loaded by app.assets."""

    number: pygame.font.Font
    """Exo 2 Bold at ``look.number.font_size``."""
    label: pygame.font.Font
    """Share Tech Mono at ``look.label.font_size``."""


@dataclass(frozen=True, slots=True)
class _Glass:
    """The two fills that blend the glass: ``dst * (1 - a) + glass * a``."""

    multiply: RGB
    """Multiply fill, ``255 - alpha`` in every channel."""
    add: RGB
    """Add fill, the glass color times ``alpha / 255``."""


@dataclass(frozen=True, slots=True)
class _Number:
    """Every picture of one level's number, centered on its resting place."""

    fall: pygame.Surface
    """The stretched pose it falls in."""
    poses: tuple[pygame.Surface, ...]
    """Landing squash to 1x, ``pose_steps + 1`` images; the last is the plain number."""
    pose_scales: tuple[tuple[float, float], ...]
    """The (scale x, scale y) of each pose."""
    glints: tuple[pygame.Surface, ...]
    """The 1x number with the glint at each of ``glint.frames`` positions."""
    drop_px: float
    """Px from its resting center to fully above the play area, in the falling pose."""


@dataclass(frozen=True, slots=True)
class _Streak:
    """One light streak: its image, the image point of its inner end and its direction."""

    image: pygame.Surface
    anchor: Point
    direction: tuple[float, float]


@dataclass(frozen=True, slots=True)
class _PipImages:
    """The diamonds' pictures by ticks since a pip starts to appear; the last is the rest image."""

    lit: tuple[pygame.Surface, ...]
    unlit: tuple[pygame.Surface, ...]
    flash: tuple[pygame.Surface, ...]
    """The new level's pip: white fading to the lit color."""


@dataclass(frozen=True, slots=True)
class _Flight:
    """The number's flight for one level: its pre-rendered sizes and where it lands."""

    frames: tuple[pygame.Surface, ...]
    """``fly.steps`` images, first the resting number, last the HUD number's arrival size, each
    tinted further toward the tier color."""
    end: Point
    """Window px: the center of the HUD's level number."""


class LevelUpView:
    """Draws the level-up banner on the play area and the number's flight over the window, both
    from the banner's age. Needs ``pygame.font`` initialized and a display set.
    """

    def __init__(
        self, look: LevelUpLook, fonts: LevelUpFonts, hud: HudView, field_origin: tuple[int, int]
    ) -> None:
        """Build every image once, for every level the banner can show (``FIRST_LEVEL + 1`` to
        ``LEVEL_COUNT``). ``field_origin`` is the play area's top-left in the window and ``hud``
        gives the flight's end; both are used here to build the flight's start, end and sizes.
        """
        self._look: LevelUpLook = look
        self._band_center: Point = (SCREEN_W // 2, SCREEN_H // 2 + look.band.center_offset_y)
        self._number_center: Point = (
            self._band_center[0],
            self._band_center[1] + look.number.center_offset_y,
        )
        self._glass: _Glass | None = _glass_fills(look)
        self._numbers: dict[int, _Number] = {
            level: _build_number(level, fonts, look, self._number_center[1])
            for level in range(FIRST_LEVEL + 1, LEVEL_COUNT + 1)
        }
        self._flight_start: Point = (
            field_origin[0] + self._number_center[0],
            field_origin[1] + self._number_center[1],
        )
        self._flights: dict[int, _Flight] = {
            level: _build_flight(
                self._numbers[level],
                hud.level_slot(level),
                hud._pop_frames[level][0].get_bounding_rect(),
                look,
            )
            for level in self._numbers
        }
        self._label: tuple[pygame.Surface, ...] = _label_images(fonts.label, look)
        self._pips: _PipImages = _pip_images(look)
        self._pip_starts: tuple[int, ...] = _pip_starts(look)
        self._pip_centers: tuple[Point, ...] = _pip_centers(look, self._band_center)
        self._ring: tuple[Tiles, ...] = _ring_frames(look)
        self._streaks: tuple[_Streak, ...] = _streaks(look)

    def draw_banner(self, field: pygame.Surface, banner: LevelUpBanner | None) -> None:
        """Draw on ``field`` everything the banner has there at ``banner.age_ticks``: glass,
        hairlines, ring, streaks, LEVEL, pips and the number (up to ``fly.start``), in that order.
        Draws nothing for None and nothing outside ``field``.
        """
        if banner is None:
            return
        age: int = banner.age_ticks
        glass_share, line_share = band_shares(age, self._look.band)
        height: int = round(self._look.band.height * glass_share)
        self._draw_glass(field, height)
        self._draw_hairlines(field, height, line_share)
        self._draw_ring(field, age)
        self._draw_streaks(field, age)
        self._draw_label(field, age)
        self._draw_pips(field, age, banner.level)
        self._draw_number(field, age, banner.level)

    def draw_flight(self, window: pygame.Surface, banner: LevelUpBanner | None) -> None:
        """Draw on ``window``, over everything drawn so far, the number flying from its resting
        place to the HUD's level number: from ``fly.start`` up to, not including, the banner's
        ``arrival_ticks``. Draws nothing for None or any other age.

        The path is ``fly_position`` with ``fly.arc_px``. Its progress is ``fly_share`` ending on
        the last drawn age (``arrival_ticks - 1``), so the last image sits on the HUD number's
        place and the HUD's pop takes over on the next tick with no jump. The image is the
        pre-made size nearest to that progress.
        """
        if banner is None or not self._look.fly.start <= banner.age_ticks < banner.arrival_ticks:
            return
        fly = self._look.fly
        flight: _Flight = self._flights[banner.level]
        share: float = fly_share(banner.age_ticks, fly, banner.arrival_ticks - 1)
        x, y = fly_position(share, self._flight_start, flight.end, fly.arc_px)
        frame: pygame.Surface = flight.frames[round(share * (len(flight.frames) - 1))]
        window.blit(frame, frame.get_rect(center=(round(x), round(y))))

    def bump_offset(self, banner: LevelUpBanner | None) -> int:
        """Return whole px the play area's picture moves down: 0 for None, else the curve at the
        banner's age.
        """
        if banner is None:
            return 0
        return bump_offset(banner.age_ticks, self._look.number, self._look.bump)

    # ----- band -----

    def _draw_glass(self, field: pygame.Surface, height: int) -> None:
        """Blend the glass over the band's ``height`` rows, centered on the band's center. Two
        fills on those rows only; nothing when there is no glass or no height.
        """
        if self._glass is None or height <= 0:
            return
        rect: pygame.Rect = pygame.Rect(0, self._band_center[1] - height // 2, SCREEN_W, height)
        field.fill(self._glass.multiply, rect, pygame.BLEND_RGB_MULT)
        field.fill(self._glass.add, rect, pygame.BLEND_RGB_ADD)

    def _draw_hairlines(self, field: pygame.Surface, height: int, line_share: float) -> None:
        """Draw the two hairlines on the glass's edges, from the center out by ``line_share`` of
        the half width, each end with a tick pointing inward. With no height both sit on one row.
        """
        band = self._look.band
        reach: int = round(line_share * SCREEN_W / 2)
        if reach <= 0:
            return
        width: int = band.hairline_width
        top: int = self._band_center[1] - height // 2
        bottom: int = max(top, top + height - width)
        tick: int = min(band.corner_tick_length, height // 2)
        left: int = SCREEN_W // 2 - reach
        right: int = SCREEN_W // 2 + reach - width
        color: RGB = self._look.colors["hairline"]
        field.fill(color, pygame.Rect(left, top, 2 * reach, width))
        field.fill(color, pygame.Rect(left, bottom, 2 * reach, width))
        if tick <= 0:
            return
        for x in (left, right):
            field.fill(color, pygame.Rect(x, top, width, tick))
            field.fill(color, pygame.Rect(x, top + height - tick, width, tick))

    # ----- landing effects -----

    def _draw_ring(self, field: pygame.Surface, age: int) -> None:
        """Blit the ring's tiles for the state ``age`` is on, from the landing tick."""
        state: int = age - self._look.number.fall_end
        if not 0 <= state < len(self._ring):
            return
        cx, cy = self._number_center
        for tile, (dx, dy) in self._ring[state]:
            field.blit(tile, (cx + dx, cy + dy))

    def _draw_streaks(self, field: pygame.Surface, age: int) -> None:
        """Blit the streaks for the state ``age`` is on, flying out and fading, from landing."""
        streaks = self._look.streaks
        state: int = age - self._look.number.fall_end
        if not 0 <= state < streaks.ticks:
            return
        radius: float = streaks.start_radius + (streaks.end_radius - streaks.start_radius) * (
            _state_share(state, streaks.ticks)
        )
        alpha: int = round(FULL_ALPHA * (1.0 - state / streaks.ticks))
        cx, cy = self._number_center
        for streak in self._streaks:
            streak.image.set_alpha(alpha)
            field.blit(
                streak.image,
                (
                    round(cx + streak.direction[0] * radius) - streak.anchor[0],
                    round(cy + streak.direction[1] * radius) - streak.anchor[1],
                ),
            )

    # ----- label and pips -----

    def _hold_opacity(self, age: int) -> float:
        """Return how visible the label and the pips are after their fade out, 1 down to 0."""
        hold = self._look.hold
        return 1.0 - fade_share(age, hold.fade_out_start, hold.fade_out_end)

    def _draw_label(self, field: pygame.Surface, age: int) -> None:
        """Draw LEVEL fading in as its letter spacing closes, then fading out with the pips."""
        label = self._look.label
        fade_in: float = fade_share(age, label.fade_in_start, label.fade_in_end)
        alpha: int = round(FULL_ALPHA * fade_in * self._hold_opacity(age))
        if alpha <= 0:
            return
        image: pygame.Surface = self._label[round(fade_in * label.spacing_steps)]
        image.set_alpha(alpha)
        center: Point = (self._band_center[0], self._band_center[1] + label.offset_y)
        field.blit(image, image.get_rect(center=center))

    def _draw_pips(self, field: pygame.Surface, age: int, level: int) -> None:
        """Draw the pip row: each pip pops in left to right, up to ``level`` lit, the new level's
        pip flashing. The row fades out with LEVEL.
        """
        alpha: int = round(FULL_ALPHA * self._hold_opacity(age))
        if alpha <= 0:
            return
        for index, (start, center) in enumerate(
            zip(self._pip_starts, self._pip_centers, strict=True)
        ):
            elapsed: int = age - start
            if elapsed < 0:
                return
            image: pygame.Surface = self._pip_image(index, level, elapsed)
            image.set_alpha(alpha)
            field.blit(image, image.get_rect(center=center))

    def _pip_image(self, index: int, level: int, elapsed: int) -> pygame.Surface:
        """Return pip ``index``'s picture ``elapsed`` ticks after it starts to appear."""
        if index == level - 1:
            frames: tuple[pygame.Surface, ...] = self._pips.flash
        else:
            frames = self._pips.lit if index < level else self._pips.unlit
        return frames[min(elapsed, len(frames) - 1)]

    # ----- number -----

    def _draw_number(self, field: pygame.Surface, age: int, level: int) -> None:
        """Draw the number at its place on the fall, until the flight takes it off the field."""
        if age >= self._look.fly.start:
            return
        number: _Number = self._numbers[level]
        cy: float = self._number_center[1] + fall_offset(age, self._look.number, number.drop_px)
        image: pygame.Surface = self._number_image(number, age)
        field.blit(image, image.get_rect(center=(self._number_center[0], round(cy))))

    def _number_image(self, number: _Number, age: int) -> pygame.Surface:
        """Return the number's picture at ``age``: the stretched fall pose, then the nearest
        squash pose, then the glint frame while the glint crosses a settled number.
        """
        if age < self._look.number.fall_end:
            return number.fall
        scale: tuple[float, float] = pose_scales(age, self._look.number)
        index: int = _nearest(number.pose_scales, scale)
        glint = self._look.glint
        if index == len(number.poses) - 1 and glint.start <= age < glint.end:
            share: float = fade_share(age, glint.start, glint.end)
            return number.glints[min(glint.frames - 1, int(share * glint.frames))]
        return number.poses[index]


# ----- builders: run once, in __init__ -----


def _mix_rgb(first: RGB, second: RGB, share: float) -> RGB:
    """Return ``first`` moved ``share`` (0..1) of the way to ``second``."""
    return (
        round(first[0] + (second[0] - first[0]) * share),
        round(first[1] + (second[1] - first[1]) * share),
        round(first[2] + (second[2] - first[2]) * share),
    )


def _state_share(state: int, states: int) -> float:
    """Return where state ``state`` of ``states`` sits, 0 on the first and 1 on the last."""
    return state / (states - 1) if states > 1 else 0.0


def _glass_fills(look: LevelUpLook) -> _Glass | None:
    """Return the glass's two fills, or None when ``band.alpha`` is 0 (no glass).

    ``dst * (1 - a) + glass * a`` is exact as one multiply by ``255 - alpha`` and one add of
    ``glass * alpha / 255``.
    """
    alpha: int = look.band.alpha
    if alpha == 0:
        return None
    glass: RGB = look.colors["glass"]
    return _Glass(
        multiply=(FULL_ALPHA - alpha,) * 3,
        add=(
            round(glass[0] * alpha / FULL_ALPHA),
            round(glass[1] * alpha / FULL_ALPHA),
            round(glass[2] * alpha / FULL_ALPHA),
        ),
    )


def _build_number(level: int, fonts: LevelUpFonts, look: LevelUpLook, center_y: int) -> _Number:
    """Make every picture of ``level``'s number: the fall pose, the squash poses and the glint.
    ``center_y`` is the number's resting center row in the field.
    """
    base, fill_alpha = _digit_image(str(level), fonts.number, look)
    number = look.number
    steps: int = number.pose_steps
    scales: tuple[tuple[float, float], ...] = tuple(
        (
            number.squash_x + (1.0 - number.squash_x) * step / steps,
            number.squash_y + (1.0 - number.squash_y) * step / steps,
        )
        for step in range(steps + 1)
    )
    poses: tuple[pygame.Surface, ...] = tuple(_scaled(base, sx, sy) for sx, sy in scales)
    fall: pygame.Surface = _scaled(base, number.fall_stretch_x, number.fall_stretch_y)
    return _Number(
        fall=fall,
        poses=poses,
        pose_scales=scales,
        glints=tuple(
            _glint_frame(poses[-1], fill_alpha, frame, look) for frame in range(look.glint.frames)
        ),
        drop_px=center_y + (fall.get_height() + 1) // 2,
    )


def _build_flight(
    number: _Number, slot: LevelSlot, pop_ink: pygame.Rect, look: LevelUpLook
) -> _Flight:
    """Make the flight's ``fly.steps`` images of one level's number.

    Step ``k`` is the resting number tinted ``k / (steps - 1)`` of the way to the HUD's tier color
    and sized that share of the way from its own size to the HUD number's arrival size: the
    slot's size times ``pop.start_scale``, rounded as the HUD rounds its first pop frame. The
    visible digit moves the same share from the resting image's ink rect to ``pop_ink``, the ink
    rect of the HUD's first pop frame, so the last step lands the digit where the pop draws it.
    """
    resting: pygame.Surface = number.poses[-1]
    resting_ink: pygame.Rect = resting.get_bounding_rect()
    arrival: Point = (
        max(1, round(slot.size[0] * look.pop.start_scale)),
        max(1, round(slot.size[1] * look.pop.start_scale)),
    )
    shares: tuple[float, ...] = tuple(
        _state_share(k, look.fly.steps) for k in range(look.fly.steps)
    )
    return _Flight(
        frames=tuple(
            _flight_frame(
                resting,
                resting_ink,
                _mix_size(resting.get_size(), arrival, share),
                _mix_rect(resting_ink, pop_ink, share),
                (slot.color, share),
            )
            for share in shares
        ),
        end=slot.center,
    )


def _mix_size(first: Point, second: Point, share: float) -> Point:
    """Return ``first`` moved ``share`` (0..1) of the way to ``second``, rounded to whole px."""
    return (
        round(first[0] + (second[0] - first[0]) * share),
        round(first[1] + (second[1] - first[1]) * share),
    )


def _mix_rect(first: pygame.Rect, second: pygame.Rect, share: float) -> pygame.Rect:
    """Return ``first`` moved ``share`` (0..1) of the way to ``second``: position and size, each
    rounded to whole px.
    """
    return pygame.Rect(
        round(first.x + (second.x - first.x) * share),
        round(first.y + (second.y - first.y) * share),
        round(first.w + (second.w - first.w) * share),
        round(first.h + (second.h - first.h) * share),
    )


def _flight_frame(
    number: pygame.Surface,
    number_ink: pygame.Rect,
    size: Point,
    ink: pygame.Rect,
    tint: tuple[RGB, float],
) -> pygame.Surface:
    """Return ``number`` mixed ``share`` of the way to the tier color (``tint`` is the tier color
    and ``share``; every color, outline included) in an image of exactly ``size``.

    The number's visible part, ``number_ink``, is scaled evenly to fit ``ink`` (never stretched)
    and centered on it, on a transparent canvas.
    """
    tier, share = tint
    image: pygame.Surface = number.copy()
    image.fill((round(FULL_ALPHA * (1.0 - share)),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    image.fill(
        tuple(round(channel * share) for channel in tier), special_flags=pygame.BLEND_RGB_ADD
    )
    if image.get_size() == size and number_ink == ink:
        return image
    scale: float = min(ink.w / number_ink.w, ink.h / number_ink.h)
    fitted: pygame.Surface = _scaled(image.subsurface(number_ink), scale, scale)
    canvas: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
    canvas.blit(fitted, fitted.get_rect(center=ink.center))
    return canvas


def _digit_image(
    text: str, font: pygame.font.Font, look: LevelUpLook
) -> tuple[pygame.Surface, pygame.Surface]:
    """Return ``text`` with a top to bottom gradient and an outline, cropped to its ink, and a
    white image of the same size whose alpha is the glyph's fill only (no outline).
    """
    glyph: pygame.Surface = font.render(text, True, WHITE)
    glyph = glyph.subsurface(glyph.get_bounding_rect()).copy()
    width: int = look.number.outline_width
    colors = look.colors
    size: Point = glyph.get_size()
    canvas: pygame.Surface = pygame.Surface(
        (size[0] + 2 * width, size[1] + 2 * width), pygame.SRCALPHA
    )
    outline: pygame.Surface = glyph.copy()
    outline.fill((*colors["number_outline"], FULL_ALPHA), special_flags=pygame.BLEND_RGBA_MULT)
    if width > 0:
        for dx, dy in _disc(width):
            canvas.blit(outline, (width + dx, width + dy))
    fill: pygame.Surface = _gradient(size, colors["number_top"], colors["number_bottom"])
    fill.blit(glyph, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    canvas.blit(fill, (width, width))
    fill_alpha: pygame.Surface = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    fill_alpha.blit(glyph, (width, width))
    return canvas, fill_alpha


def _disc(radius: int) -> list[Point]:
    """Return every whole offset within ``radius`` px of the origin."""
    return [
        (dx, dy)
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
        if dx * dx + dy * dy <= radius * radius
    ]


def _gradient(size: Point, top: RGB, bottom: RGB) -> pygame.Surface:
    """Return an opaque image of ``size`` fading from ``top`` at its first row to ``bottom``."""
    image: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
    for row in range(size[1]):
        color: RGB = _mix_rgb(top, bottom, row / max(1, size[1] - 1))
        image.fill(color, pygame.Rect(0, row, size[0], 1))
    return image


def _scaled(image: pygame.Surface, scale_x: float, scale_y: float) -> pygame.Surface:
    """Return ``image`` scaled by the two factors, at least 1 px each way; ``image`` itself when
    the size is unchanged.
    """
    size: Point = (
        max(1, round(image.get_width() * scale_x)),
        max(1, round(image.get_height() * scale_y)),
    )
    if size == image.get_size():
        return image
    return pygame.transform.smoothscale(image, size)


def _nearest(scales: tuple[tuple[float, float], ...], wanted: tuple[float, float]) -> int:
    """Return the index of the pose whose scales are closest to ``wanted``."""
    best: int = 0
    best_gap: float = math.inf
    for index, (scale_x, scale_y) in enumerate(scales):
        gap: float = (scale_x - wanted[0]) ** 2 + (scale_y - wanted[1]) ** 2
        if gap < best_gap:
            best, best_gap = index, gap
    return best


def _glint_frame(
    number: pygame.Surface, fill_alpha: pygame.Surface, frame: int, look: LevelUpLook
) -> pygame.Surface:
    """Return ``number`` with the glint band at position ``frame`` of ``glint.frames``.

    The band is a slanted stripe that crosses the number from left to right. It tints only the
    glyph's fill pixels (``fill_alpha``, the same size as ``number``), never the outline, by
    ``glint.strength``.
    """
    glint = look.glint
    width, height = number.get_size()
    lean: float = math.tan(math.radians(glint.slant_degrees)) * height / 2
    reach: float = glint.width / 2 + lean
    center: float = -reach + (width + 2 * reach) * (frame + 0.5) / glint.frames
    half: float = glint.width / 2
    mask: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA)
    mask.fill((*WHITE, 0))
    pygame.draw.polygon(
        mask,
        (*WHITE, round(FULL_ALPHA * glint.strength)),
        [
            (center + lean - half, 0),
            (center + lean + half, 0),
            (center - lean + half, height),
            (center - lean - half, height),
        ],
    )
    tint: pygame.Surface = fill_alpha.copy()
    tint.fill((0, 0, 0, FULL_ALPHA), special_flags=pygame.BLEND_RGBA_MULT)
    tint.fill((*look.colors["glint"], 0), special_flags=pygame.BLEND_RGBA_ADD)
    tint.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    frame_image: pygame.Surface = number.copy()
    frame_image.blit(tint, (0, 0))
    return frame_image


def _spaced_word(glyphs: list[pygame.Surface], spacing: int) -> pygame.Surface:
    """Return the rendered letters side by side, ``spacing`` px between each pair."""
    width: int = sum(glyph.get_width() for glyph in glyphs) + spacing * (len(glyphs) - 1)
    image: pygame.Surface = pygame.Surface(
        (width, max(glyph.get_height() for glyph in glyphs)), pygame.SRCALPHA
    )
    left: int = 0
    for glyph in glyphs:
        image.blit(glyph, (left, 0))
        left += glyph.get_width() + spacing
    return image


def _label_images(font: pygame.font.Font, look: LevelUpLook) -> tuple[pygame.Surface, ...]:
    """Return LEVEL at ``spacing_steps + 1`` letter spacings, from ``spacing_wide`` (index 0) to
    ``spacing_normal`` (the last).
    """
    label = look.label
    glyphs: list[pygame.Surface] = [
        font.render(char, True, look.colors["label"]) for char in LABEL_WORD
    ]
    return tuple(
        _spaced_word(
            glyphs,
            round(
                label.spacing_wide
                + (label.spacing_normal - label.spacing_wide) * step / label.spacing_steps
            ),
        )
        for step in range(label.spacing_steps + 1)
    )


def _diamond(size: int, color: RGB) -> pygame.Surface:
    """Return a filled diamond ``size`` px across, at least 1 px."""
    side: int = max(1, size)
    image: pygame.Surface = pygame.Surface((side, side), pygame.SRCALPHA)
    last: float = side - 1
    pygame.draw.polygon(
        image,
        color,
        [(last / 2, 0), (last, last / 2), (last / 2, last), (0, last / 2)],
    )
    return image


def _pip_frames(look: LevelUpLook, colors: list[RGB]) -> tuple[pygame.Surface, ...]:
    """Return one diamond per color: growing from nothing to ``pips.size`` over ``pop_ticks``."""
    pips = look.pips
    return tuple(
        _diamond(round(pips.size * min(1.0, (elapsed + 1) / pips.pop_ticks)), color)
        for elapsed, color in enumerate(colors)
    )


def _pip_images(look: LevelUpLook) -> _PipImages:
    """Make the lit, unlit and flashing pip pictures, indexed by ticks since the pip appears."""
    pips = look.pips
    lit: RGB = look.colors["pip_lit"]
    flash_count: int = max(pips.pop_ticks, pips.flash_ticks) + 1
    return _PipImages(
        lit=_pip_frames(look, [lit] * pips.pop_ticks),
        unlit=_pip_frames(look, [look.colors["pip_unlit"]] * pips.pop_ticks),
        flash=_pip_frames(
            look,
            [
                _mix_rgb(look.colors["flash"], lit, min(1.0, elapsed / pips.flash_ticks))
                for elapsed in range(flash_count)
            ],
        ),
    )


def _pip_starts(look: LevelUpLook) -> tuple[int, ...]:
    """Return the age each pip starts to appear: the first at ``pips.start``, the last fully in at
    ``pips.end``, the others spread evenly.
    """
    pips = look.pips
    span: int = pips.end - pips.pop_ticks - pips.start
    return tuple(
        pips.start + round(index * span / (LEVEL_COUNT - 1)) for index in range(LEVEL_COUNT)
    )


def _pip_centers(look: LevelUpLook, band_center: Point) -> tuple[Point, ...]:
    """Return each pip's center: a row on the band's center column, ``pitch`` apart."""
    pips = look.pips
    return tuple(
        (
            band_center[0] + round((index - (LEVEL_COUNT - 1) / 2) * pips.pitch),
            band_center[1] + pips.offset_y,
        )
        for index in range(LEVEL_COUNT)
    )


def _ring_frames(look: LevelUpLook) -> tuple[Tiles, ...]:
    """Return one set of ink tiles per ring state, offsets from the ring's center.

    The diameter grows from ``start_diameter`` to ``end_diameter`` and the alpha is baked in, so
    drawing is blits only.
    """
    ring = look.ring
    frames: list[Tiles] = []
    for state in range(ring.ticks):
        diameter: float = ring.start_diameter + (ring.end_diameter - ring.start_diameter) * (
            _state_share(state, ring.ticks)
        )
        alpha: int = round(FULL_ALPHA * (1.0 - state / ring.ticks))
        half: int = math.ceil(diameter / 2) + ring.width
        image: pygame.Surface = pygame.Surface((2 * half, 2 * half), pygame.SRCALPHA)
        pygame.draw.circle(
            image, (*look.colors["ring"], alpha), (half, half), round(diameter / 2), ring.width
        )
        frames.append(tuple((tile, (dx - half, dy - half)) for tile, (dx, dy) in _ink_tiles(image)))
    return tuple(frames)


def _streaks(look: LevelUpLook) -> tuple[_Streak, ...]:
    """Return one streak image per angle, evenly spread around the circle."""
    streaks = look.streaks
    return tuple(
        _streak(look, 2.0 * math.pi * index / streaks.count) for index in range(streaks.count)
    )


def _streak(look: LevelUpLook, angle: float) -> _Streak:
    """Make a streak pointing along ``angle`` (radians): its image and its inner end's point."""
    streaks = look.streaks
    direction: tuple[float, float] = (math.cos(angle), math.sin(angle))
    run: tuple[float, float] = (direction[0] * streaks.length, direction[1] * streaks.length)
    pad: int = streaks.width + 1
    image: pygame.Surface = pygame.Surface(
        (math.ceil(abs(run[0])) + 2 * pad, math.ceil(abs(run[1])) + 2 * pad), pygame.SRCALPHA
    )
    start: tuple[float, float] = (
        pad + (0.0 if run[0] >= 0 else -run[0]),
        pad + (0.0 if run[1] >= 0 else -run[1]),
    )
    pygame.draw.line(
        image,
        look.colors["streak"],
        start,
        (start[0] + run[0], start[1] + run[1]),
        streaks.width,
    )
    return _Streak(image=image, anchor=(round(start[0]), round(start[1])), direction=direction)
