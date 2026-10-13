"""Game Over box: a see-through black box with a title and a retry prompt.

Source: docs/contracts/systems/run.md, Interface and Presentation. The view only draws. It
never fills the background, never flips the display, never logs per frame, never catches an
error and never reads the run mode or a key. It reads no core state.
"""

import logging
from dataclasses import dataclass
from functools import cache

import pygame

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


@dataclass(frozen=True, slots=True)
class _Parts:
    """The surfaces the box is made of, built once.

    ``block_height`` is the title font's ``get_linesize()`` plus the prompt font's
    ``get_height()``, px. ``line_height`` is the title font's ``get_linesize()``, px.
    """

    box: pygame.Surface
    title: pygame.Surface
    prompt: pygame.Surface
    line_height: int
    block_height: int


def draw_game_over(surface: pygame.Surface) -> None:
    """Blit the box, the title and the prompt onto ``surface``, centered. Units: pixels.

    The box top-left is ((width - 320) // 2, (height - 120) // 2). Both texts are centered
    horizontally on the surface. The two-line block is centered vertically in the box, and the
    prompt's top is one title line-height below the title's top. Needs ``pygame.font``
    initialized.
    """
    parts: _Parts = _parts()
    width, height = surface.get_size()
    box_width, box_height = BOX_SIZE
    box_left: int = (width - box_width) // 2
    box_top: int = (height - box_height) // 2
    surface.blit(parts.box, (box_left, box_top))
    title_top: int = box_top + (box_height - parts.block_height) // 2
    prompt_top: int = title_top + parts.line_height
    surface.blit(parts.title, parts.title.get_rect(centerx=width // 2, top=title_top))
    surface.blit(parts.prompt, parts.prompt.get_rect(centerx=width // 2, top=prompt_top))


@cache
def _parts() -> _Parts:
    """Return the box surface, both rendered texts and the line sizes, built on first call.

    Fonts are the default font at TITLE_FONT_SIZE and PROMPT_FONT_SIZE.
    Source: 15-tech-constraints.md, rule 5.
    """
    title_font: pygame.font.Font = pygame.font.Font(None, TITLE_FONT_SIZE)
    prompt_font: pygame.font.Font = pygame.font.Font(None, PROMPT_FONT_SIZE)
    box: pygame.Surface = pygame.Surface(BOX_SIZE, pygame.SRCALPHA)
    box.fill(BOX_COLOR)
    line_height: int = title_font.get_linesize()
    return _Parts(
        box=box,
        title=title_font.render(TITLE_TEXT, True, TEXT_COLOR),
        prompt=prompt_font.render(PROMPT_TEXT, True, TEXT_COLOR),
        line_height=line_height,
        block_height=line_height + prompt_font.get_height(),
    )
