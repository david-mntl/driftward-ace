# DRA-158 impact: game audio, first iteration

Contracts reopened from frozen: `systems/run.md` (version 14) and `systems/app.md` (version 19; the part `app/frame-loop.md`, and the new part `app/integration-checks/DRA-158.md`). New contract: `systems/audio.md`. New schema: `audio.schema.json`.

The change is add-only for every existing caller. `Run` gains one field, `sound_cues`, with a default of `()`; `start_run(...)`, `next_run`, `step_run`, `hold_arrows`, `add_drifters` and `core.game_flow` keep their signatures and build what they built before. A run that is compared field by field still equals itself while no cue is produced. What changes for the player is that sounds play.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/sound_cue.py` (new) | `SoundCue` | DRA-158-01 |
| `game/core/run.py` | `Run.sound_cues`, the cue steps in `_step_playing`, `_step_last_life`, the game-over path | DRA-158-01 |
| `game/core/game_flow.py` | steps the run and holds it; `run_stepped` is what the app reads | no change |
| `game/app/audio_tuning.py`, `game/app/audio.py` (new) | the levels file, the mixer, the loop and the effects | Integration Engineer, at integration (`systems/audio.md`) |
| `game/app/frame.py` | loads the audio, starts the music, plays the cues after each tick | Integration Engineer, at integration (`systems/app/frame-loop.md`, `integration-checks/DRA-158.md`) |
| `game/tuning/audio.json` (new) | the values | content: main session, from `audio.schema.json` and the architect's hand-back |
| `game/tuning/README.md` | describes every tuning file | content: main session |
| `game/assets/audio/` (new) | the four .ogg files | the Director approves the staged files; the Art & Audio Engineer moves them |
| `game/tests/core/test_run.py`, `test_run_score.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_last_life.py`, `test_run_waves.py`, `test_run_level_up.py`, `test_game_flow.py`, `test_coin.py`, `test_graze_feedback.py`, and every drifter test that steps a run | build and step runs with `start_run`, `replace` and `step_run` | no change expected |
| `game/tests/CONTEXT.md` | describes the test files | DRA-158-02 |
| `tools/wave_editor/bench.py` | builds and steps runs | no change expected |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| none | no existing test is expected to change result: the new field defaults to `()` and a tick with no cue returns the same run as before | |

If a core test fails after DRA-158-01, it compares a run built field by field against a stepped run that had a coin, a graze or a life lost on the tick, without `sound_cues`. QA reports it against this table; the test is brought in line by the QA task that follows (DRA-158-02). `game/app/frame.py` and the committed `game/tuning/` need no change until integration: the game runs silent until the Integration Engineer wires the audio. Once the loader reads `audio.json`, the game shows the error screen at start until that file and the four sound files exist.
