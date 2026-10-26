Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-125-08, the game-over screen in `game/ui/game_over.py` (task `docs/contracts/DRA-125/tasks/DRA-125-08-ui-developer.md`), against `docs/contracts/systems/game-flow.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-08-ui-developer.md` (this file). Reviewed: `game/ui/game_over.py`, per `docs/reports/implementation/ui/DRA-125-08-ui-developer.md`.
3. **Checks:** Read only, nothing run. Compared `game/ui/game_over.py` with the contract's `ui/game_over.py`, `ui/screen_look.py` and `GameOverChoice` blocks, Presentation (shared items and Game-over screen) and the Rationale item "The views take plain values". Checked the values against scope report DRA-125, Values needed, Game-over screen (320 × 160 box, `GAME OVER` at 32 px, score, RETRY and MENU at 16 px, `>` marker) and `game/ui/screen_look.py`. Checked 10-ui.md game_over_screen and game_over_message, `game/CONTEXT.md` (logger rule) and `game/ruff.toml`. Grepped `game/` for the removed names: the only importers of `ui.game_over` (`game/app/frame.py:38`, `game/tests/ui/test_game_over.py:9`) use `draw_game_over` and `draw_final_score`, which are kept. The test's own `SCORE_FONT_SIZE` at `game/tests/ui/test_game_over.py:23` is local. `impact.md` row DRA-125-08 lists the same 3 UI tests the report says fail.
4. **Assumptions:** The acceptance numbers in the report (box 160..479 × 160..319, ink rows 212..266) are taken as reported. They agree with the code's arithmetic (`(640 - 320) // 2 = 160`, `(480 - 160) // 2 = 160`), but I did not run the script.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, with this report and `docs/reports/implementation/ui/DRA-125-08-ui-developer.md`.
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
- Call `draw_game_over` alone, then add `draw_final_score` and `draw_game_over_choices` one by one. Each line must land in the same place whatever else was drawn.
- Switch the selection between RETRY and MENU. Only the `>` must move. Both labels keep the same pixels.
- Give a very long score (e.g. 10**12). It must still draw centered without an error, even if it runs past the box edge, since the contract sets no digit limit.
- Draw the same score over many frames, then a new one. The score line must render once per distinct score, and the title, labels, marker and box only once in total (15-tech-constraints.md, rule 5).
- Use a surface other than 640 × 480 (e.g. 800 × 600). The box and all four lines must re-center.
