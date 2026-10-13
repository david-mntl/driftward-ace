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
