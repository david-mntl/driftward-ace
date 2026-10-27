Feature: DRA-126
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/saves.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-144

## Read in the contract
- saves.md: Diagram (the place table, the letter picker table)
- saves.md: Interface, the `core/saves.py` block
- saves.md: Rules: Order; Place; Message; Adding; Best; Nickname; Letter picker; Pure
- run.md: Interface, "DRA-126: the level reached"
- run.md: Rules, "The last life" (the `final_level` item), `next_run(run)`, Score ("Level reached")

## Builds
- `game/tests/core/test_saves.py` (new)
- `game/tests/core/test_run_last_life.py` (changed: the level-reached tests)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file, a line for the new tests)

## Depends on
DRA-126-01

## Not in the contract
- Runs reach the last life as the run tests already do: one life, a falling ship and short `LastLifeRules` (`dataclasses.replace`). A level rise during the last life is set up with a short wave book, as `test_run_waves.py` does. Source: tests/CONTEXT.md, Rules.

## Test
- Entries rank by score, then level reached, and an entry equal on both to an older one goes under it. Rules: Order; Place.
- `place_of` gives 1 on an empty list whatever the score, 0 included; a place on any list shorter than `TOP_N`; None for a run that ties the last entry of a full list on score and level, or ranks below it. Rules: Place.
- `message_for` maps place 1, places 2 and 3, places 4 to `TOP_N`, and None to the four messages. Rules: Message.
- `add_entry` puts the entry at its place, moves the ones below down, drops the one pushed past `TOP_N`, sets `last_nickname`, and allows the same nickname twice. Rules: Adding.
- `Saves.best` is the first entry's score, None on an empty list. Rules: Best.
- `is_valid_nickname` takes 1 to `NICKNAME_LENGTH` allowed characters with leading and inner blanks, and refuses an empty name, a trailing blank, a character not allowed and a name too long. Rules: Nickname.
- `start_picker` fills the slots from the last nickname, or all blank, with the cursor on slot 0; `turn_character` steps through `NICKNAME_CHARACTERS` both ways and wraps at both ends, changing only the cursor's slot; `move_cursor` moves and wraps both ways, changing no slot; `picked_name` drops only trailing blanks and gives `""` for all blanks. Rules: Letter picker.
- Every function leaves its input unchanged and gives the same output for the same input. Rules: Pure.
- `final_level` is the level on the tick lives reach 0, `level_reached` reads it from then on, a level rise during the last life leaves `level_reached` unchanged, `level_reached` is `level` before the last life, and `next_run` has no final level. run.md Rules: The last life; Score (Level reached); `next_run(run)`.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_saves.py` and the new `test_run_last_life.py` tests in the `core` step and all their tests passing.

## Out of scope
- The game flow's tests (DRA-126-07), the views' tests (DRA-126-08), the app's loading and writing (the Integration Engineer's browser checks).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
