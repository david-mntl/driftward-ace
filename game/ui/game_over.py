"""Game Over box: a see-through black box with a title, a final score line and a retry prompt.

Source: docs/contracts/systems/run.md, Interface and Presentation. The view only draws. It
never fills the background, never flips the display, never logs per frame, never catches an
error and never reads the run mode or a key. It reads no core state: the score is an argument.
"""

import logging
from dataclasses import dataclass
from functools import cache, lru_cache

import pygame

from ui.score_text import score_text

log = logging.getLogger(__name__)

BOX_SIZE: tuple[int, int] = (320, 120)
"""Box width and height, px. Scope report DRA-23, Game Over box, temporary stand-in approved by
the Director, not in the GDD (UI-04 is TBD)."""

BOX_COLOR: tuple[int, int, int, int] = (0, 0, 0, 90)
"""Box fill, RGBA: black at alpha 90 of 255, about 35%. Scope report DRA-23, Game Over box,
temporary stand-in approved by the Director, not in the GDD (UI-04 is TBD)."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Text color, RGB. Scope report DRA-23, Game Over box, temporary stand-in approved by the
Director, not in the GDD (UI-04 is TBD)."""

TITLE_TEXT: str = "Game Over"
"""Title line. Scope report DRA-23, Game Over box, temporary stand-in approved by the Director,
not in the GDD (UI-04 is TBD)."""

TITLE_FONT_SIZE: int = 32
"""Title font size, default font, px. Scope report DRA-23, Game Over box, temporary stand-in
approved by the Director, not in the GDD (UI-04 is TBD)."""

PROMPT_TEXT: str = "Press any arrow to retry"
"""Prompt line. Scope report DRA-23, Game Over box, temporary stand-in approved by the
Director, not in the GDD (UI-04 is TBD)."""

PROMPT_FONT_SIZE: int = 16
"""Prompt font size, default font, px. Scope report DRA-23, Game Over box, temporary stand-in
approved by the Director, not in the GDD (UI-04 is TBD)."""


SCORE_FONT_SIZE: int = 16
"""Score line font size, default font, px. Scope report DRA-61, SCORE look."""


@dataclass(frozen=True, slots=True)
class _Parts:
    """The surfaces and sizes the box is made of, built once.

    ``line_height`` is the title font's ``get_linesize()`` and ``score_line_height`` the score
    font's, px. ``block_height`` is ``line_height + score_line_height`` plus the prompt font's
    ``get_height()``, px.
    """

    box: pygame.Surface
    title: pygame.Surface
    prompt: pygame.Surface
    score_font: pygame.font.Font
    line_height: int
    score_line_height: int
    block_height: int


def draw_game_over(surface: pygame.Surface) -> None:
    """Blit the box, the title and the prompt onto ``surface``, centered. Units: pixels.

    The box top-left is ((width - 320) // 2, (height - 120) // 2). Both texts are centered
    horizontally on the surface. The three-line block (title, score, prompt) is centered
    vertically in the box. The score line's place stays empty: the prompt's top is one title
    line-height plus one score line-height below the title's top. Needs ``pygame.font``
    initialized.
    """
    parts: _Parts = _parts()
    width, height = surface.get_size()
    box_left, box_top = _box_origin(width, height)
    surface.blit(parts.box, (box_left, box_top))
    title_top: int = _title_top(box_top, parts)
    prompt_top: int = title_top + parts.line_height + parts.score_line_height
    surface.blit(parts.title, parts.title.get_rect(centerx=width // 2, top=title_top))
    surface.blit(parts.prompt, parts.prompt.get_rect(centerx=width // 2, top=prompt_top))


def draw_final_score(surface: pygame.Surface, score: int) -> None:
    """Blit the score line onto ``surface``, in its place between the title and the prompt.

    ``score`` is a whole number >= 0, trusted. The text is ``score_text(score)``, centered
    horizontally, its top one title line-height below the title's top. The box and the title top
    are worked out from ``surface.get_size()`` as ``draw_game_over`` does. Needs ``pygame.font``
    initialized.
    """
    parts: _Parts = _parts()
    width, height = surface.get_size()
    _, box_top = _box_origin(width, height)
    line_top: int = _title_top(box_top, parts) + parts.line_height
    line: pygame.Surface = _score_line(score)
    surface.blit(line, line.get_rect(centerx=width // 2, top=line_top))


def _box_origin(width: int, height: int) -> tuple[int, int]:
    """Return the box's top-left on a surface of ``width`` x ``height``, px, centered."""
    box_width, box_height = BOX_SIZE
    return (width - box_width) // 2, (height - box_height) // 2


def _title_top(box_top: int, parts: _Parts) -> int:
    """Return the title's top, px: the three-line block centered vertically in the box."""
    return box_top + (BOX_SIZE[1] - parts.block_height) // 2


@cache
def _parts() -> _Parts:
    """Return the box surface, both rendered texts, the score font and the line sizes.

    Built on first call. Fonts are the default font at TITLE_FONT_SIZE, SCORE_FONT_SIZE and
    PROMPT_FONT_SIZE. Source: 15-tech-constraints.md, rule 5.
    """
    title_font: pygame.font.Font = pygame.font.Font(None, TITLE_FONT_SIZE)
    score_font: pygame.font.Font = pygame.font.Font(None, SCORE_FONT_SIZE)
    prompt_font: pygame.font.Font = pygame.font.Font(None, PROMPT_FONT_SIZE)
    box: pygame.Surface = pygame.Surface(BOX_SIZE, pygame.SRCALPHA)
    box.fill(BOX_COLOR)
    line_height: int = title_font.get_linesize()
    score_line_height: int = score_font.get_linesize()
    return _Parts(
        box=box,
        title=title_font.render(TITLE_TEXT, True, TEXT_COLOR),
        prompt=prompt_font.render(PROMPT_TEXT, True, TEXT_COLOR),
        score_font=score_font,
        line_height=line_height,
        score_line_height=score_line_height,
        block_height=line_height + score_line_height + prompt_font.get_height(),
    )


@lru_cache(maxsize=1)
def _score_line(score: int) -> pygame.Surface:
    """Return the score line rendered for ``score``, white and antialiased.

    Holds the last score only: the score is frozen while the box shows, so it renders once.
    """
    return _parts().score_font.render(score_text(score), True, TEXT_COLOR)
