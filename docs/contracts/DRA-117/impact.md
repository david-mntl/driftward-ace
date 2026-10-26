# DRA-117 impact: graze

Contracts reopened from frozen: `systems/run.md` (version 10) and `systems/hud.md` (version 4). Contracts changed that were already draft: `systems/drifters.md` (shared base, base interface, spawner and tuning, rationale, and the graze line of each hazard's core part) and `systems/app.md` (tuning loader, frame loop, startup, release, and the new part `integration-checks/DRA-117.md`). Schemas: `hazards.schema.json` gains the optional `graze_margin`; `scoring.schema.json` is new.

The change is add-only for every existing caller: new fields and arguments all have defaults that give the GDD's values, `start_run()` and `start_run(waves)` build the run they built before, `graze_zone()` keeps its signature and, with the default margin, its zone, and `PointsPopup(...)` without `kind` is a coin's popup as before. What changes for the player is the score and the HUD's line 2.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/drifters/base.py` | `GrazeState`, `Drifter.graze_margin`, `Drifter.graze_state`, `Birth.graze_margin`, `graze_zone`, `born_drifter` | DRA-117-01 |
| `game/core/drifters/tuning.py` | `HazardRules.graze_margin` | DRA-117-01 |
| `game/core/drifters/spawner.py` | hands `graze_margin` to `Birth` | DRA-117-01 |
| `game/core/popup.py` | `PopupKind`, `PointsPopup.kind` | DRA-117-02 |
| `game/core/graze.py` (new) | the graze rules, ring, check and popup | DRA-117-02 |
| `game/core/run.py` | `Run` fields, `score`, `start_run`, steps 3a and 5b, retry, logging | DRA-117-02 |
| `game/ui/popup_view.py` | the graze popup's color | DRA-117-03 |
| `game/ui/graze_view.py` (new) | the graze ring | DRA-117-03 |
| `game/ui/score_text.py` | `graze_text`, shared grouping | DRA-117-04 |
| `game/ui/hud.py` | the GRAZE line | DRA-117-04 |
| `game/ui/game_over.py` | imports `score_text` | no change |
| `game/ui/debug_overlay.py` | reads `Run` and `graze_zone()` | no change |
| `game/core/drifters/*.py` (each drifter) | build on `born_drifter` and `replace` | no change |
| `game/app/tuning.py`, `game/app/frame.py` | load `graze_margin` and `scoring.json`; start the run with the graze values; draw the rings | Integration Engineer, at integration (`systems/app/tuning-loader.md`, `frame-loop.md`) |
| `game/tuning/scoring.json` (new) | the graze values | content: Tuning Engineer, from 06-scoring.md, Values, to `scoring.schema.json` |
| `game/tuning/debug_spawns.json` | gains one meteorite row | content (`systems/app/integration-checks/DRA-117.md`) |
| `game/tuning/hazards.json` | may set `graze_margin` | no change needed: left out means the default |
| `game/tests/ui/test_hud.py` | says line 2 is empty and compares whole HUD surfaces with the SCORE line alone | DRA-117-07 |
| `game/tests/core/test_*.py` that run hazards past the ship | compare drifters, popups or scores after `step_run` | no change expected (below) |
| `game/tests/CONTEXT.md` | describes the test files | DRA-117-05, DRA-117-06, DRA-117-07 |
| `tools/wave_check/` | builds drifters through the spawner and reads `graze_zone()` | no change expected (main session, if anything shows) |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| DRA-117-04 | `test_hud.py::test_hud_score_is_on_line_one_at_the_left_margin`: the whole HUD surface no longer equals the SCORE line alone, and ink now lies below line 1 | DRA-117-07 |
| DRA-117-04 | `test_hud.py::test_hud_line_two_is_empty_and_the_meters_are_gone`: line 2 now holds `GRAZE 0` | DRA-117-07 |
| DRA-117-04 | `test_hud.py::test_hud_score_top_is_the_overlay_bottom_plus_the_gap`: its last assertion compares the whole surface with the SCORE line alone | DRA-117-07 |
| DRA-117-04 | `test_hud.py::test_hud_score_pixels_follow_the_score` may fail: it measures the widest ink of the whole HUD, which now includes the GRAZE line | DRA-117-07 |
| DRA-117-02, at integration | the game shows the error screen at start until `game/tuning/scoring.json` exists, once the Integration Engineer's loader reads it | the tuning file |

No core test is expected to change result. The scan of `game/tests/core` found no test that compares a whole drifter, its popups or the score after a hazard's graze zone held a flying, unprotected ship that it never touched. If one turns up, it fails from DRA-117-02 (the drifter now carries `graze_state`, or the score now holds a graze): QA reports it against this table, and DRA-117-05 brings it in line with `systems/run.md`, step 5b.
