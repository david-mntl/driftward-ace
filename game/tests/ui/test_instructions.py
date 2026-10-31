"""Instructions page tests: the title, six glass cards with an icon, a topic and a caption, and the
footer, in the Glass Cockpit look.

Spec: 10-ui.md, `instructions_text_and_look`, `screens_look` and `window_screens`; the values are
in tuning/screens.json (the `screen_rules` fixture). The look is the `look` fixture.

Positions and colors are read from the drawn pixels, never from a font metric. The page is drawn
on a black surface, so any lit pixel is ink: text, an icon, the rulers or glow. The glass is read
by drawing over a lighter grey, where a see-through fill differs from both the grey and the
panel color.
"""

from dataclasses import replace
from itertools import combinations

import pygame

from app.assets import load_screen_fonts
from ui.instructions import (
    CARD_COLOR_KEYS,
    INSTRUCTION_SECTIONS,
    _wrap,
    card_rects,
    draw_instructions,
    icon_rect,
)
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

WINDOW: tuple[int, int] = (856, 518)
"""The window the page fills. Source: 10-ui.md, window_screens; hud.json, window."""

OTHER_SIZES: tuple[tuple[int, int], ...] = ((640, 480), (900, 600))
"""Other surfaces the page still has to fit."""

SECTIONS: tuple[tuple[str, str], ...] = (
    ("FLY", "Hold to thrust. Let go and gravity takes you."),
    ("PAUSE", "Press again to go on."),
    ("GRAZE", "Skim a hazard without touching. Score."),
    ("WARNING", "A hazard is coming. Get clear."),
    ("FALL", "Fall off the bottom, lose a life."),
    ("COINS", "Points. The best ones sit near danger."),
)
"""Source: 10-ui.md, instructions_text_and_look."""

GREY: int = 180
"""The lighter backdrop the glass is read on."""

BLEND_TOLERANCE: int = 3
"""SDL's alpha blend may be a few levels off the exact result."""

LIT: int = 120
"""A channel above this is a line or text. The glass fill and its scan lines stay well below."""


def _page(look: ScreenLook, size: tuple[int, int] = WINDOW, grey: int = 0) -> pygame.Surface:
    """Draw the page on a surface of ``size`` filled with ``grey`` and return it."""
    surface: pygame.Surface = pygame.Surface(size)
    surface.fill((grey, grey, grey))
    draw_instructions(surface, look)
    return surface


def _ink(surface: pygame.Surface, area: pygame.Rect) -> pygame.Rect | None:
    """Return the bounding box of the lit pixels (not pure black) inside ``area``, in surface px."""
    sub: pygame.Surface = surface.subsurface(area)
    mask: pygame.Mask = pygame.mask.from_threshold(sub, (0, 0, 0), (1, 1, 1, 255))
    mask.invert()
    boxes: list[pygame.Rect] = mask.get_bounding_rects()
    if not boxes:
        return None
    box: pygame.Rect = boxes[0].unionall(boxes[1:])
    return box.move(area.topleft)


def _lit_ink(surface: pygame.Surface, area: pygame.Rect) -> pygame.Rect | None:
    """Return the bounding box of the pixels with a channel above ``LIT`` inside ``area``.

    Glow and the glass fill are dimmer than this, so only lines and text count.
    """
    sub: pygame.Surface = surface.subsurface(area)
    mask: pygame.Mask = pygame.mask.from_threshold(sub, (0, 0, 0), (LIT, LIT, LIT, 255))
    mask.invert()
    boxes: list[pygame.Rect] = mask.get_bounding_rects()
    if not boxes:
        return None
    return boxes[0].unionall(boxes[1:]).move(area.topleft)


def _bright(surface: pygame.Surface, area: pygame.Rect) -> int:
    """Count the pixels inside ``area`` with a channel above ``LIT``."""
    sub: pygame.Surface = surface.subsurface(area)
    mask: pygame.Mask = pygame.mask.from_threshold(sub, (0, 0, 0), (LIT, LIT, LIT, 255))
    return area.width * area.height - mask.count()


def _closest(surface: pygame.Surface, area: pygame.Rect, color: tuple[int, int, int]) -> int:
    """Return the smallest summed channel distance between ``color`` and any pixel in ``area``."""
    best: int = 3 * 255
    for x in range(area.left, area.right):
        for y in range(area.top, area.bottom):
            pixel = surface.get_at((x, y))
            best = min(best, sum(abs(pixel[i] - color[i]) for i in range(3)))
    return best


