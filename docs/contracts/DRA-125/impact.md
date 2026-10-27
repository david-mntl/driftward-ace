# DRA-125 impact: screens, pause, last life, game over

Contracts reopened from frozen: `systems/run.md` (version 11), `systems/hud.md` (version 5, wording only: where the HUD shows) and `systems/app.md` (version 16: frame loop, tuning loader, general, release, and the new part `integration-checks/DRA-125.md`). New contract: `systems/game-flow.md`. New schema: `last-life.schema.json`.

What breaks on purpose: the run no longer ends on the tick lives reach 0. That tick starts the last life; game over comes `last_life_delay` ticks later, and the world moves in between. The arrow retry and `Run.retry_armed` are gone; a new run comes from `next_run`, called by the game flow. The `game over meters=%d` log line becomes `last life score=%d` on the death tick and `game over score=%d` at the end of the delay. The game-over box grows, says GAME OVER, and loses its prompt. Every other caller is add-only: `start_run()`, `start_run(waves)` and `start_run(waves, graze_rules)` build the run they built before, and `draw_game_over(surface)` and `draw_final_score(surface, score)` keep their signatures, so `game/app/frame.py` typechecks unchanged until integration.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/last_life.py` (new) | `LastLifeRules`, `Burst`, `start_burst`, `step_burst` | DRA-125-01 |
| `game/core/run.py` | `Run` fields and properties, steps 6.3 and 7.5, the last-life and game-over ticks, `next_run`, `hold_arrows`, logging | DRA-125-01 |
| `game/core/game_flow.py` (new) | the flow, its screens and keys | DRA-125-02 |
| `game/ui/burst_view.py` (new) | the burst | DRA-125-03 |
| `game/ui/screen_look.py`, `game/ui/menu.py` (new) | the shared stand-in look, the menu | DRA-125-04 |
| `game/ui/instructions.py` (new) | the instructions page | DRA-125-05 |
| `game/ui/leaderboard.py` (new) | the empty leaderboard page | DRA-125-06 |
| `game/ui/pause_box.py` (new) | the PAUSE box | DRA-125-07 |
| `game/ui/game_over.py` | box size, title, no prompt, RETRY and MENU | DRA-125-08 |
| `game/ui/hud.py` | reads `run.score` and `run.lives` | no change: the score freezes in core |
| `game/ui/debug_overlay.py` | reads `Run` | no change |
| `game/app/frame.py`, `game/app/tuning.py` | hold a `GameFlow`, read Enter, Space and the focus, load `last_life.json`, draw by screen | Integration Engineer, at integration (`systems/app/frame-loop.md`, `tuning-loader.md`, `integration-checks/DRA-125.md`) |
| `game/tuning/last_life.json` (new) | the last-life delay and the burst | content: Tuning Engineer, from 02-game-flow.md, last_life_delay, and scope report DRA-125, Values needed (Burst), to `last-life.schema.json` |
| `game/tests/core/test_run.py`, `test_run_score.py`, `test_run_waves.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_coin.py` | end a run and read `game_over`, the frozen world, `retry_armed`, the arrow retry or `game over meters=` | DRA-125-09 |
| `game/tests/ui/test_game_over.py` | reads the 120-px box, the title and the prompt | DRA-125-11 |
| `game/tests/CONTEXT.md` | describes the test files | DRA-125-09 to DRA-125-12 |
| `game/tests/core/test_*.py` for drifters (`test_ufo.py`, `test_planet.py`, `test_fireball.py`, `test_electric_ball.py`, `test_floating_island.py`) | assert `not run.game_over` in runs that never lose the last life | no change expected |
| `tools/wave_editor/bench.py` | fly mode relied on the arrow retry inside `step_run`; ghost mode pins `lives` and `game_over` | main session, if anything shows: after DRA-125-01 a fly-mode run that loses its last life plays the last life and stays at game over |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| DRA-125-01 | `typecheck`: test files that name `retry_armed` (`replace(..., retry_armed=...)` or `.retry_armed`): `test_run_graze.py`, `test_run_waves.py`, `test_coin.py`, `test_run_score.py` | DRA-125-09 |
| DRA-125-01 | `test_run.py`: `test_losing_the_last_life_ends_the_run`, `test_game_over_freezes_everything`, `test_retry_has_no_delay_when_released_at_game_over`, and the logging test that counts `game over` and `new run` lines | DRA-125-09 |
| DRA-125-01 | `test_run_score.py`: `test_score_stops_at_game_over_until_the_retry`, `test_a_retry_gives_score_0_again`, the `game over meters=` log test; the scripted-run tests if they read the state on the death tick as game over | DRA-125-09 |
| DRA-125-01 | `test_run_waves.py`: `test_game_over_freezes_the_waves_and_the_world`, `test_a_retry_starts_wave_0_at_level_1_with_a_new_seed`, `test_a_retry_logs_new_run_then_the_waves_start_and_a_tick_logs_the_waves_last`, `test_a_run_with_no_waves_is_at_level_1_with_nothing_due_and_a_retry_has_no_waves`, and the tests that read `game_over` right after `die` or the `game over meters=` line | DRA-125-09 |
| DRA-125-01 | `test_run_drifters.py`: `test_a_cooldown_counts_on_every_playing_tick_and_freezes_at_game_over`, `test_a_hit_on_the_last_life_ends_the_run`, `test_a_retry_starts_with_no_drifters`, and any test that reads `game_over` on the tick the last life is lost | DRA-125-09 |
| DRA-125-01 | `test_run_graze.py`: `test_game_over_freezes_the_grazes_and_the_rings_and_a_retry_clears_them` and the log test that expects `game over meters=0` | DRA-125-09 |
| DRA-125-01 | `test_coin.py`: `test_a_coin_paid_on_the_last_lifes_tick_is_in_the_frozen_final_score_and_a_retry_clears_it`, `test_a_popup_rises_for_its_lifetime_is_frozen_at_game_over_and_gone_after_a_retry`, and any test that reads `game over` lines | DRA-125-09 |
| DRA-125-08 | `ui/test_game_over.py`: `test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`: the box is taller, the title text changed and the prompt is gone | DRA-125-11 |
| DRA-125-01, at integration | the game shows the error screen at start until `game/tuning/last_life.json` exists, once the Integration Engineer's loader reads it | the tuning file |

The general rule for DRA-125-01: any existing core test that loses the last life and then expects `game_over` on that tick, a frozen world, a retry by arrow, `retry_armed`, or the `game over meters=` line fails for that reason only, and DRA-125-09 brings it in line with `systems/run.md` (The last life, A last-life tick, A game-over tick, `next_run`). A test that never loses the last life is not expected to change. If one does, QA reports it as a bug against DRA-125-01.
