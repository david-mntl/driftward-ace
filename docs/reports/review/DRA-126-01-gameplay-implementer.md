Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-126-01 (`game/core/saves.py` new, the level reached in `game/core/run.py`) against `docs/contracts/systems/saves.md` and `run.md`, for the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-126-01-gameplay-implementer.md`.
3. **Checks:** Read the implementation report, the task file, saves.md (all of it), run.md (DRA-126 Interface; Rules: The last life, `next_run`, Score), 11-save-data.md (Values, Rules, Edge cases), 10-ui.md game_over_message, `game/CONTEXT.md`, `game/core/saves.py` (1-184) and the changed parts of `game/core/run.py` (120-258, 360-384, 500-525). Confirmed `_start_last_life` runs in step 6/7, before `_step_run_waves` (run.py:381-384), so `final_level` is the level the tick was flown at. Checked that the smoke script's `LastLifeRules` and `Scroll` fields exist. Nothing run.
4. **Assumptions:** The constants are Final in code because the contract's Interface makes them so (locked GDD values). I did not raise this against the "everything configurable" preference.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: no open findings. See For QA.
7. **Status:** done.

## Findings
None.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- Last life lost on a tick where step 9a raises the level: `level_reached` and the saved entry keep the old level, while `level` rises (smoke tick 1).
- A full list with a run that ties #10 on score and level: `place_of` is None and the message is GAME OVER. One point above it: place 10.
- `add_entry` on a full list: the old #10 is dropped, the input `Saves` is unchanged and `last_nickname` is the new name. The smoke's "input unchanged" line only compares a reference to itself, so check the input's entries by value.
- Picker wrap at both ends: down on a blank gives `*`, up on `*` gives the blank, left on slot 0 gives slot 9. `picked_name` keeps leading and inner blanks and drops only trailing ones.
- `start_picker` with a `last_nickname` longer than 10 or with characters outside the set is not handled in core (Decision: the app checks loaded data). Cover it at the app's edge in DRA-126 app tests.