def test_the_six_sections_hold_the_gdd_text() -> None:
    assert INSTRUCTION_SECTIONS == SECTIONS


def test_each_card_has_its_own_color_key(screen_rules: ScreenRules) -> None:
    assert len(CARD_COLOR_KEYS) == len(SECTIONS)
    assert all(key in screen_rules.palette for key in CARD_COLOR_KEYS)


def test_cards_are_six_in_reading_order(look: ScreenLook) -> None:
    rects = card_rects(look, WINDOW)
    assert len(rects) == len(SECTIONS)
    columns = look.rules.instructions.columns
    for index, rect in enumerate(rects):
        assert (rect.left, rect.top) == (
            rects[index % columns].left,
            rects[index // columns * columns].top,
        )
    assert rects[0].left < rects[1].left
    assert rects[0].top < rects[2].top


def test_cards_fill_the_space_between_head_and_footer(look: ScreenLook) -> None:
    rules = look.rules.instructions
    rects = card_rects(look, WINDOW)
    top = rules.margin_top + rules.head_h
    bottom = WINDOW[1] - rules.margin_bottom - rules.foot_h
    rows = len(SECTIONS) // rules.columns
    assert min(r.top for r in rects) == top
    assert 0 <= bottom - max(r.bottom for r in rects) < rows
    assert min(r.left for r in rects) == rules.margin_x
    assert 0 <= WINDOW[0] - rules.margin_x - max(r.right for r in rects) < rules.columns


def test_cards_are_one_gap_apart_and_never_overlap(look: ScreenLook) -> None:
    rects = card_rects(look, WINDOW)
    for a, b in combinations(rects, 2):
        assert not a.colliderect(b)
    gap = look.rules.instructions.gap
    assert rects[1].left - rects[0].right == gap
    assert rects[2].top - rects[0].bottom == gap


def test_every_icon_box_sits_inside_its_card(look: ScreenLook) -> None:
    rules = look.rules.instructions
    for card in card_rects(look, WINDOW):
        box = icon_rect(look, card)
        assert card.contains(box)
        assert box.size == (rules.icon_w, rules.icon_h)
        assert box.left == card.left + rules.pad_x


def test_each_card_draws_an_icon_in_its_box(look: ScreenLook) -> None:
    page = _page(look)
    for card in card_rects(look, WINDOW):
        assert _bright(page, icon_rect(look, card)) > 50


def test_the_six_icons_are_all_different(look: ScreenLook) -> None:
    page = _page(look)
    boxes = [icon_rect(look, card) for card in card_rects(look, WINDOW)]
    pictures = [pygame.image.tobytes(page.subsurface(box), "RGB") for box in boxes]
    for a, b in combinations(pictures, 2):
        assert a != b


def test_each_topic_is_lit_in_its_card_color(look: ScreenLook) -> None:
    page = _page(look)
    rules = look.rules.instructions
    for card, key in zip(card_rects(look, WINDOW), CARD_COLOR_KEYS, strict=True):
        left = icon_rect(look, card).right + rules.text_gap
        area = pygame.Rect(
            left, card.top + 6, card.right - rules.pad_x - left, card.height // 2 - 6
        )
        assert _closest(page, area, look.palette[key]) < 90


def test_captions_are_plating_and_stay_inside_the_card(look: ScreenLook) -> None:
    page = _page(look)
    rules = look.rules.instructions
    plating = look.palette["plating"]
    for card in card_rects(look, WINDOW):
        left = icon_rect(look, card).right + rules.text_gap
        text = pygame.Rect(left, card.top + 4, card.right - rules.pad_x - left, card.height - 8)
        assert _closest(page, text, plating) < 130
        bracket = look.rules.glass.bracket_len
        outside = pygame.Rect(
            card.right - rules.pad_x + 1,
            card.top + bracket + 2,
            rules.pad_x - 4,
            card.height - 2 * bracket - 4,
        )
        assert _bright(page, outside) == 0


def test_a_caption_wraps_to_fit_its_width(look: ScreenLook) -> None:
    text = "Skim a hazard without touching. Score."
    lines = _wrap(look, text, 120)
    assert len(lines) > 1
    assert " ".join(lines) == text
    assert all(look.text_size(line, "card_text")[0] <= 120 for line in lines)


def test_a_word_wider_than_the_width_keeps_its_own_line(look: ScreenLook) -> None:
    assert _wrap(look, "WARNING now", 5) == ["WARNING", "now"]


def test_cards_are_see_through_glass(look: ScreenLook) -> None:
    rules = look.rules
    glass = rules.glass
    dark = _page(look)
    light = _page(look, grey=GREY)
    alpha = glass.fill_alpha / 255
    for card in card_rects(look, WINDOW):
        row = card.height - 24
        while row % glass.scan_pitch == glass.scan_pitch - 1:
            row -= 1
        point = (card.right - 30, card.top + row)
        assert dark.get_at(point)[:3] != (0, 0, 0)
        expected = [
            round(rules.palette["panel_body"][i] * alpha + GREY * (1 - alpha)) for i in range(3)
        ]
        got = light.get_at(point)
        assert all(abs(got[i] - expected[i]) <= BLEND_TOLERANCE for i in range(3))


def test_the_title_is_centered_at_the_top(look: ScreenLook) -> None:
    rules = look.rules.instructions
    head = pygame.Rect(60, 0, WINDOW[0] - 120, rules.margin_top + rules.head_h - 1)
    ink = _lit_ink(_page(look), head)
    assert ink is not None
    assert abs(ink.centerx - WINDOW[0] // 2) <= 2
    assert ink.bottom < rules.margin_top + rules.head_h


def test_the_footer_keys_are_centered_in_the_footer_band(look: ScreenLook) -> None:
    rules = look.rules.instructions
    foot_top = WINDOW[1] - rules.margin_bottom - rules.foot_h
    band = pygame.Rect(60, foot_top, WINDOW[0] - 120, rules.foot_h)
    ink = _lit_ink(_page(look), band)
    assert ink is not None
    assert abs(ink.centerx - WINDOW[0] // 2) <= 2
    assert abs(ink.centery - band.centery) <= 2


def test_nothing_is_drawn_outside_the_margins_except_the_rulers(look: ScreenLook) -> None:
    rules = look.rules
    glass = rules.glass
    reach = 2 * rules.glow.box_radius + glass.bracket_out + glass.bracket_w
    ruler_end = rules.rulers.inset_x + rules.rulers.w
    inner = pygame.Rect(ruler_end + 1, 0, WINDOW[0] - 2 * (ruler_end + 1), WINDOW[1])
    ink = _ink(_page(look), inner)
    assert ink is not None
    limit = pygame.Rect(
        rules.instructions.margin_x - reach,
        rules.instructions.margin_top - reach,
        WINDOW[0] - 2 * (rules.instructions.margin_x - reach),
        WINDOW[1] - rules.instructions.margin_top - rules.instructions.margin_bottom + 2 * reach,
    )
    assert limit.contains(ink)


def test_the_rulers_are_drawn_down_both_sides_when_on(look: ScreenLook) -> None:
    rulers = look.rules.rulers
    page = _page(look)
    left = pygame.Rect(0, 0, rulers.inset_x + rulers.w, WINDOW[1])
    right = pygame.Rect(
        WINDOW[0] - rulers.inset_x - rulers.w, 0, rulers.inset_x + rulers.w, WINDOW[1]
    )
    assert _bright(page, left) > 0
    assert _bright(page, right) > 0


def test_the_rulers_are_gone_when_switched_off(screen_rules: ScreenRules) -> None:
    quiet = replace(screen_rules, rulers=replace(screen_rules.rulers, enabled=False))
    look = ScreenLook(quiet, load_screen_fonts(quiet))
    column = pygame.Rect(0, 0, quiet.rulers.inset_x + quiet.rulers.w, WINDOW[1])
    assert _ink(_page(look), column) is None


def test_drawing_twice_gives_the_same_pixels(look: ScreenLook) -> None:
    first = pygame.image.tobytes(_page(look), "RGB")
    second = pygame.image.tobytes(_page(look), "RGB")
    assert first == second


def test_the_page_fits_other_surface_sizes(look: ScreenLook) -> None:
    for size in OTHER_SIZES:
        rects = card_rects(look, size)
        area = pygame.Rect((0, 0), size)
        assert all(area.contains(r) for r in rects)
        assert _ink(_page(look, size), area) is not None
