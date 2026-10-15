Feature: DRA-29
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md#rules
Status: done
Linear: DRA-37

## Do
Write permanent tests for objects inside the run: how they enter, when they hit, the one-hazard-one-hit rule, and when they leave. A hit decides whether a death is fair, and coins and grazes will build on the same tick, so it needs a guard. Test through `core.run.start_run`, `step_run`, `add_objects` and the `Run` fields, with `core.objects` (`Placement`, `ObjectType`, `Phase`, the tuning records, `Meteorite`) and `core.ship` (`Ship`, `Thrust`, `spawn`). Build a state close to the event with `Run(...)`, `Ship(...)` and `Meteorite(...)` (for example a meteorite already ACTIVE, with speed 0 so it stays put) where that keeps a test short, as `tests/core/test_run.py` does. Use `caplog` on the `core.run` logger for the log test.

`tests/core/test_run_objects.py`, one test per behavior:
1. `add_objects` spawns each placement in order at the run's level (Level 1), gives them uids 1, 2, 3 and appends them; `next_uid` moves on. An empty list, or a run at game over, comes back unchanged. Source: systems/run.md, Rules, `add_objects`.
2. An added meteorite shows its warning on the state after `add_objects` and the next 29 `step_run` states, and is ACTIVE after the 30th. While warning it never hits, even placed right on the ship. Source: 07-objects.md, rules 1 and 9; systems/run.md, Rules, step 3.
3. A hit: an active meteorite overlapping the ship, not invulnerable, costs one life, makes the ship invulnerable for 30 ticks and sets the meteorite's `hit_ship`. The ship's position and speed are exactly what the same tick gives with no object. Source: 05-lives-and-damage.md, rules 1.1, 1.3 and 1.4 (locked invuln_ticks 30).
4. An invulnerable ship: an overlapping meteorite costs no life and its `hit_ship` stays False. If it still overlaps when invulnerability ends, it hits then. Source: 05-lives-and-damage.md, rule 4; objects/01-meteorite.md, Edge cases.
5. A meteorite hits once: after a hit, the same meteorite still overlapping the ship when invulnerability ends never costs another life; it stays and keeps falling. This is the meteorite's own rule (`may_hit_ship()` False once `hit_ship` is set), not a shared one. Source: scope report DRA-29, Stand-ins (Director, 2026-10-15; LD-06 open in 05-lives-and-damage.md, Edge cases).
6. Two meteorites touching the ship on one tick cost one life, and both get `hit_ship`. Source: 05-lives-and-damage.md, Edge cases; scope report DRA-29, Decision log (2026-10-15).
7. A meteorite beside the ship whose graze zone overlaps the ship but whose hitbox doesn't costs nothing. Source: 06-scoring.md, rule 3; scope report DRA-29, Player sees ("passing just beside it doesn't").
8. A hit on the last life ends the run: lives 0, game over, the ship stays where it was hit (not respawned). On the next ticks the objects freeze with everything else, and `add_objects` adds nothing. Source: 05-lives-and-damage.md, rule 5; 02-game-flow.md, rule 5; systems/run.md, Rules.
9. A hit while the ship waits at the respawn point keeps it waiting at the respawn point. Source: 05-lives-and-damage.md, rule 1.4; scope report DRA-29, Decision log (2026-10-15).
10. On a tick where the ship falls past the floor while overlapping an active meteorite, only the fall counts: one life lost, the meteorite's `hit_ship` stays False. Source: scope report DRA-29, Decision log (2026-10-15); systems/run.md, Rules, step 6.
11. Leaving: an active meteorite is dropped on the tick its top edge reaches y 480, and not before; one above the top of the screen is never dropped. Source: 07-objects.md, rule 12; objects/01-meteorite.md, rule 5.
12. A retry starts with no objects and `next_uid` 1. Source: 02-game-flow.md, rule 6; systems/run.md, Rules.
13. Events log once, on `core.run`: one `object spawn` per object from `add_objects`, one `object active` when its warning ends, one `object touch` per object in a hit (with `effect=hit`), one `object gone` when it is dropped. A meteorite passing through an invulnerable ship logs nothing. A meteorite that never hits logs exactly three lines. Source: systems/run.md, Logging; 15-tech-constraints.md, rule 9.

Number values used, each copied with its source: lives_start 3, invuln_ticks 30 (05-lives-and-damage.md, locked); meteorite variants, hitbox radius, speed_ratio 0.75, entry_warning_ticks 30, start_y (objects/01-meteorite.md, guess); thrust_side 0.42, drag_x 0.94, gravity 0.16, ship_w 32, ship_h 32, hitbox bar 12 and foot 12 (04-ship.md, guess); graze_margin 14 (06-scoring.md, locked); screen_h 480, top line 168 (03-world-and-camera.md). Build the tuning records in the test from these values; never read `game/tuning/` here. Never import a constant from the code under test to compute an expected value.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, the `core` step runs the new tests in `tests/core/test_run_objects.py`, and every existing test in `tests/core/test_run.py` and `tests/core/test_ship.py` still passes unchanged.

## Out of scope
- The objects and spawner on their own (task DRA-29-07). Views and the registry guard (task DRA-29-09).
- Graze counting or scoring, coins, specialties, object-vs-object or wall collisions: not built.
- The debug test spawn list and the frame loop (`game/app/`, checked in integration).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, or existing tests.
