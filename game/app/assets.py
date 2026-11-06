"""Loads the painted art the game shows. Reads files, so it lives in app/, not ui/."""

import logging
import math
from pathlib import Path

import pygame

from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt, BackgroundRules, build_background
from ui.hud import HEART_CELL_COUNT, HudArt
from ui.hud_rules import HudRules
from ui.level_up_rules import LevelUpLook
from ui.level_up_view import LevelUpFonts
from ui.screen_rules import ScreenRules

log = logging.getLogger(__name__)

ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "assets"
"""The assets folder, next to main.py. Found the same way as the tuning folder."""

SWAY_FRAMES: int = 12
"""Frames in the far painting's sway loop. Must match KEYFRAMES in tools/art/background_sway.py."""

SWAY_FILES: tuple[str, ...] = tuple(
    f"background_sway_{index:02d}.png" for index in range(SWAY_FRAMES)
)
"""The far-layer painting as a loop of frames, each SCREEN_W x SCREEN_H px. Baked from
background.png by tools/art/background_sway.py. Source: 12-art-and-audio.md, Background, far
layer."""

PLANET_FILES: tuple[str, ...] = tuple(f"bg_planet_{index}.png" for index in range(6))
"""The broken planets of the middle layer, each cut to its own bounds. Source:
12-art-and-audio.md, Background, middle layer."""


def load_background(rules: BackgroundRules) -> BackgroundArt:
    """Load the painting's sway frames and the planets, and build the background from them.

    Call it once, after the display is open. A missing file raises FileNotFoundError (from
    pygame). A frame that is not SCREEN_W x SCREEN_H raises ValueError naming the file.
    """
    sway: tuple[pygame.Surface, ...] = tuple(_load_frame(name) for name in SWAY_FILES)
    planets: tuple[pygame.Surface, ...] = tuple(_load(name, alpha=True) for name in PLANET_FILES)
    log.info("background loaded %d painting frames and %d planets", len(sway), len(planets))
    return build_background(sway, planets, rules)


def _load_frame(file: str) -> pygame.Surface:
    """Read one far-painting frame and check it is screen size."""
    frame: pygame.Surface = _load(file, alpha=False)
    if frame.get_size() != (SCREEN_W, SCREEN_H):
        raise ValueError(
            f"assets/{file}: size is {frame.get_size()}, "
            f"expected {(SCREEN_W, SCREEN_H)} (screen size)"
        )
    return frame


def _load(file: str, alpha: bool) -> pygame.Surface:
    """Read one image and convert it to the display format, keeping its alpha if `alpha`."""
    image: pygame.Surface = pygame.image.load(ASSETS_DIR / file)
    return image.convert_alpha() if alpha else image.convert()


def load_hud_art(rules: HudRules) -> HudArt:
    """Load the HUD's baked pictures and its two fonts, and check each against the rules.

    Call it once, after the display is open. A missing file raises FileNotFoundError (from pygame).
    A picture whose size doesn't fit the rules raises ValueError naming the file: run
    tools/art/hud_panel.py again after changing hud.json. Source: docs/contracts/systems/hud.md.
    """
    window, panel, motion = rules.window, rules.panel, rules.motion
    frame_size: tuple[int, int] = (panel.x + rules.frame.pillar_width, window.height)
    box = rules.hearts.ship_box
    wedge: int = 2 * rules.graze.wedge_radius + 2
    ring: int = 2 * math.ceil(motion.ring_radius * motion.ring_to) + 2
    art: HudArt = HudArt(
        frame=_load_sized("hud_frame.png", True, frame_size),
        sheen=_load_sized("hud_sheen.png", True, (SCREEN_W, SCREEN_H)),
        panel=_load_sized("hud_panel.png", False, (panel.width, window.height)),
        ship=_load_sized("hud_ship.png", True, (box[2], box[3])),
        hearts=_load_cells(
            "hud_hearts.png", rules.hearts.cell_w, rules.hearts.cell_h, HEART_CELL_COUNT
        ),
        radar=_load_cells("hud_radar.png", wedge, wedge, motion.sweep_frames),
        ring=_load_cells("hud_ring.png", ring, ring, motion.ring_frames),
        scan=_load_wide("hud_scan.png", motion.scan_w),
        label_font=pygame.font.Font(ASSETS_DIR / rules.fonts.label_file, rules.fonts.label_size),
        fonts={
            "value": pygame.font.Font(ASSETS_DIR / rules.fonts.ui_file, rules.fonts.value_size),
            "tile": pygame.font.Font(ASSETS_DIR / rules.fonts.ui_file, rules.fonts.tile_size),
            "graze": pygame.font.Font(ASSETS_DIR / rules.fonts.ui_file, rules.fonts.graze_size),
            "level": pygame.font.Font(ASSETS_DIR / rules.fonts.ui_file, rules.fonts.level_size),
        },
    )
    log.info(
        "hud art loaded %d hearts, %d radar frames, %d ring frames",
        len(art.hearts),
        len(art.radar),
        len(art.ring),
    )
    return art


def _load_sized(file: str, alpha: bool, size: tuple[int, int]) -> pygame.Surface:
    """Read one picture and check it is exactly ``size``."""
    image: pygame.Surface = _load(file, alpha)
    if image.get_size() != size:
        raise ValueError(
            f"assets/{file}: size is {image.get_size()}, expected {size} (tuning/hud.json); "
            "run tools/art/hud_panel.py"
        )
    return image


def _load_cells(file: str, width: int, height: int, count: int) -> tuple[pygame.Surface, ...]:
    """Read a strip of ``count`` cells of width x height, left to right, and cut it into cells."""
    strip: pygame.Surface = _load_sized(file, True, (width * count, height))
    return tuple(
        strip.subsurface(pygame.Rect(i * width, 0, width, height)).copy() for i in range(count)
    )


def _load_wide(file: str, width: int) -> pygame.Surface:
    """Read one picture and check it is exactly ``width`` px wide, whatever its height."""
    image: pygame.Surface = _load(file, True)
    if image.get_width() != width:
        raise ValueError(
            f"assets/{file}: width is {image.get_width()}, expected {width} (tuning/hud.json); "
            "run tools/art/hud_panel.py"
        )
    return image


def load_screen_fonts(rules: ScreenRules) -> dict[str, pygame.font.Font]:
    """Load the screens' font at the size of every text role. Call it once, after pygame.init().

    A missing file raises FileNotFoundError (from pygame). Source: systems/screens.md, Interface.
    """
    path: Path = ASSETS_DIR / rules.fonts.text_file
    fonts: dict[str, pygame.font.Font] = {
        role.name: pygame.font.Font(path, role.size) for role in rules.fonts.roles
    }
    log.info("screen fonts loaded %d roles from %s", len(fonts), rules.fonts.text_file)
    return fonts


def load_level_up_fonts(hud_rules: HudRules, look: LevelUpLook) -> LevelUpFonts:
    """Load the banner's two fonts: Exo 2 Bold for the number, Share Tech Mono for LEVEL.

    Call it once, after pygame.init(). A missing file raises FileNotFoundError (from pygame).
    Source: systems/level-up/tuning.md, Interface.
    """
    fonts: LevelUpFonts = LevelUpFonts(
        number=pygame.font.Font(ASSETS_DIR / hud_rules.fonts.ui_file, look.number.font_size),
        label=pygame.font.Font(ASSETS_DIR / hud_rules.fonts.label_file, look.label.font_size),
    )
    log.info(
        "level up fonts loaded number=%s label=%s",
        hud_rules.fonts.ui_file,
        hud_rules.fonts.label_file,
    )
    return fonts
