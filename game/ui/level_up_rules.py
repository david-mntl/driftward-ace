"""The level-up moment's look as frozen records, one per section of tuning/level_up.json.

Source: docs/contracts/schemas/level-up.schema.json and docs/contracts/systems/level-up/view.md,
Interface. Field names and number types follow the schema: ticks and px counts are ``int``, shares
and scales are ``float``. The records hold what the file says and nothing else:
app/level_up_tuning.py checks the file and builds them, ui/level_up_motion.py and the views read
them. Ticks count from the tick the level rises (age 0). Stdlib only.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

log = logging.getLogger(__name__)

type RGB = tuple[int, int, int]


@dataclass(frozen=True)
class BandLook:
    """The glass band and its hairlines. Sizes in px, ages in ticks, alpha 0..255."""

    height: int
    alpha: int
    center_offset_y: int
    open_start: int
    open_end: int
    close_start: int
    close_end: int
    close_glass_share: float
    hairline_width: int
    corner_tick_length: int


@dataclass(frozen=True)
class NumberLook:
    """The big number: type, fall and landing squash. Sizes in px, ages in ticks."""

    font_size: int
    outline_width: int
    center_offset_y: int
    fall_start: int
    fall_end: int
    fall_overshoot_px: float
    fall_peak_share: float
    fall_stretch_x: float
    fall_stretch_y: float
    squash_ticks: int
    squash_x: float
    squash_y: float
    pose_steps: int


@dataclass(frozen=True)
class LabelLook:
    """The word LEVEL. Sizes and spacings in px, ages in ticks."""

    font_size: int
    offset_y: int
    fade_in_start: int
    fade_in_end: int
    spacing_wide: int
    spacing_normal: int
    spacing_steps: int


@dataclass(frozen=True)
class HoldLook:
    """When the label and the pips fade out, in ticks."""

    fade_out_start: int
    fade_out_end: int


@dataclass(frozen=True)
class PipsLook:
    """The row of level pips. Sizes in px, ages and lengths in ticks."""

    size: int
    pitch: int
    offset_y: int
    start: int
    end: int
    pop_ticks: int
    flash_ticks: int


@dataclass(frozen=True)
class RingLook:
    """The ring that bursts out on landing. Diameters and width in px, ticks in states."""

    start_diameter: float
    end_diameter: float
    width: int
    ticks: int


@dataclass(frozen=True)
class StreakLook:
    """The light streaks that fly out on landing. Lengths and radii in px, ticks in states."""

    count: int
    ticks: int
    length: float
    width: int
    start_radius: float
    end_radius: float


@dataclass(frozen=True)
class GlintLook:
    """The glint that crosses the number. Width in px, lean in degrees, strength 0..1."""

    start: int
    end: int
    frames: int
    width: int
    slant_degrees: float
    strength: float


@dataclass(frozen=True)
class BumpLook:
    """The play area's picture bump on landing. Pixels in px, ticks from the landing tick."""

    pixels: int
    ticks: int
    peak_share: float


@dataclass(frozen=True)
class FlyLook:
    """The number's flight into the HUD. Start in ticks, arc in px, steps in pre-made sizes."""

    start: int
    arc_px: float
    steps: int


@dataclass(frozen=True)
class PopLook:
    """The HUD level pop on arrival. Ticks from arrival, scales as multiples, widths in px."""

    ticks: int
    start_scale: float
    undershoot_scale: float
    undershoot_share: float
    flash_ticks: int
    steps: int
    bar_flash_ticks: int
    box_flash_ticks: int
    box_flash_width: int
    box_corner_cut: int


@dataclass(frozen=True)
class LevelUpLook:
    """Every look and motion value of the level-up moment. ``colors`` holds the 13 color keys."""

    colors: Mapping[str, RGB]
    band: BandLook
    number: NumberLook
    label: LabelLook
    hold: HoldLook
    pips: PipsLook
    ring: RingLook
    streaks: StreakLook
    glint: GlintLook
    bump: BumpLook
    fly: FlyLook
    pop: PopLook
