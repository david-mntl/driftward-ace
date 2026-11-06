"""HUD: the side panel and the cockpit frame, drawn round the play area.

Source: docs/contracts/systems/hud.md, Interface, Presentation and Rules; 10-ui.md, `hud_*` and
`cockpit_frame`. The view only draws. It never fills, flips, logs per frame, catches an error,
changes the run, or reads the run mode or a key. Everything baked (panel, wireframe, hearts, radar,
ring, frame) is a picture made ahead of time by tools/art/hud_panel.py; per frame only values
change.
"""

import itertools
import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import pygame

from core.level_up import LevelUpBanner, shown_level
from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.world import SCREEN_H, SCREEN_W
from ui.hud_rules import RGB, HudRules, MotionRules
from ui.level_up_motion import fade_share, pop_scale
from ui.level_up_rules import LevelUpLook, PopLook
from ui.score_text import group_digits

log = logging.getLogger(__name__)

DIGITS: str = "0123456789"
"""The ten characters a score tile shows. One image per character and color is made once."""

HEART_LIT: int = 0
HEART_DIM: int = 1
HEART_LAST: int = 2
HEART_WHITE: int = 3
HEART_HUE: int = 4
"""Indexes into HudArt.hearts. Cells of hud_hearts.png, left to right (tools/art/hud_panel.py)."""

HEART_CELL_COUNT: int = 5
"""Cells in hud_hearts.png, one per index above. Must match HEART_CELLS in the art tool."""

TEXT_CACHE_SIZE: int = 8
"""Most text images kept for a changing value (BEST, graze count) before the oldest are dropped."""

INK_TILE: int = 16
"""Side of the cells a thin outline's picture is cut into, px. Each cell is trimmed to its ink."""

type Anchor = str
"""Where a text image sits on its point: left, center or right (vertical center always)."""

type Tiles = tuple[tuple[pygame.Surface, tuple[int, int]], ...]
"""Small images with the window position of their top-left corner."""


class HudRun(Protocol):
    """The four numbers of a run the HUD reads. core.run.Run has all four."""

    @property
    def score(self) -> int:
        """Points, whole, >= 0."""
        ...

    @property
    def lives(self) -> int:
        """Lives left, 0..LIVES_START."""
        ...

    @property
    def grazes(self) -> int:
        """Grazes so far, >= 0."""
        ...

    @property
    def level(self) -> int:
        """The level, 1..8."""
        ...


@dataclass(frozen=True)
class HudArt:
    """The pictures and fonts the HUD needs, loaded by app.assets.load_hud_art."""

    frame: pygame.Surface
    sheen: pygame.Surface
    panel: pygame.Surface
    ship: pygame.Surface
    hearts: tuple[pygame.Surface, ...]
    radar: tuple[pygame.Surface, ...]
    ring: tuple[pygame.Surface, ...]
    scan: pygame.Surface
    label_font: pygame.font.Font
    fonts: Mapping[str, pygame.font.Font]
    """Exo 2 Bold at the sizes of hud.json: `value`, `tile`, `graze` and `level`."""


@dataclass(frozen=True)
class LevelSlot:
    """Where and how the HUD draws one level's number. Source: level-up/view.md, Interface."""

    center: tuple[int, int]
    """Window px: the center of the number image at its normal size."""
    size: tuple[int, int]
    """That image's width and height, px."""
    color: RGB
    """The number's tier color at that level."""


@dataclass(frozen=True, slots=True)
class _Pop:
    """What a level pop looks like on one frame, worked out from the banner's age."""

    level: int
    """The new level."""
    frame: int
    """Index of the number's pre-made frame."""
    flash: RGB
    """The white the number and the new climb bar fade from."""
    bar_share: float
    """0 (flash color) to 1 (lit color): where the new climb bar's fade is."""
    box_alpha: int
    """Opacity of the box outline's flash, 0..255."""


def clamp_score(score: int, digits: int) -> int:
    """Return the score the tiles can show: 0 to ``10 ** digits - 1``."""
    maximum: int = 10**digits - 1
    return max(0, min(score, maximum))


