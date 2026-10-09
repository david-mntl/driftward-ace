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
| `game/tests/check.sh` | everything: env, lint, format, core, ui |
| `game/tests/check.sh lint` | `ruff check` and `ruff format --check` on `game/` |
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
- Test files go only inside `game/tests/`. Never edit game code to make a test pass.
- Never edit `check.sh`, `pytest.ini` or the fixtures in `conftest.py` to get a pass. Change them only when the Director asks. Never use `skip`, `xfail` or `# noqa` to hide a failure. If the harness itself is wrong, report it to the Director.
- When a test task adds a fixture, folder or convention, update this file in the same run.

## When something fails
A failing test or a wrong inline run is a finding, not something for you to fix. Write it up in `docs/reports/qa/` with the failing test name or the inline command that reproduces it, the expected and actual values, and the source of the expected value (contract or GDD section). Then hand it to the agent that owns the broken file.
