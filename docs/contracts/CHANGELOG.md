# Contracts changelog

## DRA-5, 2026-10-09
- `DRA-5/DRA-5-app.md`: 0 to 1, frozen.
- New contract for the game base: entry point with the PEP 723 block, one-handler logging (browser console or stdout), run mode switch, 60 Hz async frame loop, error guard with the import boundary, error screen view, and the `pygbag.ini` release package.

## DRA-6, 2026-10-09
- `DRA-5/DRA-5-app.md`: 1 to 2, frozen.
- `DRA-6/DRA-6-world.md`: 0 to 1, frozen.
- `DRA-6/DRA-6-ship.md`: 0 to 1, frozen.
- `DRA-6/DRA-6-debug-overlay.md`: 0 to 1, frozen.
- The ship moves: core screen geometry and ship physics (gravity, arrow thrust, wall and top-line stops, respawn). Ship view and debug overlay in UI. The app now steps the ship each tick, logs keys with x/y, toggles the overlay with F3, and caps catch-up at 5 ticks per frame.

## DRA-13, 2026-10-12
- `DRA-5/DRA-5-app.md`: 2 to 3, frozen.
- `DRA-6/DRA-6-ship.md`: 1 to 2, frozen.
- `DRA-6/DRA-6-world.md`: 1 to 2, frozen.
- `DRA-6/DRA-6-debug-overlay.md`: 1 to 2, frozen.
- `DRA-13/DRA-13-scroll.md`: 0 to 1, frozen.
- `DRA-13/DRA-13-hud.md`: 0 to 1, frozen.
- The world scrolls: core scroll and distance in meters, starfield view, HUD meters readout below the debug overlay. The app starts the scroll at spawn and steps it each tick. The top line is now a permanent ceiling. The overlay reports where its text ends.
- Director verdict on the integration observations, given in the main session and relayed by the coordinator: "Manual desktop browser check: I agree it works as expected. I accept the features work." All five observations were accepted as they stand. The screenshot and hidden-tab check wording in `DRA-5-app.md` is unchanged.

## DRA-19, 2026-10-12
- `DRA-5/DRA-5-app.md`: 3 to 4, frozen.
- `DRA-6/DRA-6-ship.md`: 2 to 3, frozen.
- `DRA-6/DRA-6-world.md`: 2 to 3, frozen.
- `DRA-6/DRA-6-debug-overlay.md`: 2 to 3, frozen.
- `DRA-13/DRA-13-scroll.md`: 1 to 2, frozen.
- Review follow-ups, no new gameplay: the guard removes null characters from the debug detail line, the overlay shows `0.00` instead of `-0.00`, ship fields are documented with unit and sign, core constants are `Final` and core dataclasses use `slots`, and the ship logging rule says "after the clamps, before any respawn".
- Director verdict on the integration observations, given in the main session and relayed by the coordinator: "yes do that and dont run it through the pipeline. Just edit it." All seven observations were accepted as they stand.
- Check-method rewording, edited by the main session on the Director's instruction, outside the pipeline: `DRA-5-app.md` gains "How the browser checks below are done" (a screenshot is a canvas pixel comparison, hiding the tab is a main-thread freeze, real click-screen and hidden-tab behavior is a manual Director check when the frame loop or start-up changes and before a release), and the DRA-5 and DRA-6 click-to-start and catch-up cap checks were reworded to match.

## Contracts moved to systems/, 2026-10-12
- Contracts now live in `docs/contracts/systems/`, one file per part of the code. Task files stay in `docs/contracts/<feature-id>/tasks/`. Content and versions are unchanged. Only the paths in links changed.
- `DRA-5/DRA-5-app.md` → `systems/app.md` (v4)
- `DRA-6/DRA-6-ship.md` → `systems/ship.md` (v3)
- `DRA-6/DRA-6-world.md` → `systems/world.md` (v3)
- `DRA-6/DRA-6-debug-overlay.md` → `systems/debug-overlay.md` (v3)
- `DRA-13/DRA-13-scroll.md` → `systems/scroll.md` (v2)
- `DRA-13/DRA-13-hud.md` → `systems/hud.md` (v1)
- Closed task files, reports and the entries above still use the old paths. Read them with this mapping. `git log --follow` shows each contract's full history.
- Director decision, made in the main session, outside the pipeline.

