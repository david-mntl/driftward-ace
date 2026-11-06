"""Pause box tests: a glass box with PAUSE and the ENTER and SPACE keys, centered on the surface.

Contract: docs/contracts/systems/screens.md, Interface (ui/pause_box.py); 10-ui.md, `pause_box`
(locked content) and `pause_look`. Positions and colors are read from the drawn pixels, never from
a font size or a line height.
"""

import pygame

from ui.pause_box import draw_pause_box
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

SURFACE_SIZE: tuple[int, int] = (856, 518)
"""The window. Source: 10-ui.md, `window_screens`."""

BLACK: tuple[int, int, int] = (0, 0, 0)


def _surface(size: tuple[int, int] = SURFACE_SIZE) -> pygame.Surface:
    return pygame.Surface(size)


def _ink(surface: pygame.Surface) -> pygame.Rect:
    probe = surface.copy()
    probe.set_colorkey(BLACK)
    return probe.get_bounding_rect()


def _box(screen_rules: ScreenRules, size: tuple[int, int] = SURFACE_SIZE) -> pygame.Rect:
    box = pygame.Rect(0, 0, screen_rules.pause.w, screen_rules.pause.h)
    box.center = (size[0] // 2, size[1] // 2)
    return box


def test_the_box_is_centered_on_the_surface(look: ScreenLook) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    ink = _ink(surface)
    assert abs(ink.centerx - SURFACE_SIZE[0] // 2) <= 1
    assert abs(ink.centery - SURFACE_SIZE[1] // 2) <= 1


def test_the_box_is_centered_on_another_size(look: ScreenLook) -> None:
    surface = _surface((640, 480))
    draw_pause_box(surface, look)
    ink = _ink(surface)
    assert abs(ink.centerx - 320) <= 1
    assert abs(ink.centery - 240) <= 1


def test_the_box_has_the_size_the_tuning_file_says(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    box = _box(screen_rules)
    cyan = screen_rules.palette["frame_lights"]

    assert tuple(surface.get_at((box.left - 1, box.top - 1))[:3]) == cyan
    assert tuple(surface.get_at((box.right, box.bottom))[:3]) == cyan
    assert tuple(surface.get_at((box.centerx, box.top + 4))[:3]) != BLACK


def test_nothing_is_drawn_outside_the_box_and_its_glow(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    reach = 2 * screen_rules.glow.box_radius + screen_rules.glass.bracket_out + 2
    assert _box(screen_rules).inflate(2 * reach, 2 * reach).contains(_ink(surface))


def test_the_word_pause_is_lit_in_the_upper_half(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    box = _box(screen_rules)
    upper = surface.subsurface(pygame.Rect(box.left, box.top, box.width, box.height // 2 - 2))
    brightest = max(
        min(upper.get_at((x, y))[:3])
        for x in range(0, box.width, 1)
        for y in range(0, upper.get_height(), 1)
    )
    assert brightest > 200


def test_the_two_key_caps_sit_under_the_word(look: ScreenLook, screen_rules: ScreenRules) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    box = _box(screen_rules)
    cyan = screen_rules.palette["frame_lights"]
    lower = surface.subsurface(
        pygame.Rect(box.left, box.centery + 4, box.width, box.height // 2 - 8)
    )
    border_pixels = sum(
        1
        for x in range(lower.get_width())
        for y in range(lower.get_height())
        if abs(lower.get_at((x, y))[2] - cyan[2]) < 40 and lower.get_at((x, y))[1] > 90
    )
    assert border_pixels > 40


def test_no_icon_sits_beside_the_word(look: ScreenLook, screen_rules: ScreenRules) -> None:
    surface = _surface()
    draw_pause_box(surface, look)
    box = _box(screen_rules)
    side = surface.subsurface(pygame.Rect(box.left + 20, box.top + 20, 60, box.height // 2 - 24))
    assert (
        max(max(side.get_at((x, y))[:3]) for x in range(60) for y in range(side.get_height())) < 80
    )


def test_the_box_blurs_what_is_behind_it(look: ScreenLook, screen_rules: ScreenRules) -> None:
    assert screen_rules.pause.blur
    surface = _surface()
    for x in range(0, SURFACE_SIZE[0], 2):
        surface.fill((255, 255, 255), pygame.Rect(x, 0, 1, SURFACE_SIZE[1]))
    draw_pause_box(surface, look)
    box = _box(screen_rules)
    row = box.top + 6
    seen = {surface.get_at((x, row))[0] for x in range(box.left + 24, box.right - 24)}
    assert max(seen) - min(seen) < 60


def test_drawing_twice_gives_the_same_pixels(look: ScreenLook) -> None:
    first, second = _surface(), _surface()
    for surface in (first, second):
        surface.fill((40, 40, 60))
        draw_pause_box(surface, look)
    assert pygame.image.tobytes(first, "RGB") == pygame.image.tobytes(second, "RGB")


def test_the_box_keeps_what_is_outside_it(look: ScreenLook) -> None:
    surface = _surface()
    surface.fill((90, 40, 40))
    draw_pause_box(surface, look)
    assert tuple(surface.get_at((5, 5))[:3]) == (90, 40, 40)
    assert tuple(surface.get_at((850, 510))[:3]) == (90, 40, 40)
