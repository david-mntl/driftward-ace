Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-61 (Score), started by the Director in Integrate mode.
2. **Delivered:** `game/app/frame.py` (imports `draw_final_score`, calls `draw_final_score(surface, run.score)` right after `draw_game_over(surface)`, docstrings name the score), `docs/reports/integration/DRA-61.md`. No change to `game/main.py`, the other `game/app/` modules, `game/scripts/` or `pygbag.ini`, as the contract's DRA-61 Impact table says.
3. **Checks:**
   - All seven DRA-61 QA reports read `Verdict: pass`.
   - Headless import (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, from `game/`): `import app.loop, app.frame, app.tuning, app.debug_spawns, ui.game_over, ui.score_text` is clean. `timeout 4 python main.py` headless: `start mode=normal`, `tuning loaded ...`, then `quit`, no error.
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS. `QA: pass`.
   - `pygbag --archive game` from the repo root built `game/build/web.zip` (not committed, `game/build` is git-ignored). `game.apk` holds 47 entries, none from `tests/`, `scripts/`, `__pycache__`, `CONTEXT.md`, `requirements.txt` or `ruff.toml`. `ui/score_text.py`, `ui/game_over.py` and `app/frame.py` are in it.
   - Browser: all four required checks passed, plus every DRA-61 check from `systems/app.md` that I ran (see Browser run). Text read from canvas pixels against reference text drawn in the same page, all exact.
4. **Assumptions:** none about the game. Test method choices are in Decisions.
5. **Documentation differences:** None.
6. **Next:** Director: run `scripts/close-out.sh DRA-61` to see open review findings and the Observations below before close-out. To open the build yourself: `game/scripts/start-driftward-ace.sh`, then http://localhost:6060 (add `?debug=1` for debug mode). Build check: `pygbag --archive game` from the repo root gives `game/build/web.zip`.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (repo root) -> `game/build/web.zip`, 99 531 bytes. Not committed.
- **Served** with `game/scripts/start-driftward-ace.sh` in the background (log and pid in the scratchpad), answered on http://localhost:6060 after 1 s. Opened with the Playwright browser tools, `#canvas` clicked once. **Stopped** with `kill <script pid>`: the script logged `Stopping server` and `Server stopped`, curl got no answer and port 6060 is free.
- **How reads were done.** Keys went in as `KeyboardEvent`s on `#canvas` through `browser_evaluate`. Canvas pixels were read with `getImageData`. Reference text was drawn in the same page with `pygame.font.Font(None, size)` in white, through pygbag's `window.python.PyRun_SimpleString`. The SCORE references were written as `"SCORE " + format(n, ",").replace(",", " ")`, not with the game's `score_text`. "Exact" means every fully white reference pixel is white on the canvas (0 missing) and no other white pixel in the text box widened by 24 px to the right and 2 px around (0 extra). Game log lines came from the devtools console.

### Required checks
- **Build served and loads:** yes, three pages (`?debug=1`, then `/` twice).
- **Game started:** `INFO app.loop: start mode=debug` (debug page), `INFO app.loop: start mode=normal` (normal pages), each followed by `INFO app.tuning: tuning loaded drifters=meteorite,satellite,chain_lightning,fireball ...`. The debug page also had `INFO app.debug_spawns: debug spawns loaded mode=fireball rows=6 loop_ticks=180`.
- **No console errors:** only the known pygbag lines: the `browserfs.min.js` 404, `PyMain: BrowserFS not found`, and `MEDIA USER ACTION REQUIRED` before the click. No traceback, no game ERROR or WARNING line.
- **Arrow-key input (`?debug=1`):** ArrowUp held 300 ms, released: `DEBUG app.frame: key down key=up x=320.00 y=240.00`, then `key up key=up x=320.00 y=195.54`. y fell by 44.46 px, so the ship moved up. An earlier 80 ms tap gave y 240.00 -> 237.40.

