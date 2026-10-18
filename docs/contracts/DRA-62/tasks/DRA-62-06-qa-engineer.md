Feature: DRA-62
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md, docs/contracts/systems/scroll.md
Status: done
Linear: DRA-75

## Read in the contract
- drifters.md: Diagram, Coin and the coin timeline.
- drifters.md: Interface, `game/core/drifters/coin.py` and the DRA-62 parts of `base.py` (`TickContext.scroll_step_px`, `parked`, `collect_points`, `collect_popup`).
- drifters.md: Rules: The base (Phase; Parked and moving; Per-tick facts; Collect; Entering; Leaving); Spawner (step 4, Parked); Coin (all of it).
- run.md: Interface, `Run.popups`, `game/core/popup.py`.
- run.md: Diagram: the one-tick flowchart, the score timeline, the popup timeline.
- run.md: Rules: steps 3, 3a, 5a, 6, 7, 9; a game-over tick; Score (Coin points, Never goes down, Game over, Start and retry); Logging (`drifter touch`, the order line, the "Nothing else" line).
- scroll.md: Interface, `scroll_step_px`. Rules, The next step's movement.

## Builds
- `game/tests/core/test_coin.py` (new)
- `game/tests/core/test_scroll.py` (changed: one new test)
- `game/tests/CONTEXT.md` (changed: a paragraph for `core/test_coin.py`)

## Depends on
DRA-62-01, DRA-62-02, DRA-62-05

## Not in the contract
- Like `test_fireball.py`, `test_coin.py` builds its own `DrifterTuning` for the coin (and a meteorite, for the hit on the same tick) from the GDD values at the top of the file, reads no `game/tuning/` file, and imports no expected number from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- `scroll_step_px` is 0.0 on the steps to ticks 1 to 30 and the scroll speed from tick 31 on, and always equals the distance `step_scroll` adds on that tick. Rules: scroll.md, The next step's movement. (In `test_scroll.py`.)
- A coin is born ACTIVE, with no WARNING state: just above the top edge at its x, or at a set spot; a placement without x is refused. Rules: Coin (Born; No warning of any kind; Start).
- A coin moves only by the scroll step: still before the scroll starts, then down exactly as far as the world each tick, never sideways, the same at Level 1 and Level 8 and with the playtest switches off. Rules: Parked and moving; Coin (Update; Scales).
- The spawner gives a coin no speed and refuses a placement speed; an invert and a specialty are refused. Rules: Spawner (step 4, Parked); Coin (Born).
- A coin's touch is a collect, it has no graze zone, and it is drawn at full brightness. Rules: Coin (Touch); The base (Collect).
- Entering and leaving are judged on the crystal's box and the ring's box: a coin from the top enters on its first move and is dropped on the timeline's state, and one placed on screen at the timeline's spot too. Rules: Coin (Drawn parts; Leaving); drifters.md, Diagram (coin timeline).
- A coin the ship touches pays its variant's points into the coin points and the score, is gone on that tick, and leaves a popup at its center; each variant pays its own points. Rules: run.md, step 5a; Score (Coin points).
- An invulnerable ship collects. Rules: run.md, step 5a.1.
- A ship standing in the respawn wait collects nothing, and the coin stays and keeps moving; on the tick a press ends the wait, the ship collects it. Rules: run.md, step 5a.
- A coin and a hazard touched on one tick: the coin pays and the hit costs a life. Rules: run.md, step 5a.4.
- A coin touched by a ship that falls below the floor on that tick pays, the fall costs its life, and no hit is tested. Rules: run.md, steps 5a.1, 5a.4 and 6.
- A coin collected on the tick the last life goes is in the final score, which then stays frozen; a retry starts with 0 coin points. Rules: run.md, Score (Game over; Start and retry).
- Two coins touched on one tick both pay, with their popups in drifter order. Rules: run.md, step 5a.2.
- A popup starts at age 0 at the coin's center, rises its rise per tick up the screen with its x unchanged and the scroll not moving it, shows on exactly its lifetime of states, is frozen on game-over ticks, and is gone after a retry. Rules: run.md, step 3a; a game-over tick; Diagram (popup timeline).
- Logs: a collected coin logs `drifter spawn`, one `drifter touch` with `effect=collect` and `drifter gone` on the collect tick; a coin that leaves logs `drifter spawn` and `drifter gone`; no coin ever logs `drifter active`; no line names the score or the points. Rules: run.md, Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_coin.py` and the new `test_scroll.py` test in the `core` step.

## Out of scope
- The ship against every coin variant (task DRA-62-05).
- UI tests for the coin's view and the popup's view: not asked for (scope report DRA-62, Limits, Tests).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than the two listed.
