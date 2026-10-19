Feature: DRA-76
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/drifters.md, docs/contracts/systems/waves.md
Status: open
Linear: DRA-81

## Read in the contract
- run.md: Purpose. Diagram: the one-tick flowchart (steps 3, 5, 9a and the retry), Drifters entering, the level-rise timeline.
- run.md: Interface, `game/core/run.py`: the import line, `waves`, `level`, `wave_spawns_due`, `start_run`.
- run.md: Rules: the step-number note and The level; steps 3, 5 and 9a; the "If nothing happened" line; a game-over tick; `add_drifters` (the first bullet after "Otherwise"); Score (Level); Other rules (randomness; a run's waves kept by a retry); Logging (the order line).
- run.md: Impact, the DRA-76 table. Rationale, the DRA-76 lines and "`level` is a property".
- drifters.md: Interface, `game/core/levels.py` (the paragraph after the block). Impact, the DRA-76 table.
- waves.md: Interface, `game/core/waves.py` (to read: `WaveRun`, `step_waves`, `next_run_waves`). Rules, The wave clock (the bullets after step 4).

## Builds
- `game/core/run.py` (changed)
- `game/core/levels.py` (changed: `LEVEL_STARTS_M` and `level_at` removed)

## Depends on
DRA-76-01, DRA-76-02, DRA-76-03

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.run import start_run, step_run
from core.ship import Thrust
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, WavePlacement, start_waves
coin = WavePlacement(at_px=0.0, placement=Placement(DrifterType.COIN, x=100.0))
w0 = Wave(wave_id='w0', length_px=11.0, kind=WaveKind.FIXED, min_level=None, placements=(coin,))
p = Wave(wave_id='p', length_px=11.0, kind=WaveKind.POOL, min_level=1)
book = WaveBook(waves={'w0': w0, 'p': p}, wave_zero_id='w0', playlists=tuple(LevelPlaylist(random_count=1) for _ in range(8)))
print(start_run().level, start_run().waves, start_run().wave_spawns_due)
run = step_run(start_run(waves=start_waves(book, 3)), Thrust(up=True))
print(run.level, run.waves.current_wave_id, [placement.drifter_type.value for placement in run.wave_spawns_due])
for _ in range(50):
    run = step_run(run, Thrust(up=True))
print(run.scroll.ticks, run.level, run.waves.current_wave_id, round(run.scroll.distance_px, 6), run.scroll.raised_level_ticks)
again = step_run(replace(run, game_over=True, retry_armed=True), Thrust(left=True))
print(again.level, again.waves.current_wave_id, again.waves.run_seed != run.waves.run_seed, again.scroll.ticks)
"
```
It prints four lines:
- `1 None ()`: a run with no waves is at Level 1 with nothing due.
- `1 w0 ['coin']`: after tick 1, Wave 0 plays and its trigger-0 coin is due.
- `51 2 p 23.21 (1, 0, 0, 0, 0, 0, 0)`: Wave 0 ended on tick 40 and the pool wave on tick 50, which ended Level 1's playlist; tick 51 moved at the Level 2 speed.
- `1 w0 True 0`: a retry starts Wave 0 at Level 1 with a new seed.

Put the command and its output in the implementation report. `game/tests/check.sh` ends `QA: pass`: every existing test passes unchanged.

## Out of scope
- `core/scroll.py`, `core/waves.py`, `core/wave_files.py` beyond calling them.
- Spawning the due placements (the app's `add_drifters` call), `game/app/`, views, tests, `game/waves/`.
- Any change to steps 1, 2, 3a, 4, 5a, 6, 7, 8 and 10, to the collect, hit or fall rules, or to the score.
