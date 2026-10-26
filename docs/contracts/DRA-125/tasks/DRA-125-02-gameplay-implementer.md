Feature: DRA-125
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/game-flow.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-128

## Read in the contract
- game-flow.md: Purpose; Diagram (the state diagram, the tick flowchart, the two tables)
- game-flow.md: Interface, the `core/game_flow.py` block
- game-flow.md: Rules, all of it (Values, Presses, Start, MENU, INSTRUCTIONS and LEADERBOARD, PLAYING, PAUSED, GAME_OVER, `run_stepped`, `add_flow_drifters`, Same in both modes, Pure, Logging)
- game-flow.md: Rationale
- run.md: Interface, "DRA-125: what the last life adds and changes" (`Run.last_life`, `Run.game_over`, `next_run`, `hold_arrows`), built in DRA-125-01

## Builds
- `game/core/game_flow.py` (new)

## Depends on
DRA-125-01

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report feeds `step_flow` a scripted list of `TickInput`s, starting from `start_flow(start_run())`, and prints one row per tick (`screen`, `menu_selection`, `game_over_selection`, `run_stepped`, `run.scroll.ticks`, `run.lives`, `run.waiting`) plus every `core.game_flow` and `core.run` log line, for:
- up, up, down, down, down on the menu (wraps both ways), then Enter on Instructions, Space back (Play selected), Enter on Leaderboard, Enter back;
- Enter on Play held for 40 ticks (no pause), released, pressed again (`pause by=key`), Space to resume;
- `focus_lost` during play (paused), during the pause (nothing), on the menu (nothing);
- a pause during a respawn wait with ArrowUp pressed during the pause and held after the resume: still waiting; released and pressed: the wait ends;
- the last life with Enter pressed and `focus_lost` given during it: no pause; then GAME_OVER with RETRY selected; down, down, up; Enter on MENU (Play selected, no `new run`); Enter on Play (`new run`, a fresh run); lose again, Enter on RETRY (`new run`, PLAYING);
- `add_flow_drifters` with one meteorite placement on a paused tick, a page tick and a stepped tick: added only on the stepped one.

Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- Saves, the filled leaderboard, name entry, BEST, the place messages (DRA-126).
- The views (DRA-125-03 onward), `game/app/` (reading Enter, Space and the focus is the Integration Engineer's), tests.
- Any change to `core/run.py` or `core/last_life.py` (DRA-125-01).
