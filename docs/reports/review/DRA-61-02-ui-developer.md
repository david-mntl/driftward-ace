Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-61-02 (the SCORE line in `game/ui/hud.py` and the new `game/ui/score_text.py`) against `docs/contracts/systems/hud.md` v2. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-61-02-ui-developer.md`.
3. **Checks:** By reading only. Compared `game/ui/score_text.py` and `game/ui/hud.py` with hud.md (Purpose, Diagram, Interface, Presentation, Rules, Impact and Rationale for DRA-61), run.md (`score` is an `int` property), scope report DRA-61 (Limits, Decision log), 10-ui.md (rules 1, 2, 5), 15-tech-constraints.md, `game/CONTEXT.md` and `game/ruff.toml`. Traced `score_text` by hand for 0, 999, 1000, 1234, 1000007 and 1234567: all match the contract. Nothing run.
4. **Assumptions:** The test counts and the screenshot in the implementation report are taken as reported. QA runs them.
5. **Documentation differences:** None.
6. **Next:** Open findings: 0 must-fix, 1 should-fix, 0 notes. The UI Developer answers DRA-61-02-F1 in Review fix mode.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-61-02-F1 | should-fix | game/ui/score_text.py:34 | fixed |

### DRA-61-02-F1
The gap between the label and the digits is a literal space in the f-string (`f"{SCORE_LABEL} {...}"`), not `GROUP_SEPARATOR`. The output is the same today. But the contract names the constant for this gap. Decision 1 also says the constants are "the single source of the format", and this literal is outside them.
Rule: `score_text` is "`SCORE_LABEL`, one `GROUP_SEPARATOR` space, then the score's decimal digits"; no magic values.
Source: hud.md, Presentation, `score_text(score)`, first bullet; implementer checklist items 6 and 8; implementation report, Decisions, bullet 1.
Change: build the text from `SCORE_LABEL`, then `GROUP_SEPARATOR`, then the joined groups, so the format has no literal left.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. Every number traces to the GDD or tuning: DRA-61-02-F1
7. pass
8. Smells: DRA-61-02-F1
9. Decisions match the code: DRA-61-02-F1
10. pass

## For QA
- Play to a score that changes several times, then retry: the HUD reads `SCORE 0` again (the one-entry cache in `_score_surface` must re-render).
- Scores with inner zero groups (`1 000 007`, `10 000`): every group keeps three digits.
- Debug mode with F3 on and off: SCORE sits at `overlay_text_bottom() + 4`, never overlaps the overlay, never jumps, and line 2 is empty.
- Normal mode: no `m` readout anywhere, and the hearts stay at (544/576/608, 8).
- Tests that call `pygame.quit()` and init again between cases: the cached SCORE surface and font (`lru_cache`/`@cache`) are reused across them.

## Re-check 2026-10-18
1. **Task:** Re-check the UI Developer's answer to DRA-61-02-F1 (`## Review fix 2026-10-18` in `docs/reports/implementation/ui/DRA-61-02-ui-developer.md`). Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-61-02-ui-developer.md` (line 1, findings table, this section).
3. **Checks:** By reading only. Read `game/ui/score_text.py:34` against hud.md, Presentation, `score_text(score)`. Traced the new return line by hand for 0 and 1234567: `SCORE 0` and `SCORE 1 234 567`, as before. Nothing run.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Open findings: 0 must-fix, 0 should-fix, 0 notes. QA Engineer takes the task.
7. **Status:** done.

- DRA-61-02-F1: fixed. `game/ui/score_text.py:34` now returns `SCORE_LABEL + GROUP_SEPARATOR + GROUP_SEPARATOR.join(groups)`, with no literal left in the format. The new fix Decision says the same.
