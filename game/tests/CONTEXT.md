# game/tests: context for agents

Read this before you write or run a test.

## Purpose
This folder is the QA gate. Code reaches the Integration Engineer only after the Implementation Reviewer has read it and this folder passes. Tests prove the game behaves the way the contracts in `docs/contracts/` and the GDD in `docs/design/gdd/` say it should.

## Layout
| Path | What goes there |
|---|---|
| `core/` | tests for `game/core/`. A test for `game/core/ship.py` goes in `core/test_ship.py`. |
| `ui/` | tests for `game/ui/`. Same naming. |
| `conftest.py` | shared fixtures |
| `pytest.ini` | pytest config |
| `check.sh` | the only way to run checks |

Test files are `test_<module>.py`. Test functions are `test_<behavior>`, for example `test_ship_falls_with_no_input`.

## How to run
Run from any directory:

| Command | Does |
|---|---|
| `game/tests/check.sh` | everything: env, lint, format, typecheck, core, ui |
| `game/tests/check.sh lint` | `ruff check` and `ruff format --check` on `game/` |
| `game/tests/check.sh typecheck` | `mypy --strict` on `game/` |
| `game/tests/check.sh core [pytest args]` | core tests only, e.g. `core -k ship -v` |
| `game/tests/check.sh ui [pytest args]` | ui tests only |

Read the last line:
- `QA: pass`: every step passed or was skipped.
- `QA: fail (lint, core)`: those steps failed. The output above it says why.

Exit codes: 0 pass, 1 a check failed, 2 usage or environment error. `SKIP (no tests yet)` means that folder has no tests. It's not a failure.

Never run `check.sh fix`. It edits code you don't own.

## Fixtures
- `rng`: a `random.Random` with a fixed seed. Pass it to any code that takes randomness.
- `pygame_headless`: initialises pygame once per session. Use it in UI tests that need fonts or surfaces.
- `caplog` (built into pytest): for event-log tests. Set DEBUG on the module's logger only (`caplog.set_level(logging.DEBUG, logger="core.ship")`) and count lines by message prefix. Example: `core/test_ship.py`.

Every test runs headless (SDL dummy drivers). Import game code the way the game does: `from core.ship import Ship`.

## Markers
Only these exist. Any other marker is an error.
- `@pytest.mark.smoke`: steps a system for many ticks and checks the result.
- `@pytest.mark.determinism`: runs the same seed and inputs twice and asserts the state matches.

## What gets a test
Tests are written only when an Architect test task (`Assignee: qa-engineer`) asks for them. One test per functionality its **Do** lists, not one per function. No pile of unit tests. Until a task asks, the folder can stay empty and `check.sh` still passes.

Everything else QA checks with inline headless runs (`SDL_VIDEODRIVER=dummy python -c "..."`) that are never saved here.

## Rules
- Test behavior through the contract's Interface. Don't test private helpers or internals.
- Every expected number comes from the GDD or `game/tuning/`. Never invent one.
- Tests are deterministic. Time is ticks, never the wall clock. Randomness comes only from `rng`.
- Tests follow `game/ruff.toml`, including type hints (`-> None` on every test).
- UI tests read positions from the drawn pixels (`pygame.image.tobytes`), never from a hard-coded font size. Example: `ui/test_error_screen.py`.
- Test files go only inside `game/tests/`. Never edit game code to make a test pass.
- Never edit `check.sh`, `pytest.ini` or the fixtures in `conftest.py` to get a pass. Change them only when the Director asks. Never use `skip`, `xfail` or `# noqa` to hide a failure. If the harness itself is wrong, report it to the Director.
- When a test task adds a fixture, folder or convention, update this file in the same run.
- `core/test_collision.py` keeps one table of exact-number cases per unordered pair of shape kinds (`TABLES`). A guard test fails when `core.collision.Shape` gains a kind with no table: add the table and its cases first. Its ship-against-every-variant test reads `game/tuning/drifters/*.json` (one file per `DrifterType`) and builds the tuning records itself, so a new drifter or variant is covered by its file alone. It never imports `app`.
- `core/test_drifters.py` (base, spawner, meteorite, registry) and `core/test_satellite.py` (satellite, and the warning tilt) build their own `DrifterTuning` from the GDD values at the top of each file (`make_tuning`, `hazards=` optional, left out means the default `HazardRules`). They never read `game/tuning/` and import no expected number from the code. Each stands alone; the shared `place`, `advance` and `active` helpers are repeated, not imported.
- `core/test_run_drifters.py` (drifters inside `core.run`: entering, hits, the re-hit cooldown, drops, logs) builds its own `DrifterTuning` for the meteorite and the satellite from the GDD values at the top of the file (`make_tuning`, `hazards=` optional). It reads no `game/tuning/` file and imports no expected number from the code under test. `rock()` builds a meteorite directly; a satellite goes in through `add_drifters`. A test that must see the cooldown alone clears `invuln_ticks_left` before each tick (`replace(run, invuln_ticks_left=0)`), so protection can't hide a missed hit.

## When something fails
A failing test or a wrong inline run is a finding, not something for you to fix. Write it up in `docs/reports/qa/` with the failing test name or the inline command that reproduces it, the expected and actual values, and the source of the expected value (contract or GDD section). Then hand it to the agent that owns the broken file.
