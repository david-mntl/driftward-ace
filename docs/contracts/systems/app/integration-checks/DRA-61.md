# App, integration checks, DRA-61
Part of: app
Read when: you run or extend the browser checks for the score and the game-over score (DRA-61).

## Rules

Integration checks for DRA-61, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the score equals the meters flown, 1 point a meter (`systems/run.md`, Rules, Score). The world scrolls 1.1 px a tick from tick 31, so the score reaches 1 on tick 40 (about 0.67 s), about 62 at 10 s, and 1 000 on tick 9121 (about 152 s). "Reference text" means the text rendered in the same page with the game's default font at the stated size, in white (255, 255, 255). `score_text` is the format in `systems/hud.md`, Presentation: `SCORE`, a space, the digits in groups of three split by one space.

Earlier checks, reworded for DRA-61. Wherever an earlier check reads "the readout", "the meters readout" or `<n> m`, it now reads the SCORE line at HUD line 1, with the same number:
- **DRA-6, Catch-up cap:** SCORE doesn't jump by the hidden time's distance.
- **DRA-13, Readout counts up**, now **SCORE counts up (`/`):** a screenshot right after play starts shows `SCORE 0` at the top left, its text top near y 4, matching reference text at 16 px. Screenshots about 5 s and 10 s later, with no key held, show larger whole numbers, the 10 s one about 62. Within a run the number never goes down.
- **DRA-13, Hovering still earns meters:** SCORE keeps counting at the same rate as with no key held.
- **DRA-13, No overlap in debug mode:** the white SCORE line sits below the overlay's fourth line, with a gap and no shared pixel row, and stays exactly where it was while F3 hides the overlay.
- **DRA-23, The wait** (and its DRA-29 rewording): SCORE keeps counting, about 33 more in the 5 s (about 26 in the 4 s).
- **DRA-23, Game over:** the Game Over box now holds three white lines, all centered: "Game Over", then `score_text(<n>)` with `<n>` from the `game over meters=<n>` line (for example `SCORE 23`), then "Press any arrow to retry". They match reference text at 32, 16 and 16 px.
- **DRA-23, Everything freezes:** the two canvas reads 2 s apart are identical, SCORE and the box's score line included.
- **DRA-23, A new run plays like the first** and **Normal mode:** SCORE reads `SCORE 0` where they read `0 m`.
- Every other check stands as written.

New checks:
- **No meters readout (`/`, no key held):** for 10 s after play starts, no white (255, 255, 255) pixel lies in x 0 to 299, rows 20 to 47 (HUD line 2), while SCORE counts on line 1 above it. In `?debug=1`, the same holds for the 28 rows starting one HUD line spacing (20 px) below the SCORE line's top, left of x 300. Source: scope report DRA-61, Limits; systems/hud.md, Presentation.
- **Digits in groups (`/`, hold ArrowUp from play start):** the ship sits on the top line and normal mode spawns nothing, so the run lasts. Between about 153 s and 160 s after play start, SCORE matches reference text of one of `SCORE 1 000` to `SCORE 1 052` at 16 px: a 1, one space, then three digits. Source: scope report DRA-61, Limits (format); systems/hud.md, Presentation.
- **The final score (`?debug=1`):** end a run as in the DRA-23 game over check. The box's score line and the HUD's SCORE line show the same text, `score_text(<n>)` with `<n>` from `game over meters=<n>`, and it doesn't change while the box shows. Release every arrow and tap one: INFO `new run`, the box is gone and SCORE reads `SCORE 0`. Source: 02-game-flow.md, rules 3, 5 and 6; systems/run.md, Rules, Score.
- **Package contents:** as for DRA-56, and `ui/score_text.py` must be in `game.apk`.
