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
