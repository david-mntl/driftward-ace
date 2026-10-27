Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-125-01: build `core/last_life.py` and change `core/run.py` for the last life, game over, `next_run` and `hold_arrows` (Architect, `docs/contracts/DRA-125/tasks/DRA-125-01-gameplay-implementer.md`, contract `docs/contracts/systems/run.md` version 11).

2. **Delivered:**
   - `game/core/last_life.py` (new): `DEFAULT_*` constants, `LastLifeRules`, `DEFAULT_LAST_LIFE_RULES`, `Burst` (`opacity`, `finished`, `particle_centers`), `start_burst`, `step_burst`.
   - `game/core/run.py` (changed): `retry_armed` removed; `Run.burst`, `final_score`, `last_life_rules`, `last_life`; `score` and `ship_visible` changed; `start_run(..., last_life_rules)`; `next_run`; `hold_arrows`; steps 6.3 and 7.5 start the last life; the last-life tick; the game-over tick; log lines `last life score=%d` and `game over score=%d`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/run.py game/core/last_life.py`: clean.
   - `ruff check game` and `ruff format --check game` (from the repo root): no findings. `game/tests/check.sh lint`: PASS lint, PASS format.
   - Smoke run below (command under Acceptance script): all five acceptance cases behave as the contract says. Run twice, output byte-identical (`cmp`).
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: only hits are the ban messages in `core/ruff.toml` and `.waves` attribute matches of `\.wav` in `core/waves.py` and `core/run.py` (`self.waves`). Nothing to remove.
   - `game/tests/check.sh` (all): `ui` passes (65). `typecheck` fails with 7 errors, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py` (impact.md row DRA-125-01). `core`: 26 failed, 3205 passed. Every failure is a test that loses the last life and reads `game_over` on that tick, a frozen world, the arrow retry, or `game over meters=`: the 18 tests impact.md names, plus eight the general rule covers (`test_run.py::test_a_held_arrow_never_retries`, `::test_a_new_run_starts_like_the_first`; `test_run_drifters.py::test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall`; `test_run_graze.py::test_a_graze_and_a_hit_by_another_hazard_on_one_tick_the_graze_pays_then_the_hit_counts`; `test_run_score.py::test_no_playing_tick_changes_the_coin_points`, `::test_score_never_goes_down_and_keeps_counting_through_falls_and_waits`; `test_run_waves.py::test_the_waves_step_once_on_every_playing_tick`, `::test_the_same_first_seed_gives_the_same_run_of_waves_and_retries`). I opened each: all fail at an `assert ....game_over` on the death tick or a retry by arrow. No test that never loses the last life fails.

4. **Assumptions:**
   - `Burst.particle_centers` returns plain floats from `math.cos` and `math.sin`, no rounding (the contract gives the formula only).
   - The default burst values (12, 1.0 px, 3 px) are the scope report's stand-in (DRA-125, Values needed, Burst); the delay default 120 is `02-game-flow.md`, `last_life_delay`. They equal `game/tuning/last_life.json`.
   - `last_life.py` keeps the module `log` the contract mentions, though it logs nothing (same as `popup.py`).

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-125/tasks/DRA-125-01-gameplay-implementer.md`. Left alone: every test (DRA-125-09 brings them in line), `core/game_flow.py` (DRA-125-02), `game/app/`, `game/tuning/last_life.json`, `tools/wave_editor/bench.py` (impact.md: main session, if anything shows).

7. **Status:** done.

## Acceptance script
Saved nowhere in the repo. Save it as a file outside `game/`, then from `game/`:
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script file>`