## DRA-23, 2026-10-13
- `systems/app.md`: 4 to 5, frozen.
- `systems/ship.md`: 3 to 4, frozen.
- `systems/scroll.md`: 2 to 3, frozen.
- `systems/hud.md`: 1 to 2, frozen.
- `systems/run.md`: 0 to 1, frozen (new).
- Lives, falls and game over: the new core run holds 3 lives, invulnerability with a blink, the respawn wait until a fresh arrow press, the game-over freeze and the arrow-key retry. The ship step no longer respawns. The HUD shows lives as white hearts at the top right, and the Game Over box is drawn over the frozen frame. The app makes one `step_run` call per tick.
- `systems/ship.md`, Rationale: the stale "raised with the Director" line now cites 04-ship.md rule 3 and decision-log row 32. Approved by the Director at close-out.
- Director verdict, relayed by the coordinator: the click-screen hand check was done in a desktop browser and works. All five integration observations were accepted.
- 5 review findings (all notes) were accepted as they stand: `docs/reports/review/DRA-23-01-gameplay-implementer.md`, `docs/reports/review/DRA-23-02-ui-developer.md`, `docs/reports/review/DRA-23-03-ui-developer.md`. The `ship.md` finding was fixed in this close-out.

## DRA-29, 2026-10-15
- `systems/objects.md`: 0 to 1, frozen (new).
- `systems/run.md`: 1 to 2, frozen.
- `systems/ship.md`: 4 to 5, frozen.
- `systems/debug-overlay.md`: 3 to 4, frozen.
- `systems/app.md`: 5 to 6, frozen.
- New schemas: `schemas/object-tuning.schema.json`, `schemas/playtest-switches.schema.json`.
- The first object, the meteorite. A shared object base with phases and an entry warning. Circle and box hitboxes with a strict overlap test. The ship's hitbox is an inverted T, and the ship is drawn as that T. The level table and the spawner are the only way to create an object. In the run, a hit costs one life with no stun, and objects that have gone are dropped. Object views and the entry warning are in UI. The debug overlay draws hitbox and graze outlines with labels. The app loads the tuning files at start. In debug mode only, it adds a test spawn list. Normal mode spawns nothing yet.
- Director verdict, relayed by the coordinator: the click-screen hand check was done in a desktop browser and works as before. The "Normal mode spawns nothing" check in `systems/app.md` stays as written. All six integration observations were accepted.
- `systems/objects.md`, Interface: the `tick_warning` and `register_object` comments now show the PEP 695 type parameter form the code uses, in place of `TypeVar` (review DRA-29-02, note 3). Approved by the Director at close-out.
- Numbers-only hotfix before close-out. The Director ordered it, and the main session applied it outside the pipeline. Meteorite speed is halved: `speed_ratio` 0.75 to 0.375, about 2.4675 px/tick at Level 1. The entry warning is 0.5 s longer: 30 to 60 ticks.
  - Changed: `game/tuning/objects/meteorite.json`; GDD `objects/01-meteorite.md` and `91-decision-log.md` row 40; the timeline, speed lines and rationale in `systems/objects.md`; the DRA-29 browser-check timings in `systems/app.md`.
  - The recomputed timings: hits at about 3.2, 6.2 and 9.2 s on the top line; 3.53 s at the respawn point; a 1 s warning; id 1 gone at about 4.4 s.
  - The labels of the two test constants in `game/tests/core/test_objects.py` and `test_run_objects.py` now say "fixed test value, not the live tuning file". The numbers are unchanged.
  - `game/tests/check.sh` ends `QA: pass`.
  - The browser build was not re-run for the hotfix, at the Director's request. The integration report's browser timings are from before it.

