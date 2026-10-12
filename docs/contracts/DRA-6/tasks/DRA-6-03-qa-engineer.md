Feature: DRA-6
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/DRA-6/DRA-6-ship.md#rules
Status: done
Linear: DRA-11

## Do
Write permanent tests for the ship physics in `game/tests/core/test_ship.py`. Test through `core.ship` (`spawn`, `step`, `Thrust`, `Ship` and its constants) and `core.world` only. Build a `Ship` directly when a test needs a start state other than `spawn()`. Every expected number is computed from the GDD values named in each line, never typed in as a bare result. Compare floats with `pytest.approx`. Use pytest's `caplog` for the logging test.

Test each behavior:
1. With no key held, one tick from `spawn()` gives `vy = gravity`, `y = 240 + gravity`, and `x` and `vx` unchanged. Source: 04-ship.md, rule 2 (steps 2 and 5), gravity; 03-world-and-camera.md, ship_start.
2. With Up held, one tick from rest gives `vy = gravity - thrust_up` (the ship climbs). Source: 04-ship.md, rule 2 (steps 1 and 2), Derived (net climb).
3. With Right held for one tick from rest, `vx = thrust_side × drag_x`. A second tick with no key multiplies `vx` by `drag_x` again. `vy` is never multiplied by `drag_x`. Source: 04-ship.md, rule 2 (steps 1 and 3), rule 7.
4. Opposite keys cancel: Left with Right gives the same ship as no side key, and Up with Down gives the same ship as no vertical key. Source: 04-ship.md, Edge cases, rule 2.1.
5. Fall speed never goes past `fall_cap`: a ship already falling near the cap, with Down held, ends the tick at exactly `fall_cap`. Source: 04-ship.md, rule 2.4, fall_cap; 01-vision.md, locked decision 4.
6. Side walls stop the ship with no bounce: a ship moving left past the left wall ends with its left edge at 0 and `vx = 0`. The same on the right, with the right edge at `screen_w`. A following tick with no key doesn't move it away from the wall. Source: 03-world-and-camera.md, rule 6; 01-vision.md, locked decision 3.
7. Top line (temporary): with Up held for 300 ticks from `spawn()`, the ship's top edge is never above `screen_h × top_line_ratio` after any tick, and it ends with its top edge on that line and `vy = 0`. Source: DRA-6 scope report, Limits (temporary top-line stop); 03-world-and-camera.md, rule 2.
8. Floor respawn (temporary): a ship whose top edge ends the tick at or past `screen_h` comes back as `spawn()`: (320, 240), `vx = vy = 0`. A ship whose top edge ends the tick just above `screen_h` keeps falling and is not moved. Source: DRA-6 scope report, Limits (temporary floor respawn); 03-world-and-camera.md, rule 5; 05-lives-and-damage.md, fall_respawn.
9. Events log once, not every tick: holding Left against the left wall for 60 ticks logs exactly one `wall hit` line, holding Up at the top line for 60 ticks logs exactly one `top line stop` line, and one fall logs exactly one `respawn` line. Source: 15-tech-constraints.md, rule 9; game/CONTEXT.md, Logging; DRA-6-ship.md, Rules, Logging.

Number values used: gravity 0.16, thrust_side, thrust_up and thrust_down 0.42, drag_x 0.94, fall_cap 5.5 (04-ship.md, Values); ship_w and ship_h 32 (04-ship.md); screen_w 640, screen_h 480, top_line_ratio 0.35 (03-world-and-camera.md); ship_start and fall_respawn (320, 240) (03 and 05). All are `guess` except fall_respawn and top_line_ratio, which are locked.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the new tests in `tests/core/test_ship.py`.

## Out of scope
- The ship view and the debug overlay. The Integration Engineer checks them in the browser.
- The frame loop, key reading, the F3 toggle and the key log lines in `game/app/`. `check.sh` has no `app` step.
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
