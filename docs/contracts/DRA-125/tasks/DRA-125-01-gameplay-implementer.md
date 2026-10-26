Feature: DRA-125
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-127

## Read in the contract
- Purpose (the last-life paragraph)
- Diagram: the state diagram; the tick flowchart (the `LL` branch, the `HG` and `FALL` nodes); the score table; the last-life table
- Interface: the `Run` block (the `lives` and `game_over` comments, `retry_armed` removed); "DRA-125: what the last life adds and changes" (the `core/last_life.py` and `core/run.py` blocks)
- Rules: the Values paragraph (its last sentences); step 6.3; step 7.5; The last life; A last-life tick; A game-over tick; `next_run`; Burst; `hold_arrows`; `add_drifters` (first item); Score (Start and a new run; Last life and game over; the closing property line); Other rules (the first, the third and the last item); Logging (`last life`, `game over`, `drifter gone`, `new run`, the order inside one tick, Nothing else)
- Rationale: the DRA-125 bullets

## Builds
- `game/core/last_life.py` (new)
- `game/core/run.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report runs `step_run` with no key held and prints one row per tick (`lives`, `last_life`, `game_over`, `ship_visible`, `burst.age_ticks`, `burst.opacity`, the first two `particle_centers`, `final_score`, `score`, `scroll.meters`), plus every `core.run` log line, for:
- three falls, each wait ended by one ArrowUp press tick: the third fall starts the last life with the burst at (the ship's x, 480), `last life score=<n>`, then the world moves for `delay_ticks` ticks while `score` stays `<n>`, and `game over score=<n>` on tick L + `delay_ticks`; ten more ticks change nothing;
- a hit on the last life (put an ACTIVE meteorite on the ship with `lives=1`): the burst at the ship's center;
- the first case with `start_run(last_life_rules=LastLifeRules(delay_ticks=5, burst_particle_count=4))`: game over 5 ticks after the death, four centers;
- `next_run` on the game-over run: `new run`, a run equal to `start_run` with the same graze and last-life values (Wave 0 again when started with waves);
- `hold_arrows` during a respawn wait, then a step with the same arrow held: the wait doesn't end.

Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects from DRA-125-01; every other existing test passes unchanged.

## Out of scope
- `core/game_flow.py` (DRA-125-02), the views (DRA-125-03 onward), `game/app/` (the loader and the frame loop are the Integration Engineer's), tuning files, tests.
- The screen flash, the HUD life break, the real burst and the rebuild (LD-08); the game-over sound (AA-03).
- Any change to `core/drifters/`, `core/ship.py`, `core/waves.py`, `core/graze.py`, `core/popup.py` or `tools/`.
