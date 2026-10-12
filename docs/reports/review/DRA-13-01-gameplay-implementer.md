Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/gameplay/DRA-13-01-gameplay-implementer.md` (Gameplay Implementer, task `docs/contracts/DRA-13/tasks/DRA-13-01-gameplay-implementer.md`) against `docs/contracts/DRA-13/DRA-13-scroll.md` and the Impact sections of `DRA-6-ship.md` and `DRA-6-world.md`. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-13-01-gameplay-implementer.md` (this file). Reviewed: `game/core/scroll.py`, `game/core/ship.py`, `game/core/world.py`.
3. **Checks:** by reading only. Nothing run.
   - Interface: six constants, `Scroll` (fields, defaults, `frozen=True`, two properties), `start_scroll`, `step_scroll` checked line by line against the contract. All match.
   - Step and distance traced by hand. Acceptance output recomputed: after 30 steps `0 * 10 + 0 * 1.1 = 0.0`, `floor(0.0) = 0`. After 130 steps, scrolled 100: `100 * 1.1 = 110.00000000000001`, prints `110.0` after `round(.., 2)`, `floor(11.000000000000002) = 11`. Matches `0.0 0` / `110.0 11`. The 40-tick determinism claim also agrees: one log at tick 31, then scrolled 10, 11 px, 1 m.
   - Meter boundaries: `fl(1.1)` is slightly above 1.1, so `n * SCROLL_PER_TICK` never rounds below a whole-meter px value. The contract's Rationale holds for this code.
   - Docstring rewording in `ship.py` and `world.py` checked against the two Impact tables. Code line positions in `ship.py` match those cited in the DRA-6-01 review (`ship.py:109-116`, `128-133`), consistent with a docstring-only change. I could not diff, so this is indirect.
   - The "9 tests" claim matches the 9 `test_` functions in `game/tests/core/test_ship.py`.
   - Read against `game/CONTEXT.md`, `game/ruff.toml` (line length 100, ANN, I) and the gameplay-implementer standards.
   - 0 must-fix, 0 should-fix, 3 notes.
4. **Assumptions:**
   - As in the DRA-6-01 review, I read "implementers' standards" as the Python standards in `.claude/agents/gameplay-implementer.md`, and treat the contract as the rule where it narrows them (no pygame in core).
5. **Documentation differences:** None. The contract agrees with 03-world-and-camera.md, 06-scoring.md, 08-difficulty.md, 15-tech-constraints.md and 91-decision-log.md row 24.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/gameplay/DRA-13-01-gameplay-implementer.md` (test task DRA-13-04). Must-fix count: 0.
   - Integration Engineer: `start_scroll` and `step_scroll` are ready to wire in `game/app/frame.py` per `DRA-5-app.md`.
7. **Status:** done.

## Findings
1. **note** `game/core/scroll.py:16-33, 36`: the constants are not `Final`, and `Scroll` is `frozen=True` without `slots=True`. The standards ask for `Final` constants and `slots=True` where it fits. This matches `core/ship.py` and the contract's Interface text, and the DRA-6-01 review raised the same note. Decisions does not mention it. Source: gameplay-implementer Python standards. Change: optional, in a later task that touches both core modules, so they stay alike.
2. **note** `game/core/scroll.py:72-74`: the start log fires whenever the returned scroll has `scrolled_ticks == 1`, not only on tick 31. A hand-built `Scroll(ticks=100, scrolled_ticks=0)` would log `tick=101`. This is exactly the contract's rule (DRA-13-scroll.md, Rules, Logging), and from `start_scroll()` it can only be tick 31. Source: DRA-13-scroll.md, Rules. Change: none. QA should build inputs through `start_scroll()` when it checks the logged tick.
3. **note** `game/core/world.py:3-4`: the new sentence ends "the rules use screen px", and the next line repeats "Screen px, x right, y down." Harmless overlap. The wording matches the task's Do. Source: task DRA-13-01, Do; DRA-6-world.md, Impact. Change: none required.

## Checklist
1. Interface matches exactly: **pass**. `SCROLL_BASE`, `LEVEL_1_SCROLL_MULT`, `SCROLL_PER_TICK`, `SCROLL_START_DELAY`, `DISTANCE_START`, `PX_PER_METER` with the contract's types and values. `Scroll(ticks: int = 0, scrolled_ticks: int = 0)`, frozen, with `distance_px -> float` and `meters -> int` using the contract's formulas. `start_scroll() -> Scroll`, `step_scroll(scroll: Scroll) -> Scroll`. Nothing renamed, added or dropped.
2. UI/core split: **pass**. `scroll.py` imports only `logging`, `math`, `dataclasses` (`scroll.py:10-12`). No pygame, `ui`, `app` or `core.ship`. `ship.py` and `world.py` imports unchanged.
3. Fixed 60 Hz tick: **pass**. One call is one tick. The start delay counts ticks (`scroll.py:69-70`). No clock or frame time.
4. Randomness only from a passed-in `random.Random`: **n/a**. No randomness, no iteration.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio or path.
6. Every number traces to the GDD: **pass**. 1.1, 30, 0 and 10 match 03-world-and-camera.md Values with status. 1.0 matches the 08-difficulty.md Level table. `SCROLL_PER_TICK` is computed, never a bare 1.1 (`scroll.py:22`). Each docstring names its source. The literal `0` and `1` in `step_scroll` are counter steps from the contract's Rules, not tuning values.
7. Pillars and locked decisions: **pass**. The scroll never reads or changes the ship, and the ship's step takes no scroll (Pillar 1; 03, rule 4). Distance only grows: `scrolled_ticks` only ever increases. The screen stays fixed. No weapons, walls untouched. Hazard rules: n/a.
8. Smells: **finding** (note 1). No god class, short functions, one level of nesting, no duplicated blocks, no magic numbers, no dead or commented-out code. Module state is `log` plus constants. Every function is type-hinted. Logging is lazy, by event, at DEBUG, on `core.scroll` via `__name__`.
9. Decisions present and matching the code: **pass**. Five bullets. The early return on `ticks <= SCROLL_START_DELAY` with the log only on the moving branch (`scroll.py:70-74`), the computed `SCROLL_PER_TICK`, the guess/locked sources, and the single multiplication for distance (`scroll.py:49`) all match.
10. Report claims match the files: **pass**. The acceptance output, the 40-tick determinism output and the 9-test count all agree with the code and the test file. The `ship.py` and `world.py` changes are docstrings only, as claimed: TEMPORARY now sits only on the floor respawn (`ship.py:4, 149`), the top line is a ceiling (`ship.py:137-140`), and no "camera" or "same space" text remains in `game/core/`. Nothing was run.

## For QA
- From `start_scroll()`: ticks 1 to 30 keep `distance_px == 0.0`. Tick 31 gives scrolled 1, 1.1 px, 0 m, and exactly one DEBUG line `scroll start tick=31`. No further lines over many ticks.
- Meters are exact at boundaries: at scrolled `100 * j`, `meters == 11 * j`. Over a long run, `meters` equals `scrolled_ticks * 11 // 100` and never goes down.
- `step_scroll` never mutates its input, and the same scroll always gives the same result.
- Existing ship tests still pass. Ship behavior and log lines are unchanged by the docstring edits.
