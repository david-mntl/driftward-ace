"""Credits page tests: the credit text, the card stack, the title, the footer and the drawing rules.

Contract: docs/contracts/systems/screens.md, Interface (ui/credits.py) and Presentation, Credits
page; 10-ui.md, `credits_page`. Every size and color is read from the real tuning/screens.json
through the `screen_rules` fixture, so a changed value moves the test with it.

Positions are read from the drawn pixels where the page is drawn: on a black surface a bright pixel
is ink.
"""

from itertools import pairwise
from pathlib import Path

import pygame

import ui.credits as credits_module
from ui.credits import CREDIT_CARDS, LINK_COLOR_KEY, card_rects, draw_credits
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

WINDOW: tuple[int, int] = (856, 518)
"""The window the page fills. Source: 10-ui.md, window_screens; hud.json, window."""

OTHER_SIZES: tuple[tuple[int, int], ...] = ((640, 480), (900, 600))
"""Other surfaces the page still has to fit."""

LIT: int = 100
"""A pixel with a channel above this is lit ink; the glass fill and scan lines stay below it."""

CC_BY_REQUIRED: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "MUSIC",
        (
            "Lo-fi Music Guitar (Loop)",
            "Migfus20",
            "freesound.org/people/Migfus20/sounds/569791/",
            "Rain, sheet roof.wav",
            "snarcle",
            "freesound.org/people/snarcle/sounds/569370/",
            "Changed:",
            "CC BY 4.0",
            "creativecommons.org/licenses/by/4.0/",
        ),
    ),
    (
        "LEVEL-UP SOUND",
        (
            "Achievement 2",
            "sonically_sound",
            "freesound.org/people/Sonically_Sound/sounds/625715/",
            "Changed:",
            "CC BY 4.0",
            "creativecommons.org/licenses/by/4.0/",
        ),
    ),
)
"""What each CC BY 4.0 card must name: the work, the author, the source, the changes and the
license. Source: 12-art-and-audio.md, rule 12; game/assets/CREDITS.md."""


def _page(look: ScreenLook, size: tuple[int, int] = WINDOW, grey: int = 0) -> pygame.Surface:
    """Draw the page on a surface of ``size`` filled with ``grey`` and return it."""
    surface: pygame.Surface = pygame.Surface(size)
    surface.fill((grey, grey, grey))
    draw_credits(surface, look)
    return surface


def _lit_ink(surface: pygame.Surface, area: pygame.Rect) -> pygame.Rect | None:
    """Return the bounding box of the lit pixels inside ``area``, in surface px; None if none."""
    sub: pygame.Surface = surface.subsurface(area.clip(surface.get_rect()))
    mask: pygame.Mask = pygame.mask.from_threshold(sub, (0, 0, 0), (LIT, LIT, LIT, 255))
    mask.invert()
    boxes: list[pygame.Rect] = mask.get_bounding_rects()
    if not boxes:
        return None
    return boxes[0].unionall(boxes[1:]).move(area.topleft)


def _card_text(heading: str) -> str:
    """Return every line of the card with ``heading``, joined by new lines."""
    card = next(card for card in CREDIT_CARDS if card.heading == heading)
    return "\n".join(line.text for line in card.lines)


def test_each_cc_by_card_names_the_work_the_author_the_source_the_changes_and_the_license() -> None:
    for heading, required in CC_BY_REQUIRED:
        text = _card_text(heading)
        for part in required:
            assert part in text, f"{heading}: {part!r} is missing"


def test_the_source_links_are_link_lines() -> None:
    links = {line.text for card in CREDIT_CARDS for line in card.lines if line.link}
    for _, required in CC_BY_REQUIRED:
        for part in required:
            if part.startswith("freesound.org"):
                assert part in links


def test_the_source_never_holds_text_the_pygbag_build_rewrites() -> None:
    # pygbag's build replaces .wav, .mp3, .bmp and .xm followed by a double quote in every Python
    # file, which would change the credited file name in the browser.
    source = Path(credits_module.__file__).read_text(encoding="utf-8")
    for extension in ("wav", "mp3", "bmp", "xm"):
        assert f'.{extension}"' not in source
    assert "Rain, sheet roof.wav" in _card_text("MUSIC")


