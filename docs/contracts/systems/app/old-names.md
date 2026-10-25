# App, old names
Part of: app
Read when: a citation names a section of the old single file, such as "Rules, Frame loop".

## Old names
Code and docs cite sections of the old single file. This table says where each one lives now.

| Old name | Now in |
|---|---|
| Interface, `game/app/debug_spawns.py`; Rules, Debug test spawn list; Rules, File; Rules, Checks; Rules, Checks the schema can't express; Rules, Errors; Rules, Defaults; Rules, What plays; Rules, Rows in play; Rules, Chain lightning rows; Rules, Fireball rows; Rules, Coin rows; Rules, Floating island rows; Rules, Planet rows; Rules, UFO rows; Rules, Timing; Rules, Log | [debug-spawns](debug-spawns.md) |
| Interface, `game/app/guard.py`; Interface, `game/ui/look.py`; Interface, `game/ui/error_screen.py`; Presentation (all of it); Rules, Error guard | [error-handling](error-handling.md) |
| Interface, `game/app/loop.py`; Interface, `game/app/frame.py`; Rules, Frame loop; Rules, Game over; Rules, Held keys; Rules, Tick; Rules, Draw; Rules, Drifters behind the ship; Rules, Popups over the drifters; Rules, below_overlay; Rules, Arrow keys; Rules, F3; Rules, Log by event; Rules, Catch-up cap; Rules, Cap log | [frame-loop](frame-loop.md) |
| Purpose (all but its first sentence); Interface (opening paragraph); Interface, `game/app/drifters/registry.py`; Interface, `game/app/drifters/checks.py`; Interface, `game/app/drifters/<drifter>_tuning.py` | [general](general.md) |
| Rules, Integration checks for DRA-104 | [integration-checks/DRA-104](integration-checks/DRA-104.md) |
| Rules, Integration checks for DRA-13 | [integration-checks/DRA-13](integration-checks/DRA-13.md) |
| Rules, Integration checks for DRA-19 | [integration-checks/DRA-19](integration-checks/DRA-19.md) |
| Rules, Integration checks for DRA-23 | [integration-checks/DRA-23](integration-checks/DRA-23.md) |
| Rules, Integration checks for DRA-29 | [integration-checks/DRA-29](integration-checks/DRA-29.md) |
| Rules, Integration checks for DRA-39 | [integration-checks/DRA-39](integration-checks/DRA-39.md) |
| Rules, Integration checks for DRA-47 | [integration-checks/DRA-47](integration-checks/DRA-47.md) |
| Rules, Integration checks for DRA-5 | [integration-checks/DRA-5](integration-checks/DRA-5.md) |
| Rules, Integration checks for DRA-56 | [integration-checks/DRA-56](integration-checks/DRA-56.md) |
| Rules, Integration checks for DRA-6 | [integration-checks/DRA-6](integration-checks/DRA-6.md) |
| Rules, Integration checks for DRA-61 | [integration-checks/DRA-61](integration-checks/DRA-61.md) |
| Rules, Integration checks for DRA-62 | [integration-checks/DRA-62](integration-checks/DRA-62.md) |
| Rules, Integration checks for DRA-76 | [integration-checks/DRA-76](integration-checks/DRA-76.md) |
| Rules, Integration checks for DRA-86 | [integration-checks/DRA-86](integration-checks/DRA-86.md) |
| Rules, Integration checks for DRA-96 | [integration-checks/DRA-96](integration-checks/DRA-96.md) |
| Rules, How the browser checks | [integration-checks/method](integration-checks/method.md) |
| Rationale | [rationale/debug-spawns](rationale/debug-spawns.md) |
| Rationale | [rationale/error-handling](rationale/error-handling.md) |
| Rationale | [rationale/frame-loop](rationale/frame-loop.md) |
| Rationale | [rationale/integration-checks](rationale/integration-checks.md) |
| Rationale | [rationale/release](rationale/release.md) |
| Rationale | [rationale/startup](rationale/startup.md) |
| Rationale | [rationale/tuning-loader](rationale/tuning-loader.md) |
| Rationale | [rationale/wave-loading](rationale/wave-loading.md) |
| Interface, `pygbag.ini`; Interface, `game/scripts/start-driftward-ace.sh`; Rules, Launch script; Rules, Release package | [release](release.md) |
| Diagram (all of it); Interface, `game/main.py`; Interface, `game/app/mode.py`; Interface, `game/app/log.py`; Interface, `game/app/settings.py`; Rules, Startup; Rules, Import boundary; Rules, Run mode; Rules, Logging | [startup](startup.md) |
| Interface, `game/app/tuning.py`; Rules, Tuning loader; Rules, Hazards file; Rules, The chain lightning's file; Rules, What the loader builds for the chain lightning; Rules, The fireball's file; Rules, What the loader builds for the fireball; Rules, The coin's file; Rules, What the loader builds for the coin; Rules, The floating island's file; Rules, What the loader builds for the floating island; Rules, The planet's file; Rules, What the loader builds for the planet; Rules, The UFO's file; Rules, What the loader builds for the UFO; Rules, A drifter's own fields; Rules, Loaders are registered by type | [tuning-loader](tuning-loader.md) |
| Interface, `game/app/waves.py`; Rules, Wave files; Rules, Files; Rules, Errors; Rules, Log | [wave-loading](wave-loading.md) |

The old Impact sections are gone. `git log --follow docs/contracts/systems/app.md` shows them.
