# Side panel HUD: away log

The Director went to sleep on 2026-10-31 and said: handle everything; the HTML and the mock are the source of truth; if in doubt, look at them; the GDD adapts. Every decision taken without the Director, newest at the bottom.

Sources: `local/hud-mock/` (mock_hud.py, `out-ship2/*.png`, STEPS.md) and the earlier session's `hud-hull-workbench.html` (kept in that session's scratchpad: `/tmp/claude-1000/-workspace/f11d690e-8b24-453f-8e02-6b32a371b34a/scratchpad/`).

## Director's answers in chat
1. Frame: option A. Glass exactly 640 × 480, a rectangle. Everything else at the mock's pixel sizes. Window 896 × 518.
2. Motion: option C. Radar sweep, scan line, last-life heartbeat, and everything else the HTML moves.
3. Colors: keep every color as in the HTML and the plan. A HUD-only color exception is allowed.

## Decisions taken by the main session
| # | Decision | Why |
|---|---|---|
| A1 | Branch `feat/side-panel-hud` created, because `main` was checked out. | Rule: never commit on main. |
| A2 | Motion also includes the HTML's other panel motions: last-life lamp pulse, heart break, graze count bump, graze ring pop (7 in all). | "Stick to the HTML". STEPS.md listed only three. |
| A3 | Level bars: 8, not the mock's 9. Same step, right edge kept. | 08-difficulty.md has 8 levels; STEPS.md says the bars equal that number. |
| A4 | Score bar kept. Score tiles 7, clamped at 9 999 999. | In the mock and the HTML. |
| A5 | BEST shows commas (112,430), set by `score.best_separator`. Other screens keep spaces. | The mock picture shows commas. |
| A6 | Panel content centered in the 38 px taller window (`panel.content_y` 19). Every distance in the panel is the mock's. | Keeps the mock's pixel layout. |
| A7 | The frame's inner edge is a plain rectangle round the glass. The corner cuts of the mock's octagon would hide the field's corners. The outer bevel keeps small cut corners. Corner lights sit in the ring's corners. | Director allowed a rectangle. Margins are the mock's: 16 left and right, 10 above, 28 below. |
| A8 | Window size lives in `tuning/hud.json` (`window`), not in an app constants file. | "Everything configurable" and one home for the tool and the game. The loader checks every picture against it. |
| A9 | Labels use Share Tech Mono 10 px (ship it, credit it). | The mock and HTML use it. The Director's prompt named only Exo 2 Bold. |
| A10 | Menu, instructions and leaderboard get a full-window background: the background drawn at play-area size and scaled to cover the window. Dim for pause and game over: black alpha 110 (guess). | The window is wider than the 640 × 480 painting. |
| A11 | Edits to the GDD files the Director named, plus `14-glossary.md` (Camera row) and `90-open-questions.md` (UI-01 and WC-07 removed; UI-04 and LD-08 narrowed). | Needed to close UI-01 and WC-07 consistently. |
| A12 | Feature id `HUD-PANEL` for the contract Features lines and `docs/contracts/HUD-PANEL/impact.md`. No Linear issue. | The crew was skipped, so no DRA key exists. |
