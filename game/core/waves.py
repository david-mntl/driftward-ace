"""Waves: the wave book, the wave state of one run, the wave clock and the random picker.

A wave is a hand-authored group of drifters, each placed at a scroll distance from the wave's
start. `step_waves` is the wave clock and the playlist runner: one call per playing tick, with the
run's scroll distance. It hands out the placements that came due; the caller adds them as
drifters. Seeds live in the state, so every step is a pure function of its inputs. Stdlib and
`core` only, no frame time, no run mode.

Source: docs/contracts/systems/waves.md, Interface and Rules.
"""

import logging
import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Final

from core.drifters.spawner import Placement
from core.levels import FIRST_LEVEL, LEVEL_COUNT, check_level, rest_gap_mult
from core.scroll import DISTANCE_DECIMALS

log = logging.getLogger(__name__)

REST_GAP_BASE_TICKS: Final[int] = 0
"""Rest gap before the level multiplier, ticks. Source: 08-difficulty.md, rest_gap_base
(guess; the real value is DF-02)."""

SEED_BITS: Final[int] = 64
"""Width of the next seed drawn from a generator, bits. Source: docs/contracts/systems/waves.md,
Interface (`getrandbits(64)`)."""


REST_GAP_DECIMALS: Final[int] = 6
"""Decimals kept when the scaled rest gap is rounded up, so float noise adds no tick.
Source: docs/contracts/systems/waves.md, Rules, The rest gap."""


class WaveKind(Enum):
    """How a wave is played."""

    FIXED = "fixed"
    """Played where a playlist names it."""

    POOL = "pool"
    """Picked for random slots."""


