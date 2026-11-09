"""The debug start wave: a run that starts a few seconds before the chosen wave's level-up.

Debug mode only. It builds a copy of the wave book: Wave 0 is an empty lead-in, every level
below the wave's level has an empty playlist, and the wave's level starts its playlist at the
wave. The first level rise then lands on that level, its banner plays, and the chosen wave comes
next. The rest of that level and every level after it play as normal. A retry starts the same
way, because the run keeps the book. Core's rules are not changed, only the book they read.
Not a startup module: it imports core, so only app.frame imports it, inside the guard.

Source: 15-tech-constraints.md, debug_start_wave and debug_start_lead.
"""

import logging
from dataclasses import replace
from typing import Final

from core.levels import FIRST_LEVEL
from core.scroll import SCROLL_START_DELAY, scroll_speed
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind

log = logging.getLogger(__name__)

LEAD_IN_WAVE_ID: Final[str] = "debug_lead_in"
"""Id of the empty Wave 0 the debug book plays first. No wave file has it."""

START_LEAD_TICKS: Final[int] = 180
"""Ticks from the start of play to the level rise into the chosen wave's level (3 s).
Source: 15-tech-constraints.md, debug_start_lead."""


def start_book(book: WaveBook, wave_id: str | None) -> WaveBook:
    """Return the book a debug run starting at `wave_id` plays, or `book` with nothing to do.

    No id, an empty id or Wave 0's id: `book` as it is. An id with no wave: `book` and one
    WARNING. Otherwise the debug book, and one INFO line naming the wave and its level.
    """
    if not wave_id or wave_id == book.wave_zero_id:
        return book
    wave: Wave | None = book.waves.get(wave_id)
    if wave is None:
        log.warning("start wave %r not found, playing the normal waves", wave_id)
        return book
    level: int = _level_of(book, wave)
    log.info("start wave id=%s level=%d", wave_id, level)
    return _book_starting_at(book, wave, level)


def _level_of(book: WaveBook, wave: Wave) -> int:
    """Return the first level whose playlist names `wave`, else its pool level, else Level 1."""
    for index, playlist in enumerate(book.playlists):
        if wave.wave_id in playlist.fixed:
            return index + FIRST_LEVEL
    if wave.kind is WaveKind.POOL and wave.min_level is not None:
        return wave.min_level
    return FIRST_LEVEL


def _book_starting_at(book: WaveBook, wave: Wave, level: int) -> WaveBook:
    """Return the debug book: the lead-in as Wave 0, no waves below `level`, `wave` first at it."""
    playlists: list[LevelPlaylist] = list(book.playlists)
    for index in range(level - FIRST_LEVEL):
        playlists[index] = LevelPlaylist()
    own: LevelPlaylist = playlists[level - FIRST_LEVEL]
    playlists[level - FIRST_LEVEL] = replace(own, fixed=_from_wave(own.fixed, wave.wave_id))
    lead_in: Wave = Wave(
        wave_id=LEAD_IN_WAVE_ID, length_px=_lead_in_px(), kind=WaveKind.FIXED, min_level=None
    )
    return replace(
        book,
        waves={**book.waves, LEAD_IN_WAVE_ID: lead_in},
        wave_zero_id=LEAD_IN_WAVE_ID,
        playlists=tuple(playlists),
    )


def _from_wave(fixed: tuple[str, ...], wave_id: str) -> tuple[str, ...]:
    """Return the fixed list from `wave_id` on, or `wave_id` then the list when it is not in it."""
    if wave_id in fixed:
        return fixed[fixed.index(wave_id) :]
    return (wave_id, *fixed)


def _lead_in_px() -> float:
    """Return the lead-in's length, px: the scroll at Level 1 after the still start, >= 1 tick."""
    moving_ticks: int = max(START_LEAD_TICKS - SCROLL_START_DELAY, 1)
    return moving_ticks * scroll_speed(FIRST_LEVEL)