## Rename: objects are drifters, 2026-10-15
- The Director renamed "object" to **drifter** everywhere: anything that appears in the ship's path, good or bad. Two kinds: hazards (touching costs a life) and pickups (touching pays). GDD: `07-drifters.md`, `14-glossary.md`, `91-decision-log.md` row 41.
- Applied by the main session outside the pipeline, at the Director's request. Names and wording only; no rule, value or behavior changed, so no contract version changed.
- Renamed files: `systems/objects.md` to `systems/drifters.md`; `schemas/object-tuning.schema.json` to `schemas/drifter-tuning.schema.json`; `game/core/objects/`, `game/ui/objects/` and `game/tuning/objects/` to `drifters/`; the three test files to `test_drifters.py`, `test_run_drifters.py`, `test_drifter_registry.py`; GDD `07-objects.md` to `07-drifters.md` and `objects/` to `drifters/`.
- Renamed names: `GameObject` to `Drifter`, `ObjectType` to `DrifterType`, `ObjectTuning` to `DrifterTuning`, `ObjectTypeTuning` to `DrifterTypeTuning`, `ObjectView` to `DrifterView`, `object_type` to `drifter_type`, `spawn_object`, `register_object`, `available_objects`, `object_class`, `add_objects`, `render_object` to their `drifter` forms, `run.objects` to `run.drifters`, local `obj` to `drifter`. Log lines `object spawn|active|touch|gone` are now `drifter ...`; the tuning line reads `tuning loaded drifters=...`.
- Python's `object` type and JSON "object" (schemas, loader messages) are unchanged.
- Earlier changelog entries, task files and reports keep the old word as history. Their links to `07-objects.md` and `objects/` now point to renamed files.
- `game/tests/check.sh` ends `QA: pass`. A headless run loads the tuning and a meteorite drifter spawns, warns, turns active and falls. The browser build was not re-run.

## DRA-39, 2026-10-18
- `systems/app.md`: 6 to 7, frozen.
- `systems/drifters.md`: 1 to 2, frozen.
- `systems/run.md`: 2 to 3, frozen.
- Adds the satellite drifter, a re-hit cooldown for hazards, and an editable debug spawn list.

## Hotfix: one fixed entry warning size, 2026-10-18
- The Director ordered it, and the main session applied it outside the pipeline. No contract version changed.
- Every entry warning is now 24 px across, the same for every drifter, in place of "as wide as the drifter, copy at half size". The glow is 18 px across. The copy is scaled so its longest side is 14 px, so it sits inside the glow. The satellite warning was too big, and its parts looked too far apart. GDD: `07-drifters.md` (`entry_warning_look`, `entry_warning_size`), `drifters/06-fireball.md` (size), `drifters/03-chain-lightning.md` (`entry_warning_size`), `91-decision-log.md` row 63.
- `warning_center()` now keeps the whole 24 px warning on screen (12 px from each edge), so it no longer depends on the drifter's size. The satellite's warning sits at x 12 (628 with `invert`), the small meteorite's at y 12. The chain lightning's own `warning_center()` clamps by the same 12 px, so its warning sits at y 12 (it was 70). The chain lightning still shows the `trio_triangle` icon, now scaled so its 140 px width is 14 px (the discs are 1 px in radius); `warning_copy()` no longer sizes the warning.
- Changed: `game/core/drifters/base.py` (`ENTRY_WARNING_SIZE`, `warning_center`); `game/core/drifters/chain_lightning.py` (`warning_center`); `game/ui/drifters/entry_warning.py` (`ENTRY_WARNING_COPY_SIZE` replaces `ENTRY_WARNING_SCALE` and `WARNING_SIZE_RATIO`); `systems/drifters.md` (Presentation, Entry warning, Rules, Rationale); the DRA-29, DRA-39 and DRA-47 warning checks in `systems/app.md`.
- Tests: `test_drifters.py`, `test_satellite.py` and `test_chain_lightning.py` expect the new warning centers. New `game/tests/ui/test_entry_warning.py`: every warning image has one size, nothing is drawn past the radius, and the copy sits inside the glow.
- `game/tests/check.sh` ends `QA: pass`. The browser build was not re-run.

## DRA-47, 2026-10-18
- `systems/app.md`: 7 to 8, frozen.
- `systems/drifters.md`: 2 to 3, frozen.
- `systems/run.md`: 3 to 4, frozen.
- Adds the chain lightning drifter, the line hitbox shape and its charge rays, and one fixed entry warning size for every drifter.

## DRA-56, 2026-10-18
- `systems/app.md`: 8 to 9, frozen.
- `systems/drifters.md`: 3 to 4, frozen.
- Fireballs: a new drifter with a head and a trailing tail that flies across the screen, hits on head or tail, and leaves only when both are off. The app loads fireball tuning and the debug spawn list has fireball rows.

