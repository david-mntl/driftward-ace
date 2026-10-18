Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-62/tasks/DRA-62-06-qa-engineer.md` (the coin, its popup and coins in the run), started by the Director's agent.
2. **Delivered:** `game/tests/core/test_coin.py` (new, 15 tests), `game/tests/core/test_scroll.py` (changed: one new test, `test_scroll_step_px_is_zero_to_tick_30_then_the_scroll_speed_and_matches_step_scroll`), `game/tests/CONTEXT.md` (changed: a paragraph for `core/test_coin.py`), this report.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. The `core` step runs both new files (16 new tests: 15 in `test_coin.py`, 1 in `test_scroll.py`). Lint, format and mypy `--strict` pass on them.
   - One test per `## Test` line, in the task's order:
     - `scroll_step_px`: 0.0 on the steps to ticks 1 to 30, 1.1 from tick 31, equal to what `step_scroll` adds on all 300 steps, the scroll unchanged and nothing logged by the read.
     - born: ACTIVE, `ticks_in_phase` 0, no `warning_ticks`, at its x with y -10 or a set spot; no x refused with or without y (also through `add_drifters`).
     - movement: only the scroll step (0.0, 1.1, 3.7), x never changes, same at Level 1 and 8 and with the switches off, still on ticks 1 to 30 and first moves on tick 31 in a run.
     - spawner: speed 0.0 at every level; a speed (0.0, 1.0, 4.5), an invert and a specialty refused.
     - touch: COLLECT, `graze_zone()` is `()`, `brightness()` 1.0 also after a hit elsewhere on the field; the meteorite is the control (HIT, graze zone, base `collect_points` 0 and `collect_popup` None).
     - entering and leaving: crystal and ring boxes at the top, both sides and the floor, by name; the timeline in the run (dropped on T+455 at y 490.50 from the top, on n = 255 from (440, 210)).
     - collect: each variant pays its own points into the coin points and the score, is gone on that tick, popup at the coin's center after the scroll moved it; edge contact does not collect, a hair inside does.
     - invulnerable ship (30, 5 and 1 ticks left) collects; respawn wait collects nothing (coin stays and moves), the press tick collects.
     - coin and meteorite on one tick: coin pays, one life lost, log order checked.
     - fall tick (unprotected and protected): coin pays, the fall costs its life, no hit is tested.
     - last-life tick (by fall and by hit): coin in the final score, frozen for the box, 0 after a retry.
     - two coins on one tick, popups after the older ones, in drifter order.
     - popup: 60 states, x unchanged, rises 0.5 a tick with the scroll moving, ages on wait and protected ticks, frozen at game over, gone after a retry.
     - logs: collected coin `drifter spawn`, `drifter touch ... effect=collect`, `drifter gone`; a missed coin `drifter spawn` and `drifter gone`; no `drifter active`; no line names the score, points or a popup.
   - Sensitivity, not saved: 10 inline code mutants (coin moves at a fixed speed, rare pays 50, popup one scroll step off, protected ship skipped, crystal-only drawn parts, popup one state too long, y default 0, coin touch is HIT, no collect on a fall tick, popup rising with the scroll) and 2 source mutants in a scratch copy (collect while waiting; hit tested on a fall tick) each fail at least one new test.
   - Expected numbers come from the GDD values and the contract's tables at the top of `test_coin.py`; none is imported from the code under test, and no `game/tuning/` file is read.
4. **Assumptions:** a placement with `speed` 0.0 counts as "set" and is refused, as the spawner's rule reads (`speed` not None). Meters in the score checks are worked out from `Scroll(ticks=100, scrolled_ticks=70)`, one step on (7 m).
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, or the Director's next task. The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
