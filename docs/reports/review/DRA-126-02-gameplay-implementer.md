Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-126-02 (saves in `game/core/game_flow.py`), built by the Gameplay Implementer from `docs/contracts/systems/game-flow.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-126-02-gameplay-implementer.md`.
3. **Checks:** By reading only. I compared `game/core/game_flow.py` (all 368 lines) with the contract parts the task names: Interface (DRA-126 block), Rules (Presses, Start, Opening GAME_OVER, GAME_OVER, `saves_changed`, `stop_saves`, `best` and `leaderboard`, Pure, Logging), the tick flowchart and Rationale. I also checked it against the `core/saves.py` functions it calls, `docs/contracts/DRA-126/impact.md`, 11-save-data.md rules 5 to 9 and nickname_char_order, `game/CONTEXT.md` and `game/ruff.toml`. I traced the smoke output against each acceptance bullet: all six are shown. Nothing was run.
4. **Assumptions:** I did not look at the git diff for the DRA-125 parts the task left alone; I only checked that they still match the contract. The one core test failure the report names is the one `impact.md` expects.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Two notes, neither asks for a change. The `core` check has one expected failure until DRA-126-07.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-126-02-F1 | note | game/core/game_flow.py:361 | no action |
| DRA-126-02-F2 | note | game/core/game_flow.py:352 | no action |

### DRA-126-02-F1
The save log line uses `place=%s`, but the contract gives `place=%d` (game-flow.md, Rules, Logging). For an int place the output is the same, and `%s` won't break the log call on a None. Change: none.

### DRA-126-02-F2
A confirm while `saves` is None returns before the empty-name check, so an empty name logs nothing there. The contract's Logging rule asks for `name empty, nothing saved` on any empty-name confirm. The app can't reach this: `stop_saves` follows a failed write, and a write only follows a save tick, after picking has ended. The report declares it under Assumptions. Change: none.

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
- Hold Enter through the save: `saves_changed` is True on the save tick only, and RETRY needs a fresh press.
- Press up and right on the same tick in the picker: the character turns in the old slot, then the cursor moves. Up with down, or left with right, does nothing.
- Hold an arrow in the picker: it steps once, never repeats.
- A run that ties an entry on score and level goes under it. The smoke shows place 2, TOP_3, for score 0 under ACE 0.
- `stop_saves` on GAME_OVER after a save: the screen, message and picker stay, BEST hides, and the next game over has no picker. Until DRA-126-07 lands, the logging test around `test_game_flow.py:901` is the only expected failure.
