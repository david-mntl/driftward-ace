Feature: DRA-117
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/hud.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-117/impact.md
Status: done
Linear: DRA-124

## Read in the contract
- hud.md: Presentation: the row `run.grazes`; `graze_text(grazes)`; SCORE line; GRAZE line
- hud.md: Rules: the first two rules
- run.md: Presentation: the rows `popup.kind` and `run.graze_rings`; Graze popup; Graze ring

## Builds
- `game/tests/ui/test_hud.py` (changed: the tests `impact.md` lists, brought in line with line 2 holding GRAZE, and new GRAZE line tests)
- `game/tests/ui/test_score_text.py` (changed: `graze_text` tests)
- `game/tests/ui/test_graze_view.py` (new: the graze popup's color and the ring)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-117-03, DRA-117-04

## Not in the contract
None.

## Test
- `graze_text` puts the label, one space and the count's digits in groups of three, with no digit limit, grouped exactly like `score_text` for the same number. Rules: hud.md, graze_text.
- The GRAZE line is `graze_text(run.grazes)` at the left margin, one HUD line below SCORE, in SCORE's look, in normal and debug mode; it never overlaps the overlay's text or the hearts and ends above the top line. Rules: hud.md, GRAZE line; Rules (first two).
- SCORE stays exactly where and as it was on line 1, with the GRAZE line beside it on line 2; `GRAZE 0` shows for a fresh run. Rules: hud.md, SCORE line; GRAZE line.
- The GRAZE text changes with the count and is re-rendered only when the count changes. Rules: hud.md, GRAZE line.
- A popup of kind GRAZE is drawn in `GRAZE_POPUP_COLOR`, one of kind COIN in the coin color, the same text at the same size, centered on the popup's place. Rules: run.md, Graze popup.
- A ring is a circle outline centered on the ship's center, of radius half its diameter rounded and its line width, in `GRAZE_RING_COLOR` at its opacity; it follows the ship; nothing else is drawn and the ship is untouched. Rules: run.md, Graze ring.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the `test_hud.py` failures `impact.md` expects from DRA-117-04 gone, and `test_graze_view.py` in the `ui` step with all its tests passing.

## Out of scope
- Core graze rules (tasks DRA-117-05 and DRA-117-06). The app's draw order (the Integration Engineer's browser checks).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
