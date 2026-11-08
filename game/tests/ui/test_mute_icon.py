"""Mute icon tests: `MuteIconView.draw`, and the shipped picture and tuning that feed it.

Every number comes from `game/tuning/mute_icon.json` (margin, size), `game/tuning/hud.json` (the
window and the play area's corner) and `core.world` (the play area's size). The pictures drawn are
stand-ins built here; only the shipped-picture test opens `game/assets/mute_icon.png`.

Source: docs/contracts/systems/mute-icon.md, Interface, Rules, Look (2, 5), Placement (6, 8, 9),
Loading (15), Cost (18); 10-ui.md, `mute_icon_look` and `mute_icon_place`.
"""

import json
from pathlib import Path

import pygame
import pytest

from core.world import SCREEN_H, SCREEN_W
from ui.mute_icon import MuteIconLook, MuteIconView

GAME_DIR: Path = Path(__file__).resolve().parents[2]
TUNING: dict[str, object] = json.loads((GAME_DIR / "tuning" / "mute_icon.json").read_text())
HUD: dict[str, dict[str, int]] = json.loads((GAME_DIR / "tuning" / "hud.json").read_text())
PICTURE: Path = GAME_DIR / "assets" / "mute_icon.png"

MARGIN: int = int(TUNING["margin"])  # type: ignore[call-overload]
SIZE: int = int(TUNING["size"])  # type: ignore[call-overload]
WINDOW_W: int = HUD["window"]["width"]
WINDOW_H: int = HUD["window"]["height"]
PLAY_AREA: pygame.Rect = pygame.Rect(
    HUD["window"]["field_x"], HUD["window"]["field_y"], SCREEN_W, SCREEN_H
)
ICON_RECT: pygame.Rect = pygame.Rect(WINDOW_W - MARGIN - SIZE, WINDOW_H - MARGIN - SIZE, SIZE, SIZE)

STAND_IN: tuple[int, int, int, int] = (250, 20, 20, 255)
"""An opaque stand-in for the picture."""


def _pattern() -> bytes:
    raw = bytearray()
    for y in range(WINDOW_H):
        for x in range(WINDOW_W):
            raw += bytes(((x * 3) % 200, (y * 5) % 200, (x + y) % 200))
    return bytes(raw)


PATTERN: bytes = _pattern()
"""Window pixels: red under 200 everywhere, so the stand-in (red 250) never matches one."""


def make_window() -> pygame.Surface:
    """A window-sized surface whose every pixel has its own color, so a shift shows."""
    return pygame.image.frombytes(PATTERN, (WINDOW_W, WINDOW_H), "RGB")


def make_view(image: pygame.Surface) -> MuteIconView:
    return MuteIconView(MuteIconLook(margin=MARGIN, size=SIZE), image)


def opaque_image() -> pygame.Surface:
    image = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    image.fill(STAND_IN)
    return image


def changed_pixels(before: pygame.Surface, after: pygame.Surface) -> set[tuple[int, int]]:
    """Every (x, y) whose RGB differs, read from the pixel bytes."""
    width, height = before.get_size()
    a = pygame.image.tobytes(before, "RGB")
    b = pygame.image.tobytes(after, "RGB")
    row = width * 3
    found: set[tuple[int, int]] = set()
    for y in range(height):
        if a[y * row : (y + 1) * row] == b[y * row : (y + 1) * row]:
            continue
        for x in range(width):
            i = y * row + x * 3
            if a[i : i + 3] != b[i : i + 3]:
                found.add((x, y))
    return found


def test_unmuted_draw_leaves_every_pixel(pygame_headless: None) -> None:
    window = make_window()
    before = window.copy()
    make_view(opaque_image()).draw(window, False)
    assert pygame.image.tobytes(window, "RGB") == pygame.image.tobytes(before, "RGB")


def test_muted_draw_puts_the_picture_margin_from_the_corner(pygame_headless: None) -> None:
    window = make_window()
    before = window.copy()
    make_view(opaque_image()).draw(window, True)
    changed = changed_pixels(before, window)
    assert len(changed) == SIZE * SIZE
    xs = [x for x, _ in changed]
    ys = [y for _, y in changed]
    assert (max(xs) + 1, max(ys) + 1) == (WINDOW_W - MARGIN, WINDOW_H - MARGIN)
    assert (min(xs), min(ys)) == (WINDOW_W - MARGIN - SIZE, WINDOW_H - MARGIN - SIZE)
    for x, y in changed:
        assert window.get_at((x, y))[:3] == STAND_IN[:3]


def test_muted_draw_changes_nothing_outside_the_rectangle(pygame_headless: None) -> None:
    window = make_window()
    before = window.copy()
    make_view(opaque_image()).draw(window, True)
    outside = changed_pixels(before, window) - {
        (x, y)
        for x in range(ICON_RECT.left, ICON_RECT.right)
        for y in range(ICON_RECT.top, ICON_RECT.bottom)
    }
    assert outside == set()
    play_before = before.subsurface(PLAY_AREA)
    play_after = window.subsurface(PLAY_AREA)
    assert pygame.image.tobytes(play_after, "RGB") == pygame.image.tobytes(play_before, "RGB")


@pytest.mark.determinism
def test_drawing_twice_or_a_frame_later_gives_the_same_pixels(pygame_headless: None) -> None:
    view = make_view(opaque_image())
    once = make_window()
    view.draw(once, True)
    twice = make_window()
    view.draw(twice, True)
    view.draw(twice, True)
    later = make_window()
    view.draw(later, True)
    assert pygame.image.tobytes(twice, "RGB") == pygame.image.tobytes(once, "RGB")
    assert pygame.image.tobytes(later, "RGB") == pygame.image.tobytes(once, "RGB")


def test_transparent_region_leaves_the_pixels_under_it(pygame_headless: None) -> None:
    window = make_window()
    before = window.copy()
    image = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    image.fill((0, 0, 0, 0))
    half = SIZE // 2
    image.fill(STAND_IN, pygame.Rect(half, 0, SIZE - half, SIZE))
    make_view(image).draw(window, True)
    for y in range(ICON_RECT.top, ICON_RECT.bottom):
        for x in range(ICON_RECT.left, ICON_RECT.right):
            if x - ICON_RECT.left < half:
                assert window.get_at((x, y)) == before.get_at((x, y)), (x, y)
            else:
                assert window.get_at((x, y))[:3] == STAND_IN[:3], (x, y)


def test_shipped_picture_is_size_square_with_alpha(pygame_headless: None) -> None:
    image = pygame.image.load(str(PICTURE))
    assert image.get_size() == (SIZE, SIZE)
    assert image.get_masks()[3] != 0, "the picture has no alpha channel"
    alphas = set(pygame.image.tobytes(image, "RGBA")[3::4])
    assert 0 in alphas, "no transparent pixel"
    assert 255 in alphas, "no opaque pixel"


def test_tuning_rectangle_is_inside_the_window_and_clear_of_the_play_area() -> None:
    assert MARGIN >= 0
    assert SIZE >= 1
    assert pygame.Rect(0, 0, WINDOW_W, WINDOW_H).contains(ICON_RECT)
    assert not ICON_RECT.colliderect(PLAY_AREA)
