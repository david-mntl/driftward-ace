Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-126-02-gameplay-implementer (saves in `game/core/game_flow.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-126-02-gameplay-implementer.md. Nothing saved in `game/tests/` (Verify mode). Inline scripts ran from the scratchpad.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui PASS. core: 3287 passed, 1 failed, `test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`. That is the one failure `docs/contracts/DRA-126/impact.md` lists for DRA-126-02 (the new DEBUG line `game over message=game_over place=none` comes before `screen game_over`), cleared by DRA-126-07. The last line is therefore `QA: fail (core)`, not `QA: pass`. I count it as a pass because the task's acceptance check allows exactly this failure. Re-check after DRA-126-07.
   - Acceptance check: ran the implementer's smoke script twice from `game/` with the dummy drivers. The two outputs are byte-identical (`cmp`). It shows every bullet: NEW_BEST_SCORE with a blank picker; `saves_changed` on held tick 1 of 30 only, no RETRY; the next game over starts with `ACE`; place 2 gives TOP_3 and place 4 gives TOP_10; a full list gives GAME_OVER with no picker; no saves gives `best` None and an empty leaderboard; a blank confirm saves nothing; `stop_saves` leaves the screen, hides BEST, and the next game over has no picker.
   - Edge cases, all correct, from my own script (`qa126_02.py`):
     - Place limits on a full list of ten: a tie on score and level, a lower level and a lower score give None. A higher level on the same score, or a higher score than the 10th, gives place 10 and TOP_10. A saved 10th place cuts the list to 10 and logs `place=10`. A run that beats every entry gives NEW_BEST_SCORE.
     - A tie goes under the older entry, and the log says `place=2`.
     - A 10-character last nickname fills all ten slots.
     - Presses: Enter held through the opening tick and the next one does not confirm. Up held through the opening tick does not turn. A fresh up then turns the character.
     - Combined keys: up+right turns the old slot, then moves the cursor. down+left wraps to slot 9. up+down, left+right and all four together do nothing. up+down+right moves the cursor only. A confirm with arrows ignores the arrows and does not pick RETRY on the save tick.
     - After the save: `saves_changed` is cleared the next tick. The picker stays as picked and takes no keys. Up moves the selection to MENU. Right does nothing. A name with a leading blank (`" X"`) saves as is.
     - Focus loss at GAME_OVER does nothing. All 16 arrow combinations leave the run, screen and `saves_changed` as they were.
     - The input flow is never mutated (compared with a deep copy). The same input gives an equal output.
     - `stop_saves` during picking keeps the picker and message and the picker still turns. A confirm then ends the picking and saves nothing.
     - An empty name with saves logs `name empty, nothing saved`, and `saves` is the same object.
     - After RETRY `saves` is kept. Via MENU the menu opens on Play.
     - With no saves, right does nothing and RETRY stays selected. `start_flow(run)` and the old `GameFlow(...)` call without the new fields both keep the defaults.
   - Review items (**For QA**) all covered above. F1 (`place=%s` on the save line) prints the same text as `%d` for an int place: seen in the logs. F2 is described under Next.
4. **Assumptions:** To control score and level for the place cases I set `final_score` and `final_level` with `dataclasses.replace` on the run at its last-life state, before the game-over tick. A test device only.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can proceed only once the whole feature is ready. The `core` failure above stays until DRA-126-07 updates that test. One note for the Architect, no bug: the contract does not say what a confirm does while `picking` is True and `saves` is None. That is only reachable by calling `stop_saves` mid-picking, which the app does not do (it follows a write, which follows a save tick, after picking has ended). Core ends the picking and saves nothing. With an empty name it logs nothing, where the Logging rule says to log on any empty-name confirm. If the Architect wants this written down, DRA-126-07 can test it then.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1 failed, 3287 passed: the failure `impact.md` expects until DRA-126-07) · ui PASS (89 passed)
QA: fail (core)