```python
"""DRA-125-01 smoke run. From game/: PYTHONPATH=. python <this file>. Prints one row per tick plus core.run logs."""

import logging
import sys
from core.collision import Circle
from core.drifters.base import Phase
from core.drifters.meteorite import Meteorite
from core.last_life import LastLifeRules
from core.levels import LEVEL_COUNT
from core.run import Run, hold_arrows, next_run, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, next_run_waves, start_waves

logger = logging.getLogger("core.run")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("    LOG %(levelname)s %(message)s"))
logger.addHandler(handler)
wave_log = logging.getLogger("core.waves")
wave_log.setLevel(logging.DEBUG)
wave_log.addHandler(handler)

NONE = Thrust()
UP = Thrust(up=True)


def row(tick: int, run: Run) -> None:
    b = run.burst
    age = b.age_ticks if b else "-"
    opa = f"{b.opacity:.4f}" if b else "-"
    cs = [(round(x, 2), round(y, 2)) for x, y in b.particle_centers[:2]] if b else "-"
    print(
        f"t={tick} lives={run.lives} last_life={run.last_life} game_over={run.game_over} "
        f"ship_visible={run.ship_visible} age={age} opacity={opa} centers={cs} "
        f"final_score={run.final_score} score={run.score} meters={run.scroll.meters}"
    )


def play_three_falls(run: Run, extra: int) -> Run:
    tick = 0
    after_over = 0
    while after_over < extra:
        thrust = UP if run.waiting else NONE
        run = step_run(run, thrust)
        tick += 1
        row(tick, run)
        if run.game_over:
            after_over += 1
    return run


print("== case 1: three falls, default rules (delay 120), then ten more ticks")
over = play_three_falls(start_run(), 11)  # game over tick + 10 more

print("== case 2: a hit on the last life, ACTIVE meteorite on the ship, lives=1")
rock = Meteorite(
    uid=1, x=320.0, y=240.0, variant="medium", width=28.0, height=28.0, speed=0.0,
    hitbox=(Circle(0, 0, 14.0),), warning_ticks=60, rehit_cooldown_ticks=180, rehit_dim=0.75,
    phase=Phase.ACTIVE,
)
run = Run(
    ship=Ship(x=320.0, y=240.0, vx=0.0, vy=0.0),
    scroll=Scroll(ticks=200, scrolled_ticks=170),
    lives=1,
    drifters=(rock,),
    next_uid=2,
)
run = step_run(run, NONE)
row(1, run)
print(f"    burst origin=({run.burst.x}, {run.burst.y}) ship=({run.ship.x}, {run.ship.y})")

print("== case 3: three falls with LastLifeRules(delay_ticks=5, burst_particle_count=4)")
rules = LastLifeRules(delay_ticks=5, burst_particle_count=4)
run = start_run(last_life_rules=rules)
tick = 0
while not run.game_over:
    run = step_run(run, UP if run.waiting else NONE)
    tick += 1
    if run.burst is not None:
        row(tick, run)
        print(f"    centers={len(run.burst.particle_centers)}")

print("== case 4: next_run on the game-over run, then with waves")
fresh = next_run(over)
same = start_run(graze_rules=over.graze_rules, last_life_rules=over.last_life_rules)
print(f"    next_run == start_run: {fresh == same}")
zero = Wave(wave_id="w0", length_px=1000.0, kind=WaveKind.FIXED, min_level=None, placements=())
book = WaveBook(
    waves={"w0": zero},
    wave_zero_id="w0",
    playlists=tuple(LevelPlaylist() for _ in range(LEVEL_COUNT)),
)
waved = start_run(start_waves(book, 7), last_life_rules=rules)
done = waved
while not done.game_over:
    done = step_run(done, UP if done.waiting else NONE)
again = next_run(done)
print(f"    waves again at level {again.level}, rules kept: {again.last_life_rules == rules}")
expected = start_run(next_run_waves(done.waves), last_life_rules=rules)
print(f"    equal to start_run with the next waves: {again == expected}")

print("== case 5: hold_arrows during a respawn wait, then the same arrow held")
run = start_run()
while not run.waiting:
    run = step_run(run, NONE)
print(f"    waiting={run.waiting} lives={run.lives}")
run = hold_arrows(run, UP)
run = step_run(run, UP)
print(f"    after hold_arrows(UP) then step(UP): waiting={run.waiting}")
run = step_run(run, NONE)
run = step_run(run, UP)
print(f"    after release then press: waiting={run.waiting}")
```

Output. The command prints every tick; runs of rows with nothing new are elided here (marked), and case 1's ten extra game-over rows are kept. Case 1: the third fall is on tick 195, the last life starts on tick 196 (L), `last life score=18`, burst at (320.0, 480.0) = (the ship's x, 480), `score` stays 18 while `meters` goes 18 to 31, `game over score=18` on tick 316 = L + 120, and the ten rows after change nothing. Case 2: burst at (320.0, 240.16), the ship's center. Case 3: game over on tick 201, 5 ticks after the death on tick 196, four centers. Case 4: `new run`, and `next_run` equals `start_run` with the same values; with waves, Wave 0 starts again (`wave start id=w0`) right after `new run`. Case 5: the wait does not end on the step after `hold_arrows` with the same arrow held; it ends on a real press.

