Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-6-03-qa-engineer (permanent ship physics tests), set by the Architect.
2. **Delivered:** game/tests/core/test_ship.py (9 tests), game/tests/CONTEXT.md (one Fixtures line: `caplog` for event-log tests), docs/reports/qa/DRA-6-03-qa-engineer.md
3. **Checks:** check.sh ends `QA: pass`; the `core` step collects and passes the 9 new tests, one per Do line:
   - `test_ship_falls_with_no_input` (Do 1)
   - `test_up_thrust_beats_gravity` (Do 2)
   - `test_drag_slows_vx_only` (Do 3)
   - `test_opposite_keys_cancel` (Do 4)
   - `test_fall_speed_stops_at_fall_cap` (Do 5)
   - `test_side_walls_stop_without_bounce` (Do 6)
   - `test_top_line_stops_climb` (Do 7, marked `smoke`)
   - `test_floor_respawns_at_spawn` (Do 8)
   - `test_events_log_once` (Do 9)

   The tests caught all 8 deliberate breaks made in a scratch copy of `core/ship.py` (left-wall bounce, drag on vy, wall line every tick, floor check `>` instead of `>=`, no fall cap, up thrust ignored, top-line stop keeps vy, gravity 0.17). Game code was not touched.
4. **Assumptions:**
   - The GDD values are written once as sourced constants in the test file, not imported from `core.ship` or `core.world`. A wrong constant in game code then fails a test instead of passing silently. When a GDD value changes, the test file changes with it.
   - `TOP_LINE_Y` is `round(SCREEN_H × TOP_LINE_RATIO)`, as `DRA-6-world.md` Interface says. Without the round, 480 × 0.35 in floating point is a hair above 168.
   - Start states built with `Ship(...)` use test-input numbers that are not game values: vx ±3.0 toward a wall from 1 px away, vx 2.0 / vy −1.0 for the cancel test, vy `fall_cap − gravity / 2` for "near the cap", 0.5 px for "just above the floor", 1 px for "past the floor", x 100 for the falling ship.
   - Do 9, wall part: Left and Up are held together, starting with the ship on the left wall and on the top line. Left alone lets the ship fall off the floor and respawn inside 60 ticks, which would leave the wall. Only `wall hit` lines are counted there.
   - Do 9, respawn part: "one fall" is stepping from `spawn()` with no key until the ship comes back as `spawn()`.
5. **Documentation differences:** None.
6. **Next:** Architect closes DRA-6-03. The task file stays `Status: open`.
7. **Status:** done.

## Bugs
None.

## Harness
PASS env · PASS lint · PASS format · PASS core (9 passed) · PASS ui (3 passed)
QA: pass
