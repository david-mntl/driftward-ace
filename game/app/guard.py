"""Top-level error guard: log the error, show the error screen, idle until the page closes.

Source: 15-tech-constraints.md, rule 8. 10-ui.md, rule 8, error_screen, error_debug_line.
docs/contracts/systems/app.md, Rules, Error guard and Import boundary.
This module holds the game's only `except Exception`. At module level it imports only the
standard library and startup modules. pygame, core.world and ui.error_screen are imported
in the error step.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.mode import RunMode

log = logging.getLogger(__name__)


async def guarded(body: Callable[[], Awaitable[None]], mode: RunMode) -> None:
    """Await body(). On an unexpected error, log it and switch to the error screen."""
    try:
        await body()
    except Exception as exc:
        log.exception("unexpected error, showing the error screen")
        if _show_error_screen(_detail(exc, mode)):
            await _idle()


def _detail(exc: Exception, mode: RunMode) -> str | None:
    """Return the one-line `<ErrorType>: <message>` in debug mode, None in normal mode.

    Newlines become spaces and null characters are removed, so the error screen can
    render the line. Source: systems/app.md, Rules, Error guard (nulls from DRA-19).
    """
    if mode is not RunMode.DEBUG:
        return None
    return " ".join(f"{type(exc).__name__}: {exc}".splitlines()).replace("\x00", "")


def _show_error_screen(detail: str | None) -> bool:
    """Draw the error screen once, opening a window if none exists. Return False if it failed."""
    try:
        import pygame

        from core.world import SCREEN_H, SCREEN_W
        from ui.error_screen import draw_error_screen

        surface: pygame.Surface | None = pygame.display.get_surface()
        if surface is None:
            pygame.init()
            surface = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        draw_error_screen(surface, detail)
        pygame.display.flip()
    except Exception:
        log.exception("error screen failed")
        return False
    return True


async def _idle() -> None:
    """Drain events each frame, no tick and no redraw. Leave only on pygame.QUIT (desktop)."""
    import pygame

    while True:
        if any(event.type == pygame.QUIT for event in pygame.event.get()):
            return
        await asyncio.sleep(0)
