Feature: DRA-76
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/waves.md
Status: done
Linear: DRA-80

## Read in the contract
- Purpose.
- Interface, `game/core/wave_files.py`. Interface, `game/core/waves.py` (to read: the shapes it builds).
- Rules: The wave files (all of it); Logging (the `core.wave_files` sentence); Other rules.
- Rationale: "The loader's checks live in core", "One file per wave", "The spawn spot is in screen px", "The seam is checked only at the start", "Every placement is spawned once at load", "`min_level` is refused on a fixed wave", "Candidates sorted by id".
- To read only: `docs/contracts/schemas/wave.schema.json`, `docs/contracts/schemas/playlist.schema.json`.

## Builds
- `game/core/wave_files.py` (new)

## Depends on
DRA-76-03

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from app.tuning import load_tuning
from core.wave_files import build_wave_book
tuning = load_tuning()
rock = {'at_px': 150, 'type': 'meteorite', 'x': 320}
coin = {'at_px': 0, 'type': 'coin', 'x': 300}
waves = {'w0': {'length_px': 400, 'kind': 'fixed', 'placements': [rock, coin]}, 'p': {'length_px': 400, 'kind': 'pool', 'min_level': 1, 'extra_rest_ticks': 30, 'placements': [rock]}}
playlist = {'wave_zero': 'w0', 'levels': [{'fixed': [], 'random_count': 1}] * 8}
book = build_wave_book(waves, playlist, tuning)
print(sorted(book.waves), book.wave_zero_id, [p.at_px for p in book.waves['w0'].placements], book.waves['w0'].extra_rest_ticks, book.waves['p'].extra_rest_ticks, book.pool_ids(8))
def refused(wave_documents, playlist_document):
    try:
        build_wave_book(wave_documents, playlist_document, tuning)
    except ValueError as error:
        return str(error)
    return 'accepted'
print(refused({**waves, 'w0': {'length_px': 400, 'kind': 'fixed', 'placements': [{**rock, 'at_px': 100}]}}, playlist))
print(refused({**waves, 'w0': {'length_px': 400, 'kind': 'fixed', 'placements': [{**coin, 'at_px': 100}]}}, playlist))
print(refused(waves, {**playlist, 'wave_zero': 'nope'}))
print(refused({'w0': waves['w0']}, playlist))
"
```
It prints five lines:
- `['p', 'w0'] w0 [0.0, 150.0] 0 30 ('p',)`: the book, its placements sorted by trigger, the extra rest defaulting to 0.
- `waves/w0.json: placements[0]: a hazard (meteorite) at 100 px is inside the first 120 px`
- `accepted`: a coin may come inside the first 120 px.
- `waves/playlist.json: wave_zero names 'nope', which is not a wave`
- `waves/playlist.json: levels[0] (level 1) has random_count 1 but no pool wave with min_level <= 1`

Put the command and its output in the implementation report. `game/tests/check.sh` ends `QA: pass`.

## Out of scope
- Reading or listing files, decoding JSON, the load log line: `game/app/waves.py` (Integration Engineer).
- `core/waves.py` beyond reading it, `core/run.py`, views, tests, `game/waves/`.
- Any check the contract lists under "Not checked at load".