def test_the_courtesy_card_names_the_game_over_sound_both_fonts_and_piskel() -> None:
    text = _card_text("ALSO USED")
    parts = ("Game Over Arcade", "Mountain_Man", "CC0", "Exo 2", "Share Tech Mono", "OFL")
    for part in (*parts, "Piskel", "Apache 2.0"):
        assert part in text, f"{part!r} is missing"


def test_every_color_key_is_in_the_palette(screen_rules: ScreenRules) -> None:
    assert LINK_COLOR_KEY in screen_rules.palette
    assert all(card.color_key in screen_rules.palette for card in CREDIT_CARDS)


def test_cards_are_centered_one_gap_apart_and_fit_between_head_and_footer(
    look: ScreenLook,
) -> None:
    rules = look.rules.credits
    for size in (WINDOW, *OTHER_SIZES):
        rects = card_rects(look, size)
        assert len(rects) == len(CREDIT_CARDS)
        for rect in rects:
            assert rect.width == rules.card_w
            assert abs(rect.centerx - size[0] // 2) <= 1
        for upper, lower in pairwise(rects):
            assert lower.top - upper.bottom == rules.card_gap
        assert rects[0].top >= rules.margin_top + rules.head_h, f"{size}: cards reach the title"
        foot_top = size[1] - rules.margin_bottom - rules.foot_h
        assert rects[-1].bottom <= foot_top, f"{size}: cards reach the footer"


def test_the_stack_is_centered_between_head_and_footer(look: ScreenLook) -> None:
    rules = look.rules.credits
    rects = card_rects(look, WINDOW)
    above = rects[0].top - (rules.margin_top + rules.head_h)
    below = (WINDOW[1] - rules.margin_bottom - rules.foot_h) - rects[-1].bottom
    assert abs(above - below) <= 1


def test_every_line_fits_inside_its_card(look: ScreenLook) -> None:
    rules = look.rules.credits
    room = rules.card_w - 2 * rules.pad_x
    for card in CREDIT_CARDS:
        assert look.text_size(card.heading, "card_title")[0] <= room
        for line in card.lines:
            assert look.text_size(line.text, "card_text")[0] <= room, f"too wide: {line.text}"


def test_each_card_draws_its_text_inside_itself(look: ScreenLook) -> None:
    page = _page(look)
    rules = look.rules.credits
    for rect in card_rects(look, WINDOW):
        inner = rect.inflate(-2 * rules.pad_x, -2 * rules.pad_y)
        ink = _lit_ink(page, inner)
        assert ink is not None
        assert inner.contains(ink)


def test_the_title_is_centered_at_the_top(look: ScreenLook) -> None:
    rules = look.rules.credits
    head = pygame.Rect(60, 0, WINDOW[0] - 120, rules.margin_top + rules.head_h - 1)
    ink = _lit_ink(_page(look), head)
    assert ink is not None
    assert abs(ink.centerx - WINDOW[0] // 2) <= 2
    assert ink.bottom < rules.margin_top + rules.head_h


def test_the_footer_keys_are_centered_in_the_footer_band(look: ScreenLook) -> None:
    rules = look.rules.credits
    foot_top = WINDOW[1] - rules.margin_bottom - rules.foot_h
    band = pygame.Rect(60, foot_top, WINDOW[0] - 120, rules.foot_h)
    ink = _lit_ink(_page(look), band)
    assert ink is not None
    assert abs(ink.centerx - WINDOW[0] // 2) <= 2
    assert abs(ink.centery - band.centery) <= 2


def test_the_page_never_fills_the_background(look: ScreenLook) -> None:
    surface = _page(look, grey=60)
    for point in ((40, 3), (WINDOW[0] // 2, WINDOW[1] - 3)):
        assert surface.get_at(point)[:3] == (60, 60, 60), f"{point} was painted over"


def test_drawing_twice_gives_the_same_pixels(look: ScreenLook) -> None:
    first = pygame.image.tobytes(_page(look), "RGB")
    assert pygame.image.tobytes(_page(look), "RGB") == first


def test_the_page_fits_other_surface_sizes(look: ScreenLook) -> None:
    for size in OTHER_SIZES:
        area = pygame.Rect((0, 0), size)
        assert all(area.contains(rect) for rect in card_rects(look, size))
        assert _lit_ink(_page(look, size), area) is not None
