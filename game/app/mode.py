"""Run mode: normal or debug, read once at startup.

Source: 15-tech-constraints.md, run_mode_default, debug_switch_browser,
debug_switch_desktop, debug_switch_other_value, rule 7.
"""

import logging
import os
import platform
import sys
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs

log = logging.getLogger(__name__)

URL_SWITCH: str = "debug"
"""URL query parameter that selects the mode in the browser."""

ENV_SWITCH: str = "DRIFTWARD_DEBUG"
"""Environment variable that selects the mode on desktop."""

DEBUG_VALUE: str = "1"
"""The only switch value that selects debug mode."""


class RunMode(Enum):
    NORMAL = "normal"
    DEBUG = "debug"


@dataclass(frozen=True)
class ModeChoice:
    mode: RunMode
    rejected: str | None
    """The switch value that was present but not "1"; None otherwise."""


def read_switch() -> str | None:
    """Return the raw debug switch value, or None when the switch is absent.

    Browser: the first value of the URL query parameter. Desktop: the environment variable.
    A switch present with an empty value returns "".
    """
    if sys.platform == "emscripten":
        return _read_url_switch()
    return os.environ.get(ENV_SWITCH)


def _read_url_switch() -> str | None:
    """Return the first value of the debug URL parameter, read through pygbag's window bridge."""
    query: str = str(platform.window.location.search).removeprefix("?")
    values: list[str] = parse_qs(query, keep_blank_values=True).get(URL_SWITCH, [])
    return values[0] if values else None


def choose_mode(raw: str | None) -> ModeChoice:
    """Map the raw switch value to a mode. Pure: no logging, no I/O."""
    if raw is None:
        return ModeChoice(mode=RunMode.NORMAL, rejected=None)
    if raw == DEBUG_VALUE:
        return ModeChoice(mode=RunMode.DEBUG, rejected=None)
    return ModeChoice(mode=RunMode.NORMAL, rejected=raw)
