Feature: DRA-13
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/DRA-13/DRA-13-scroll.md#rules
Status: done
Linear: DRA-17

## Do
Write permanent tests for the world scroll and the distance counter in `game/tests/core/test_scroll.py`. Test through `core.scroll` only (`start_scroll`, `step_scroll`, `Scroll`, `distance_px`, `meters`). Every expected number is computed from the GDD values named below, never typed in as a bare result. Compute expected meters with exact arithmetic (for example `fractions.Fraction("1.1")` for `scroll_base`), so the test doesn't copy the code's float math. Compare `distance_px` with `pytest.approx`. Use pytest's `caplog` for the logging test.

Test each behavior:
1. Play starts at zero: `start_scroll()` has distance 0 px and 0 m. Source: 03-world-and-camera.md, distance_start, rule 8.
2. The world stays still for `scroll_start_delay` ticks: after 30 steps from `start_scroll()`, distance is still 0. The 31st step moves it by `scroll_base × 1.0`. Source: 03-world-and-camera.md, rule 4, scroll_start_delay; 08-difficulty.md, Level table (Level 1 scroll speed); 91-decision-log.md, row 24.
3. Steady speed: after `30 + n` steps, distance is `n × scroll_base × 1.0` px, for n = 1, 60 and 6000. Source: 03-world-and-camera.md, rule 4.
4. Whole meters, rounded down: after `30 + n` steps, meters is `floor(n × scroll_base / px_per_meter)`, for every n from 0 to 1000. That covers the ticks just before and on each meter boundary. Source: 06-scoring.md, rule 1, meters_rounding; 03-world-and-camera.md, px_per_meter.
5. The scroll never stops and never goes back: over 6000 steps, distance grows on every tick after the delay and never shrinks, and meters never go down. Mark it `smoke`. Source: 03-world-and-camera.md, rule 4; 06-scoring.md, rule 1.
6. The step is pure: `step_scroll` leaves its input unchanged, and two runs of 200 steps from `start_scroll()` end in equal states. Mark it `determinism`. Source: 15-tech-constraints.md, rule 2.
7. The scroll start logs once: 600 steps from `start_scroll()` log exactly one `scroll start` line, and it carries `tick=31`. Source: 15-tech-constraints.md, rule 9; game/CONTEXT.md, Logging; DRA-13-scroll.md, Rules, Logging.

Number values used: scroll_base 1.1 px/tick (guess), scroll_start_delay 30 ticks (guess), distance_start 0 m (locked), px_per_meter 10 (locked) from 03-world-and-camera.md, Values; Level 1 scroll speed × 1.0 (locked) from 08-difficulty.md, Values.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the new tests in `tests/core/test_scroll.py` next to the existing `tests/core/test_ship.py`.

## Out of scope
- The starfield and the HUD views (task DRA-13-05 covers the HUD layout). The Integration Engineer checks the starfield in the browser.
- Creating and stepping the scroll in `game/app/`. `check.sh` has no `app` step.
- Changes to `tests/core/test_ship.py`. Ship behavior doesn't change in DRA-13.
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
