"""Credits page: the title, one glass card per credit group, and the footer.

Source: docs/contracts/systems/screens.md, Interface (ui/credits.py); 10-ui.md, `credits_page`.
The view takes the surface and the look and only draws. It never fills the background, never flips
the display, never logs per frame, never catches an error and never reads the run mode, a key or
the focus.
"""

import logging
from dataclasses import dataclass
from typing import Final

import pygame

from ui.screen_look import ScreenLook
from ui.screen_rules import CreditsRules

log = logging.getLogger(__name__)

CREDITS_TITLE_TEXT: Final[str] = "CREDITS"
"""Page title. 10-ui.md, credits_page."""


@dataclass(frozen=True)
class CreditLine:
    """One line of a card. A ``link`` line is a web address and is drawn in the link color."""

    text: str
    link: bool = False


@dataclass(frozen=True)
class CreditCard:
    """One card: its heading, the palette key that lights the heading, and its lines in order."""

    heading: str
    color_key: str
    lines: tuple[CreditLine, ...]


CREDIT_CARDS: Final[tuple[CreditCard, ...]] = (
    CreditCard(
        "MUSIC",
        "ship_lines_light",
        (
            CreditLine('"Lo-fi Music Guitar (Loop)", track 52 "Under the Rain", by Migfus20'),
            CreditLine("freesound.org/people/Migfus20/sounds/569791/", link=True),
            # Split so the source never holds the extension followed by a double quote: pygbag's
            # build rewrites that text to .ogg in every Python file.
            CreditLine('Built on "Rain, sheet roof.wav' + '" by snarcle'),
            CreditLine("freesound.org/people/snarcle/sounds/569370/", link=True),
            CreditLine("Changed: cut to a seamless loop, crossfaded, converted to Ogg."),
            CreditLine("License: CC BY 4.0, creativecommons.org/licenses/by/4.0/"),
        ),
    ),
    CreditCard(
        "LEVEL-UP SOUND",
        "level",
        (
            CreditLine('"Achievement 2" by sonically_sound'),
            CreditLine("freesound.org/people/Sonically_Sound/sounds/625715/", link=True),
            CreditLine("Changed: made louder, short fade-in, converted to Ogg."),
            CreditLine("License: CC BY 4.0, creativecommons.org/licenses/by/4.0/"),
        ),
    ),
    CreditCard(
        "ALSO USED",
        "frame_lights",
        (
            CreditLine('Game over sound: "Game Over Arcade" by Mountain_Man (CC0)'),
            CreditLine("Font: Exo 2, by The Exo 2 Project Authors (SIL OFL 1.1)"),
            CreditLine("Font: Share Tech Mono, by Carrois Type Design (SIL OFL 1.1)"),
            CreditLine("Sprites made in Piskel (Apache 2.0)"),
        ),
    ),
)
"""The cards, top first. The two CC BY 4.0 groups name the work, the author, the source, what was
changed and the license, as the license asks. The last card is a courtesy. 10-ui.md, credits_page;
game/assets/CREDITS.md."""

LINK_COLOR_KEY: Final[str] = "frame_lights"
"""The palette key of a link line. 12-art-and-audio.md, Screen colors."""

BACK_KEYS: Final[tuple[str, ...]] = ("ENTER", "SPACE")
"""The keys that go back to the menu, shown in the footer. 10-ui.md, credits_page."""

BACK_WORD: Final[str] = "BACK"
"""The footer's word after the key caps. 10-ui.md, credits_page."""


def draw_credits(surface: pygame.Surface, look: ScreenLook) -> None:
    """Draw the title, the rulers, the cards and the footer onto ``surface``. Units: px.

    The title sits ``margin_top`` from the top. The cards are ``card_w`` wide, centered across the
    width, ``card_gap`` apart, each as tall as its lines; the stack is centered between the head
    band and the footer band. The footer's key caps are centered in a band ``foot_h`` tall,
    ``margin_bottom`` above the bottom. Needs ``pygame.font`` initialized.
    """
    rules: CreditsRules = look.rules.credits
    width, height = surface.get_size()
    look.blit_rulers(surface)
    look.blit_text(
        surface,
        CREDITS_TITLE_TEXT,
        "title",
        look.palette["plating"],
        {"midtop": (width // 2, rules.margin_top)},
    )
    for card, rect in zip(CREDIT_CARDS, card_rects(look, surface.get_size()), strict=True):
        _draw_card(surface, look, card, rect)
    foot_centery: int = height - rules.margin_bottom - rules.foot_h // 2
    look.blit_keys(surface, BACK_KEYS, BACK_WORD, {"center": (width // 2, foot_centery)})


def card_rects(look: ScreenLook, size: tuple[int, int]) -> list[pygame.Rect]:
    """Return one rect per card for a window of ``size``, in card order, px."""
    rules: CreditsRules = look.rules.credits
    width, height = size
    heights: list[int] = [_card_height(look, card) for card in CREDIT_CARDS]
    stack: int = sum(heights) + (len(heights) - 1) * rules.card_gap
    band_top: int = rules.margin_top + rules.head_h
    band_bottom: int = height - rules.margin_bottom - rules.foot_h
    top: int = band_top + (band_bottom - band_top - stack) // 2
    left: int = (width - rules.card_w) // 2
    rects: list[pygame.Rect] = []
    for card_h in heights:
        rects.append(pygame.Rect(left, top, rules.card_w, card_h))
        top += card_h + rules.card_gap
    return rects


def _card_height(look: ScreenLook, card: CreditCard) -> int:
    """Return the height of ``card``: padding, heading, gap and its lines, px."""
    rules: CreditsRules = look.rules.credits
    heading_h: int = look.text_size(card.heading, "card_title")[1]
    lines_h: int = sum(_line_height(look, line) for line in card.lines)
    return 2 * rules.pad_y + heading_h + rules.heading_gap + lines_h


def _line_height(look: ScreenLook, line: CreditLine) -> int:
    """Return the height one line takes, its gap below included, px."""
    return look.text_size(line.text, "card_text")[1] + look.rules.credits.line_gap


def _draw_card(
    surface: pygame.Surface, look: ScreenLook, card: CreditCard, rect: pygame.Rect
) -> None:
    """Draw one card: the glass, the heading, then the lines, left-aligned inside the padding."""
    rules: CreditsRules = look.rules.credits
    look.glass(surface, rect, rules.blur)
    left: int = rect.left + rules.pad_x
    top: int = rect.top + rules.pad_y
    heading: pygame.Rect = look.blit_text(
        surface, card.heading, "card_title", look.palette[card.color_key], {"topleft": (left, top)}
    )
    top = heading.bottom + rules.heading_gap
    for line in card.lines:
        color_key: str = LINK_COLOR_KEY if line.link else "plating"
        alpha: int = rules.link_alpha if line.link else rules.text_alpha
        look.blit_text(
            surface,
            line.text,
            "card_text",
            look.palette[color_key],
            {"topleft": (left, top)},
            glow=False,
            alpha=alpha,
        )
        top += _line_height(look, line)
