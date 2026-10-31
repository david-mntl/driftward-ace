# HUD-PANEL impact: the side panel HUD and the wider window

Contracts reopened from frozen: `systems/hud.md` (version 7, rewritten for the panel), `systems/world.md` (version 3, the play area is no longer the whole window), `systems/game-flow.md` (version 2, the screens' surface and the dim) and `systems/app.md` (version 18, `app/frame-loop.md` and `app/tuning-loader.md`: the window, the HUD art, `hud.json`). New schema: `schemas/hud.schema.json`.

This feature ran in one main session, without Linear tasks, at the Director's request. There are no task files. The Director is the approval gate and the main session reviewed and tested it. It is `HUD-PANEL`, not a `DRA-` key, for that reason.

What changes on purpose: the window grows from 640 × 480 to 856 × 518; the play area stays 640 × 480 at (16, 10); the text HUD becomes a panel; the menu, instructions and leaderboard fill the window; the pause box and game over center on the window and dim it. `core` doesn't change.

## Files that depend on the changed contracts

| File | Why it depends | Change |
|---|---|---|
| `game/ui/hud.py` | replaced by `HudView` | rewritten |
| `game/ui/hud_rules.py` (new) | `HudRules` records | new |
| `game/ui/window_view.py` (new) | `WindowBackdrop`, the full-window background | new |
| `game/app/hud_tuning.py` (new) | loads and checks `hud.json` | new |
| `game/app/assets.py` | `load_hud_art` | add only |
| `game/app/frame.py` | window, play-area subsurface, draw order, dim | changed |
| `game/tuning/hud.json` (new), `game/assets/hud_*.png`, `game/assets/fonts/` | the values and the pictures | new |
| `game/ui/score_text.py` | `score_text`, `group_digits` still used by game over and the leaderboard | no change |
| `game/ui/debug_overlay.py` | draws on the play-area subsurface; `overlay_text_bottom` no longer used by the HUD | no change |
| `game/ui/menu.py`, `instructions.py`, `leaderboard.py`, `pause_box.py`, `game_over.py` | lay out from the surface's size, so they center on the window | no change |
| `game/ui/starfield.py`, `ship_view.py`, `burst_view.py`, `graze_view.py`, `popup_view.py`, `ui/drifters/*` | use play-area coordinates; drawn on the subsurface | no change |
| `game/core/*` | `SCREEN_W`, `SCREEN_H` stay the play area | no change |
| `game/tests/ui/test_hud.py` | the old text HUD's tests | rewritten |
| `game/tests/ui/test_hud_tuning.py` (new), `test_window_view.py` (new) | the loader and the backdrop | new |
| `tools/art/hud_panel.py` (new) | bakes the pictures from `hud.json` | new |
| `game/assets/CREDITS.md` | the two fonts and their SIL Open Font License | add only |
| `app/error-handling.md` | the error screen opens `set_mode((SCREEN_W, SCREEN_H))` only when no window exists yet | no change |

## Failures expected until each part lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Between the contract commit and the code commit, `test_hud.py` fails because the old HUD constants are gone. After the code commit nothing is expected to fail. Every failure not in this table is a bug.
