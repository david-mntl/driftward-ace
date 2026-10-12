Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-5-01-ui-developer (error screen view and shared background color), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-5-01-ui-developer.md
3. **Checks:** All inline runs from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. Nothing saved in `game/tests/`.
   - check.sh: `QA: pass`, exit 0.
   - Acceptance check, 640×480. `detail=None`: one white band, rows 232..247, x 183..457, center x 320.0, rest (0, 0, 0). `detail="ValueError: boom"`: the same main band, plus a band at rows 250..257, x 270..369, center x 319.5. Main rect `Rect(182, 231, 276, 18)`, `get_linesize()` 18, detail rect top 249 = 231 + 18. Images: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/qa_none.png`, `.../qa_detail.png`.
   - For QA lines: main-line pixels identical between `None` and detail: True. Surface pre-filled (200, 10, 10): all four corners (0, 0, 0), 0 pixels off the grey/white text scale. `detail=""`: no raise, bytes identical to `None`. No `pygame.font` init: raises `pygame.error: font not initialized`, as the contract allows.
   - Cut limits: 91 `a` chars render 637 px (fits, no log line). 92 chars render 644 px, cut to 91 with one DEBUG line `error detail cut from 92 to 91 characters`. 500 `E` cut to 91, band x 3..638. 505 mixed cut to 63, band x 5..635. `None` and a short detail log nothing.
   - Surface sizes: 800×300 centers on x 400, rows 142..157. 100×50, 10×10, 1×1 and 0×0 draw without raising. SRCALPHA surface corner becomes (0, 0, 0, 255).
   - Determinism: same input drawn twice, byte-identical: True.
   - Unicode and tab detail: draw without raising. A detail with `\x00` raises `ValueError`. The contract allows that (Presentation: "If it fails, it raises"). Review note 3 already routes it to the Architect.
   - 0 bugs.
4. **Assumptions:** "the main line's top" read as the top of its rendered text rect, the same reading as the implementation report and the review.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The view is ready to be wired into `game/app/guard.py`. The QA test task `docs/contracts/DRA-5/tasks/DRA-5-02-qa-engineer.md` is still open and runs separately. Review notes 1 and 3 (font passed in for DRA-6, strip `\x00` in the guard) stay with the Architect through the Director.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core SKIP (no tests yet) · ui SKIP (no tests yet)
QA: pass
