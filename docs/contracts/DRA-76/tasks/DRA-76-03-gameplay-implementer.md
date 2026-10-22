Feature: DRA-76
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/waves.md
Status: done
Linear: DRA-79

## Read in the contract
- Purpose.
- Diagram: the order of one run, Data, the one-tick flowchart, Starting the next wave, the rest gap timeline, the placeholder timeline.
- Interface, `game/core/waves.py`.
- Rules: Values; The order; The wave clock; Starting a wave; Random picks; Seeds; The rest gap; Logging; Other rules.
- Rationale, every line up to "Seeds in the state, not a live generator".
- To read only: `docs/contracts/systems/drifters.md`, Interface, `game/core/levels.py`; `docs/contracts/systems/scroll.md`, Interface (`DISTANCE_DECIMALS`).

## Builds
- `game/core/waves.py` (new)

## Depends on
DRA-76-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
import random
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, WavePlacement, next_run_waves, pick_pool_wave, start_waves, step_waves
rock = WavePlacement(at_px=150.0, placement=Placement(DrifterType.METEORITE, x=320.0))
def wave(wave_id, kind, min_level=None, extra=0):
    return Wave(wave_id=wave_id, length_px=200.0, kind=kind, min_level=min_level, extra_rest_ticks=extra, placements=(rock,))
waves = (wave('w0', WaveKind.FIXED), wave('a', WaveKind.FIXED, extra=2), wave('p', WaveKind.POOL, 1), wave('q', WaveKind.POOL, 2))
playlists = (LevelPlaylist(fixed=('a',), random_count=1),) + tuple(LevelPlaylist(random_count=1) for _ in range(7))
book = WaveBook(waves={w.wave_id: w for w in waves}, wave_zero_id='w0', playlists=playlists)
state = start_waves(book, 7)
seen = []
for step in range(1, 16):
    state = step_waves(state, step * 50.0)
    name = state.current_wave_id or 'rest'
    seen.append(f'{name}/{state.level}/{len(state.spawns_due)}')
print(' '.join(seen))
print(pick_pool_wave(book, 2, 'p', random.Random(1)), pick_pool_wave(book, 1, 'p', random.Random(1)), book.level_slots(1), book.pool_ids(8))
again = next_run_waves(state)
print(again.current_wave_id, again.level, again.run_seed != state.run_seed)
"
```
It prints three lines:
- `w0/1/0 w0/1/0 w0/1/1 a/1/0 a/1/0 a/1/0 a/1/1 rest/1/0 rest/1/0 p/1/0 p/1/0 p/1/0 p/1/1 q/2/0 q/2/0`: Wave 0, the fixed wave, its 2-tick rest, the only pool wave allowed at Level 1, then Level 2 with a pick that is not the wave that just played. Each rock comes due once, at 150 px into its wave.
- `q p ('a', None) ('p', 'q')`: the picker leaves out the last wave when it can, repeats the only allowed one, and the book's slots and pool.
- `w0 1 True`: the next run starts Wave 0 at Level 1 with a new seed.

Put the command and its output in the implementation report. `game/tests/check.sh` ends `QA: pass`.

## Out of scope
- `core/wave_files.py` (task DRA-76-04), `core/run.py` (task DRA-76-05).
- Reading files, `game/app/`, `game/waves/`, views, tests.
- Tier checks, generated waves, per-wave drifter values.