## DRA-61, 2026-10-18
- `systems/app.md`: 9 to 10, frozen.
- `systems/hud.md`: 2 to 3, frozen.
- `systems/run.md`: 4 to 5, frozen.
- `systems/scroll.md`: 3 to 4, frozen.
- Run score, score text on the HUD, and the game-over screen with score.

## DRA-62, 2026-10-18
- `systems/app.md`: 10 to 11, frozen.
- `systems/drifters.md`: 4 to 5, frozen.
- `systems/run.md`: 5 to 6, frozen.
- `systems/scroll.md`: 4 to 5, frozen.
- The coin drifter: a pickup that moves only with the scroll, pays points when the ship touches it and shows a points popup. Adds the coin tuning file and schema, the popup in core and UI, the coin view, and coin rows in the debug spawn list.

## DRA-76, 2026-10-19
- `systems/app.md`: 11 to 12, frozen.
- `systems/debug-overlay.md`: 4 to 5, frozen.
- `systems/drifters.md`: 5 to 6, frozen.
- `systems/hud.md`: 3 to 4, frozen.
- `systems/run.md`: 6 to 7, frozen.
- `systems/scroll.md`: 5 to 6, frozen.
- `systems/waves.md`: 0 to 1, frozen.
- Waves and playlists: hand-authored wave files and an 8-level playlist, a wave clock that plays Wave 0 and then each level's fixed and random waves and raises the level when a playlist ends, and checked loading at startup with named errors.

## DRA-86, 2026-10-22
- `systems/app.md`: 12 to 13, frozen.
- `systems/drifters.md`: 6 to 7, frozen.
- `systems/run.md`: 7 to 8, frozen.
- `systems/ship.md`: 5 to 6, frozen.
- Floating islands: solid drifters the ship can stand on and ride, in five shapes, with their own tuning file and debug-spawn rows.

## DRA-96, 2026-10-22
- `systems/app.md`: 13 to 14, frozen.
- `systems/drifters.md`: 7 to 8, frozen.
- `systems/run.md`: 8 to 9, frozen.
- `systems/ship.md`: 6 to 7, frozen.
- Planet drifter: a gravity well that pulls the ship toward its center inside a drawn field; touching the body costs a life.

## DRA-104, 2026-10-23
- `systems/app.md`: 14 to 15, frozen.
- `systems/drifters.md`: 8 to 9, frozen.
- `systems/run.md`: 9 to 10, frozen.
- `systems/waves.md`: 1 to 2, frozen.
- The UFO drifter crosses the screen in a weave, with a warning before it enters, a seeded spawn row and its own tuning file, and wave_check counts it as a hazard.

## Contract split: drifters, 2026-10-25
- `systems/drifters.md`: restructured into a hub and parts, no content change. The Impact section and the Purpose task list are removed (history is in git).

## Drifter registration refactor, 2026-10-25
- `systems/app.md`, `systems/drifters.md`: no version change. The tuning loader registers by drifter type in `app/drifters/`, `wave_check` asks the drifter instead of its type, a test guards both, and the base gains the `telegraph_ticks` hook.

## Contract split: app, 2026-10-25
- `systems/app.md`: restructured into a hub and parts, no content change. The Impact section and the Purpose task list are removed (history is in git).

## Contract split: run Impact, 2026-10-25
- `systems/run.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: ship Impact, 2026-10-25
- `systems/ship.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: scroll Impact, 2026-10-25
- `systems/scroll.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: hud Impact, 2026-10-25
- `systems/hud.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: debug-overlay Impact, 2026-10-25
- `systems/debug-overlay.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: world Impact, 2026-10-25
- `systems/world.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## Contract split: waves Impact, 2026-10-25
- `systems/waves.md`: Impact section and the Purpose task list removed (history is in git), no other change.

## DRA-117, 2026-10-25
- `systems/app.md`: 15 to 16, frozen.
- `systems/drifters.md`: 9 to 10, frozen.
- `systems/hud.md`: 4 to 5, frozen.
- `systems/run.md`: 10 to 11, frozen.
- Graze: a near miss scores points, draws a ring on the ship and shows a popup. The HUD counts grazes. New scoring file and graze margin in the hazards file.

