# DRA-148 impact: level-up moment

Contracts reopened from frozen: `systems/waves.md` (version 3) and `systems/run.md` (version 13). Contracts changed that were already draft: `systems/hud.md` (the level readout), `systems/app.md` (frame loop, tuning loader, and the new part `integration-checks/DRA-148.md`). New contract: `systems/level-up.md` (hub, `core`, `view`, `tuning`, `rationale`). New schema: `level-up.schema.json`.

The change is add-only for every existing caller. `WaveRun` and `Run` gain fields with defaults; `start_waves(book, seed)`, `next_run_waves`, `start_run(...)` and `next_run` keep their signatures and build what they built before (a `WaveRun` without rules is `NO_LEVEL_UP`: rest 0, no banner); `HudView(rules, art)` and `HudView.draw(window, run, best, tick)` draw the old HUD; `HudRun` is unchanged. What changes for the player is the rest after a level rise, the banner, the HUD pop and the picture bump.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/level_up.py` (new) | `LevelUpRules`, `NO_LEVEL_UP`, `LevelUpBanner`, `start_level_up`, `step_level_up`, `shown_level` | DRA-148-01 |
| `game/core/waves.py` | `WaveRun.level_up_rules`, `WaveRun.level_rose`, `start_waves`, `next_run_waves`, the rest in `_end_wave` | DRA-148-01 |
| `game/core/run.py` | `Run.level_up`, `hud_level`, `level_up_cue`, step 9b | DRA-148-02 |
| `game/core/game_flow.py` | steps the run and holds it | no change |
| `game/ui/level_up_rules.py`, `level_up_motion.py` (new) | the look records and the pure curves | DRA-148-03 |
| `game/ui/level_up_view.py` (new) | the banner, the bump offset, the flight | DRA-148-04, DRA-148-06 |
| `game/ui/hud.py` | `LevelSlot`, `level_slot`, the optional look and banner, the pop | DRA-148-05 |
| `game/ui/debug_overlay.py` | reads `run.level` and `wave rest` | no change |
| `game/app/frame.py`, `game/app/assets.py`, `game/app/level_up_tuning.py` (new) | load the file, start the waves with the rules, build the view, draw order, bump, flight | Integration Engineer, at integration (`systems/app/frame-loop.md`, `tuning-loader.md`, `integration-checks/DRA-148.md`) |
| `game/tuning/level_up.json` (new) | the values | content: main session, from `level-up.schema.json` and the architect's hand-back |
| `game/tests/core/test_waves.py`, `test_run_waves.py`, `test_run_last_life.py`, `test_run_graze.py`, `test_game_flow.py` | build waves and runs with `start_waves(book, seed)` and step them | no change expected |
| `game/tests/ui/test_hud.py` | `FakeRun` with only `level`, `HudView(rules, art)`, `view.draw(window, run, best, tick)` | no change needed: the defaults keep the old HUD. DRA-148-09 adds the pop tests |
| `game/tests/CONTEXT.md` | describes the test files | DRA-148-07, DRA-148-08, DRA-148-09 |
| `tools/wave_editor/bench.py` | builds and steps runs with waves | no change expected |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| none | no existing test is expected to change result: every new field and argument has a default that gives the old behavior | |

If a core test fails after DRA-148-01 or DRA-148-02, it compares a whole `WaveRun` or `Run` against one built field by field without the new fields, or it counts the rest of a level rise. QA reports it against this table; the test is brought in line by the QA task that follows (DRA-148-07 or DRA-148-08). Any `ui` test that fails after DRA-148-05 is a bug against that task: called the old way, the HUD draws what it drew. `game/app/frame.py` and the committed `game/tuning/` need no change until integration: the game runs without the rest and the banner until the Integration Engineer wires it. Once the loader reads `level_up.json`, the game shows the error screen at start until that file exists.
