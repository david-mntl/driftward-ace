Feature: DRA-148
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/waves.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-149

## Read in the contract
- systems/level-up/core.md: Diagram, Interface, The level-up rest, The rise flag, Purity
- waves.md: Interface, WaveRun, start_waves, next_run_waves, The wave clock, 3.1, 3.2, 2a, Rationale

## Builds
- `game/core/level_up.py` (new): the rules record, `NO_LEVEL_UP`, the banner record and its start and step functions, `shown_level`
- `game/core/waves.py` (changed): the two new `WaveRun` fields, the new `start_waves` argument, `next_run_waves` keeping the rules, the rest and the flag in `_end_wave` and `step_waves`

## Depends on
None

## Not in the contract
None.

## Acceptance check
A headless script (in the implementation report) builds a small wave book whose Level 1 playlist is one fixed wave, steps `step_waves` with the contract's rules and a rest gap and extra rest of your choosing, and prints, tick by tick around the end of that wave: `level`, `level_rose`, `resting` and `rest_ticks_left`. It shows: the rest equal to the gap plus the extra rest plus the level-up rest on the rise tick, `level_rose` True on that state only, the same book with no rules resting as before, no flag and no extra rest when Wave 0 ends, and none after Level 8's playlist. `game/tests/check.sh lint` and `typecheck` pass and `core` has no failure `impact.md` doesn't expect.

## Out of scope
- The run and the banner's state in it (task DRA-148-02). Any view, the tuning file and its loader, `game/app/`. Tests.
- Any change to `rest_gap_ticks`, the picker, the wave files or the loader checks.
