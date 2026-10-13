Feature: DRA-23
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md#rules
Status: done
Linear: DRA-27

## Do
Write permanent tests for the run in `game/tests/core/test_run.py`, and replace the two ship tests that tested the DRA-6 respawn stand-in. Losing lives, the wait and the retry decide whether a run is fair, and later hazards will build on them, so they need a guard. Test through `core.run.start_run`, `core.run.step_run` and the `Run` fields and properties, with `core.ship.Ship`, `Thrust`, `spawn` and `core.scroll.Scroll`, `start_scroll`. Build a state close to the event with `Run(...)` and `Ship(...)` where that keeps a test short, as `tests/core/test_ship.py` does. Use `caplog` on the `core.run` logger for the log test.

`tests/core/test_run.py`, one test per behavior:
1. A run starts with 3 lives, the ship at (320, 240) at rest (`spawn()`), a scroll at tick 0 (`start_scroll()`), not invulnerable, not waiting, not game over. Source: 02-game-flow.md, rule 3; 05-lives-and-damage.md, lives_start (locked); 03-world-and-camera.md, ship_start.
2. A fall that isn't protected costs one life and respawns the ship at (320, 240) at rest, waiting, with 30 ticks of invulnerability. Source: 05-lives-and-damage.md, rules 2.1, 2.3, 2.4 and 2.5, fall_respawn and invuln_ticks (locked).
3. While waiting with no key held, the ship stays exactly at the respawn point for many ticks (for example 600), and the scroll keeps going: `scrolled_ticks` grows by one each tick once the start delay is over. Source: 05-lives-and-damage.md, rule 2.5; 03-world-and-camera.md, rule 4.
4. The arrow press that ends the wait also thrusts on that tick: the ship after that tick equals `step(spawn(), thrust)`, and `waiting` is False. Source: 05-lives-and-damage.md, rule 2.5; 91-decision-log.md, row 28.
5. An arrow held through the fall doesn't end the wait. Holding it longer doesn't either. Releasing it and pressing an arrow again does. Source: 05-lives-and-damage.md, rule 2.5 ("the first arrow key press"); systems/run.md, Rules, step 1.
6. Invulnerability lasts 30 ticks from the respawn and ends on time whether or not the wait has ended: `invulnerable` is True on the respawn state and the next 29 states, and False on the 30th. Check it once with no key held and once with a press partway through. Source: 05-lives-and-damage.md, invuln_ticks (locked); scope report DRA-23, Limits ("It ends on time, wait or no wait").
7. The blink: over those 30 states `ship_visible` is visible for 6, hidden for 6, visible for 6, hidden for 6, visible for 6, then visible from then on. Source: scope report DRA-23, blink (one visible/hidden swap every 0.1 s, approved by the Director in chat, not in the GDD); 15-tech-constraints.md, tick_rate 60 (0.1 s = 6 ticks); systems/run.md, Diagram.
8. A fall while invulnerable costs no life: the ship respawns at (320, 240) at rest, doesn't wait, and the timer keeps counting down from where it was (it is one less than before the tick, not 30). Source: 05-lives-and-damage.md, rule 2.6; 91-decision-log.md, rows 29 and 31.
9. Losing the last life ends the run: lives 0, game over, and the ship is not respawned (its top edge is still at or past the floor at y 480). Source: 05-lives-and-damage.md, rule 5; 02-game-flow.md, rule 5; systems/run.md, Rules, step 5.3.
10. Game over freezes everything: for many ticks (for example 300) with no key held, the ship, the scroll and the lives don't change. Source: 02-game-flow.md, rule 5; 91-decision-log.md, row 30.
11. An arrow held when the game ends doesn't retry, however long it is held. Releasing every arrow and then pressing one starts a new run. Source: 02-game-flow.md, rule 6 and Edge cases; 91-decision-log.md, row 31.
12. With no arrow held when the game ends, the very next tick with an arrow held starts a new run: no delay. Source: 02-game-flow.md, rule 6 ("There is no delay").
13. A new run after a retry starts like the first: 3 lives, `spawn()`, `start_scroll()`, not invulnerable, no wait, not game over. On the next tick with no key, the ship falls under gravity (vy 0.16). Source: 02-game-flow.md, rules 3 and 6; 91-decision-log.md, row 30.
14. Events log once, on `core.run`: one `life lost` and one `respawn from` per fall, one `invulnerable end` per respawn, one `respawn wait end` per press that ends a wait, one `game over` and one `new run`. A ship waiting 600 ticks with no key logs nothing after its `invulnerable end`. Source: systems/run.md, Logging; 15-tech-constraints.md, rule 9.

`tests/core/test_ship.py`, replace two tests. Every other test in the file stays as it is:
15. Replace `test_floor_respawns_at_spawn`: `step` never respawns the ship. A ship stepped past the floor keeps its stepped position and speed. `is_below_floor` is True when the top edge is at or past y 480 and False just above it. Source: systems/ship.md, Rules, step 8 and "Then `step` returns the ship"; 03-world-and-camera.md, rule 5.
16. In `test_events_log_once`, replace the respawn part: a ship that falls past the floor logs no `respawn` line on `core.ship`. Keep the wall and top-line parts as they are. Source: systems/ship.md, Rules, Logging (DRA-23).

Number values used: lives_start 3 (locked), invuln_ticks 30 (locked), fall_respawn (320, 240) (locked), from 05-lives-and-damage.md; blink swap every 6 ticks (scope report DRA-23, approved in chat, not in the GDD); gravity 0.16 (04-ship.md, guess); screen_h 480 (03-world-and-camera.md, guess); scroll_start_delay 30 (03-world-and-camera.md, guess). Copy each with its source, as `tests/core/test_ship.py` does. Never import a constant from the code under test to compute an expected value.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the new tests in `tests/core/test_run.py` and the two replaced tests in `tests/core/test_ship.py`.

## Out of scope
- The hearts and the Game Over box views (task DRA-23-05 tests the hearts; the box is checked by eye and in the browser).
- The frame loop's draw order and the blink in the draw (`game/app/`; `check.sh` has no `app` step).
- `tests/ui/test_hud.py` (task DRA-23-05).
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