```
== case 1: three falls, default rules (delay 120), then ten more ticks
t=1 lives=3 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=0 meters=0
t=2 lives=3 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=0 meters=0
    ... (rows elided here; the command prints every tick)
t=62 lives=3 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=3 meters=3
t=63 lives=3 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=3 meters=3
    LOG DEBUG life lost lives=2
    LOG DEBUG respawn from x=320.00 y=500.20 wait=True
t=64 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=3 meters=3
    LOG DEBUG respawn wait end
t=65 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=3 meters=3
t=66 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=3 meters=3
    ... (rows elided here; the command prints every tick)
t=92 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=6 meters=6
t=93 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=6 meters=6
    LOG DEBUG invulnerable end
t=94 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=7 meters=7
t=95 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=7 meters=7
    ... (rows elided here; the command prints every tick)
t=128 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=10 meters=10
t=129 lives=2 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=10 meters=10
    LOG DEBUG life lost lives=1
    LOG DEBUG respawn from x=320.00 y=496.44 wait=True
t=130 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=11 meters=11
    LOG DEBUG respawn wait end
t=131 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=11 meters=11
t=132 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=11 meters=11
    ... (rows elided here; the command prints every tick)
t=158 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=14 meters=14
t=159 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=14 meters=14
    LOG DEBUG invulnerable end
t=160 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=14 meters=14
t=161 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=14 meters=14
    ... (rows elided here; the command prints every tick)
t=194 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=18 meters=18
t=195 lives=1 last_life=False game_over=False ship_visible=True age=- opacity=- centers=- final_score=None score=18 meters=18
    LOG DEBUG life lost lives=0
    LOG INFO last life score=18
t=196 lives=0 last_life=True game_over=False ship_visible=False age=0 opacity=1.0000 centers=[(320.0, 480.0), (320.0, 480.0)] final_score=18 score=18 meters=18
t=197 lives=0 last_life=True game_over=False ship_visible=False age=1 opacity=0.9917 centers=[(321.0, 480.0), (320.87, 480.5)] final_score=18 score=18 meters=18
t=198 lives=0 last_life=True game_over=False ship_visible=False age=2 opacity=0.9833 centers=[(322.0, 480.0), (321.73, 481.0)] final_score=18 score=18 meters=18
    ... (rows elided here; the command prints every tick)
t=256 lives=0 last_life=True game_over=False ship_visible=False age=60 opacity=0.5000 centers=[(380.0, 480.0), (371.96, 510.0)] final_score=18 score=18 meters=24
    ... (rows elided here; the command prints every tick)
t=314 lives=0 last_life=True game_over=False ship_visible=False age=118 opacity=0.0167 centers=[(438.0, 480.0), (422.19, 539.0)] final_score=18 score=18 meters=31
t=315 lives=0 last_life=True game_over=False ship_visible=False age=119 opacity=0.0083 centers=[(439.0, 480.0), (423.06, 539.5)] final_score=18 score=18 meters=31
    LOG INFO game over score=18
t=316 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=317 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=318 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=319 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=320 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=321 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=322 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=323 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=324 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=325 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
t=326 lives=0 last_life=False game_over=True ship_visible=False age=120 opacity=0.0000 centers=[(440.0, 480.0), (423.92, 540.0)] final_score=18 score=18 meters=31
== case 2: a hit on the last life, ACTIVE meteorite on the ship, lives=1
    LOG DEBUG drifter touch id=1 type=meteorite effect=hit
    LOG DEBUG life lost lives=0
    LOG INFO last life score=18
t=1 lives=0 last_life=True game_over=False ship_visible=False age=0 opacity=1.0000 centers=[(320.0, 240.16), (320.0, 240.16)] final_score=18 score=18 meters=18
    burst origin=(320.0, 240.16) ship=(320.0, 240.16)
== case 3: three falls with LastLifeRules(delay_ticks=5, burst_particle_count=4)
    LOG DEBUG life lost lives=2
    LOG DEBUG respawn from x=320.00 y=500.20 wait=True
    LOG DEBUG respawn wait end
    LOG DEBUG invulnerable end
    LOG DEBUG life lost lives=1
    LOG DEBUG respawn from x=320.00 y=496.44 wait=True
    LOG DEBUG respawn wait end
    LOG DEBUG invulnerable end
    LOG DEBUG life lost lives=0
    LOG INFO last life score=18
t=196 lives=0 last_life=True game_over=False ship_visible=False age=0 opacity=1.0000 centers=[(320.0, 480.0), (320.0, 480.0)] final_score=18 score=18 meters=18
    centers=4
t=197 lives=0 last_life=True game_over=False ship_visible=False age=1 opacity=0.8000 centers=[(321.0, 480.0), (320.0, 481.0)] final_score=18 score=18 meters=18
    centers=4
t=198 lives=0 last_life=True game_over=False ship_visible=False age=2 opacity=0.6000 centers=[(322.0, 480.0), (320.0, 482.0)] final_score=18 score=18 meters=18
    centers=4
t=199 lives=0 last_life=True game_over=False ship_visible=False age=3 opacity=0.4000 centers=[(323.0, 480.0), (320.0, 483.0)] final_score=18 score=18 meters=18
    centers=4
t=200 lives=0 last_life=True game_over=False ship_visible=False age=4 opacity=0.2000 centers=[(324.0, 480.0), (320.0, 484.0)] final_score=18 score=18 meters=18
    centers=4
    LOG INFO game over score=18
t=201 lives=0 last_life=False game_over=True ship_visible=False age=5 opacity=0.0000 centers=[(325.0, 480.0), (320.0, 485.0)] final_score=18 score=18 meters=18
    centers=4
== case 4: next_run on the game-over run, then with waves
    LOG INFO new run
    next_run == start_run: True
    LOG DEBUG wave start id=w0 level=1 random=False
    LOG DEBUG life lost lives=2
    LOG DEBUG respawn from x=320.00 y=500.20 wait=True
    LOG DEBUG respawn wait end
    LOG DEBUG invulnerable end
    LOG DEBUG life lost lives=1
    LOG DEBUG respawn from x=320.00 y=496.44 wait=True
    LOG DEBUG respawn wait end
    LOG DEBUG invulnerable end
    LOG DEBUG life lost lives=0
    LOG INFO last life score=18
    LOG INFO game over score=18
    LOG INFO new run
    LOG DEBUG wave start id=w0 level=1 random=False
    waves again at level 1, rules kept: True
    LOG DEBUG wave start id=w0 level=1 random=False
    equal to start_run with the next waves: True
== case 5: hold_arrows during a respawn wait, then the same arrow held
    LOG DEBUG life lost lives=2
    LOG DEBUG respawn from x=320.00 y=500.20 wait=True
    waiting=True lives=2
    after hold_arrows(UP) then step(UP): waiting=True
    LOG DEBUG respawn wait end
    after release then press: waiting=False
```

