Verdict: pass
Created by: integration-engineer

1. **Task:** integrate `background-sway` (12 baked far-painting frames, alpha-blended per frame, `sway_loop_ticks` tuning). Started by the Director's main session. No contract or task files exist for it.
2. **Delivered:** `docs/reports/integration/background-sway.md`. I changed no game code. The wiring was already in `game/app/assets.py` and `game/app/background_tuning.py`. A scratch control build lives in my scratchpad only, not in the repo.
3. **Checks:**
   - Headless import of `app.loop`, `app.assets` and `app.background_tuning` (run from `game/`, with the dummy SDL drivers) is clean. `import game.main` is not a usable check here. `main.py` runs the loop at import, so it never returns, and `main.py` imports `app.loop`, so `game/` must be on the path.
   - `pygbag --archive game` built `game/build/web.zip`, 3,988,641 bytes (about 3.9 MB). It is git-ignored.
   - The zip holds `index.html`, `favicon.png` and `game.apk`. The apk has 131 entries. All 12 `assets/background_sway_00..11.png` files are in it. No tests, scripts, `CONTEXT.md`, `requirements.txt` or `ruff.toml` is in it.
   - The browser checks are in **Browser run**. The extra full-screen blend is small: about 9% less idle main-thread time, and no frame-rate loss.
4. **Assumptions:**
   - Presented frames are counted by wrapping `putImageData` on `#canvas`. In pygbag 0.9.3 that is the SDL present call.
   - The "idle" figure comes from a `MessageChannel` ping-pong loop. It counts how many tasks the page runs per second while the game runs. A busier game gives a lower count.
5. **Documentation differences:** None.
6. **Next:** Director: run `scripts/close-out.sh background-sway` to see open review findings and the Observations below. To look at it yourself, run `game/scripts/start-driftward-ace.sh`, open http://localhost:6060, and check the build with `pygbag --archive game` (`game/build/web.zip`). Please also check the frame rate in your own browser (see Observations).
7. **Status:** done.

## Browser run
- Build check: `pygbag --archive game` from the repo root -> `game/build/web.zip` (3,988,641 bytes, not committed).
- Started with `game/scripts/start-driftward-ace.sh` in the background and loaded in Playwright at http://localhost:6060. Stopped with `kill` on the script's pid. Ports 6060 and 6061 are free and no pygbag process is left.
- **Required**
  - Build served and loads: pass.
  - Start line: `INFO app.loop: start mode=normal` (and `mode=debug` with `?debug=1`). `app.assets: background loaded 12 painting frames and 6 planets`. `background_tuning` shows `sway_loop_ticks=900`.
  - Console errors: only the two known pygbag ones. These are the `browserfs.min.js` 404 and "PyMain: BrowserFS not found". Warnings are all pygbag or browser noise (iframe sandbox, `ScriptProcessorNode`, `getImageData` readback). Same result in normal and debug runs, and after reaching play. Pass.
  - Arrow-key input in `?debug=1`. I sent ArrowUp as a keydown, a 400 ms hold, then a keyup. The DEBUG lines are `key down key=up x=320.00 y=240.00` and `key up key=up x=320.00 y=184.00`. y fell from 240 to 184, so the ship went up. Pass. (184 is the top-line stop, which the log also shows: `core.ship: top line stop x=320.00 y=184.00`.)
  - Playwright's `keyboard.press('Enter')` did not move the menu. A dispatched `KeyboardEvent` pair with a 150 ms hold did. This is a Playwright quirk, not a game bug. Enter then logged `key down key=enter ... core.game_flow: screen playing`.
- **Extra 2: the far painting really moves.** I read `getImageData` on the 640x480 canvas in a region of the menu at x 440-630, y 20-340. That region is away from the black hole (bottom left), the menu text, the planets and the bottom glow. Samples were taken every 4 s, 8 in all:

  | Measure | Result |
  |---|---|
  | Mean abs RGB difference, sample 0 vs samples 1-7 | 2.97, 3.26, 3.46, 3.14, 3.45, 3.45, 3.22 |
  | Mean abs difference, consecutive samples | 2.97, 3.23, 3.18, 3.16, 3.16, 3.14, 2.94 |
  | Mean brightness (0-255) | 8.005, 8.046, 8.069, 8.004, 8.017, 8.017, 7.983, 7.889 |

  The painting changes by about 3 levels per channel on average every 4 s. Brightness stays within 8.0 +/- 0.1, and the last sample's drift to 7.89 is small. Pass: it moves and does not pulse. Control build with one sway frame, same region, over 5 s: mean abs difference 0.16. That is only planets, swirls and river lights. So the sway adds roughly 3 and the rest of the background roughly 0.2. (Control mean 6.9 is not comparable: a planet or another layer may sit in the region, so brightness was only checked within the sway build.) Screenshots of the menu and play screens (read from the canvas, not compared) look right: a painted purple-black swirl, a black hole at the bottom left, planets, and the ship and HUD in play.
