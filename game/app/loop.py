"""Startup: run mode, logging, then the frame loop inside the error guard.

Module level imports only the standard library and startup modules. pygame and ui are
first imported by start(), inside the guard, so an import error there is logged and
shows the error screen.
Source: docs/contracts/systems/app.md, Rules, Startup and Import boundary.
"""

import functools
import logging

from app.guard import guarded
from app.log import setup_logging
from app.mode import RunMode, choose_mode, read_switch

log = logging.getLogger(__name__)


async def run() -> None:
    """Read the run mode, set up logging, then run start(mode) inside the error guard."""
    choice = choose_mode(read_switch())
    setup_logging(choice.mode)
    if choice.rejected is not None:
        log.warning("debug switch value %r is not 1, using normal mode", choice.rejected)
    log.info("start mode=%s", choice.mode.value)
    await guarded(functools.partial(start, choice.mode), choice.mode)


async def start(mode: RunMode) -> None:
    """The guarded body. Import app.frame here, inside the guard, then run the frame loop."""
    from app.frame import frame_loop

    await frame_loop(mode)
