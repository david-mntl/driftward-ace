Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the implementation report `docs/reports/implementation/gameplay/DRA-23-01-gameplay-implementer.md` (`core/run.py` new, `core/ship.py` without the respawn stand-in). The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-23-01-gameplay-implementer.md` (this file).
3. **Checks:** I only read the code. I ran nothing.
   - I compared `game/core/run.py` and `game/core/ship.py` line by line with `docs/contracts/systems/run.md` (Interface, Rules, Logging) and `docs/contracts/systems/ship.md` (Interface, Rules, Impact), the task's Do list, `05-lives-and-damage.md`, `02-game-flow.md`, decision-log rows 27 to 32, scope report DRA-23, `game/CONTEXT.md` and `game/ruff.toml`.
   - I traced the acceptance script by hand. The first fall comes on tick 64 at y 500.20. Up from rest gives 240 − 0.42 + 0.16 = 239.74. Lives go 2, then 1, then 0, and game over arms the retry because no arrow is held. The retry returns `start_run()`. All four claimed output lines and the `game over meters=50` log line match the code.
   - I traced the blink pattern `VVVVVV......VVVVVV......VVVVVVV` against `ship_visible` (`run.py:78-81`). It matches the contract table.
   - Grep of `game/core/` for pygame, print, random, time, threading, asyncio and ui/app imports: no hits in code.
   - The two expected failures, `test_ship.py:165` (`test_floor_respawns_at_spawn`) and `test_ship.py:199-206` (the respawn part of `test_events_log_once`), test exactly the stand-in that was removed.
4. **Assumptions:** Without a diff, I can't confirm the claim that nothing else in `ship.py` changed. I checked that every constant, `Thrust`, `Ship`, `spawn`, steps 1 to 7 and both log lines match the contract text exactly. The class docstring sentence "x and y are the ship's center" was already there in DRA-19 (review DRA-19-01, finding 1).
5. **Documentation differences:** None in the code. One stale contract line is noted for the Architect: finding 3. I propose no edit to it.
6. **Next:** QA Engineer: run task DRA-23-04 against `docs/reports/implementation/gameplay/DRA-23-01-gameplay-implementer.md` and this review. 0 must-fix. The Director should know that the playable build has no fall handling until the Integration Engineer wires `step_run` into `game/app/frame.py` (finding 2).
7. **Status:** done.

## Findings
1. **note** `game/core/run.py:146`: `_apply_fall(stepped, protected, thrust)` takes `thrust` only to set `retry_armed` at `run.py:172`. But `stepped.held` already equals `thrust`, because it is set at `run.py:139`. The parameter adds nothing. Rule: keep functions short and names plain, no redundant inputs. Source: game/CONTEXT.md, Good practice. Change: optional. Use `not _any_arrow(stepped.held)` and drop the parameter in a later task that touches the file.
2. **note** `game/app/frame.py:18`: the app still imports and calls `core.ship.step` directly. Since `step` no longer respawns, a desktop or browser run of the current tree lets the ship fall off the screen for good, until the Integration Engineer switches the app to `start_run`/`step_run`. This is out of this task's scope (task DRA-23-01, Out of scope; `systems/ship.md`, Impact, `game/app/frame.py` row). It is not a fault in this code. Source: CLAUDE.md, "Leave a result the Director can check". Change: none here. The Integration Engineer's task closes it. The acceptance script in the implementation report is the checkable result until then.
3. **note** `docs/contracts/systems/ship.md:172`: the Rationale says the 04-ship.md rule 3 wording difference "is raised with the Director". `04-ship.md` rule 3 and `91-decision-log.md` row 32 now name the respawn wait and the game-over freeze as the two exceptions, so the open point is resolved and the line is stale. The code follows the resolved rule. Rule: no doc drift. Source: Documentation rule. Change: the Architect may update the line. I edit nothing.

## Checklist
1. Interface matches exactly: **pass**. The four `Final` constants with their values, `Run`'s eight fields in contract order with their defaults and field docs, `invulnerable`, `ship_visible`, `start_run() -> Run`, `step_run(run, thrust) -> Run` and `is_below_floor(ship) -> bool` (`ship.py:158`) all match. Every added name is private (`_`-prefixed).
2. UI/core split: **pass**. `run.py` imports only stdlib, `core.scroll` and `core.ship` (`run.py:11-16`). There are no `ui` or `app` imports.
3. Fixed 60 Hz tick: **pass**. The invulnerability and the blink count ticks (`run.py:129`, `run.py:80`). There is no frame time and no wall clock.
4. Randomness: **pass** (n/a in substance). There is no randomness and no order-dependent iteration. `zip(..., strict=True)` over a fixed tuple is deterministic.
5. Browser rules: **pass**. No blocking call, sleep, thread, await, audio file or path.
6. Numbers trace: **pass**. `LIVES_START` and `INVULN_TICKS` come from 05-lives-and-damage.md (locked). `BLINK_SWAP_TICKS` comes from scope report DRA-23 (approved in chat, LD-04 TBD), as the contract states. `RESPAWN_WAIT_LIMIT = None` comes from rule 2.5. The only literals left are structural (`- 1`, `% 2`, `0`).
7. Pillars and locked decisions: **pass**. No weapons. The wait holds the ship only as GDD rule 2.5 and decision-log rows 27 and 32 allow. Walls are untouched, with no bounce. Retry uses arrows only (locked decision 1, `retry_key`). Hazards are n/a in DRA-23.
8. Smells: **finding**, note 1 only. Functions are short with early returns and no deep nesting. There is no module-level state, no dead or commented-out code, and every signature is annotated.
9. Decisions: **pass**. All seven entries match the code: tick order, `replace` on a frozen `Run`, `_is_press` with `strict=True`, `waits` used only for the log, the game-over ship staying where it fell, constants only, and the frozen `Thrust()` default.
10. Report claims match the files: **pass**. The acceptance output, log order, blink string and the two named test failures all follow from the code as written. Two claims can't be confirmed by reading: the ruff pass, and the "16 passed" count. QA runs them.

## For QA
- Protected fall on the tick the timer goes 1 to 0 (`invuln_ticks_left=1`, ship about to cross the floor): no life lost, `respawn from ... wait=False`, `invulnerable end` logged before it, timer 0 after.
- Arrow held through a life-costing fall: the wait does not end while it stays held. Pressing a second arrow while the first is still held does end it, and that tick thrusts.
- Game over with an arrow held: no retry until every arrow is released. A second arrow pressed while one is held doesn't retry. On the retry tick the result equals `start_run()` except `held`.
- Game-over ticks freeze everything: `ship`, `scroll.ticks`, `lives` and `invuln_ticks_left` unchanged over many ticks, and the input `Run` is never mutated.
- No log line on idle ticks: a 10 s wait logs only its single `invulnerable end`. Exactly six `core.run` messages exist, at the contract's levels.
