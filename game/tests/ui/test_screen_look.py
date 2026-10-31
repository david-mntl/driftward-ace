"""Screen look tests: text with letter-spacing and glow, glass panels, key caps, choices, rulers.

Source: docs/contracts/systems/screens.md, Interface (`ScreenLook`); 10-ui.md, `screens_look` and
`ui_glow`. Positions are read from the drawn pixels, never from a font size.
"""

import dataclasses

import pygame

from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

SIZE: tuple[int, int] = (856, 518)
BLACK: tuple[int, int, int] = (0, 0, 0)


def _surface(size: tuple[int, int] = SIZE, gray: int = 0) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    return surface


def _ink(surface: pygame.Surface) -> pygame.Rect | None:
    """The bounding box of every pixel that is not pure black, or None when there is none."""
    probe = surface.copy()
    probe.set_colorkey(BLACK)
    rect = probe.get_bounding_rect()
    return rect if rect.width and rect.height else None


def test_letter_spacing_makes_a_word_wider(look: ScreenLook, screen_rules: ScreenRules) -> None:
    plain = sum(look._fonts["title"].size(char)[0] for char in "PAUSE")
    width, _ = look.text_size("PAUSE", "title")
    assert screen_rules.fonts.roles[0].name == "title"
    assert width > plain


def test_text_size_has_no_trailing_gap(look: ScreenLook) -> None:
    one, _ = look.text_size("A", "title")
    two, _ = look.text_size("AA", "title")
    assert two - one > one


def test_text_lands_on_its_anchor_and_returns_its_rect(look: ScreenLook) -> None:
    surface = _surface()
    rect = look.blit_text(surface, "PAUSE", "title", (255, 255, 255), {"center": (400, 200)})
    assert rect.center == (400, 200)
    assert rect.size == look.text_size("PAUSE", "title")
    assert _ink(surface) is not None


def _glowing(look: ScreenLook) -> ScreenLook:
    """A look with the same rules but every glow switched on (the shipped file has them at 0)."""
    glow = dataclasses.replace(
        look.rules.glow, box_strength=0.55, text_strength=0.6, icon_strength=0.5
    )
    return ScreenLook(dataclasses.replace(look.rules, glow=glow), look._fonts)


def test_the_shipped_screens_are_flat(look: ScreenLook) -> None:
    glow = look.rules.glow
    assert (glow.box_strength, glow.text_strength, glow.icon_strength) == (0.0, 0.0, 0.0)
    plain = _surface()
    look.blit_text(plain, "PAUSE", "title", (255, 255, 255), {"center": (400, 200)}, glow=True)
    flat = _surface()
    look.blit_text(flat, "PAUSE", "title", (255, 255, 255), {"center": (400, 200)}, glow=False)
    assert pygame.image.tobytes(plain, "RGB") == pygame.image.tobytes(flat, "RGB")


def test_glow_adds_light_around_the_text_but_not_far(look: ScreenLook) -> None:
    glowing = _glowing(look)
    flat, lit = _surface(), _surface()
    anchor = {"center": (400, 200)}
    glowing.blit_text(flat, "PAUSE", "title", (255, 255, 255), anchor, glow=False)
    glowing.blit_text(lit, "PAUSE", "title", (255, 255, 255), anchor, glow=True)
    glyphs = _ink(flat)
    assert glyphs is not None
    just_above = (glyphs.centerx, glyphs.top - 3)
    far_above = (glyphs.centerx, glyphs.top - 40)
    assert max(flat.get_at(just_above)[:3]) == 0
    assert max(lit.get_at(just_above)[:3]) > 0
    assert max(lit.get_at(far_above)[:3]) == 0


def test_glass_glow_reaches_past_the_brackets_only_when_it_is_on(look: ScreenLook) -> None:
    box = pygame.Rect(300, 200, 200, 100)
    flat, lit = _surface(), _surface()
    look.glass(flat, box, blur=False)
    _glowing(look).glass(lit, box, blur=False)
    outside = box.inflate(
        2 * look.rules.glass.bracket_out + 6, 2 * look.rules.glass.bracket_out + 6
    )
    lit_ink, flat_ink = _ink(lit), _ink(flat)
    assert lit_ink is not None
    assert flat_ink is not None
    assert not outside.contains(lit_ink)
    assert outside.contains(flat_ink)


