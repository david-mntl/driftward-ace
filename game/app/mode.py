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

URL_START_WAVE: str = "wave"
"""URL query parameter that names the wave a debug run starts at, in the browser."""

ENV_START_WAVE: str = "DRIFTWARD_WAVE"
"""Environment variable that names the wave a debug run starts at, on desktop."""


class RunMode(Enum):
    """How the game runs. Debug adds logs and the overlay, never a rule change."""

    NORMAL = "normal"
    DEBUG = "debug"


@dataclass(frozen=True)
class ModeChoice:
    """The chosen mode, and the switch value that was rejected, if any."""

    mode: RunMode
    rejected: str | None
    """The switch value that was present but not "1"; None otherwise."""


def read_switch() -> str | None:
    """Return the raw debug switch value, or None when the switch is absent.

    Browser: the first value of the URL query parameter. Desktop: the environment variable.
    A switch present with an empty value returns "".
    """
    if sys.platform == "emscripten":
        return _read_url_value(URL_SWITCH)
    return os.environ.get(ENV_SWITCH)


def read_start_wave() -> str | None:
    """Return the wave id a debug run starts at, or None when none is given.

    Browser: the first value of the `wave` URL parameter. Desktop: the environment variable.
    Read in debug mode only; the value is checked against the wave book by app.start_wave.
    """
    if sys.platform == "emscripten":
        return _read_url_value(URL_START_WAVE)
    return os.environ.get(ENV_START_WAVE)


def _read_url_value(name: str) -> str | None:
    """Return the first value of the URL parameter `name`, read through pygbag's window bridge."""
    # pygbag adds `window` to `platform` in the browser only, so type checkers can't see it.
    query: str = str(platform.window.location.search).removeprefix("?")  # type: ignore[attr-defined]
    values: list[str] = parse_qs(query, keep_blank_values=True).get(name, [])
    return values[0] if values else None


def choose_mode(raw: str | None) -> ModeChoice:
    """Map the raw switch value to a mode. Pure: no logging, no I/O."""
    if raw is None:
        return ModeChoice(mode=RunMode.NORMAL, rejected=None)
    if raw == DEBUG_VALUE:
        return ModeChoice(mode=RunMode.DEBUG, rejected=None)
    return ModeChoice(mode=RunMode.NORMAL, rejected=raw)
