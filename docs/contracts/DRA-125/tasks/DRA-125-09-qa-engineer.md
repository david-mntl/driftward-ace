Feature: DRA-125
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-135

## Read in the contract
- Diagram: the state diagram; the score table; the last-life table
- Interface: "DRA-125: what the last life adds and changes" (`core/last_life.py`, `core/run.py`)
- Rules: step 6.3; step 7.5; The last life; A last-life tick; A game-over tick; `next_run`; Burst; `hold_arrows`; `add_drifters` (first item); Score (Start and a new run; Last life and game over); Other rules (the first and the third item); Logging (`last life`, `game over`, `new run`, the order inside one tick, Nothing else)

## Builds
- `game/tests/core/test_run_last_life.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file, and the lines about the changed files that mention game over, retry or `retry_armed`)
- The existing core tests `impact.md` lets fail from DRA-125-01 (changed), only where they fail for that reason: brought in line with the last life, the frozen game-over tick and `next_run`

## Depends on
DRA-125-01

## Not in the contract
- The last-life values are written at the top of the new file: `last_life_delay` from 02-game-flow.md, Values (guess), and the burst's count, speed and size from scope report DRA-125, Values needed (Burst), which the GDD doesn't hold yet (LD-08). Build `LastLifeRules` from them; read no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- Losing the last life by a fall starts the last life on that tick: lives 0, no respawn, not game over, the burst at age 0 at the ship's x on the bottom edge, the final score equal to that tick's score. Rules: step 6.3; The last life.
- Losing it by a hit (and by a hit during the respawn wait) puts the burst at the ship's center. Rules: step 7.5; The last life.
- A coin collected and a graze paid on the death tick are in the final score. Rules: The last life; Score (Last life and game over).
- During the last life the scroll moves, the drifters move, popups and rings age, cooldowns count down, drifters leave and the wave clock runs; no collect, graze, fall or hit happens, even with a hazard or a coin on the ship; the score stays the final score while the meters grow; arrows do nothing. Rules: A last-life tick.
- `add_drifters` adds drifters during the last life and nothing at game over. Rules: `add_drifters`.
- Game over comes exactly `delay_ticks` ticks after the death tick, with the burst finished; the burst shows on `delay_ticks` states; also with non-default `LastLifeRules`. Rules: A last-life tick, item 7; Diagram (the last-life table).
- A game-over tick changes nothing but `held`, whatever arrows are pressed, released or held; no arrow ever starts a new run. Rules: A game-over tick.
- The burst: every square on the origin at age 0; at age `a` square `k` at the origin plus `a × speed` along `2πk / count` from straight right toward straight down; the opacity falls evenly from 1.0 to 0.0; `step_burst` and the properties never mutate and give the same result twice. Rules: Burst.
- `ship_visible` is False from the death tick on, and as before until then. Rules: Interface (`ship_visible`); step 6.3, 7.5.
- `next_run` gives a fresh run equal to `start_run` with the same graze and last-life values: 0 score, no final score, no burst, no drifters, 3 lives; with waves, Wave 0 at Level 1 with the next seed; with none, none. Rules: `next_run`; Score (Start and a new run).
- `hold_arrows` changes only `held`; after it, an arrow held into the next tick doesn't end a respawn wait, and a fresh press does. Rules: `hold_arrows`.
- `start_run()`, `start_run(waves)` and `start_run(waves, graze_rules)` build the run they built before, with the default last-life values. Rules: Interface (`start_run`).
- It logs `last life score=<n>` on the death tick, after `life lost`; `game over score=<n>` once, on the tick the burst finishes; `new run` from `next_run`, then the waves' `wave start`; nothing on the last-life ticks but drifter, scroll and wave lines. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_run_last_life.py` in the `core` step, all its tests passing, and none of `impact.md`'s DRA-125-01 failures left.

## Out of scope
- The game flow's tests (DRA-125-10), the views' tests (DRA-125-11, DRA-125-12).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
