Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-76-03 (Architect): build `game/core/waves.py`, the wave book, the wave state, the wave clock, the playlist runner and the random picker, to `docs/contracts/systems/waves.md`.
2. **Delivered:** `game/core/waves.py` (new): `REST_GAP_BASE_TICKS`, `WaveKind`, `WavePlacement`, `Wave`, `LevelPlaylist`, `WaveBook` (`level_slots`, `pool_ids`), `WaveRun` (`current_wave_id`), `start_waves`, `step_waves`, `next_run_waves`, `pick_pool_wave`, `rest_gap_ticks`. Interface names and fields are as the contract gives them. Nothing else changed.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/waves.py`: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 67 files formatted.
   - `game/tests/check.sh`: env, lint, format, typecheck (mypy strict), core, ui all PASS. Last line `QA: pass`. 46 tests passed.
   - Acceptance command, from `game/` (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, the task's script run as a file with `PYTHONPATH=.`), output:
     ```
     w0/1/0 w0/1/0 w0/1/1 a/1/0 a/1/0 a/1/0 a/1/1 rest/1/0 rest/1/0 p/1/0 p/1/0 p/1/0 p/1/1 q/2/0 q/2/0
     q p ('a', None) ('p', 'q')
     w0 1 True
     ```
     All three lines match the task.
   - Determinism: the same script run twice gives identical output (`diff` empty).
   - Extra smoke: a book whose Level 1 and 2 playlists are empty, Wave 0 of 100 px with a trigger at 0, stepped once to 100 px. Log order `wave start id=w0`, `wave end id=w0`, `level up level=3`, `wave start id=p level=3 random=True`. State level 3, next_slot 1, 2 placements due (Wave 0's and the next wave's, same tick). `rest_gap_ticks(8, 3)` is 3.
   - Grep of `game/core/waves.py` for sleep, threading, asyncio, pygame.display/event/key, `random.random(`, `.mp3`, `.wav`: the only hits are `.wave_id` (matches the `.wav` pattern), no audio. No other hits.
4. **Assumptions:**
   - I added two private-purpose constants the contract does not name: `SEED_BITS` (64, from `getrandbits(64)` in the Interface) and `REST_GAP_DECIMALS` (6, from the `rest_gap_ticks` formula), to avoid magic numbers. Both are `Final` and carry values the contract gives.
   - `level_slots` and `pool_ids` call `check_level`, so a bad level raises `ValueError` as the other level functions do. The contract is silent.
   - The wave clock loop assumes `placements` are sorted by `at_px`, as the contract says the book holds them: due placements are a prefix from `spawned` on.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-76/tasks/DRA-76-03-gameplay-implementer.md`. Left alone on purpose: `core/wave_files.py` (DRA-76-04), `core/run.py` (DRA-76-05), `game/app/`, `game/waves/`, tests.
7. **Status:** done.

## Decisions
- `step_waves` is one loop: collect due placements, test the end, end the wave, start the next one at `old start_px + length_px` if no rest. It exits on a rest or when the playing wave has not ended. It ends because each pass moves `start_px` forward by a positive length. This follows the contract's one-tick flowchart.
- State is replaced with `dataclasses.replace` at each step; the input is never mutated. The start of `step_waves` clears `spawns_due`, so the rest path returns `()`.
- Seeds: each random pick builds `random.Random(pick_seed)` and stores `getrandbits(64)` as the next seed. `next_run_waves` does the same from `run_seed`. No module-level `random.*`.
- The level rise helper `_next_level_with_slots` raises one level, then skips empty playlists while the level is below `LEVEL_COUNT`, so `level up` is logged once with the final level.
- Logging is DEBUG, by event, in the contract's order (`wave end`, `level up`, `rest start` or `wave start`). `start_waves` logs Wave 0's start. No line per tick or per due placement.
- Sources: `REST_GAP_BASE_TICKS` 0 is a GDD guess (08-difficulty.md, rest_gap_base; DF-02). Level count, multipliers and `FIRST_LEVEL` come from `core.levels`, `DISTANCE_DECIMALS` from `core.scroll`. No tuning keys are read.
- Update order is the clock order in the contract; no Euler step is involved.
