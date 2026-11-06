Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Add the level-up banner to the run: the `level_up` field, `hud_level`, `level_up_cue` and step 9b on the playing and last-life tick (`docs/contracts/DRA-148/tasks/DRA-148-02-gameplay-implementer.md`, from the Architect).
2. **Delivered:** `game/core/run.py` (changed): import of `core.level_up`; `Run.level_up` (last field, default None); properties `hud_level` and `level_up_cue`; `_step_run_waves` now runs 9a then the new `_step_level_up_banner` (9b). `start_run`, `next_run` and `step_run` keep their signatures.
3. **Checks:**
   - IS_CE true. `py_compile` clean on `game/core/run.py`.
   - `game/tests/check.sh` (all): lint PASS (ruff check and format), typecheck PASS (mypy strict), core PASS, ui PASS, `QA: pass`. No failure in `core`.
   - Smoke (script below), run as `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -I smoke.py`, inline, not saved in the repo. Book: Wave 0 and fixed wave `a`, 10 px each, Level 2 has one random slot. Run 1 rules: rest 40, arrival 6, banner 20. The rise is on tick 49. Output:
     ```
     t= 49 level=2 hud_level=1 level_up=0  cue=True      <- state after the rise tick
     t= 50 level=2 hud_level=1 level_up=1  cue=False
     t= 54 level=2 hud_level=1 level_up=5  cue=False     <- last tick of the old level
     t= 55 level=2 hud_level=2 level_up=6  cue=False     <- arrival tick: new level
     t= 64 lives 5 -> 4 (a hit or fall during the banner): the banner keeps aging
     t= 68 level=2 hud_level=2 level_up=19 cue=False
     t= 69 level=2 hud_level=2 level_up=None cue=False   <- lifetime 20 reached
     ```
     Run 2 (rest 60, arrival 30, banner 40; lives set to 1 on the rise state, the ship falls):
     ```
     t= 63 level=2 hud_level=1 level_up=14 burst=False
     t= 64 level=2 hud_level=2 level_up=None lives=0 burst=True   <- last life: banner None at once, hud_level == level
     t= 65..79 level_up=None, hud_level == level, cue False
     600 more ticks to game over (level rose to 3 on the way): banner None and hud_level == level on every tick
     next_run: level_up None hud_level 1 cue False
     ```
   - Determinism: the script run twice, outputs byte-identical (`cmp`).
   - Grep of `game/core/run.py` and `game/core/level_up.py` for the banned names: only `.waves` matches `\.wav` (false positive). None real.
4. **Assumptions:** None beyond the contract. With `waves` None, `level_up` stays None (contract rule 4).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-02-gameplay-implementer.md`. Left alone: `core/waves.py` and `core/level_up.py` (task -01), `core/game_flow.py`, the `game/ui/level_up_*.py` files already in the tree, tests, tuning.
7. **Status:** done.

## Decisions
- Step 9b is `_step_level_up_banner`, called from `_step_run_waves` right after 9a, so the playing tick and the last-life tick both get it from the one call. `previous_level` is `run.level` going into 9a, read before `step_waves`. Contract order kept: burst first (None), then a rise with `rest_ticks > 0` starts a banner, then an existing banner ages, else nothing.
- The tick that loses the last life sets the burst in step 6 or 7, so its 9b sees the burst and clears the banner on that same tick. No banner starts on a last-life tick even when the level rises (run 2).
- `game_over` ticks return before any of this in `step_run`, so nothing changes there. `next_run` builds `start_run`, whose `level_up` default is None.
- No numbers in code: all come from the rules carried by the waves. No new log line (contract, Logging).

## Smoke script
```python
import sys
from dataclasses import replace
sys.path.insert(0, "/workspace/game")
from core.level_up import LevelUpRules
from core.run import Run, next_run, start_run, step_run
from core.ship import Thrust
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, start_waves

def wave(i: str, kind: WaveKind, ml: int | None) -> Wave:
    return Wave(wave_id=i, length_px=10.0, kind=kind, min_level=ml)

book = WaveBook(
    waves={"w0": wave("w0", WaveKind.FIXED, None),
           "a": wave("a", WaveKind.FIXED, None),
           "p": wave("p", WaveKind.POOL, 1)},
    wave_zero_id="w0",
    playlists=(LevelPlaylist(fixed=("a",)), LevelPlaylist(random_count=1))
    + (LevelPlaylist(random_count=1),) * 6,
)
rules = LevelUpRules(rest_ticks=40, arrival_ticks=6, banner_ticks=20)
idle = Thrust()

def row(t: int, r: Run) -> str:
    age = None if r.level_up is None else r.level_up.age_ticks
    return f"t={t:3d} level={r.level} hud_level={r.hud_level} level_up={age} cue={r.level_up_cue} lives={r.lives}"

def play_to_rise(rl: LevelUpRules = rules) -> tuple[Run, int]:
    run = start_run(start_waves(book, 7, rl))
    t = 0
    while not (run.waves and run.waves.level_rose):
        run = step_run(run, idle)
        t += 1
        assert t < 2000
    return run, t

print("run 1: banner")
run, t = play_to_rise()
print(" before rise tick: level 1; rise at tick", t)
for k in range(24):
    print(" ", row(t + k, run))
    run = step_run(run, idle)

print("run 2: last life lost during the banner")
run, t = play_to_rise(LevelUpRules(rest_ticks=60, arrival_ticks=30, banner_ticks=40))
run = replace(run, lives=1, waiting=False, invuln_ticks_left=0)
print(" ", row(t, run), "(lives set to 1)")
for k in range(1, 40):
    run = step_run(run, idle)
    if k <= 2 or 14 <= k <= 20 or k % 10 == 0:
        print(" ", row(t + k, run), f"burst={run.burst is not None} game_over={run.game_over}")
    if run.burst is not None:
        assert run.level_up is None and run.hud_level == run.level
assert run.burst is not None
# level rises again during the last life: no banner
for k in range(600):
    run = step_run(run, idle)
    assert run.level_up is None and run.hud_level == run.level
    if run.game_over:
        break
print("  last-life/game-over ticks: banner None, hud_level == level, final level", run.level, "game_over", run.game_over)
fresh = next_run(run)
print("next_run: level_up", fresh.level_up, "hud_level", fresh.hud_level, "cue", fresh.level_up_cue)
```
