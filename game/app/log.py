"""The one place that configures logging. Called once, at startup.

Source: 15-tech-constraints.md, log_level_normal, log_level_debug, log_format.
docs/contracts/DRA-5/DRA-5-app.md, Rules, Logging (Director decision D2).
"""

import logging
import platform
import sys

from app.mode import RunMode

log = logging.getLogger(__name__)

LEVELS: dict[RunMode, int] = {RunMode.NORMAL: logging.INFO, RunMode.DEBUG: logging.DEBUG}
"""Root logger level per run mode."""

LINE_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"
"""Gives `HH:MM:SS LEVEL logger: message` with DATE_FORMAT."""

DATE_FORMAT: str = "%H:%M:%S"


class BrowserConsoleHandler(logging.Handler):
    """Write each formatted line to the devtools console with console.log.

    pygbag sends stdout and stderr only to its hidden terminal, so this is the only
    way log lines reach the browser console. Every level uses console.log.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            platform.window.console.log(self.format(record))
        except (AttributeError, TypeError, ValueError):
            self.handleError(record)


def setup_logging(mode: RunMode) -> None:
    """Install one handler on the root logger, at the level for this mode.

    Browser: the devtools console. Desktop: stdout.
    """
    handler: logging.Handler
    if sys.platform == "emscripten":
        handler = BrowserConsoleHandler()
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LINE_FORMAT, DATE_FORMAT))
    logging.basicConfig(level=LEVELS[mode], handlers=[handler], force=True)
