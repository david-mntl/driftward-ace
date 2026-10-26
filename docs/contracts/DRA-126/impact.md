# DRA-126 impact: saves, top 10, name entry, game-over messages, BEST

Contracts reopened from frozen: `systems/game-flow.md` (version 1), `systems/run.md` (version 12: `final_level`, `level_reached`), `systems/hud.md` (version 6: BEST, `group_digits`) and `systems/app.md` (version 17: frame loop, general, and the new parts `save-storage.md`, `rationale/save-storage.md` and `integration-checks/DRA-126.md`). New contract: `systems/saves.md`. New schema: `save-data.schema.json`.

What changes on purpose: the game-over screen's message follows the run's place, and a top-10 score opens the letter picker, which takes the keys before RETRY and MENU. Everything else is add-only. Every new `GameFlow` and `Run` field has a default, and every changed function keeps its old call valid with the old meaning: `start_flow(run)` is a flow whose saves don't work (GAME OVER, no picker, as in DRA-125); `draw_game_over(surface)`, `draw_final_score(surface, score)`, `draw_game_over_choices(surface, selection)` and `draw_leaderboard(surface)` draw the DRA-125 screens; `draw_hud(surface, run, below_overlay)` draws no BEST. So `game/app/frame.py` typechecks unchanged until integration.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/saves.py` (new) | `Saves`, `ScoreEntry`, `GameOverMessage`, `NamePicker`, the place and picker functions | DRA-126-01 |
| `game/core/run.py` | `final_level`, `level_reached`, set in the last life, cleared by `next_run` | DRA-126-01 |
| `game/core/game_flow.py` | the new fields, opening GAME_OVER, the picker's keys, `saves_changed`, `stop_saves`, `best`, `leaderboard`, the new log lines | DRA-126-02 |
| `game/ui/score_text.py`, `game/ui/hud.py` | `group_digits`, `best_text`, BEST on line 1 | DRA-126-03 |
| `game/ui/game_over.py` | the message by place, the picker layout, `draw_name_picker`, grey choices, the after-save look | DRA-126-04 |
| `game/ui/leaderboard.py` | the rows and their columns | DRA-126-05 |
| `game/ui/menu.py` | imports `core.game_flow` (`MenuItem`) | no change |
| `game/ui/debug_overlay.py` | reads `Run` | no change |
| `game/app/saves.py` (new), `game/app/frame.py` | load and write the saves, `start_flow(run, saves)`, the write after a save tick, `stop_saves`, the new draw calls, `best` to the HUD | Integration Engineer, at integration (`systems/app/save-storage.md`, `frame-loop.md`, `integration-checks/DRA-126.md`) |
| `game/tests/core/test_saves.py` (new) | the top 10, the place, the message, the picker | DRA-126-06 |
| `game/tests/core/test_game_flow.py` | the flow's log lines, the game-over screen's keys | DRA-126-07 |
| `game/tests/core/test_run_last_life.py` | the last-life tick and `next_run` | no change needed: the new field is added the same way as `final_score`, and `test_hold_arrows_...` compares every field generically. DRA-126-06 adds the level-reached tests to it |
| `game/tests/core/test_run.py`, `test_run_score.py`, `test_run_waves.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_coin.py`, and the drifter tests (`test_ufo.py`, `test_planet.py`, `test_fireball.py`, `test_electric_ball.py`, `test_floating_island.py`, `test_chain_lightning.py`, `test_graze_feedback.py`) | build and step runs | no change expected |
| `game/tests/ui/test_game_over.py`, `test_leaderboard.py`, `test_hud.py`, `test_score_text.py`, `test_menu.py` | the DRA-125 views and the HUD, called with the old signatures | no change needed: the defaults keep the old screens. DRA-126-08 adds the DRA-126 tests to `test_game_over.py`, `test_leaderboard.py`, `test_hud.py` and `test_score_text.py` |
| `game/tests/CONTEXT.md` | describes the test files | DRA-126-06, DRA-126-07, DRA-126-08 |
| `tools/wave_editor/bench.py` | builds and steps runs | no change expected |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| DRA-126-02 | `test_game_flow.py`, the logging test that expects exactly `["screen game_over"]` from the flow on the tick game over comes (around line 901): the flow now logs DEBUG `game over message=game_over place=none` right before it | DRA-126-07 |

Any other core test that fails after DRA-126-01 or DRA-126-02 is a bug against that task: no other existing behavior changes when the flow has no saves. Any `ui` test that fails after DRA-126-03, -04 or -05 is a bug against that task: called the DRA-125 way, every view draws what it drew.
