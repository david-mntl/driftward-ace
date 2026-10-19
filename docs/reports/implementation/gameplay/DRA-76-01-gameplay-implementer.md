Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-76-01 (Architect): the scroll speed follows the level. `core/levels.py` gets `FIRST_LEVEL` and the scroll speed and Rest gap rows. `core/scroll.py` gets `scroll_speed`, `raised_level_ticks` and the `level` argument.
2. **Delivered:**
   - `game/core/levels.py`: `FIRST_LEVEL`, `SCROLL_MULT`, `REST_GAP_MULT`, `scroll_mult`, `rest_gap_mult`. `LEVEL_STARTS_M` and `level_at` are untouched (task DRA-76-05 removes them).
   - `game/core/scroll.py`: `DISTANCE_DECIMALS`, `Scroll.raised_level_ticks`, `scroll_speed`, `level` argument on `step_scroll` and `scroll_step_px`, `distance_px` per level, `meters` rounded before the floor. `LEVEL_1_SCROLL_MULT` and `SCROLL_PER_TICK` removed. No code under `game/` imported them (the tests define their own copies).
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `py_compile` on both files: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 66 files formatted.
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS. Last line `QA: pass`. Existing tests unchanged.
   - Acceptance command, run from `game/`:
     ```
     python -c "
     from core.levels import rest_gap_mult, scroll_mult
     from core.scroll import Scroll, scroll_speed, scroll_step_px, start_scroll, step_scroll
     print(scroll_mult(1), scroll_mult(8), rest_gap_mult(1), rest_gap_mult(8))
     print(scroll_speed(1), round(scroll_speed(8), 6))
     s = Scroll(ticks=30)
     for level in (1, 2, 2, 8):
         s = step_scroll(s, level)
     print(s.ticks, s.scrolled_ticks, s.raised_level_ticks, round(s.distance_px, 6), s.meters)
     print(scroll_step_px(start_scroll(), 8), round(scroll_step_px(s, 8), 6), Scroll(ticks=130, scrolled_ticks=100).meters)
     "
     ```
     Output:
     ```
     1.0 1.7 1.0 0.48
     1.1 1.87
     34 4 (2, 0, 0, 0, 0, 0, 1) 5.39 0
     0.0 1.87 11
     ```
     All four lines match the task.
   - Extra smoke (inline, 400 ticks, level cycling 1 to 8 every 50 ticks, run twice): final state `Scroll(ticks=400, scrolled_ticks=370, raised_level_ticks=(50, 50, 50, 50, 50, 50, 50))`, distance 561.0, 56 m, and `step_scroll(s, l).distance_px - s.distance_px` equals `scroll_step_px(s, l)` within 1e-9 on every tick. `step_scroll(s, 9)` raises `ValueError: level 9 is outside 1 to 8`. Both runs print identical output.
   - Grep of `game/core/scroll.py` and `levels.py` for sleep, threading, asyncio, pygame.display/event/key, `random.random(`, `.mp3`, `.wav`: no hits.
4. **Assumptions:**
   - `scroll_step_px` calls `check_level` on every call, including during the start delay, so it raises on a bad level like `step_scroll` does. The contract says only that `step_scroll` raises.
   - `step_scroll` checks the level before the start-delay test, so a bad level raises on every tick, not only on moving ticks.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-76/tasks/DRA-76-01-gameplay-implementer.md`. Left alone on purpose: `core/run.py` still calls both functions with no level (Level 1), and `LEVEL_STARTS_M` and `level_at` stay until DRA-76-05.
7. **Status:** done.

## Decisions
- Imports in `scroll.py` use `core.levels` (`FIRST_LEVEL`, `LEVEL_COUNT`, `check_level`, `scroll_mult`), the same style as the other core modules. No import cycle: `levels.py` imports nothing from core.
- `raised_level_ticks` defaults to `(0,) * (LEVEL_COUNT - 1)`, so the 7 entries follow the level count and `Scroll(ticks=..., scrolled_ticks=...)` still means Level 1 only.
- `distance_px` adds the per-level terms in a loop over `raised_level_ticks` and multiplies by `SCROLL_BASE` once, as the contract formula says. Level 1 ticks are `scrolled_ticks - sum(raised_level_ticks)`.
- Ticks inside the start delay use `dataclasses.replace(scroll, ticks=ticks)`, which keeps the other fields.
- A private helper `_count_level_tick` returns a new tuple with one entry raised. The tuple stays immutable and the input is never mutated.
- Every number comes from the contract Interface (which copies 03-world-and-camera.md and 08-difficulty.md). Nothing from `game/tuning/`.