def test_alpha_dims_the_text(look: ScreenLook) -> None:
    bright, dim = _surface(), _surface()
    look.blit_text(bright, "MENU", "button", (255, 255, 255), {"center": (100, 100)}, False)
    look.blit_text(dim, "MENU", "button", (255, 255, 255), {"center": (100, 100)}, False, 100)
    assert max(max(p[:3]) for p in _pixels(dim)) < max(max(p[:3]) for p in _pixels(bright))


def _pixels(surface: pygame.Surface) -> list[tuple[int, ...]]:
    width, height = surface.get_size()
    return [tuple(surface.get_at((x, y))) for y in range(height) for x in range(width)]


def test_drawing_the_same_text_twice_gives_the_same_pixels(look: ScreenLook) -> None:
    first, second = _surface(), _surface()
    for surface in (first, second):
        look.blit_text(surface, "RETRY", "button", (255, 255, 255), {"center": (200, 100)})
    assert pygame.image.tobytes(first, "RGB") == pygame.image.tobytes(second, "RGB")


def test_glass_fills_the_box_and_draws_brackets_on_the_corners(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    box = pygame.Rect(200, 150, 320, 120)
    look.glass(surface, box, blur=False)
    cyan = screen_rules.palette["frame_lights"]
    assert tuple(surface.get_at((box.centerx, box.centery + 1))[:3]) != BLACK
    assert tuple(surface.get_at((box.left - 1, box.top - 1))[:3]) == cyan
    assert tuple(surface.get_at((box.right, box.bottom))[:3]) == cyan
    assert tuple(surface.get_at((box.centerx, box.top - 1))[:3]) != cyan


def test_glass_stays_inside_its_glow_margin(look: ScreenLook) -> None:
    surface = _surface()
    box = pygame.Rect(300, 200, 200, 100)
    look.glass(surface, box, blur=False)
    margin = 2 * look.rules.glow.box_radius + look.rules.glass.bracket_out + 2
    ink = _ink(surface)
    assert ink is not None
    assert box.inflate(2 * margin, 2 * margin).contains(ink)


def test_glass_border_takes_the_color_it_is_given(look: ScreenLook) -> None:
    surface = _surface()
    box = pygame.Rect(200, 150, 320, 46)
    look.glass(surface, box, blur=False, color=(255, 209, 102))
    assert tuple(surface.get_at((box.left - 1, box.top - 1))[:3]) == (255, 209, 102)


def test_blur_softens_what_is_behind_the_box(look: ScreenLook) -> None:
    box = pygame.Rect(100, 100, 200, 100)
    stripes = pygame.Surface(SIZE)
    for x in range(0, SIZE[0], 2):
        stripes.fill((255, 255, 255), pygame.Rect(x, 0, 1, SIZE[1]))
    sharp, blurred = stripes.copy(), stripes.copy()
    look.blur_behind(blurred, box)
    row = box.top + 50
    spread_before = {sharp.get_at((x, row))[0] for x in range(box.left + 10, box.right - 10)}
    spread_after = {blurred.get_at((x, row))[0] for x in range(box.left + 10, box.right - 10)}
    assert spread_before == {0, 255}
    assert max(spread_after) - min(spread_after) < 100
    assert blurred.get_at((box.left - 5, row)) == sharp.get_at((box.left - 5, row))


def test_blur_off_leaves_the_picture_alone(look: ScreenLook) -> None:
    surface = _surface(gray=90)
    surface.fill((200, 10, 10), pygame.Rect(150, 150, 20, 20))
    before = pygame.image.tobytes(surface, "RGB")
    flat = ScreenLook(
        dataclasses.replace(look.rules, glass=dataclasses.replace(look.rules.glass, blur_down=1)),
        look._fonts,
    )
    flat.blur_behind(surface, pygame.Rect(100, 100, 120, 120))
    assert pygame.image.tobytes(surface, "RGB") == before


def test_key_row_is_as_wide_as_it_says(look: ScreenLook) -> None:
    surface = _surface()
    rect = look.blit_keys(surface, ("ENTER", "SPACE"), "BACK", {"center": (400, 300)})
    assert rect.size == look.keys_size(("ENTER", "SPACE"), "BACK")
    assert rect.center == (400, 300)
    ink = _ink(surface)
    assert ink is not None
    assert rect.inflate(2, 2).contains(ink)


def test_an_arrow_key_is_a_drawn_triangle(look: ScreenLook, screen_rules: ScreenRules) -> None:
    surface = _surface()
    rect = look.blit_keys(surface, ("UP",), None, {"center": (100, 100)})
    assert rect.width == screen_rules.keycap.min_w
    cyan = screen_rules.palette["frame_lights"]
    assert tuple(surface.get_at(rect.center)[:3]) == cyan


def test_the_selected_choice_is_lit_and_the_others_are_dim(look: ScreenLook) -> None:
    rect = pygame.Rect(0, 0, 150, 21)
    brightness = {}
    for state in ("selected", "dim", "off"):
        surface = _surface((150, 21))
        look.blit_choice(surface, "MENU", rect, "button", state)
        brightness[state] = sum(sum(p[:3]) for p in _pixels(surface))
    assert brightness["selected"] > brightness["dim"] > brightness["off"]


def test_the_selected_choice_has_brackets_at_both_ends(look: ScreenLook) -> None:
    surface = _surface((200, 30))
    rect = pygame.Rect(0, 0, 200, 30)
    look.blit_choice(surface, "PLAY", rect, "menu_item", "selected")
    inset = look.rules.choice.bracket_inset
    left = [surface.get_at((x, y))[2] for x in range(inset, inset + 8) for y in range(30)]
    right = [
        surface.get_at((x, y))[2] for x in range(200 - inset - 8, 200 - inset) for y in range(30)
    ]
    assert max(left) > 150
    assert max(right) > 150


def test_rulers_mark_both_sides_and_leave_the_middle_clear(look: ScreenLook) -> None:
    surface = _surface()
    look.blit_rulers(surface)
    inset = look.rules.rulers.inset_x
    assert _ink(surface) is not None
    rulers = look.rules.rulers
    left = {
        surface.get_at((x, y))[2] for x in range(inset, inset + rulers.w) for y in range(60, 200)
    }
    right = {
        surface.get_at((SIZE[0] - 1 - x, y))[2]
        for x in range(inset, inset + rulers.w)
        for y in range(60, 200)
    }
    assert max(left) > 0
    assert left == right
    middle = surface.subsurface(pygame.Rect(100, 0, SIZE[0] - 200, SIZE[1]))
    assert _ink(middle) is None


def test_rulers_can_be_switched_off(look: ScreenLook, screen_rules: ScreenRules) -> None:
    off = ScreenLook(
        dataclasses.replace(
            screen_rules, rulers=dataclasses.replace(screen_rules.rulers, enabled=False)
        ),
        look._fonts,
    )
    surface = _surface()
    off.blit_rulers(surface)
    assert _ink(surface) is None


def test_every_nickname_character_has_a_glyph_in_the_screen_font(look: ScreenLook) -> None:
    from core.saves import NICKNAME_CHARACTERS

    font = look._fonts["picker"]
    for character in NICKNAME_CHARACTERS:
        if character == " ":
            continue
        assert font.metrics(character)[0] is not None, character
    assert font.metrics("\u2212")[0] is not None


def test_text_size_is_the_same_the_second_time(look: ScreenLook) -> None:
    first = look.text_size("LEADERBOARD", "title")
    assert look.text_size("LEADERBOARD", "title") == first


def test_a_cached_picture_is_not_changed_by_drawing_it_dimmed(look: ScreenLook) -> None:
    bright_before, bright_after = _surface(), _surface()
    look.blit_text(bright_before, "RETRY", "button", (255, 255, 255), {"center": (100, 40)}, False)
    look.blit_text(_surface(), "RETRY", "button", (255, 255, 255), {"center": (100, 40)}, False, 60)
    look.blit_text(bright_after, "RETRY", "button", (255, 255, 255), {"center": (100, 40)}, False)
    assert pygame.image.tobytes(bright_before, "RGB") == pygame.image.tobytes(bright_after, "RGB")
