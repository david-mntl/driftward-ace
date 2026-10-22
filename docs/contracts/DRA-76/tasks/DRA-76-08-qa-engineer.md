Feature: DRA-76
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/waves.md
Status: done
Linear: DRA-84

## Read in the contract
- Interface, `game/core/wave_files.py`; `game/core/waves.py` (the shapes it builds).
- Rules: The wave files (all of it); Logging (the `core.wave_files` sentence).
- To read: `docs/contracts/schemas/wave.schema.json`, `docs/contracts/schemas/playlist.schema.json`.

## Builds
- `game/tests/core/test_wave_files.py` (new)
- `game/tests/core/wave_files/` (new: a small good set of test-only wave files and a playlist, JSON, to the two schemas)
- `game/tests/CONTEXT.md` (changed: the new folder and a paragraph for `core/test_wave_files.py`)

## Depends on
DRA-76-04

## Not in the contract
- The test-only wave files are the scope report's "test-only wave files" (scope report DRA-76, Limits, Tests). The test reads them with `json` and passes the decoded documents to `build_wave_book`; each refusal is that good set with one change made in the test. They are never read by the game.
- Like the other drifter tests, the file builds its own `DrifterTuning` from the GDD values at the top of the file and reads no `game/tuning/` or `game/waves/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The good set builds a book: ids from the keys, Wave 0, eight playlists, placements sorted by trigger with ties in file order, lengths and triggers as floats, extra rest 0 when left out, the pool ids per level. Rules: The wave files (Built).
- Every refusal the contract lists raises `ValueError`, one test row each, with a message that starts with the file named from the game folder down and names the field or the problem: a bad wave id; a wave or placement that isn't an object; an unknown field (including `speed` on a placement); each required field missing; each type or range broken (a `bool` for a number or an integer included); `min_level` missing on a pool wave and present on a fixed one; an unknown drifter type; what the load-time spawn refuses (an unknown variant, a missing coordinate, an `invert` or a specialty the drifter refuses), named by the placement; a playlist with other than 8 levels, or a bad level; `wave_zero` or a `fixed` entry naming no wave; a level with random slots and no allowed pool wave; no pool wave at Level 8. Rules: The wave files.
- The seam start: a hazard below 120 px is refused, one at exactly 120 px is accepted, and a coin below 120 px is accepted. Rules: The wave files (Seam start).
- What is not checked is accepted: a placement past the wave's length, a level with no slots, a pool wave in a `fixed` list. Rules: The wave files (Not checked at load).
- `build_wave_book` logs nothing. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_wave_files.py` in the `core` step.

## Out of scope
- Reading files from `game/waves/`, invalid JSON, a missing playlist file: `game/app/waves.py`, checked at integration.
- The wave clock (task DRA-76-07), the run (task DRA-76-09).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, `game/waves/`, or test files other than those listed.
