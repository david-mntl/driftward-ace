Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-126-01-gameplay-implementer (`game/core/saves.py` new, the level reached in `game/core/run.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-126-01-gameplay-implementer.md. Nothing saved in `game/tests/` (Verify mode). Inline scripts ran from the scratchpad.
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (env, lint, format, typecheck, core 3288, ui 89).
   - Acceptance check reproduced with my own script, not the implementer's. `place_of` and `message_for` on saves.md's table (A 1500 LV4, B 900 LV4, C 900 LV3): 900/LV3 gives 4 TOP_10, 900/LV4 gives 3 TOP_3, 1500/LV4 gives 2 TOP_3, 1500/LV5 gives 1 NEW_BEST_SCORE, 900/LV5 gives 2, 899/LV9 gives 4. Empty list, score 0: place 1. Full list tying #10 on score and level: None, GAME_OVER. One point above #10: place 10, TOP_10. Same score with a lower level than #10: None.
   - `add_entry` on a full list: 10 entries kept, old #10 gone, `last_nickname` is the new name. The input's entries compared by value before and after: equal, `last_nickname` still None. A tie with #1 goes to place 2 (under the older entry). Above #1 by level only: place 1. Ties on an empty list: the older entry stays above. `best` changes only for an entry at place 1. A run with no place raises `ValueError` (the contract's caller never does this). `Saves` and `ScoreEntry` are frozen.
   - Fewer than 10 entries: a run of score 0 against nine tied entries gets place 10.
   - Picker: down on a blank gives `*`, up on `*` gives the blank, left on slot 0 gives cursor 9, right on slot 9 gives 0. A full turn of 43 steps returns the same character (43 unique characters). `start_picker(None)` and `start_picker("")` give all blanks, `""` picked. `" A B"` keeps leading and inner blanks. A 10-character name fills all slots. `turn_character` returns a new picker, the old one is unchanged. 2000 random picker walks: every non-empty `picked_name` passes `is_valid_nickname`.
   - `is_valid_nickname`: `ACE`, ` A`, `A B`, `*?!` and a 10-character name true; `A `, empty, 11 characters, lowercase, `é` and `A\n` false.
   - Level reached on the death tick, by a fall and by a hit, with the first-tick level before the tick at 18, 19, 20 ticks of scroll and others (0, 1, 17, 25, 60): the tick where step 9a raises the level keeps `final_level` at the old level (`level` 2, `final_level` 1, `level_reached` 1); a run already at level 2 keeps 2. `final_level` stays the same through the last life and game over. With 2 lives, the first fall leaves `final_level` None and `level_reached` follows `level`. A run with no waves: level 1 everywhere. `next_run`: `final_level` None, `level_reached` 1.
   - Determinism: the same run stepped twice gives equal state lists.
4. **Assumptions:** The picker character order is the GDD's guess (`nickname_char_order`); the tests of the order belong to DRA-126-06.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The review's note that `start_picker` does not handle a long or foreign `last_nickname` stays for the app's edge (DRA-126 app tests), not a bug here.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
