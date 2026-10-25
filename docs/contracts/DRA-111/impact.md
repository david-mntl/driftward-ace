# DRA-111 impact: the electric ball

Contracts reopened from frozen: `systems/drifters.md` (version 9), `systems/waves.md` (version 2), `systems/app.md` (version 15). The change is add-only: one new `DrifterType` member, `ELECTRIC_BALL`, added last, and the drifter's own modules. No existing signature, field or rule changes. What breaks does so because code and tests enumerate `DrifterType`.

## Files that depend on the changed contracts

| File | Why it depends | Changed by |
|---|---|---|
| `game/core/drifters/base.py` | holds `DrifterType` | DRA-111-01 |
| `game/core/drifters/__init__.py` | imports every drifter module | DRA-111-01 |
| `game/core/drifters/electric_ball.py` | new | DRA-111-01 |
| `game/ui/drifters/__init__.py` | imports every view module | DRA-111-02 |
| `game/ui/drifters/electric_ball_view.py` | new | DRA-111-02 |
| `game/app/tuning.py` | reads one file per `DrifterType`, through the type's registered loader | no change; works once the two rows below exist |
| `game/app/drifters/__init__.py`, `game/app/drifters/electric_ball_tuning.py` (new) | the electric ball's loader | Integration Engineer, at integration (`systems/app/tuning-loader.md`) |
| `game/tuning/drifters/electric_ball.json` (new) | the electric ball's tuning file | content: Tuning Engineer, from drifters/10-electric-ball.md, Values |
| `game/tuning/debug_spawns.json` | gains the five example rows | content (`systems/app/integration-checks/DRA-111.md`) |
| `game/app/debug_spawns.py`, `game/core/wave_files.py` | list the types from the enum in their messages | no change |
| `game/tests/ui/test_drifter_registry.py` | every type has one tuning file, one class and one view | no change |
| `game/tests/core/test_drifter_registration.py` | every type names itself in its own core module; the telegraph hook | DRA-111-05 (extends the telegraph test) |
| `game/tests/core/test_collision.py` | builds a case per variant of every type's tuning file | DRA-111-04 |
| `game/tests/core/test_wave_files.py` | the unknown-type message lists every type | DRA-111-05 |
| `game/tests/CONTEXT.md` | describes the test files | DRA-111-03, DRA-111-04 |
| `tools/wave_check/`, `tools/wave_editor/` | list the types from the enum; wave_check asks the drifter's hooks | main session, if anything shows (none expected) |

## Failures expected until each task lands

`game/tests/check.sh` steps `lint`, `typecheck`, `core` and `ui`. Every failure not in this table is a bug.

| From | Failure | Cleared by |
|---|---|---|
| DRA-111-01 | `test_drifter_registry.py::test_drifter_lists_match_everywhere`: no view and no tuning file for `electric_ball` | DRA-111-02 (view) and the tuning file |
| DRA-111-01 | `test_wave_files.py`: the two tests that spell out the type list (they end `planet, ufo)`) | DRA-111-05 |
| DRA-111-01 | `test_collision.py`: the ship-against-every-variant tests fail on the electric ball's missing-file case (`drifter_at` asserts a tuning) | the tuning file, then DRA-111-04 |
| the tuning file | `test_collision.py` fails to collect: `load_variant_cases` reads `electric_ball.json` as a plain file and finds no `hitbox` | DRA-111-04 |
| DRA-111-01 | the game shows the error screen at start (desktop and browser): `app.tuning` finds no `electric_ball.json`, then no loader for it | the tuning file and the Integration Engineer's loader |

No other test is expected to change result: the electric ball's `telegraph_ticks(None)` is None, so `test_only_a_drifter_with_a_telegraph_says_so` keeps passing until DRA-111-05 extends it.