@dataclass(frozen=True, slots=True, kw_only=True)
class WavePlacement:
    """One drifter of a wave: when it comes and how it is placed."""

    at_px: float
    """Trigger: px of scroll from the wave's start, >= 0."""

    placement: Placement
    """Where and how (core.drifters.spawner). Its speed is always None."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Wave:
    """One hand-authored wave."""

    wave_id: str
    """The file name without .json."""

    length_px: float
    """Length, px of scroll, > 0."""

    kind: WaveKind
    """Fixed or pool."""

    min_level: int | None
    """POOL: lowest level it may play at, 1 to 8. FIXED: None."""

    extra_rest_ticks: int = 0
    """Ticks added to the rest gap after this wave, >= 0."""

    placements: tuple[WavePlacement, ...] = ()
    """Its drifters, by at_px, ties in file order."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LevelPlaylist:
    """One level's playlist."""

    fixed: tuple[str, ...] = ()
    """Wave ids, in play order."""

    random_count: int = 0
    """Random slots after the fixed waves, >= 0."""


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveBook:
    """Every wave and every playlist, checked. Never changes after loading."""

    waves: Mapping[str, Wave]
    """Waves by wave id."""

    wave_zero_id: str
    """The id of Wave 0."""

    playlists: tuple[LevelPlaylist, ...]
    """One playlist per level, LEVEL_COUNT entries, Level 1 first."""

    def level_slots(self, level: int) -> tuple[str | None, ...]:
        """Return the level's fixed wave ids in order, then None for each random slot."""
        check_level(level)
        playlist: LevelPlaylist = self.playlists[level - 1]
        random_slots: tuple[None, ...] = (None,) * playlist.random_count
        return (*playlist.fixed, *random_slots)

    def pool_ids(self, level: int) -> tuple[str, ...]:
        """Return the ids of the POOL waves with min_level <= level, sorted by id."""
        check_level(level)
        return tuple(
            wave_id
            for wave_id, wave in sorted(self.waves.items())
            if wave.kind is WaveKind.POOL and wave.min_level is not None and wave.min_level <= level
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveRun:
    """One run's waves after a tick."""

    book: WaveBook
    """The wave book. Never changes."""

    level: int
    """The run's level, 1 to LEVEL_COUNT."""

    next_slot: int
    """Slots of this level's playlist started so far. Wave 0 is no slot."""

    wave_id: str
    """The wave playing. While resting, the wave that just ended."""

    resting: bool = False
    """A rest gap is running."""

    rest_ticks_left: int = 0
    """Ticks of rest still to come, > 0 only while resting."""

    start_px: float = 0.0
    """Scroll distance where the playing wave started, px."""

    spawned: int = 0
    """Placements of the playing wave already due."""

    pick_seed: int
    """Seed of the next random pick, >= 0."""

    run_seed: int
    """The seed this run's waves started from, >= 0."""

    spawns_due: tuple[Placement, ...] = ()
    """Placements that came due on the last tick, in order."""

    @property
    def current_wave_id(self) -> str | None:
        """Return the playing wave's id, or None while resting."""
        return None if self.resting else self.wave_id


def start_waves(book: WaveBook, seed: int) -> WaveRun:
    """Return a run's waves at tick 0: Wave 0 at Level 1, starting at 0 px, nothing due.

    Source: waves.md, Rules, The order.
    """
    log.debug("wave start id=%s level=%d random=%s", book.wave_zero_id, FIRST_LEVEL, False)
    return WaveRun(
        book=book,
        level=FIRST_LEVEL,
        next_slot=0,
        wave_id=book.wave_zero_id,
        start_px=0.0,
        spawned=0,
        pick_seed=seed,
        run_seed=seed,
    )


def step_waves(waves: WaveRun, distance_px: float) -> WaveRun:
    """Advance the waves one playing tick and return the new state. Never mutates `waves`.

    `distance_px` is the run's scroll distance after this tick's scroll step, px. The returned
    `spawns_due` holds every placement that came due on this tick, across every wave that played
    on it. Source: waves.md, Rules, The wave clock.
    """
    state: WaveRun = replace(waves, spawns_due=())
    if state.resting:
        rest_left: int = state.rest_ticks_left - 1
        if rest_left > 0:
            return replace(state, rest_ticks_left=rest_left)
        state = _start_next_wave(state, distance_px)
    due: list[Placement] = []
    while True:
        wave: Wave = state.book.waves[state.wave_id]
        into: float = round(distance_px - state.start_px, DISTANCE_DECIMALS)
        spawned: int = _count_due(wave, state.spawned, into)
        due.extend(item.placement for item in wave.placements[state.spawned : spawned])
        state = replace(state, spawned=spawned)
        if into < wave.length_px:
            break
        state = _end_wave(state, wave)
        if state.resting:
            break
        state = _start_next_wave(state, state.start_px + wave.length_px)
    return replace(state, spawns_due=tuple(due))


def next_run_waves(waves: WaveRun) -> WaveRun:
    """Return the waves of the next run, started from a seed drawn from this run's seed.

    Source: waves.md, Rules, Seeds.
    """
    next_seed: int = random.Random(waves.run_seed).getrandbits(SEED_BITS)
    return start_waves(waves.book, next_seed)


def pick_pool_wave(book: WaveBook, level: int, last_wave_id: str, chooser: random.Random) -> str:
    """Return the id of one pool wave allowed at `level`, drawing from `chooser` only.

    With more than one candidate, `last_wave_id` is left out. With one, it plays even if it just
    played. Source: waves.md, Rules, Random picks.
    """
    candidates: tuple[str, ...] = book.pool_ids(level)
    if len(candidates) > 1:
        candidates = tuple(wave_id for wave_id in candidates if wave_id != last_wave_id)
    return chooser.choice(candidates)


def rest_gap_ticks(level: int, extra_rest_ticks: int) -> int:
    """Return the rest gap after a wave at `level`, ticks, >= 0.

    The level-scaled part rounds up to a whole tick. The extra rest is not scaled.
    Source: waves.md, Rules, The rest gap; 08-difficulty.md, rules 4 and 6.
    """
    scaled: float = round(REST_GAP_BASE_TICKS * rest_gap_mult(level), REST_GAP_DECIMALS)
    return math.ceil(scaled) + extra_rest_ticks


def _count_due(wave: Wave, spawned: int, into: float) -> int:
    """Return how many placements of `wave` are due once `into` px have scrolled."""
    count: int = spawned
    while count < len(wave.placements) and wave.placements[count].at_px <= into:
        count += 1
    return count


def _end_wave(state: WaveRun, wave: Wave) -> WaveRun:
    """Return the state after `wave` ends: the level rise, then the rest gap if it is above 0."""
    log.debug("wave end id=%s", wave.wave_id)
    level: int = state.level
    next_slot: int = state.next_slot
    if next_slot >= len(state.book.level_slots(level)) and level < LEVEL_COUNT:
        level = _next_level_with_slots(state.book, level)
        next_slot = 0
        log.debug("level up level=%d", level)
    rest: int = rest_gap_ticks(level, wave.extra_rest_ticks)
    if rest > 0:
        log.debug("rest start ticks=%d", rest)
    return replace(state, level=level, next_slot=next_slot, resting=rest > 0, rest_ticks_left=rest)


def _next_level_with_slots(book: WaveBook, level: int) -> int:
    """Return the level above `level`, past any level whose playlist has no slots."""
    raised: int = level + 1
    while raised < LEVEL_COUNT and not book.level_slots(raised):
        raised += 1
    return raised


def _start_next_wave(state: WaveRun, start_px: float) -> WaveRun:
    """Return the state with the next wave of the playlist started at `start_px`.

    Never Wave 0. A wave id slot plays that wave; a random slot, or the slots past Level 8's
    playlist, plays `pick_pool_wave` and stores the next pick seed.
    """
    slots: tuple[str | None, ...] = state.book.level_slots(state.level)
    next_slot: int = state.next_slot
    slot: str | None = None
    if next_slot < len(slots):
        slot = slots[next_slot]
        next_slot += 1
    pick_seed: int = state.pick_seed
    wave_id: str
    if slot is None:
        chooser: random.Random = random.Random(pick_seed)
        wave_id = pick_pool_wave(state.book, state.level, state.wave_id, chooser)
        pick_seed = chooser.getrandbits(SEED_BITS)
    else:
        wave_id = slot
    log.debug("wave start id=%s level=%d random=%s", wave_id, state.level, slot is None)
    return replace(
        state,
        next_slot=next_slot,
        wave_id=wave_id,
        resting=False,
        rest_ticks_left=0,
        start_px=start_px,
        spawned=0,
        pick_seed=pick_seed,
    )
