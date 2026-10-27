Feature: DRA-126
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/saves.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-139

## Read in the contract
- saves.md: Purpose; Diagram (the place table, the letter picker table)
- saves.md: Interface, the `core/saves.py` block
- saves.md: Rules, all of it (Values, What is saved, Order, Place, Message, Adding, Best, Nickname, Letter picker, Pure, Same in both modes)
- saves.md: Rationale
- run.md: Interface, "DRA-126: the level reached"
- run.md: Rules, "The last life" (the `final_level` item), `next_run(run)` (no final level), Score ("Level reached")
- run.md: Rationale, "`final_level` is kept like `final_score`"

## Builds
- `game/core/saves.py` (new)
- `game/core/run.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report prints:
- `place_of` and `message_for` for the runs in saves.md's place table against that list, plus an empty list with a score of 0, a full list with a run that ties the last entry on score and level, and a full list with a run just above it;
- `add_entry` on a full list: the new list and its `last_nickname`, the entry pushed past `TOP_N` gone;
- the picker sequence in saves.md's letter picker table, starting from `start_picker("ACE")` and from `start_picker(None)`, with `picked_name` after each step, and `is_valid_nickname` for `"ACE"`, `" A"`, `"A "`, `""` and an 11-character name;
- a run brought to its last life (one life, a falling ship, short `LastLifeRules`, as the run tests do) and stepped to game over: `level`, `final_level` and `level_reached` on every state, then `next_run`'s `final_level`.

Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- `core/game_flow.py` (DRA-126-02), the views (DRA-126-03 to -05), tests (DRA-126-06 to -08).
- Reading or writing localStorage, and checking the loaded data: `game/app/`, the Integration Engineer's (`systems/app/save-storage.md`).
