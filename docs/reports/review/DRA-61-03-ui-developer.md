Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-61-03 (the three-line layout and `draw_final_score` in `game/ui/game_over.py`) against `docs/contracts/systems/run.md` v4 and `hud.md` v2. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-61-03-ui-developer.md`.
3. **Checks:** By reading only. Compared `game/ui/game_over.py` with run.md (Interface for `game/ui/game_over.py`; Presentation: the `run.game_over` and `run.score` rows, Box, Title, Score, Prompt, Vertical place, Width, build-once line; Rules, Values; Impact and Rationale for DRA-61) and hud.md (Interface and Presentation of `score_text`). Also read `game/ui/score_text.py`, `game/ui/hud.py`, `game/app/frame.py:167-168`, `game/CONTEXT.md` and `game/ruff.toml`. Traced the layout by hand: title top `box_top + (120 - block) // 2`, score top one title `get_linesize()` below it, prompt top one score `get_linesize()` below that, in both functions through the shared `_box_origin` and `_title_top`. Nothing run.
4. **Assumptions:** The acceptance output, the screenshot, the cache counts and the `check.sh` result in the implementation report are taken as reported. QA runs them.
5. **Documentation differences:** None.
6. **Next:** Open findings: 0 must-fix, 0 should-fix, 0 notes needing a change (1 note, no action). QA Engineer takes the task.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-61-03-F1 | note | game/ui/game_over.py:140 | no action |

### DRA-61-03-F1
Decisions, bullet 3 calls the `lru_cache(maxsize=1)` score line "the same pattern as `hud.py` from DRA-61-02". That `hud.py` change was reverted by the DRA-61-02 QA fix, so `game/ui/hud.py` has no such helper today. The code itself matches the contract's build-once line (run.md, Presentation). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. Decisions match the code: DRA-61-03-F1
10. pass

## For QA
- With and without `draw_final_score`: the title and the prompt land on the same rows, and nothing draws in the score place while `frame.py` makes only the `draw_game_over` call.
- Two game overs in a row with different scores (retry in between): the second box shows the new score. The one-entry `_score_line` cache must render again.
- Tests that call `pygame.quit()` then init again: `_parts()` (`@cache`) and `_score_line` keep fonts and surfaces from the first init.
- A very long score (for example `10**20`): the line stays centered and inside the 320 px box.
- `SCORE 0` and `SCORE 1 234 567` on the box read in the same font and size as the HUD's SCORE line once DRA-61-06 lands.
