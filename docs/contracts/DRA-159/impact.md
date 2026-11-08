# DRA-159 impact: music mute and its icon

Contracts changed: `systems/mute-icon.md` (new, draft, never frozen), `systems/audio.md` (draft, new in DRA-158), and `systems/app.md` (version 19, draft since DRA-158; the part `app/frame-loop.md` and the part `app/integration-checks/DRA-159.md`). New schema: `mute_icon.schema.json`. No contract that is frozen now is changed by this feature; the draft ones were reopened by DRA-158.

The change is add-only for every existing caller. `frame._draw` gains two trailing arguments with defaults (`mute_icon_view=None`, `music_muted=False`), so a call that passes neither draws what it drew before. What changes for the player is the M key, the music mute and the icon.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/ui/mute_icon.py` (new) | `MuteIconLook`, `MuteIconView` | DRA-159-02 |
| `tools/art/mute_icon.py` (new), `game/assets/mute_icon.png` (new) | bake and hold the picture from `mute_icon.json` | DRA-159-01 |
| `game/tuning/mute_icon.json` (new) | margin, size and the two colors | content: main session, from `mute_icon.schema.json` and the architect's hand-back; before DRA-159-01 runs |
| `game/tuning/README.md` | describes every tuning file | content: main session |
| `game/app/mute_icon_tuning.py` (new) | loads and checks the file | Integration Engineer, at integration (`systems/mute-icon.md`) |
| `game/app/assets.py` | `load_mute_icon` | Integration Engineer, at integration |
| `game/app/audio.py` | `pause_music`, `resume_music`, `music_paused` | Integration Engineer, at integration (`systems/audio.md`) |
| `game/app/frame.py` | the M key, the loader calls, the two `_draw` arguments and the draw call before the dim | Integration Engineer, at integration (`systems/app/frame-loop.md`, `integration-checks/DRA-159.md`) |
| `game/tests/ui/test_window_view.py` | calls `frame._draw` with ten positional arguments; the sentinel check on every screen | no change expected: the new arguments default to no icon |
| `game/tests/CONTEXT.md` | describes the test files | DRA-159-03 |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| none | no existing test is expected to change result. `game/ui/mute_icon.py` adds a file nothing imports until integration | |

`DRA-159-03` reads `game/tuning/mute_icon.json` and `game/assets/mute_icon.png`: until the main session writes the file and DRA-159-01 ships the picture, its tests fail on a missing file. That is not a bug in the tests; QA waits for both before it runs. If `test_window_view.py` fails after integration, the Integration Engineer gave the new `_draw` arguments no default: that is a bug, report it against the contract (`systems/app/frame-loop.md`, Interface).
