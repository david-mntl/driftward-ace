"""The HUD's values as frozen records, one per section of tuning/hud.json.

Source: docs/contracts/schemas/hud.schema.json and docs/contracts/systems/hud.md, Interface. The
records hold what the file says and nothing else: app/hud_tuning.py checks the file and builds them,
ui/hud.py reads them. Positions marked panel space count from the panel's top-left plus
``PanelRules.content_y``. Stdlib only.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

log = logging.getLogger(__name__)

type RGB = tuple[int, int, int]
type Rect4 = tuple[int, int, int, int]
"""x, y, width, height."""
type Point2 = tuple[int, int]
type BreakKey = tuple[float, float, str]
"""A key of a heart's break: share of the break 0..1, brightness 0..1, look (white, hue, plain)."""

BREAK_LOOKS: tuple[str, ...] = ("white", "hue", "plain")
"""The looks a break key may name. Source: hud.schema.json, motion.break_keys."""

PALETTE_KEYS: tuple[str, ...] = (
    "ship_lines",
    "ship_lines_light",
    "plating",
    "hearts",
    "last_life",
    "score",
    "level",
    "graze",
    "panel_body",
    "frame_metal",
    "frame_highlight",
    "frame_lights",
    "fuchsia_spill",
    "dim",
    "line",
    "tile_bg",
    "footer_dot",
)
"""The palette's keys. Source: 12-art-and-audio.md, HUD colors."""


@dataclass(frozen=True)
class WindowRules:
    """The window and where the play area sits, px. dim_alpha is 0..255."""

    width: int
    height: int
    field_x: int
    field_y: int
    dim_alpha: int


@dataclass(frozen=True)
class PanelRules:
    """The side panel: left edge in the window, width, and the row where its space starts, px.

    ``scale`` is the design's size against the mock-up. Only the art tool reads it.
    """

    x: int
    width: int
    content_y: int
    scale: float


@dataclass(frozen=True)
class FrameRules:
    """The frame: pillar width, glass sheen on or off and its strips, corner light radius, px."""

    pillar_width: int
    sheen: bool
    sheen_rows: int
    light_radius: float
    spill: float


@dataclass(frozen=True)
class ScoreRules:
    """Score box, tiles, bar and best, in panel space px."""

    box: Rect4
    label_x: int
    label_y: int
    tile_count: int
    tile_x: int
    tile_y: int
    tile_w: int
    tile_h: int
    tile_pitch: int
    tile_top: int
    bar_x: int
    bar_y: int
    bar_w: int
    bar_h: int
    bar_segments: int
    bar_gap: int
    bar_step: int
    best_label_x: int
    best_y: int
    best_right: int
    best_separator: str


@dataclass(frozen=True)
class HeartRules:
    """The heart centers in fill order, one per life (panel space px), a heart image's size, the

    wireframe's box.
    """

    slots: tuple[Point2, ...]
    cell_w: int
    cell_h: int
    ship_box: Rect4


@dataclass(frozen=True)
class LevelRules:
    """Level box, number and climb bars in panel space px. tier_mid and tier_high are levels."""

    box: Rect4
    label_x: int
    label_y: int
    number_x: int
    number_y: int
    bars: int
    bar_w: int
    bar_pitch: int
    bar_base_h: int
    bar_step_h: int
    bars_right: int
    bars_bottom: int
    tier_mid: int
    tier_high: int
    tier_mid_mix: float


@dataclass(frozen=True)
class DialRules:
    """The graze dial in panel space px. count_limit is the widest the count may be, px."""

    center: Point2
    radius: int
    inner_radius: int
    wedge_radius: int
    count_limit: int
    label_x: int
    label_y: int


@dataclass(frozen=True)
class MotionRules:
    """Periods in ticks, scales as multiples, shares 0..1 of a motion, px in panel space."""

    sweep_ticks: int
    sweep_frames: int
    scan_ticks: int
    scan_x: int
    scan_w: int
    scan_from: int
    scan_to: int
    beat_ticks: int
    beat_scale: float
    beat_peak_at: float
    beat_end_at: float
    beat_steps: int
    break_ticks: int
    break_keys: tuple[BreakKey, ...]
    bump_ticks: int
    bump_scale: float
    bump_peak_at: float
    ring_ticks: int
    ring_frames: int
    ring_from: float
    ring_to: float
    ring_radius: int


@dataclass(frozen=True)
class FontRules:
    """The two font files (under assets/), sizes in px, label letter spacing in px, text color mixes

    0..1.
    """

    ui_file: str
    label_file: str
    label_size: int
    value_size: int
    tile_size: int
    graze_size: int
    level_size: int
    label_spacing: int
    label_mix: float
    value_mix: float


@dataclass(frozen=True)
class HudRules:
    """Every HUD value, one record per section of tuning/hud.json."""

    palette: Mapping[str, RGB]
    window: WindowRules
    panel: PanelRules
    frame: FrameRules
    score: ScoreRules
    hearts: HeartRules
    level: LevelRules
    graze: DialRules
    motion: MotionRules
    fonts: FontRules
