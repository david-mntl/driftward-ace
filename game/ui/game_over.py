"""Game-over screen: a glass box with a message, the score, an optional name picker, and RETRY above
MENU.

Source: docs/contracts/systems/screens.md, Interface (ui/game_over.py); 10-ui.md,
`game_over_screen`, `game_over_message` and `game_over_look`. The views take the look and plain
values (the message, the score, the picker, the selection) and only draw. They never fill the
background, never flip the display, never log per frame, never catch an error and never read the
run mode, a key or the focus.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache, lru_cache
from types import MappingProxyType
from typing import Final

import pygame

from core.game_flow import GameOverChoice
from core.saves import BLANK, GameOverMessage, NamePicker
from ui.score_text import SCORE_LABEL
from ui.screen_look import ScreenLook
from ui.screen_rules import RGB

log = logging.getLogger(__name__)

MESSAGE_TEXTS: Final[Mapping[GameOverMessage, str]] = MappingProxyType(
    {
        GameOverMessage.NEW_BEST_SCORE: "NEW BEST SCORE",
        GameOverMessage.TOP_3: "TOP 3",
        GameOverMessage.TOP_10: "TOP 10",
        GameOverMessage.GAME_OVER: "GAME OVER",
    }
)
"""The first line, by message. 10-ui.md, game_over_message (locked)."""

RETRY_TEXT: Final[str] = "RETRY"
"""First choice's label. 02-game-flow.md, game_over_choices (locked)."""

MENU_TEXT: Final[str] = "MENU"
"""Second choice's label. 02-game-flow.md, game_over_choices (locked)."""

_CHOICE_TEXTS: Final[dict[GameOverChoice, str]] = {
    GameOverChoice.RETRY: RETRY_TEXT,
    GameOverChoice.MENU: MENU_TEXT,
}

PICKER_HINTS: Final[tuple[tuple[tuple[str, ...], str], ...]] = (
    (("UP", "DOWN"), "LETTER"),
    (("LEFT", "RIGHT"), "SLOT"),
    (("ENTER",), "SAVE"),
)
"""The picker's key hints, in order: the key caps and the word after them. 10-ui.md,
`game_over_look`."""

SCORE_SPACE: Final[str] = " "
"""A digit group's separator. It draws as a gap of `score_group_gap`, not as a character."""


@dataclass(frozen=True, slots=True)
class _Layout:
    """Where the box and its lines sit on one surface, px.

    ``box`` is the box; each ``*_top`` is the top of that line. Without the picker the slot row and
    the hint have no height: their tops equal ``choices_top``.
    """

    box: pygame.Rect
    message_top: int
    score_top: int
    slots_top: int
    hint_top: int
    choices_top: int


