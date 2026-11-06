Feature: DRA-148
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/waves.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-155

## Read in the contract
- systems/level-up/core.md: Interface, The level-up rest, The rise flag
- waves.md: Rules, The wave clock, 3.1, 3.2, 2a

## Builds
- `game/tests/core/test_level_up_waves.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-148-01

## Not in the contract
- Like `test_waves.py`, the new file builds its own wave book and its own rules at the top of the file and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- A level rise adds the level-up rest to the rest gap and the wave's extra rest, never scaled, and the rest counts down to the next wave on exactly that many states. Rules: The level-up rest; waves.md, step 3.2.
- The rest after a rise at a level whose gap is scaled adds the unscaled level-up rest to the scaled gap. Rules: The level-up rest.
- A wave that ends with no rise (a playlist with waves left) adds nothing. Rules: The level-up rest.
- Wave 0 ending is no rise, and Level 8's last playlist wave and every random wave after it are no rise: no flag, no extra rest. Rules: The level-up rest.
- A level with an empty playlist is passed on the same tick and the rest is added once. Rules: The level-up rest.
- With `NO_LEVEL_UP` (the default of `start_waves`) the same book rests exactly as before, and with a rest of 0 there is no extra rest. Interface (`NO_LEVEL_UP`, `start_waves`).
- `level_rose` is True on the state after the rise tick and False on the next state and on every state of the rest; it is False on every other wave end. Rules: The rise flag.
- `next_run_waves` keeps the rules. Interface (`next_run_waves`).
- `step_level_up` ages by one a tick and returns None when the age reaches the lifetime; `start_level_up` gives age 0; `shown_level` gives the previous level below the arrival age, the real level from it and with no banner. Interface (`core/level_up.py`).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_level_up_waves.py` in the `core` step and all its tests passing.

## Out of scope
- The run, its step 9b and the properties (task DRA-148-08). The views and the HUD (task DRA-148-09). The loaders in `game/app/`.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
