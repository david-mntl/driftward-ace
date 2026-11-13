"""One game tick as the soak harness plays it, and the running totals of a run.

runner.py, chunk_worker.py, tail_clock.py and the determinism replay all advance a run tick by tick. They share
this code, so a change to how a tick is played is made once.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field

import paths  # noqa: F401  (puts game/ on sys.path)
from simkit import refill_lives

from core.run import add_drifters, step_run
from core.scroll import scroll_speed

WINDOW_TICKS = 3600  # one minute of play at 60 ticks a second: how often a progress window is written
TRACE_CHARS = 1800  # how much of a traceback a finding keeps
KEY_CHARS = 120  # how much of the last traceback line names the finding


def advance(kit, run, thrust, *, checker=None, inject=None, tick=0, immortal=False, spawn=True):
    """Play one tick. Return (next_run, lives_lost_this_tick).

    The order is the app's: step the run, let the oracle check the step, add the drifters the waves
    ask for, then (immortal only) refill the lives. `inject(stepped_run, tick)` may add more drifters.
    `spawn=False` drops the wave spawns, to study the clock on an empty field.
    """
    stepped = step_run(run, thrust)
    if checker is not None:
        checker.check(run, thrust, stepped)
    if spawn:
        due = tuple(stepped.wave_spawns_due)
        if inject is not None:
            due += tuple(inject(stepped, tick))
        stepped = add_drifters(stepped, due, kit.tuning)
    lives_lost = max(0, run.lives - stepped.lives)
    return (refill_lives(stepped) if immortal else stepped), lives_lost


def record_crash(checker, run, tick):
    """Call inside `except Exception`. Add an "exception" finding to `checker` (if any); return a record of it."""
    trace = traceback.format_exc()
    wave = run.waves.wave_id if run.waves else None
    if checker is not None:
        checker.add("exception", key=trace.strip().splitlines()[-1][:KEY_CHARS], trace=trace[-TRACE_CHARS:], wave=wave)
    return dict(tick=tick, wave=wave, level=run.level, trace=trace[-TRACE_CHARS:])


@dataclass
class Progress:
    """What a run has done so far: ticks played, lives lost, furthest level, and one window per minute."""

    ticks: int = 0
    lives_lost: int = 0
    furthest_level: int = 1
    level8_tick: int | None = None
    windows: list = field(default_factory=list)
    _count: int = 0  # ticks and drifters seen in the open window
    _drifter_sum: int = 0
    _drifter_max: int = 0

    def observe(self, run, lives_lost):
        """Record the run after a tick. Closes a window every WINDOW_TICKS."""
        self.ticks += 1
        self.lives_lost += lives_lost
        self.furthest_level = max(self.furthest_level, run.level)
        if run.level == 8 and self.level8_tick is None:
            self.level8_tick = self.ticks
        drifters = len(run.drifters)
        self._count += 1
        self._drifter_sum += drifters
        self._drifter_max = max(self._drifter_max, drifters)
        if self.ticks % WINDOW_TICKS == 0:
            self.windows.append(self._close_window(run))

    def _close_window(self, run):
        window = dict(
            t=self.ticks,
            level=run.level,
            score=run.score,
            meters=run.scroll.meters,
            speed=round(scroll_speed(run.level), 3),
            drifters_avg=round(self._drifter_sum / self._count, 2),
            drifters_max=self._drifter_max,
            lives_lost=self.lives_lost,
            grazes=run.grazes,
            coin_points=run.coin_points,
            wave=run.waves.wave_id if run.waves else None,
            banner=run.level_up is not None,
        )
        self._count = self._drifter_sum = self._drifter_max = 0
        return window