### Extra checks (DRA-61, `systems/app.md` Integration checks)
- **The final score (`?debug=1`):** the debug spawn list ended the run: `INFO core.run: game over meters=33`. The box held three white lines, all centered on x 320: "Game Over" at top-left (260, 216), 32 px, 0 missing (1 extra white pixel, under the see-through box); `SCORE 33` at (293, 240), 16 px, exact; "Press any arrow to retry" at (257, 252), 16 px, exact. The HUD read `SCORE 33` at (4, 56), exact. Two full-canvas reads 2 s apart: 0 bytes differ, so the box score and SCORE didn't change while the box showed. ArrowUp tap: `INFO core.run: new run`; the title no longer matched (464 to 500 of 500 ink pixels missing), and SCORE read `SCORE 0` at (4, 56), exact, from 90 ms to about 590 ms, then `SCORE 1` at 692 ms and up to `SCORE 6` at 1.49 s. A second run ended with `game over meters=33` again.
- **SCORE counts up (`/`, no key held):** 1 445 frames over 24 s, every frame an exact match at top-left (4, 4). `SCORE 0` for the first 39 frames, `SCORE 1` at 640 ms (expected tick 40, about 0.67 s), `SCORE 29` at 5.0 s, `SCORE 62` at 10.0 s (expected about 62), `SCORE 95` at 15.0 s, `SCORE 128` at 20.0 s. The number never went down (0 decreases).
- **No meters readout (`/`):** 601 frames over the 10 s after play start, 0 white pixels in x 0 to 299, rows 20 to 47. In `?debug=1`: SCORE top at y 56, 233 frames over 4 s, 0 white pixels in x 0 to 299, rows 76 to 103.
- **No overlap in debug mode:** overlay's lowest green row 50, SCORE's first white row 57, no shared row. F3 hid the overlay (`overlay visible=False`, 0 green pixels top left): SCORE still exact at (4, 56). F3 again (`overlay visible=True`): still exact at (4, 56).
- **Digits in groups (`/`, ArrowUp held from page load):** play start `start mode=normal` at page time 4.1 s. 249 frames read from 145.9 s to 170 s after play start, all exact, 0 decreases. `SCORE 1 000` first at 152.3 s (expected tick 9121, about 152 s). In the 153 s to 160 s window, 70 of 70 frames read `SCORE 1 005` to `SCORE 1 050`. `SCORE 1000` with no space never matched. This also shows hovering on the top line earns at the no-key rate.
- **Package contents:** `ui/score_text.py` is in `game.apk`.

## Observations
- **SCORE sits over the top-left corner warning.** The debug fireball list puts a warning at the top-left corner, under SCORE, the same as the hearts at the top right. This was a Director override of scope Objection 2 and is in `docs/TODO.md`. Not a bug in this feature.
- **Earlier checks from DRA-5 to DRA-56 were not re-run one by one.** `systems/app.md` says they must still pass, reworded for SCORE. The only app change is one draw call after `draw_game_over`. The DRA-61 rewordings for readout counting, hovering, debug overlap, game over, freeze, new run and normal mode were covered above. Not run: DRA-6 catch-up cap with a hidden tab, DRA-23 "the wait" timing, the bad-tuning error-screen checks and the desktop import-error checks.
- **The game runs before the click here.** In this headless Chromium, `start mode=...` logs about 4 s after page load, before the canvas click, and the run starts then. So for the long hold, ArrowUp was sent from page load, before play started.
- **The long hold used repeated keydowns.** ArrowUp keydown went to `#canvas` every 100 ms with no keyup, the way OS key repeat works. Normal mode logs key lines at DEBUG only, so the hold is shown by the score timing and the run lasting, not by key lines.
- **The title's 1 extra white pixel.** The Game Over box is see-through. One white pixel under the box (a drifter or the ship behind it) fell in the title's text box. The title's ink matched with 0 missing.
- I closed and reopened the browser tab between pages, because a reload raised a `beforeunload` dialog my tools can't answer.

## Decisions
- **One added call, no new argument.** `draw_final_score(surface, run.score)` goes right after `draw_game_over(surface)` inside `if run.game_over:`, before `draw_hud`. Source: `systems/app.md`, Interface (DRA-61 calls), Rules (Draw), Impact (DRA-61 table), Rationale ("a call of its own").
- **The HUD call stays as it was:** `draw_hud(surface, run, below_overlay=debug)`. The HUD reads `run.score` itself. Source: `systems/app.md`, Interface (DRA-61 calls).
- **No change to `pygbag.ini`, the scripts or the loop.** The fixed 60 Hz accumulator, `await asyncio.sleep(0)` each frame and event-only logging stay as before. Source: `systems/app.md`, Impact (DRA-61 table); `CLAUDE.md` and `15-tech-constraints.md`.
- **SCORE references written independently of `score_text`,** so the format check doesn't test the game's code against itself. Source: `systems/app.md`, Integration checks for DRA-61 ("reference text").
- **The play-start frame** for the counting check is the first frame that read `SCORE 0`, captured from page load so nothing was missed.