def draw_game_over(
    surface: pygame.Surface,
    look: ScreenLook,
    message: GameOverMessage = GameOverMessage.GAME_OVER,
    picker_shown: bool = False,
) -> None:
    """Draw the box and the message on ``surface``, centered. Units: pixels.

    The box is ``picker_w`` x ``picker_h`` when ``picker_shown`` and ``w`` x ``h`` otherwise,
    centered on the surface. ``MESSAGE_TEXTS[message]`` is centered across the box in the first
    line's place. The other lines' places stay empty. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(look, surface.get_size(), picker_shown)
    look.glass(surface, layout.box, look.rules.game_over.blur)
    look.blit_text(
        surface,
        MESSAGE_TEXTS[message],
        "message",
        look.palette["plating"],
        {"midtop": (layout.box.centerx, layout.message_top)},
    )


def draw_final_score(
    surface: pygame.Surface, look: ScreenLook, score: int, picker_shown: bool = False
) -> None:
    """Draw the score line on ``surface``, centered, in the second line's place.

    ``score`` is a whole number >= 0, trusted. The line is the label SCORE, then the digits in
    cells, in groups of three, with the leading zeros dim. At least ``score_digits`` digits show;
    a longer score shows in full. The place is worked out as ``draw_game_over`` does.
    """
    layout: _Layout = _layout(look, surface.get_size(), picker_shown)
    rules = look.rules.game_over
    cells: tuple[tuple[str, bool], ...] = _score_cells(score, rules.score_digits)
    label_w: int = look.text_size(SCORE_LABEL, "label")[0]
    digits_w: int = _digits_width(cells, rules.score_cell_w, rules.score_group_gap)
    left: int = layout.box.centerx - (label_w + rules.score_gap + digits_w) // 2
    centery: int = layout.score_top + _score_height(look) // 2
    plating: RGB = look.palette["plating"]
    look.blit_text(
        surface,
        SCORE_LABEL,
        "label",
        plating,
        {"midleft": (left, centery)},
        glow=False,
        alpha=rules.label_alpha,
    )
    left += label_w + rules.score_gap
    for char, dim in cells:
        if char == SCORE_SPACE:
            left += rules.score_group_gap
            continue
        look.blit_text(
            surface,
            char,
            "digit",
            look.palette["score"],
            {"center": (left + rules.score_cell_w // 2, centery)},
            alpha=rules.dim_digit_alpha if dim else 255,
        )
        left += rules.score_cell_w


def draw_name_picker(
    surface: pygame.Surface, look: ScreenLook, picker: NamePicker, picking: bool
) -> None:
    """Draw the slot row and, while ``picking``, the cursor and the key hints.

    Draws in the picker layout's third and fourth places, so it is called with the picker
    layout's other functions (``picker_shown`` True). Each slot is a cell with its character and
    a line under it; the cursor's slot is lit, with an arrow above and below. After the save
    (``picking`` False) the slots stay as picked, and the cursor and the hint places stay empty.
    """
    layout: _Layout = _layout(look, surface.get_size(), True)
    rules = look.rules.game_over
    cells: list[pygame.Rect] = _slot_cells(look, layout, len(picker.slots))
    plating: RGB = look.palette["plating"]
    cyan: RGB = look.palette["frame_lights"]
    for index, (cell, character) in enumerate(zip(cells, picker.slots, strict=True)):
        current: bool = picking and index == picker.cursor
        if current:
            _fill(surface, cell, cyan, rules.cursor_alpha)
        line: pygame.Rect = pygame.Rect(
            cell.left, cell.bottom - rules.slot_line_w, cell.width, rules.slot_line_w
        )
        _fill(
            surface, line, cyan if current else plating, 255 if current else rules.slot_line_alpha
        )
        if character != BLANK:
            look.blit_text(surface, character, "picker", plating, {"center": cell.center})
    if not picking:
        return
    _blit_arrows(surface, cells[picker.cursor], cyan, rules.arrow_size, rules.arrow_gap)
    _blit_hints(surface, look, layout)


def draw_game_over_choices(
    surface: pygame.Surface,
    look: ScreenLook,
    selection: GameOverChoice,
    picker_shown: bool = False,
    active: bool = True,
) -> None:
    """Draw RETRY and MENU on ``surface`` in the last two places, one of them selected.

    Both labels are centered in the box, one above the other. While ``active`` the selected one
    is lit and framed and the other is dim. While not ``active`` (the picker still takes the
    keys) both are faint and none is framed. The place is worked out as ``draw_game_over`` does.
    """
    layout: _Layout = _layout(look, surface.get_size(), picker_shown)
    rules = look.rules.game_over
    for index, choice in enumerate(GameOverChoice):
        rect: pygame.Rect = pygame.Rect(0, 0, rules.choice_w, rules.choice_h)
        rect.midtop = (
            layout.box.centerx,
            layout.choices_top + index * (rules.choice_h + rules.choice_gap),
        )
        state: str = "off" if not active else "selected" if choice is selection else "dim"
        look.blit_choice(surface, _CHOICE_TEXTS[choice], rect, "button", state)


@cache
def _layout(look: ScreenLook, size: tuple[int, int], picker_shown: bool) -> _Layout:
    """Return the box and the line tops for a surface of ``size``.

    The lines (message, score, [slot row, hint,] the two choices) are spread evenly between
    ``pad_top`` and ``pad_bottom`` inside the box, like flex's space-between.
    """
    rules = look.rules.game_over
    width, height = (rules.picker_w, rules.picker_h) if picker_shown else (rules.w, rules.h)
    box: pygame.Rect = pygame.Rect(0, 0, width, height)
    box.center = (size[0] // 2, size[1] // 2)
    heights: list[int] = [look.text_size("X", "message")[1], _score_height(look)]
    if picker_shown:
        heights += [rules.slot_h + 2 * rules.slot_pad_y, look.rules.keycap.h]
    heights.append(2 * rules.choice_h + rules.choice_gap)
    pad_top: int = rules.picker_pad_top if picker_shown else rules.pad_top
    free: int = height - pad_top - rules.pad_bottom - sum(heights)
    gap: float = free / (len(heights) - 1)
    tops: list[int] = []
    cursor: float = box.top + pad_top
    for line in heights:
        tops.append(round(cursor))
        cursor += line + gap
    if not picker_shown:
        tops[2:2] = [tops[2], tops[2]]
    return _Layout(box, tops[0], tops[1], tops[2], tops[3], tops[4])


def _score_height(look: ScreenLook) -> int:
    """Return the score line's height, px: the digit font's."""
    return look.text_size("0", "digit")[1]


@lru_cache(maxsize=1)
def _score_cells(score: int, digits: int) -> tuple[tuple[str, bool], ...]:
    """Return the score as (character, dim) cells: ``digits`` digits at least, grouped by three
    with a space between groups. A leading zero is dim; the last digit never is.

    Holds the last score only: the score is frozen while the screen shows.
    """
    grouped: str = _group(str(score).zfill(digits))
    cells: list[tuple[str, bool]] = []
    leading: bool = True
    last: int = max(i for i, char in enumerate(grouped) if char != SCORE_SPACE)
    for index, char in enumerate(grouped):
        if char != SCORE_SPACE and char != "0":
            leading = False
        cells.append((char, char == "0" and leading and index < last))
    return tuple(cells)


def _group(digits: str) -> str:
    """Return ``digits`` in groups of three from the right, a space between groups."""
    first: int = len(digits) % 3 or 3
    groups: list[str] = [digits[:first], *(digits[i : i + 3] for i in range(first, len(digits), 3))]
    return SCORE_SPACE.join(groups)


def _digits_width(cells: tuple[tuple[str, bool], ...], cell_w: int, group_gap: int) -> int:
    """Return the width of the digit cells, px: ``cell_w`` per digit, ``group_gap`` per space."""
    return sum(group_gap if char == SCORE_SPACE else cell_w for char, _ in cells)


def _slot_cells(look: ScreenLook, layout: _Layout, count: int) -> list[pygame.Rect]:
    """Return ``count`` slot cells side by side, ``slot_gap`` apart, centered on the box."""
    rules = look.rules.game_over
    row_w: int = count * rules.slot_w + (count - 1) * rules.slot_gap
    left: int = layout.box.centerx - row_w // 2
    top: int = layout.slots_top + rules.slot_pad_y
    return [
        pygame.Rect(left + i * (rules.slot_w + rules.slot_gap), top, rules.slot_w, rules.slot_h)
        for i in range(count)
    ]


def _fill(surface: pygame.Surface, rect: pygame.Rect, color: RGB, alpha: int) -> None:
    """Blend ``color`` at ``alpha`` (0..255) over ``rect``."""
    surface.blit(_plate(rect.size, color, alpha), rect.topleft)


@cache
def _plate(size: tuple[int, int], color: RGB, alpha: int) -> pygame.Surface:
    """Return a ``size`` plate of ``color`` at ``alpha``, made once."""
    image: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
    image.fill((*color, alpha))
    return image


def _blit_arrows(
    surface: pygame.Surface, cell: pygame.Rect, color: RGB, half: int, gap: int
) -> None:
    """Draw a solid triangle ``gap`` px above the cell pointing up, and one below pointing down."""
    height: int = half + 2
    x: int = cell.centerx
    top: int = cell.top - gap
    bottom: int = cell.bottom + gap
    pygame.draw.polygon(surface, color, [(x, top - height), (x + half, top), (x - half, top)])
    pygame.draw.polygon(
        surface, color, [(x, bottom + height), (x + half, bottom), (x - half, bottom)]
    )


def _blit_hints(surface: pygame.Surface, look: ScreenLook, layout: _Layout) -> None:
    """Draw the three key hints in a row, centered on the box, ``hint_gap`` apart."""
    gap: int = look.rules.keycap.group_gap
    sizes: list[int] = [look.keys_size(keys, word)[0] for keys, word in PICKER_HINTS]
    left: int = layout.box.centerx - (sum(sizes) + gap * (len(sizes) - 1)) // 2
    for (keys, word), width in zip(PICKER_HINTS, sizes, strict=True):
        look.blit_keys(surface, keys, word, {"topleft": (left, layout.hint_top)})
        left += width + gap