def lit_segments(score: int, best: int | None, segments: int, step: int) -> int:
    """Return how many score bar segments are lit, 0..``segments``.

    The target is ``best`` when it is above 0, else the next multiple of ``step`` above the score.
    Lit is ``ceil(min(1, score / target) * segments)``; 0 at score 0. Source: 10-ui.md,
    `hud_score_bar`.
    """
    if score <= 0:
        return 0
    target: int = best if best is not None and best > 0 else (score // step + 1) * step
    return math.ceil(min(1.0, score / target) * segments)


def tier_color_key(level: int, tier_mid: int, tier_high: int) -> str:
    """Return the level number's color: ``level`` below tier_mid, ``mid`` below tier_high, else

    ``last_life``.
    """
    if level >= tier_high:
        return "last_life"
    if level >= tier_mid:
        return "mid"
    return "level"


def beat_scale_at(elapsed: int, motion: MotionRules) -> float:
    """Return the last heart's size multiple, 1..``beat_scale``, ``elapsed`` ticks into the beat
    loop.

    Rises to the peak at ``beat_peak_at`` of the beat, falls back to 1 by ``beat_end_at``, rests
    until the end.
    """
    share: float = (elapsed % motion.beat_ticks) / motion.beat_ticks
    grow: float = motion.beat_scale - 1.0
    if share < motion.beat_peak_at:
        return 1.0 + grow * share / motion.beat_peak_at
    if share < motion.beat_end_at:
        return motion.beat_scale - grow * (share - motion.beat_peak_at) / (
            motion.beat_end_at - motion.beat_peak_at
        )
    return 1.0


def bump_scale_at(elapsed: int, motion: MotionRules) -> float:
    """Return the graze count's size multiple, ``elapsed`` ticks after a graze (1 once

    ``bump_ticks`` pass).
    """
    if not 0 <= elapsed < motion.bump_ticks:
        return 1.0
    share: float = elapsed / motion.bump_ticks
    grow: float = motion.bump_scale - 1.0
    if share < motion.bump_peak_at:
        return 1.0 + grow * share / motion.bump_peak_at
    return motion.bump_scale - grow * (share - motion.bump_peak_at) / (1.0 - motion.bump_peak_at)


def break_state_at(elapsed: int, motion: MotionRules) -> tuple[float, str] | None:
    """Return (brightness 0..1, look) of a heart's break ``elapsed`` ticks in, or None once it is
    over.

    Brightness is blended between the two keys round the share of the break; the look is the earlier
    key's.
    """
    if not 0 <= elapsed < motion.break_ticks:
        return None
    share: float = elapsed / motion.break_ticks
    keys = motion.break_keys
    for earlier, later in itertools.pairwise(keys):
        if earlier[0] <= share <= later[0]:
            span: float = later[0] - earlier[0]
            blend: float = 0.0 if span <= 0 else (share - earlier[0]) / span
            return earlier[1] + (later[1] - earlier[1]) * blend, earlier[2]
    return keys[-1][1], keys[-1][2]


def _mix(a: RGB, b: RGB, share: float) -> RGB:
    """Return color ``a`` moved ``share`` (0..1) of the way to color ``b``."""
    return (
        round(a[0] + (b[0] - a[0]) * share),
        round(a[1] + (b[1] - a[1]) * share),
        round(a[2] + (b[2] - a[2]) * share),
    )


class HudView:
    """The side panel and frame. Keeps the view state the motions need: the last lives and grazes
    and the tick each running motion started on. Needs ``pygame.font`` initialized and a display
    set.
    """

    def __init__(
        self, rules: HudRules, art: HudArt, level_up_look: LevelUpLook | None = None
    ) -> None:
        """Build every picture once. With ``level_up_look`` also build the level pop's frames for
        every level a banner can show; with None no pop is ever drawn.
        """
        palette: Mapping[str, RGB] = rules.palette
        self._rules: HudRules = rules
        self._art: HudArt = art
        self._look: LevelUpLook | None = level_up_look
        self._origin: tuple[int, int] = (rules.panel.x, rules.panel.content_y)
        self._label_color: RGB = _mix(
            palette["panel_body"], palette["plating"], rules.fonts.label_mix
        )
        self._value_color: RGB = _mix(
            palette["panel_body"], palette["plating"], rules.fonts.value_mix
        )
        self._digits: dict[bool, tuple[pygame.Surface, ...]] = {
            lit: tuple(
                art.fonts["tile"].render(char, True, palette["plating" if lit else "dim"])
                for char in DIGITS
            )
            for lit in (True, False)
        }
        self._best_label: pygame.Surface = self._label("BEST")
        self._panel: pygame.Surface = self._compose_panel()
        self._bar: tuple[tuple[pygame.Rect, RGB], ...] = self._bar_cells()
        self._beat: tuple[pygame.Surface, ...] = self._beat_hearts()
        self._hearts: tuple[pygame.Surface, ...] = tuple(heart.copy() for heart in art.hearts)
        self._level_numbers: dict[int, pygame.Surface] = {}
        self._graze_numbers: dict[int, pygame.Surface] = {}
        self._best_numbers: dict[int, pygame.Surface] = {}
        self._frame_strips: tuple[tuple[pygame.Surface, tuple[int, int]], ...] = self._strips()
        self._sheen_pieces: tuple[tuple[pygame.Surface, tuple[int, int]], ...] = (
            self._sheen_slices()
        )
        self._dim_level: int = 255 - rules.window.dim_alpha
        self._lives: int | None = None
        self._grazes: int = 0
        self._breaks: dict[int, int] = {}
        self._bump_start: int | None = None
        self._ring_start: int | None = None
        self._pop_frames: dict[int, tuple[pygame.Surface, ...]] = {}
        self._box_flash: Tiles = ()
        if level_up_look is not None:
            self._build_pop(level_up_look)

    def draw(
        self,
        window: pygame.Surface,
        run: HudRun,
        best: int | None,
        tick: int,
        level_up: LevelUpBanner | None = None,
    ) -> None:
        """Draw the panel, the frame and the sheen on ``window``. ``tick`` is the view clock, in
        ticks.

        Never draws on the play area except the sheen. Starts the heart's break and the graze
        motions when ``run.lives`` falls or ``run.grazes`` rises since the last call. The level
        readout shows ``shown_level(level_up, run.level)`` and plays the pop after the banner's
        arrival tick; with ``level_up`` None, or no look given at construction, it shows
        ``run.level`` as the HUD always did. The pop runs on the banner's age, not on ``tick``.
        """
        self._update(run, tick)
        rules: HudRules = self._rules
        window.blit(self._panel, (rules.panel.x, 0))
        self._draw_score(window, run.score, best)
        self._draw_hearts(window, run.lives, tick)
        self._draw_scan(window, tick)
        banner: LevelUpBanner | None = level_up if self._look is not None else None
        self._draw_level(window, shown_level(banner, run.level), self._active_pop(banner))
        self._draw_graze(window, run.grazes, tick)
        for strip, position in self._frame_strips:
            window.blit(strip, position)
        for piece, position in self._sheen_pieces:
            window.blit(piece, position)

    def level_slot(self, level: int) -> LevelSlot:
        """Return where the HUD draws ``level``'s number: its center in window px, its image's
        size and its tier color. Draws and changes nothing.
        """
        number: pygame.Surface = self._level_number(level)
        return LevelSlot(
            center=self._number_rect(number).center,
            size=number.get_size(),
            color=self._tier_color(level),
        )

    def dim(self, window: pygame.Surface) -> None:
        """Darken the whole window: black at ``window.dim_alpha``. Draw the box after it.

        A multiply fill, not a blended layer: the same result for black, and about twice as fast.
        """
        window.fill((self._dim_level,) * 3, special_flags=pygame.BLEND_RGB_MULT)

    # ----- state -----

    def _update(self, run: HudRun, tick: int) -> None:
        """Start the motions a change of lives or grazes asks for. A new run clears them all."""
        lives: int = run.lives
        if self._lives is None or lives > self._lives or run.grazes < self._grazes:
            self._breaks.clear()
            self._bump_start = None
            self._ring_start = None
        else:
            for slot in range(lives, self._lives):
                self._breaks[slot] = tick
            if run.grazes > self._grazes:
                self._bump_start = tick
                self._ring_start = tick
        self._lives = lives
        self._grazes = run.grazes

    def _active_pop(self, banner: LevelUpBanner | None) -> _Pop | None:
        """Return the pop to draw, or None before the arrival tick, after the pop and with no
        banner. Reads the banner's age: it is the only clock the pop has.
        """
        if self._look is None or banner is None:
            return None
        pop: PopLook = self._look.pop
        elapsed: int = banner.age_ticks - banner.arrival_ticks
        if not 0 <= elapsed < pop.ticks:
            return None
        last: int = max(1, pop.steps - 1)
        return _Pop(
            level=banner.level,
            frame=min(pop.steps - 1, round(elapsed * last / pop.ticks)),
            flash=self._look.colors["flash"],
            bar_share=fade_share(elapsed, 0, pop.bar_flash_ticks),
            box_alpha=round(255 * (1.0 - fade_share(elapsed, 0, pop.box_flash_ticks))),
        )

    # ----- building (once) -----

    def _build_pop(self, look: LevelUpLook) -> None:
        """Make the pop's pictures: the number's frames for each level a banner can show and the
        box outline's flash. Also renders the level numbers, so no draw renders text.
        """
        for level in range(FIRST_LEVEL, LEVEL_COUNT + 1):
            self._level_number(level)
        for level in range(FIRST_LEVEL + 1, LEVEL_COUNT + 1):
            self._pop_frames[level] = self._number_frames(level, look)
        self._box_flash = self._box_outline(look)

    def _number_frames(self, level: int, look: LevelUpLook) -> tuple[pygame.Surface, ...]:
        """Return ``pop.steps`` images of ``level``'s number across the pop, first to last.

        Frame ``k`` is the pop at tick ``round(k * pop.ticks / (steps - 1))``: the size from
        ``pop_scale`` and a color mixed from ``colors.flash`` to the tier color over
        ``pop.flash_ticks``. The first frame is the arrival size, the last the normal image.
        """
        pop: PopLook = look.pop
        tier: RGB = self._tier_color(level)
        font: pygame.font.Font = self._art.fonts["level"]
        frames: list[pygame.Surface] = []
        for step in range(pop.steps):
            elapsed: int = round(step * pop.ticks / max(1, pop.steps - 1))
            color: RGB = _mix(look.colors["flash"], tier, fade_share(elapsed, 0, pop.flash_ticks))
            image: pygame.Surface = font.render(str(level), True, color)
            scale: float = pop_scale(elapsed, pop)
            if scale != 1.0:
                size: tuple[int, int] = (
                    max(1, round(image.get_width() * scale)),
                    max(1, round(image.get_height() * scale)),
                )
                image = pygame.transform.smoothscale(image, size)
            frames.append(image)
        return tuple(frames)

    def _box_outline(self, look: LevelUpLook) -> Tiles:
        """Return the level box's outline in ``colors.box_flash`` as small images in window px.

        The outline follows the baked box: cut top-right and bottom-left corners
        (``pop.box_corner_cut``), ``pop.box_flash_width`` thick, drawn over the baked edge.
        """
        pop: PopLook = look.pop
        left, top, width, height = self._rules.level.box
        cut: int = pop.box_corner_cut
        pad: int = pop.box_flash_width
        image: pygame.Surface = pygame.Surface((width + 2 * pad, height + 2 * pad), pygame.SRCALPHA)
        corners: list[tuple[int, int]] = [
            (pad, pad),
            (pad + width - cut, pad),
            (pad + width - 1, pad + cut - 1),
            (pad + width - 1, pad + height - 1),
            (pad + cut - 1, pad + height - 1),
            (pad, pad + height - cut),
        ]
        pygame.draw.polygon(image, (*look.colors["box_flash"], 255), corners, pop.box_flash_width)
        origin: tuple[int, int] = (
            self._origin[0] + left - pad,
            self._origin[1] + top - pad,
        )
        return tuple(
            (tile, (origin[0] + at[0], origin[1] + at[1])) for tile, at in ink_tiles(image)
        )

    def _label(self, text: str) -> pygame.Surface:
        """Return ``text`` in the label font, letter-spaced, as one image in the label color."""
        spacing: int = self._rules.fonts.label_spacing
        glyphs: list[pygame.Surface] = [
            self._art.label_font.render(char, True, self._label_color) for char in text
        ]
        width: int = sum(glyph.get_width() for glyph in glyphs) + spacing * (len(glyphs) - 1)
        image: pygame.Surface = pygame.Surface(
            (width, max(glyph.get_height() for glyph in glyphs)), pygame.SRCALPHA
        )
        left: int = 0
        for glyph in glyphs:
            image.blit(glyph, (left, 0))
            left += glyph.get_width() + spacing
        return image

    def _compose_panel(self) -> pygame.Surface:
        """Return the panel picture with the wireframe and the static labels on it, once."""
        rules: HudRules = self._rules
        panel: pygame.Surface = self._art.panel.copy()
        top: int = rules.panel.content_y
        box = rules.hearts.ship_box
        panel.blit(self._art.ship, (box[0], top + box[1]))
        for text, x, y, anchor in (
            ("SCORE", rules.score.label_x, rules.score.label_y, "left"),
            ("LEVEL", rules.level.label_x, rules.level.label_y, "left"),
            ("GRAZE", rules.graze.label_x, rules.graze.label_y, "center"),
        ):
            image: pygame.Surface = self._label(text)
            panel.blit(image, self._anchored(image, x, top + y, anchor))
        return panel

    @staticmethod
    def _anchored(image: pygame.Surface, x: int, y: int, anchor: Anchor) -> pygame.Rect:
        """Return the rect of ``image`` with its vertical center on ``y`` and its ``anchor`` edge on

        ``x``.
        """
        rect: pygame.Rect = image.get_rect()
        rect.centery = y
        if anchor == "left":
            rect.left = x
        elif anchor == "right":
            rect.right = x
        else:
            rect.centerx = x
        return rect

    def _bar_cells(self) -> tuple[tuple[pygame.Rect, RGB], ...]:
        """Return each score bar segment's rect (window px) and its lit color, once."""
        score = self._rules.score
        palette: Mapping[str, RGB] = self._rules.palette
        gap_total: int = (score.bar_segments - 1) * score.bar_gap
        width: float = (score.bar_w - gap_total) / score.bar_segments
        left: int = self._origin[0] + score.bar_x
        top: int = self._origin[1] + score.bar_y
        cells: list[tuple[pygame.Rect, RGB]] = []
        for index in range(score.bar_segments):
            start: float = index * (width + score.bar_gap)
            x0: int = left + round(start)
            x1: int = left + round(start + width)
            share: float = index / max(1, score.bar_segments - 1)
            color: RGB = _mix(palette["ship_lines"], palette["score"], share)
            cells.append((pygame.Rect(x0, top, x1 - x0, score.bar_h), color))
        return tuple(cells)

    def _beat_hearts(self) -> tuple[pygame.Surface, ...]:
        """Return the last-life heart pre-scaled in ``beat_steps`` + 1 sizes from 1 to

        ``beat_scale``.
        """
        motion: MotionRules = self._rules.motion
        base: pygame.Surface = self._art.hearts[HEART_LAST]
        sizes: list[pygame.Surface] = [base]
        for step in range(1, motion.beat_steps + 1):
            scale: float = 1.0 + (motion.beat_scale - 1.0) * step / motion.beat_steps
            size: tuple[int, int] = (
                round(base.get_width() * scale),
                round(base.get_height() * scale),
            )
            sizes.append(pygame.transform.smoothscale(base, size))
        return tuple(sizes)

    def _strips(self) -> tuple[tuple[pygame.Surface, tuple[int, int]], ...]:
        """Return the frame picture cut into four strips round the play area, each with its window
        position.

        The glass is transparent in the picture, so the play area is never blitted over.
        """
        win = self._rules.window
        frame: pygame.Surface = self._art.frame
        right: int = win.field_x + SCREEN_W
        bottom: int = win.field_y + SCREEN_H
        rects: tuple[pygame.Rect, ...] = (
            pygame.Rect(0, 0, frame.get_width(), win.field_y),
            pygame.Rect(0, bottom, frame.get_width(), frame.get_height() - bottom),
            pygame.Rect(0, win.field_y, win.field_x, SCREEN_H),
            pygame.Rect(right, win.field_y, frame.get_width() - right, SCREEN_H),
        )
        return tuple((frame.subsurface(rect), rect.topleft) for rect in rects)

    def _sheen_slices(self) -> tuple[tuple[pygame.Surface, tuple[int, int]], ...]:
        """Return the sheen cut into strips ``sheen_rows`` tall, each trimmed to where it has any
        sheen, with its window position. Empty when the sheen is off. Blending only these pixels
        is what keeps the browser build at full speed: the whole play area costs about half the
        frame.
        """
        rules = self._rules
        if not rules.frame.sheen:
            return ()
        sheen: pygame.Surface = self._art.sheen
        pieces: list[tuple[pygame.Surface, tuple[int, int]]] = []
        for top in range(0, sheen.get_height(), rules.frame.sheen_rows):
            height: int = min(rules.frame.sheen_rows, sheen.get_height() - top)
            bounds: pygame.Rect = sheen.subsurface(
                pygame.Rect(0, top, sheen.get_width(), height)
            ).get_bounding_rect()
            if bounds.width and bounds.height:
                area: pygame.Rect = bounds.move(0, top)
                pieces.append(
                    (
                        sheen.subsurface(area),
                        (rules.window.field_x + area.x, rules.window.field_y + area.y),
                    )
                )
        return tuple(pieces)

    # ----- per frame -----

    def _draw_score(self, window: pygame.Surface, score: int, best: int | None) -> None:
        """Draw the tiles, the score bar and BEST (when ``best`` is not None)."""
        rules = self._rules
        spec = rules.score
        palette: Mapping[str, RGB] = rules.palette
        shown: str = str(clamp_score(score, spec.tile_count)).zfill(spec.tile_count)
        leading: int = min(
            spec.tile_count - len(str(clamp_score(score, spec.tile_count))), spec.tile_count - 1
        )
        ox, oy = self._origin
        text_y: int = oy + spec.tile_y + spec.tile_top + (spec.tile_h - spec.tile_top) // 2
        for index, char in enumerate(shown):
            left: int = ox + spec.tile_x + index * spec.tile_pitch
            dim: bool = index < leading
            window.fill(
                palette["dim" if dim else "score"],
                pygame.Rect(left, oy + spec.tile_y, spec.tile_w, spec.tile_top),
            )
            image: pygame.Surface = self._digits[not dim][DIGITS.index(char)]
            window.blit(image, image.get_rect(center=(left + spec.tile_w // 2, text_y)))
        lit: int = lit_segments(score, best, spec.bar_segments, spec.bar_step)
        for index, (rect, color) in enumerate(self._bar):
            window.fill(color if index < lit else palette["dim"], rect)
        if best is not None:
            window.blit(
                self._best_label,
                self._anchored(self._best_label, ox + spec.best_label_x, oy + spec.best_y, "left"),
            )
            number: pygame.Surface = self._best_number(best)
            window.blit(
                number, self._anchored(number, ox + spec.best_right, oy + spec.best_y, "right")
            )

    def _best_number(self, best: int) -> pygame.Surface:
        """Return the best score's text image, grouped with the file's separator. Kept per value."""
        if best not in self._best_numbers:
            if len(self._best_numbers) >= TEXT_CACHE_SIZE:
                self._best_numbers.clear()
            text: str = group_digits(best).replace(" ", self._rules.score.best_separator)
            self._best_numbers[best] = self._art.fonts["value"].render(
                text, True, self._value_color
            )
        return self._best_numbers[best]

    def _draw_hearts(self, window: pygame.Surface, lives: int, tick: int) -> None:
        """Draw one heart per slot: lit while it is a life left, dim when lost, orange and beating

        on the last life.
        """
        motion: MotionRules = self._rules.motion
        ox, oy = self._origin
        for slot, (x, y) in enumerate(self._rules.hearts.slots):
            image: pygame.Surface = self._heart_image(slot, lives, tick, motion)
            window.blit(image, image.get_rect(center=(ox + x, oy + y)))

    def _heart_image(self, slot: int, lives: int, tick: int, motion: MotionRules) -> pygame.Surface:
        """Return heart ``slot``'s picture: its break while one runs, else lit, last or dim."""
        hearts = self._hearts
        started: int | None = self._breaks.get(slot)
        state = break_state_at(tick - started, motion) if started is not None else None
        if state is not None:
            brightness, look = state
            source: pygame.Surface = hearts[
                {"white": HEART_WHITE, "hue": HEART_HUE}.get(look, HEART_LIT)
            ]
            source.set_alpha(round(255 * brightness))
            return source
        if slot >= lives:
            return hearts[HEART_DIM]
        if lives == 1:
            scale: float = beat_scale_at(tick, motion)
            step: int = (
                round((scale - 1.0) / (motion.beat_scale - 1.0) * motion.beat_steps)
                if motion.beat_scale > 1.0
                else 0
            )
            return self._beat[step]
        hearts[HEART_LIT].set_alpha(255)
        return hearts[HEART_LIT]

    def _draw_scan(self, window: pygame.Surface, tick: int) -> None:
        """Draw the scan line at its place in the fall that repeats every ``scan_ticks``."""
        motion: MotionRules = self._rules.motion
        share: float = (tick % motion.scan_ticks) / motion.scan_ticks
        row: int = motion.scan_from + round((motion.scan_to - motion.scan_from) * share)
        ox, oy = self._origin
        window.blit(
            self._art.scan, (ox + motion.scan_x, oy + row - self._art.scan.get_height() // 2)
        )

    def _draw_level(self, window: pygame.Surface, level: int, pop: _Pop | None) -> None:
        """Draw the level box's flash, the number (its pop frame while ``pop`` runs) in its tier
        color, and the climb bars: lit up to ``level``.
        """
        if pop is None:
            number: pygame.Surface = self._level_number(level)
            window.blit(number, self._number_rect(number))
        else:
            self._draw_box_flash(window, pop)
            frame: pygame.Surface = self._pop_frames[pop.level][pop.frame]
            window.blit(frame, frame.get_rect(center=self.level_slot(pop.level).center))
        spec = self._rules.level
        ox, oy = self._origin
        span: int = (spec.bars - 1) * spec.bar_pitch + spec.bar_w
        lit: int = min(level, spec.bars)
        for index in range(spec.bars):
            height: int = spec.bar_base_h + index * spec.bar_step_h
            left: int = ox + spec.bars_right - span + index * spec.bar_pitch
            window.fill(
                self._bar_color(index, lit, pop),
                pygame.Rect(left, oy + spec.bars_bottom - height, spec.bar_w, height),
            )

    def _bar_color(self, index: int, lit: int, pop: _Pop | None) -> RGB:
        """Return climb bar ``index``'s color: ``dim`` past ``lit``, else its ramp color, mixed
        from the flash white while it is the new level's bar and the pop's flash runs.
        """
        spec = self._rules.level
        palette: Mapping[str, RGB] = self._rules.palette
        if index >= lit:
            return palette["dim"]
        color: RGB = _mix(palette["level"], palette["last_life"], index / max(1, spec.bars - 1))
        if pop is None or index != min(pop.level, spec.bars) - 1:
            return color
        return _mix(pop.flash, color, pop.bar_share)

    def _draw_box_flash(self, window: pygame.Surface, pop: _Pop) -> None:
        """Draw the box outline's flash at the pop's opacity, over the baked outline."""
        if pop.box_alpha == 0:
            return
        for tile, position in self._box_flash:
            tile.set_alpha(pop.box_alpha)
            window.blit(tile, position)

    def _number_rect(self, number: pygame.Surface) -> pygame.Rect:
        """Return where the level number image is blitted: left edge at ``number_x``, vertically
        centered on ``number_y``.
        """
        spec = self._rules.level
        return self._anchored(
            number, self._origin[0] + spec.number_x, self._origin[1] + spec.number_y, "left"
        )

    def _tier_color(self, level: int) -> RGB:
        """Return the level number's tier color: ``level``, a mix toward ``last_life``, or
        ``last_life``.
        """
        spec = self._rules.level
        palette: Mapping[str, RGB] = self._rules.palette
        key: str = tier_color_key(level, spec.tier_mid, spec.tier_high)
        if key == "mid":
            return _mix(palette["level"], palette["last_life"], spec.tier_mid_mix)
        return palette[key]

    def _level_number(self, level: int) -> pygame.Surface:
        """Return the level number's image in its tier color. Kept per level."""
        if level not in self._level_numbers:
            self._level_numbers[level] = self._art.fonts["level"].render(
                str(level), True, self._tier_color(level)
            )
        return self._level_numbers[level]

    def _draw_graze(self, window: pygame.Surface, grazes: int, tick: int) -> None:
        """Draw the radar wedge, the graze count (swelling after a graze) and the ring (growing

        after one).
        """
        motion: MotionRules = self._rules.motion
        ox, oy = self._origin
        center: tuple[int, int] = (
            ox + self._rules.graze.center[0],
            oy + self._rules.graze.center[1],
        )
        wedge: pygame.Surface = self._art.radar[
            (tick % motion.sweep_ticks) * motion.sweep_frames // motion.sweep_ticks
        ]
        window.blit(wedge, wedge.get_rect(center=center))
        count: pygame.Surface = self._graze_number(grazes)
        scale: float = (
            bump_scale_at(tick - self._bump_start, motion) if self._bump_start is not None else 1.0
        )
        if scale > 1.0:
            count = pygame.transform.smoothscale(
                count, (round(count.get_width() * scale), round(count.get_height() * scale))
            )
        window.blit(count, count.get_rect(center=center))
        if self._ring_start is not None and 0 <= tick - self._ring_start < motion.ring_ticks:
            ring: pygame.Surface = self._art.ring[
                (tick - self._ring_start) * motion.ring_frames // motion.ring_ticks
            ]
            window.blit(ring, ring.get_rect(center=center))

    def _graze_number(self, grazes: int) -> pygame.Surface:
        """Return the graze count's image, shrunk to fit ``count_limit``. Kept per value."""
        if grazes not in self._graze_numbers:
            if len(self._graze_numbers) >= TEXT_CACHE_SIZE:
                self._graze_numbers.clear()
            image: pygame.Surface = self._art.fonts["graze"].render(
                str(grazes), True, self._rules.palette["graze"]
            )
            limit: int = self._rules.graze.count_limit
            if image.get_width() > limit:
                height: int = max(1, round(image.get_height() * limit / image.get_width()))
                image = pygame.transform.smoothscale(image, (limit, height))
            self._graze_numbers[grazes] = image
        return self._graze_numbers[grazes]


def ink_tiles(image: pygame.Surface) -> Tiles:
    """Cut ``image`` into ``INK_TILE`` cells, each trimmed to its ink, as copies with their offset.

    A thin shape then costs a few small blits, never one blit of its whole bounding box. Cells with
    no ink are dropped.
    """
    tiles: list[tuple[pygame.Surface, tuple[int, int]]] = []
    for top in range(0, image.get_height(), INK_TILE):
        for left in range(0, image.get_width(), INK_TILE):
            cell: pygame.Rect = pygame.Rect(left, top, INK_TILE, INK_TILE).clip(image.get_rect())
            ink: pygame.Rect = image.subsurface(cell).get_bounding_rect()
            if ink.width and ink.height:
                area: pygame.Rect = ink.move(cell.topleft)
                tiles.append((image.subsurface(area).copy(), area.topleft))
    return tuple(tiles)