## Decisions
- Update order: unchanged. The contract fixes it (steps 1 to 10); the last-life tick follows its own list. No Euler choice was needed: the last-life tick does not step the ship.
- `step_run` dispatch: `game_over` goes to `hold_arrows` (held = thrust, nothing else); `burst` set goes to `_step_last_life`; else the playing tick. `last_life` is the property of the contract; the dispatch tests `burst is not None` so the type checker has the burst in hand.
- The death tick runs in full: `_start_last_life` is called from the fall and the hit branches, and steps 8, 9, 9a then run as before. `final_score` is read from `stepped.score` there, after steps 5a and 5b, so a coin or graze paid on that tick is in it.
- Burst origin: fall: `(ship.x, SCREEN_H)` with the ship as it fell (`SCREEN_H` from `core.world`); hit: the ship's center. Source: run.md, steps 6.3 and 7.5.
- Log order on the death tick: `drifter touch`, `life lost`, `last life` (hit) or `life lost`, `last life` (fall), then `drifter gone`, the waves' lines. On the tick the burst finishes, `game over score=` is logged after the waves' lines (`_end_last_life` runs last). Source: run.md, Logging, order inside one tick.
- `next_run` logs `new run` before it builds the new run, so `core.waves`' `wave start` line follows it. Source: run.md, Logging.
- `_apply_fall` and `_apply_hit` lost their `thrust` argument: it was only used by the old `_end_run` for `retry_armed`. `_any_arrow` and `_step_game_over` are gone for the same reason. Private functions only.
- `Burst.particle_centers` computes the angle `2 pi k / particle_count` per square and the reach `age * speed` once. Place depends on age alone, as the contract says.
- Every number: `last_life_delay` 120 from `02-game-flow.md` (guess); burst count 12, speed 1 px per tick, size 3 px from scope report DRA-125, Values needed, Burst. Run values reach the run through `LastLifeRules`; no number in `run.py`.