## DRA-111, 2026-10-26
- `systems/app.md`: 15 to 16, frozen.
- `systems/drifters.md`: 9 to 10, frozen.
- `systems/waves.md`: 2 to 3, frozen.
- Electric ball: a purple drifter that charges, then fires a lightning circle as it falls. Its tuning loads from its own file.

## DRA-125, 2026-10-26
- `systems/app.md`: 16 to 17, frozen.
- `systems/game-flow.md`: 0 to 1, frozen.
- `systems/hud.md`: 5 to 6, frozen.
- `systems/run.md`: 11 to 12, frozen.
- Screens: menu, instructions, pause, the 2-second last life and one game-over screen with MENU and RETRY. New game-flow contract and last-life file.

## DRA-126, 2026-10-27
- `systems/app.md`: 17 to 18, frozen.
- `systems/game-flow.md`: 1 to 2, frozen.
- `systems/hud.md`: 6 to 7, frozen.
- `systems/run.md`: 12 to 13, frozen.
- `systems/saves.md`: 0 to 1, frozen.
- Saves: top 10 scores in browser storage, a three-letter name picker at game over, place messages, BEST on the HUD and a filled leaderboard. New saves contract.

## DRA-147, 2026-10-31
- `systems/screens.md`: 0 to 1, draft (not frozen: the feature ran in one session without task files, so close-out has not run).
- `systems/game-flow.md`: look and Interface notes marked superseded by `systems/screens.md`. Flow rules unchanged. Draft, version 2.
- `systems/app/frame-loop.md` (in `systems/app.md`): the Draw rule's screen calls take the `look` argument. Draft, version 18.
- `systems/run.md`: one pointer to `systems/screens.md`. Frozen, version 13.
- Screens look: Glass Cockpit in Mono Violet with soft glow for the menu, pause box, game-over screens, instructions page and leaderboard. New screens tuning file and schema (`tuning/screens.json`, `schemas/screens.schema.json`). Closes UI-03 and UI-04.


