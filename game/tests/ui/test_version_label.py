"""Version tests: the shipped VERSION file, its loader, and the label in the bottom-left corner.

Source: docs/contracts/systems/screens.md, Interface (app/version.py, ui/version_label.py) and
Presentation, Version label; 10-ui.md, `version_label`. The margins and the alpha come from
tuning/screens.json (the `look` fixture).
"""

from pathlib import Path

import pygame
import pytest

import app.version as version_module
from app.version import VERSION_FILE, load_version
from ui.screen_look import ScreenLook
from ui.version_label import VERSION_PREFIX, draw_version

WINDOW: tuple[int, int] = (856, 518)
"""The window the label sits in. Source: hud.json, window."""


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    path = tmp_path / "VERSION"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(version_module, "VERSION_FILE", path)


def _ink(surface: pygame.Surface) -> pygame.Rect | None:
    """Return the bounding box of every pixel that is not pure black."""
    mask: pygame.Mask = pygame.mask.from_threshold(surface, (0, 0, 0), (1, 1, 1, 255))
    mask.invert()
    boxes: list[pygame.Rect] = mask.get_bounding_rects()
    if not boxes:
        return None
    return boxes[0].unionall(boxes[1:])


def _label(look: ScreenLook, version: str = "1.0.0") -> pygame.Surface:
    surface = pygame.Surface(WINDOW)
    draw_version(surface, look, version)
    return surface


def test_the_shipped_version_file_is_at_the_game_root() -> None:
    assert VERSION_FILE.name == "VERSION"
    assert (VERSION_FILE.parent / "main.py").is_file()


def test_the_shipped_version_loads() -> None:
    assert version_module.VERSION_FORMAT.fullmatch(load_version()) is not None


def test_the_trailing_newline_is_dropped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, "2.13.0\n")
    assert load_version() == "2.13.0"


@pytest.mark.parametrize("text", ["", "1.0", "v1.0.0", "1.0.0.1", "01.0.0", "1.0.x", "1. 0.0"])
def test_a_bad_version_names_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    _write(tmp_path, monkeypatch, text)
    with pytest.raises(ValueError, match=r"VERSION: .* is not MAJOR\.MINOR\.PATCH"):
        load_version()


def test_a_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(version_module, "VERSION_FILE", tmp_path / "VERSION")
    with pytest.raises(FileNotFoundError):
        load_version()


def test_the_label_is_the_version_with_a_v_in_front() -> None:
    assert VERSION_PREFIX == "v"


def test_the_label_sits_in_the_bottom_left_corner(look: ScreenLook) -> None:
    rules = look.rules.version
    ink = _ink(_label(look))
    assert ink is not None
    assert abs(ink.left - rules.margin_left) <= 2
    assert abs(ink.bottom - (WINDOW[1] - rules.margin_bottom)) <= 3
    assert ink.right < WINDOW[0] // 4
    assert ink.top > WINDOW[1] * 3 // 4


def test_the_label_is_dim_plating(look: ScreenLook) -> None:
    surface = _label(look)
    ink = _ink(surface)
    assert ink is not None
    brightest = max(
        max(surface.get_at((x, y))[:3])
        for x in range(ink.left, ink.right)
        for y in range(ink.top, ink.bottom)
    )
    plating_top = max(look.palette["plating"])
    assert brightest <= plating_top * look.rules.version.text_alpha / 255 + 3


def test_a_longer_version_runs_to_the_right(look: ScreenLook) -> None:
    short = _ink(_label(look, "1.0.0"))
    long = _ink(_label(look, "12.40.103"))
    assert short is not None
    assert long is not None
    assert long.left == short.left
    assert long.right > short.right