- **Extra 3: frame rate (AA-02 browser check).** Playwright Chromium on this dev container, canvas shown at 960x720 (640x480 backing). Measured over 10-12 s windows by `requestAnimationFrame` count. "Presented" is the count of `putImageData` calls on the game canvas.

  | Build | Screen | rAF fps | Presented fps | Idle probe, tasks per second |
  |---|---|---|---|---|
  | 12 sway frames (shipped) | menu | 58.7 (32 s window), then 59.2, 59.9, 60.0, 59.8 | equal to rAF | 65261, 62675, 64552, 59127 (mean 62,904) |
  | 12 sway frames (shipped) | play | 57.5, 58.1 | equal to rAF | not measured |
  | 12 sway frames (shipped) | menu, 3 x 10 s repeat | 60.0, 59.7, 60.1 | equal to rAF | see the menu row above |
  | Control: 1 sway frame, no second blit | menu | 60, 60, 60 | equal to rAF | 71028, 70148, 66960, 69479 (mean 69,404) |

  - The shipped build holds about 60 fps on the menu and 57.5-58 fps on the play screen. The control holds 60 on the menu. So the extra full-screen alpha blend does not drop the frame rate here. The only low reading was the first 3 s after load (36 presented fps), probably start-up. It never came back, and every later window was at least 57.5.
  - The idle probe shows the cost. The shipped build leaves about 9% less idle main-thread time than the control (62.9k vs 69.4k tasks per second). That is a cost, but small. It is inside the 6-7% run-to-run spread of each build, so I call it "small, not clearly measurable" rather than a number.
  - The play screen was measured only with the shipped build. The ship had died and respawned by then, and the screen is not directly comparable to the menu. I did not run a play-screen control.
  - The control is a copy of `game/` and `pygbag.ini` in the scratchpad, with `SWAY_FRAMES = 1`, sway frames 01-11 deleted and served on port 6061. The view skips the second blit with one frame, so it is a true without-blend comparison. No committed file was edited.

## Observations
- **Headless and Playwright fps are not the Director's real browser.** This is a software-rendered Chromium in a dev container with a 60 Hz rAF. Real GPU and 4K or 120 Hz+ displays, or weaker laptops, can behave differently. The 9% idle cost may matter more on a slow machine. Please check the fps in your own browser. For example, run `requestAnimationFrame` counting in the devtools console, or watch for stutter on the menu.
- Presented-frame count is a proxy for the game's own frame rate. I could not hook the Python loop without adding per-tick logging, which the rules forbid. If the game ever ran below rAF, the two counts would differ, as they did for the first 3 s only.
- The 12 sway PNGs are untracked files (`?? game/assets/background_sway_*.png`) at the time of the run, and the build uses them. They need to be committed with the feature, or the release build loses the sway. `game/build/` is ignored.
- The play-screen frame rate dipped to 57.5-58 in two windows. The menu had no such dip. I did not run a play-screen control, so I cannot say whether the blend, the drifters or the HUD cause it.
- The zip is 3.99 MB, mostly `game.apk`. The sway frames are about 270-280 KB each, so roughly 3.3 MB of the apk. Worth knowing if the itch.io size budget is tight.
- `browser_handle_dialog` is not available here. Navigating away from a running game raises a `beforeunload` dialog (the known "page reload blocked" to-do). I closed the tab with `browser_close` between pages to get around it.
- Control-build mean brightness (6.9) differs from the shipped build's (8.0). I did not chase this. The region samples a moving planet, swirl and river-light layers, and the two runs are at different times. A flat difference of about 1 level is not a regression.

## Decisions
- Measured with `requestAnimationFrame` counts plus a `putImageData` counter over 10-12 s windows, and an idle `MessageChannel` probe on top. The rAF count alone is capped at the display rate and could not show a cost under the 16.7 ms budget. Source: the task brief, check 3.
- The control build removes both the extra frames and the second blit (one frame skips it in `_draw_painting`), so the difference is the alpha blend itself. It was built and served from the scratchpad on port 6061, so no committed file changed. Source: the task brief, check 3 ("do not edit the committed files").
- Sent keys as dispatched `KeyboardEvent`s with a hold, because Playwright's instant `press` was not seen by the game. Source: CLAUDE.md Tech rules (browser testing), and the debug key log in `game/app/frame.py` carries the ship x/y.
- Headless import check uses the `app.*` modules, not `game.main`, since `main.py` starts the loop on import and imports `app.loop` by its relative name. This is the existing entry-point shape (CLAUDE.md, `game/main.py` stays thin), not something I changed.