## Entry warning sign, 2026-11-02
- Every entry warning is one plain warning sign: an orange (#ff9e5e) point-up triangle with a see-through fill and an exclamation mark, 24 px across, the same for every drifter. The drifter copy, the glow and the spikes are gone. Director's call in the main session, no pipeline. GDD: `07-drifters.md` (`entry_warning_look`, `entry_warning_color`, `entry_warning_size`; `entry_warning_glow` and `entry_warning_spikes` removed), `drifters/02-satellite.md` and `drifters/06-fireball.md` (rule 1, no tilted copy), `drifters/03-chain-lightning.md` (`entry_warning_icon` no longer shown), `91-decision-log.md` row 130.
- Changed: `game/ui/drifters/entry_warning.py` (one cached sign image; `draw_entry_warning(surface, obj)` loses its `view` argument; `drop_entry_warning` removed); `game/ui/drifters/registry.py` (calls); `systems/drifters/shared/views.md` (Diagram, Interface, Presentation, Entry warning).
- Tests: `game/tests/ui/test_entry_warning.py` rewritten for the sign: its size, nothing past the radius, its color, the mark, and the same image at the warning center.
- Not changed, now unused by the UI: core `warning_copy()` and `warning_tilt_degrees()` on every drifter, the chain lightning's `entry_warning_icon` tuning field, and the contract text that describes them (`shared/base.md`, `shared/base-interface.md`, the drifter `core.md`, `view.md` and `rationale.md` files, integration checks DRA-47 and DRA-56). Removing them is a structural change for the Architect.

## Invulnerability 1 s, 2026-11-06
- Numbers-only hotfix. The Director ordered it, and the main session applied it outside the pipeline. `invuln_ticks` 30 to 60 (0.5 s to 1 s). GDD: `05-lives-and-damage.md` Values and Summary, `90-open-questions.md` LD-08, `91-decision-log.md` row 134.
- Changed: `INVULN_TICKS` in `game/core/run.py`; `systems/run.md` constant line and the blink table (now T to T+60). No interface change, so the version stays 13.
- Tests: the `INVULN_TICKS` copies in 13 core test files are 60. Four scenarios were timed around 30 ticks and now follow `INVULN_TICKS`: the blink pattern and the log test (`test_run.py`), the slow rock's speed 0.5 to 0.25 so it still overlaps the ship past the longer window (`test_run_drifters.py`), the last-life rock's cooldown (`test_run_last_life.py`) and the UFO's end-of-invulnerability tick (`test_ufo.py`).
- Not changed: past task files and integration checks keep their 30-tick timings as history. The browser build was not re-run.

## Five lives, 2026-11-06
- The Director's call in the main session, no pipeline. `lives_start` 3 to 5, a locked decision. GDD: `05-lives-and-damage.md` Values and Summary, `01-vision.md` locked decision 5, `02-game-flow.md` rule 5, `10-ui.md` `hud_lives` and the layout sketch, `91-decision-log.md` row 135.
- HUD: two more heart sockets on the wireframe, top (103, 150) on the nose over the cockpit window and bottom (103, 211) above the main exhaust. Fill order center, right, left, top, bottom. `tuning/hud.json` `hearts.slots` holds 5; `schemas/hud.schema.json` slots 3 to 5 items; `hud_ship.png` re-baked with `tools/art/hud_panel.py` (the other HUD pictures came out byte-identical). The view needed no code change: slot `i` is lit while `i < lives`.
- Changed: `LIVES_START` in `game/core/run.py`; `systems/run.md` constant line; `systems/hud.md` sketch, Interface comment, Presentation rows and States (draft, version stays 7); docstrings in `game/ui/hud_rules.py` and `tools/art/hud_panel.py`.
- Tests: the `LIVES_START` copies in the core tests are 5, with new copies in `test_game_flow.py`, `test_graze_feedback.py` and `ui/test_hud.py`. Log lines that named the life count after the first loss now use `LIVES_START - 1`. The log test in `test_run.py` starts its falls at 3 lives. The HUD heart tests cover 5, 4, 3 and 2 lives and all 5 slots.
- Not changed: past task files, reports and integration checks keep their 3-life numbers as history. The browser build was not re-run.

## DRA-148, 2026-11-06
- `systems/app.md`: 18 to 19, frozen.
- `systems/hud.md`: 7 to 8, frozen.
- `systems/level-up.md`: 0 to 1, frozen.
- `systems/run.md`: 13 to 14, frozen.
- `systems/waves.md`: 3 to 4, frozen.
- Level-up moment: a 2.5 s rest after each level rise, a banner that drops the new level in and flies it into the HUD, and a HUD level pop. All values in tuning/level_up.json; glass fill off for frame rate.

## DRA-158, 2026-11-08
- `systems/app.md`: 19 to 20, frozen.
- `systems/audio.md`: 0 to 1, frozen.
- `systems/run.md`: 14 to 15, frozen.
- The game plays a looping song and five effects (hit, graze, coin, game over, level up) on the run's sound cues.

## DRA-159, 2026-11-08
- `systems/mute-icon.md`: 0 to 1, frozen.
- M mutes and unmutes the music on every screen after the start page, and a small speaker icon shows while it is muted.

## Credits page, 2026-11-08
- The Director's call in the main session, no pipeline. The menu gets a fourth item, CREDITS, and a credits page that shows the CC BY 4.0 credits for the music loop and the level-up sound, plus courtesy lines (the CC0 game-over sound, the two fonts). Changes locked decision 8 and `menu_items`. Closes AA-05. GDD: `01-vision.md` locked decision 8, `02-game-flow.md` (`menu_items`, rule 14, diagram, edge cases), `10-ui.md` (`credits_page`, `credits_look`, `menu_screen`, `menu_look`, `window_screens`, `ui_font`), `12-art-and-audio.md` rule 12, `90-open-questions.md`, `91-decision-log.md` rows 151 and 152.
- `systems/game-flow.md`: `Screen.CREDITS`, `MenuItem.CREDITS`; the credits page steps like the other pages (a confirm press goes to MENU). Draft, version stays 2.
- `systems/screens.md`: new view `ui/credits.py` (`draw_credits`, `card_rects`, `CREDIT_CARDS`), new record `CreditsRules`, its Presentation. Draft, version stays 1.
- `systems/app/frame-loop.md` and `systems/app/general.md` (in `systems/app.md`): the Draw rule calls `draw_credits` on CREDITS. Version unchanged.
- `schemas/screens.schema.json`: new required section `credits`. `tuning/screens.json` gains it.
- `game/assets/CREDITS.md`: new Audio section with the shipped sounds' sources and licenses.
