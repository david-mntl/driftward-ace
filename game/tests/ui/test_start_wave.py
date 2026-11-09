"""Debug start wave tests: the run starts a few seconds before the wave's level-up, then plays it.

Source: 15-tech-constraints.md, debug_start_wave and debug_start_lead. A run is played here with
core's own scroll and wave clock, as core.run steps them: the scroll at the run's level, then the
waves with the new distance.
"""

from collections.abc import Iterator

import pytest

from app.start_wave import LEAD_IN_WAVE_ID, START_LEAD_TICKS, start_book
from app.tuning import load_tuning
from app.waves import load_wave_book
from core.level_up import LevelUpRules
from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.scroll import Scroll, start_scroll, step_scroll
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WaveRun,
    next_run_waves,
    start_waves,
    step_waves,
)

RULES: LevelUpRules = LevelUpRules(rest_ticks=120, arrival_ticks=30, banner_ticks=120)
WAVE_PX: float = 600.0


def _wave(wave_id: str, kind: WaveKind = WaveKind.FIXED, min_level: int | None = None) -> Wave:
    return Wave(wave_id=wave_id, length_px=WAVE_PX, kind=kind, min_level=min_level)


def _book() -> WaveBook:
    """Level 1 plays a1 a2, Level 2 nothing, Level 3 c1 c2 c3, then pool p (from Level 3)."""
    waves: tuple[Wave, ...] = (
        _wave("zero"),
        _wave("a1"),
        _wave("a2"),
        _wave("c1"),
        _wave("c2"),
        _wave("c3"),
        _wave("p", WaveKind.POOL, min_level=3),
    )
    playlists: list[LevelPlaylist] = [LevelPlaylist() for _ in range(LEVEL_COUNT)]
    playlists[0] = LevelPlaylist(fixed=("a1", "a2"))
    playlists[2] = LevelPlaylist(fixed=("c1", "c2", "c3"))
    return WaveBook(
        waves={wave.wave_id: wave for wave in waves},
        wave_zero_id="zero",
        playlists=tuple(playlists),
    )


def _play(waves: WaveRun, ticks: int) -> Iterator[tuple[int, WaveRun]]:
    scroll: Scroll = start_scroll()
    for tick in range(1, ticks + 1):
        scroll = step_scroll(scroll, waves.level)
        waves = step_waves(waves, scroll.distance_px)
        yield tick, waves


def _wave_starts(book: WaveBook, ticks: int) -> list[tuple[int, str, int]]:
    """Return (tick, wave id, level) for every wave that starts within `ticks`, Wave 0 first."""
    first: WaveRun = start_waves(book, 7, RULES)
    starts: list[tuple[int, str, int]] = [(0, first.wave_id, first.level)]
    playing: str | None = first.current_wave_id
    for tick, waves in _play(first, ticks):
        now: str | None = waves.current_wave_id
        if now is not None and now != playing:
            starts.append((tick, now, waves.level))
        playing = now
    return starts


def _rise_tick(book: WaveBook, ticks: int) -> tuple[int, int]:
    """Return the tick of the first level rise and the level reached."""
    for tick, waves in _play(start_waves(book, 7, RULES), ticks):
        if waves.level_rose:
            return tick, waves.level
    raise AssertionError("no level rise")


def test_no_wave_named_keeps_the_book() -> None:
    book: WaveBook = _book()
    assert start_book(book, None) is book
    assert start_book(book, "") is book


def test_wave_zero_keeps_the_book() -> None:
    book: WaveBook = _book()
    assert start_book(book, "zero") is book


def test_an_unknown_wave_keeps_the_book_and_warns(caplog: pytest.LogCaptureFixture) -> None:
    book: WaveBook = _book()
    assert start_book(book, "nope") is book
    assert "start wave 'nope' not found" in caplog.text


def test_the_level_rises_to_the_wave_s_level_after_the_lead_in() -> None:
    tick, level = _rise_tick(start_book(_book(), "c2"), 2 * START_LEAD_TICKS)
    assert level == 3
    assert abs(tick - START_LEAD_TICKS) <= 1


def test_the_chosen_wave_plays_after_the_level_up_rest_then_the_rest_of_its_level() -> None:
    starts = _wave_starts(start_book(_book(), "c2"), START_LEAD_TICKS + RULES.rest_ticks + 2000)
    assert starts[0][1] == LEAD_IN_WAVE_ID
    assert starts[0][2] == FIRST_LEVEL
    assert starts[1][1:] == ("c2", 3)
    assert abs(starts[1][0] - (START_LEAD_TICKS + RULES.rest_ticks)) <= 1
    assert starts[2][1:] == ("c3", 3)


def test_a_level_1_wave_plays_after_the_lead_in_with_no_level_up() -> None:
    book: WaveBook = start_book(_book(), "a2")
    starts = _wave_starts(book, START_LEAD_TICKS + 5)
    assert starts[1][1:] == ("a2", FIRST_LEVEL)
    assert abs(starts[1][0] - START_LEAD_TICKS) <= 1


def test_a_pool_wave_plays_first_at_its_lowest_level() -> None:
    starts = _wave_starts(start_book(_book(), "p"), START_LEAD_TICKS + RULES.rest_ticks + 5)
    assert starts[1][1:] == ("p", 3)


def test_a_retry_starts_at_the_same_place() -> None:
    first: WaveRun = start_waves(start_book(_book(), "c2"), 7, RULES)
    again: WaveRun = next_run_waves(first)
    assert again.wave_id == LEAD_IN_WAVE_ID
    assert again.book is first.book


def test_the_normal_book_is_not_changed() -> None:
    book: WaveBook = _book()
    start_book(book, "c2")
    assert book.wave_zero_id == "zero"
    assert book.playlists[0].fixed == ("a1", "a2")
    assert LEAD_IN_WAVE_ID not in book.waves


def _game_book() -> WaveBook:
    return load_wave_book(load_tuning())


@pytest.mark.parametrize("wave_id", sorted(set(_game_book().waves) - {_game_book().wave_zero_id}))
def test_every_game_wave_starts_first_at_its_playlist_level(wave_id: str) -> None:
    real: WaveBook = _game_book()
    want: int = next(
        index + FIRST_LEVEL
        for index, playlist in enumerate(real.playlists)
        if wave_id in playlist.fixed
    )
    starts = _wave_starts(start_book(real, wave_id), START_LEAD_TICKS + RULES.rest_ticks + 5)
    assert starts[1][1:] == (wave_id, want)
