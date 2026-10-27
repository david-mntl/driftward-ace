# DRA-126 away log

The Director asked on 2026-10-26 to "trigger the next open task DRA-126", then, while the Architect ran: "Please handle everything while im gone - like triggering the implementation once the architect finishes." Every call made without the Director is listed here. Review each one when you're back.

## Decisions
1. **"Trigger DRA-126" read as the go.** Scope report docs/reports/scope/DRA-126.md set to `Verdict: ship`, Linear DRA-126 to Todo. DRA-125 set to Done in Linear: all 12 of its sub-issues were Done after close-out, but the feature issue was still Todo.
2. **Architect Q1, rule 5 wording: accepted the Architect's text.** 11-save-data.md rule 5 said saves are off when localStorage is "empty". That clashed with its own edge case (the first score makes #1) and the scope report's Player sees. New rule 5: saves are off only when localStorage is missing, can't be read or written, or the data is broken; an empty list works. Written to the GDD: 11-save-data.md rule 5, decision log row 94. The frozen scope report still says "empty, missing or broken" in Feature; the GDD wins.
3. **Architect Q2, level reached: the level when the last life is lost**, frozen with the score, through a new `Run.final_level`. The score is frozen at that tick too, so both fields describe the same moment. Written to the GDD: 11-save-data.md Edge cases, decision log row 95.
4. **Architect Q3, picker after the save: accepted as proposed.** The slots keep the name; the cursor outline and the hint line hide, and their places stay empty so nothing moves. Underline and outline are 1 px. While the picker is open, RETRY and MENU are grey with no `>`. Stand-ins, not written to the GDD.
5. **Architect Q4, leaderboard rows: accepted as proposed.** Four columns, each as wide as its widest cell, the table centered. Place and score right-aligned, nickname and `LV n` left-aligned, 24 px between columns. Stand-ins, not written to the GDD.
6. **docs/TODO.md: added the top-left corner entry** (SCORE, GRAZE, BEST over corner warnings). hud.md already said TODO.md tracks it, but only the top-right hearts were listed.
7. **Browser storage errors: option (a).** The first integration run was blocked. pygbag 0.9.3 raises a bare `Exception` when the browser refuses localStorage ("The operation is insecure." on read, "The quota has been exceeded." on write), and the rules allowed `except Exception` only in the error guard. That meant a blocked or full storage showed the error screen, against 11-save-data.md rule 5. Chose (a): catch `Exception` around the storage calls in `game/app/saves.py` only, log a WARNING, turn saves off. Rejected (b), a JS wrapper built with `platform.window.eval`, because it puts JS source inside Python. Changed: `game/CONTEXT.md`, Error handling (main session, it has no agent owner); `save-storage.md` Errors, its rationale, and `error-handling.md` (fresh Architect run).
8. **Linear sub-issues DRA-139 to DRA-146 moved to In QA**, each with its QA pass comment. DRA-126 stays Todo until close-out.

## Things for you to look at
- **Not re-checked after the fix:** the second integration run re-ran only the two storage checks and the required checks. The other DRA-126 browser checks passed in round 1, before the change, which touched only the storage `try` blocks.
- **A contract gap, not a bug:** a confirm while the picker is open and saves were just turned off (`stop_saves` mid-pick) ends the picking, saves nothing, and logs nothing. The app can only get there if a write fails while a later picker is open. Review DRA-126-02 F2, QA DRA-126-02 and -07.
- **Cosmetic:** the `name saved` log line uses `place=%s` where the contract says `%d`. Same output. Review DRA-126-02 F1.
- **`scripts/contracts.sh verify` warnings:** the task files' "Read in the contract" lines use the `contract.md: section` style that the checker splits wrongly (about 69 warnings). DRA-125 used the same style. The pointers read fine; nothing changed.
- **Saved stand-ins live here only.** Decisions 4 and 5 are cited by game-flow.md and the tests from this log, because the scope report is frozen. If you want them in the scope report's Decision log, that's a Scope Guardian edit.
- The Architect's FYI list (in its hand-back, repeated here): one localStorage key holding one JSON document; desktop runs have no localStorage, so saves are off there; a score of 0 can make the list; held arrows never repeat in the picker; two open tabs, last write wins; broken stored data keeps saves off and is never overwritten, so only clearing browser data brings saves back; BEST stays at x 200 and a long SCORE would overlap it (UI-01).

## What happened
- Architect design run: contracts written, blocked on Q1 to Q4. A revision run closed them and wrote 8 tasks (Linear DRA-139 to DRA-146).
- Tasks 01 to 05 (2 core, 3 UI): each reviewed with no must-fix or should-fix, then QA pass. No fix rounds.
- Tasks 06 to 08 (tests): all pass. `game/tests/check.sh` ends `QA: pass` (core 3406, ui 115).
- wave_check `--changed`: no wave changed, exit 0.
- Integration round 1: blocked on the storage exception (Decision 7). Round 2: `Verdict: pass`, docs/reports/integration/DRA-126.md. The Integration Engineer added `game/app/saves.py` and wired `game/app/frame.py`.
- Close-out is yours: `scripts/close-out.sh DRA-126`, in a fresh session.
