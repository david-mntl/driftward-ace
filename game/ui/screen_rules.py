"""The screens' values as frozen records, one per section of tuning/screens.json.

Source: docs/contracts/schemas/screens.schema.json and docs/contracts/systems/screens.md,
Interface. The records hold what the file says and nothing else: app/screens_tuning.py checks the
file and builds them, ui/screen_look.py and the views read them. Field names carry their range:
``*_alpha`` is 0..255, ``*_strength`` is 0..1, ``*_size``, ``*_w``, ``*_h`` and ``*_pitch`` are 1 or
more, any other whole number is 0 or more. Stdlib only.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

log = logging.getLogger(__name__)

type RGB = tuple[int, int, int]

PALETTE_KEYS: tuple[str, ...] = (
    "ship_lines",
    "ship_lines_light",
    "frame_lights",
    "panel_body",
    "score",
    "level",
    "hearts",
    "graze",
    "last_life",
    "plating",
    "rank_1",
    "rank_2",
    "rank_3",
)
"""The screens' palette keys. Source: 12-art-and-audio.md, Screen colors."""

FONT_ROLES: tuple[str, ...] = (
    "title",
    "message",
    "menu_title",
    "menu_item",
    "button",
    "label",
    "digit",
    "picker",
    "key",
    "hint",
    "row",
    "top_name",
    "top_score",
    "level",
    "card_title",
    "card_text",
    "empty",
)
"""The text roles, each with its own size and letter-spacing. Source: screens.schema.json."""


@dataclass(frozen=True)
class GlassRules:
    """The see-through panel every box and card shares. Alphas are 0..255.

    ``blur_down`` is how many times smaller the picture behind is made before it is scaled back
    up: the blur. 1 is no blur. ``scan_pitch`` rows apart, one row is a scan line.
    """

    fill_alpha: int
    border_alpha: int
    border_w: int
    bracket_len: int
    bracket_w: int
    bracket_out: int
    scan_pitch: int
    scan_alpha: int
    blur_down: int


@dataclass(frozen=True)
class GlowRules:
    """The soft glow, baked ahead of time. Radius is px, strength 0..1.

    ``box_*`` is the glow round a panel's border and brackets, ``text_*`` the glow behind lit text,
    ``icon_*`` the glow behind an icon's lines.
    """

    box_radius: int
    box_strength: float
    text_radius: int
    text_strength: float
    icon_radius: int
    icon_strength: float


@dataclass(frozen=True)
class FontRole:
    """One text role: its name (in FONT_ROLES), size px and letter-spacing in em."""

    name: str
    size: int
    spacing: float


@dataclass(frozen=True)
class FontRules:
    """The screens' font file and the text roles. Letter-spacing is in em (0.3 is 30% of size)."""

    text_file: str
    roles: tuple[FontRole, ...]


@dataclass(frozen=True)
class RulerRules:
    """The tick marks down both sides of a full-window page. ``enabled`` is off or on."""

    enabled: bool
    inset_x: int
    inset_y: int
    w: int
    minor_pitch: int
    major_pitch: int
    minor_w: int
    minor_alpha: int
    major_alpha: int


@dataclass(frozen=True)
class KeyCapRules:
    """The small key cap behind a key name (ENTER, SPACE, an arrow). Alphas 0..255, px."""

    min_w: int
    h: int
    pad_x: int
    radius: int
    fill_alpha: int
    border_alpha: int
    gap: int
    hint_gap: int
    group_gap: int
    word_alpha: int
    play_w: int
    arrow_size: int


@dataclass(frozen=True)
class ChoiceRules:
    """A choice (RETRY, MENU, a menu item): its fade and brackets. Alphas 0..255, px.

    ``off_alpha`` is how bright a choice that can't be picked yet is, ``dim_alpha`` a choice that
    isn't selected.
    """

    fade_alpha: int
    bracket_inset: int
    dim_alpha: int
    off_alpha: int


@dataclass(frozen=True)
class PauseRules:
    """The pause box. ``gap`` is px between the word and the key caps. ``blur`` is off or on."""

    w: int
    h: int
    gap: int
    blur: bool


@dataclass(frozen=True)
class GameOverRules:
    """The game-over box with and without the picker. Alphas are 0..255, px.

    The lines of a box are spread evenly between ``pad_top`` and ``pad_bottom``.
    """

    w: int
    h: int
    picker_w: int
    picker_h: int
    pad_top: int
    pad_bottom: int
    picker_pad_top: int
    score_digits: int
    score_gap: int
    score_cell_w: int
    score_group_gap: int
    label_alpha: int
    dim_digit_alpha: int
    choice_w: int
    choice_h: int
    choice_gap: int
    slot_w: int
    slot_h: int
    slot_gap: int
    slot_pad_y: int
    slot_line_w: int
    slot_line_alpha: int
    cursor_alpha: int
    arrow_size: int
    arrow_gap: int
    blur: bool


@dataclass(frozen=True)
class MenuRules:
    """The menu: title, the items, hint. All centered. px."""

    item_w: int
    item_h: int
    item_gap: int
    title_gap: int
    hint_bottom: int
    hint_alpha: int


@dataclass(frozen=True)
class InstructionsRules:
    """The instructions page. The cards fill the window between the title and the footer. px."""

    margin_x: int
    margin_top: int
    margin_bottom: int
    head_h: int
    foot_h: int
    gap: int
    columns: int
    icon_w: int
    icon_h: int
    pad_x: int
    pad_y: int
    text_gap: int
    caption_gap: int
    caption_alpha: int
    blur: bool


@dataclass(frozen=True)
class LeaderboardRules:
    """The leaderboard page. The table is ``table_w`` wide and centered. px, alphas 0..255."""

    margin_top: int
    margin_bottom: int
    head_h: int
    foot_h: int
    table_w: int
    top_h: int
    top_gap: int
    row_h: int
    rest_gap: int
    pad_x: int
    place_w: int
    top_place_w: int
    column_gap: int
    score_w: int
    top_score_w: int
    level_w: int
    medal_size: int
    rule_alpha: int
    empty_top: int
    empty_alpha: int
    place_alpha: int
    medal_fill_alpha: int
    blur: bool


@dataclass(frozen=True)
class CreditsRules:
    """The credits page. The cards are ``card_w`` wide and centered. px, alphas 0..255.

    A card is as tall as its padding, heading and lines. ``line_gap`` is the space below each line.
    """

    margin_top: int
    margin_bottom: int
    head_h: int
    foot_h: int
    card_w: int
    card_gap: int
    pad_x: int
    pad_y: int
    heading_gap: int
    line_gap: int
    text_alpha: int
    link_alpha: int
    blur: bool


@dataclass(frozen=True)
class ScreenRules:
    """Every value of tuning/screens.json."""

    palette: Mapping[str, RGB]
    glass: GlassRules
    glow: GlowRules
    fonts: FontRules
    rulers: RulerRules
    keycap: KeyCapRules
    choice: ChoiceRules
    pause: PauseRules
    game_over: GameOverRules
    menu: MenuRules
    instructions: InstructionsRules
    leaderboard: LeaderboardRules
    credits: CreditsRules
