Feature: DRA-104
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/waves.md, docs/contracts/systems/drifters.md
Status: done
Linear: DRA-106

## Read in the contract
- waves.md: Interface, `game/core/wave_files.py` (the import line) and `WavePlacement` (the `placement` comment).
- waves.md: Rules, The wave files (Placement: `seed`; Drifter type; Built drifter, with Seed; One path per UFO); Other rules (randomness).
- waves.md: Impact, the DRA-104 table. Rationale, the DRA-104 lines.
- drifters.md: Interface, `game/core/drifters/spawner.py` (`Placement.seed`, `MAX_SEED`, `placement_seed`); Rules: The base (Seeded); Spawner (step 8, Placement seed); UFO (Born: the band refusal).

## Builds
- `game/core/wave_files.py` (changed)

## Depends on
DRA-104-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
import copy
from core.collision import Circle
from core.drifters.base import DrifterType
from core.drifters.spawner import placement_seed
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.drifters.ufo import UfoTypeExtra, ufo_hitbox
from core.wave_files import build_wave_book
weave = UfoTypeExtra(weave_change_ticks_min=60, weave_change_ticks_max=96, weave_step_min=40.0, weave_step_max=120.0, weave_speed_max=1.6, weave_turn=0.1, band_top=188.0, band_bottom=440.0)
ufo_type = DrifterTypeTuning(variants={'standard': VariantTuning(width=40.0, height=10.0, hitbox=ufo_hitbox(40.0, 10.0, 9.0))}, default_variant='standard', speed_ratio=0.3, entry_warning_ticks=60, extra=weave)
rock_type = DrifterTypeTuning(variants={'small': VariantTuning(width=20.0, height=20.0, hitbox=(Circle(0.0, 0.0, 10.0),))}, default_variant='small', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.UFO: ufo_type, DrifterType.METEORITE: rock_type}, switches=PlaytestSwitches())
playlist = {'wave_zero': 'wave_0', 'levels': [{'fixed': [], 'random_count': 1} for _ in range(8)]}
def waves(placements):
    return {'wave_0': {'length_px': 1000, 'kind': 'fixed', 'placements': placements}, 'pool_a': {'length_px': 1000, 'kind': 'pool', 'min_level': 1, 'placements': []}}
good = [{'at_px': 300, 'type': 'ufo', 'y': 300}, {'at_px': 200, 'type': 'ufo', 'y': 250, 'seed': 5}, {'at_px': 150, 'type': 'meteorite', 'x': 100}]
book = build_wave_book(waves(good), playlist, tuning)
by_type = [(item.placement.drifter_type.value, item.placement.seed) for item in book.waves['wave_0'].placements]
print(by_type[0], by_type[1], by_type[2] == ('ufo', placement_seed('wave_0', 0)))
for change in ({'seed': 5}, {'seed': -1}, {'seed': True}, {'y': 100}, {'type': 'comet'}):
    bad = copy.deepcopy(good)
    bad[0].update(change)
    try:
        build_wave_book(waves(bad), playlist, tuning)
    except ValueError as error:
        print(error)
bad = copy.deepcopy(good)
bad[2]['seed'] = 3
try:
    build_wave_book(waves(bad), playlist, tuning)
except ValueError as error:
    print(error)
"
```
It prints seven lines:
- `('meteorite', None) ('ufo', 5) True`: sorted by `at_px`, the meteorite has no seed, the given seed is kept, and the UFO with none gets the default for `wave_0`, index 0.
- `waves/wave_0.json: placements[1]: seed 5 is already used by placements[0]`
- `waves/wave_0.json: placements[0].seed must be an integer from 0 to 4294967295` (twice: for -1 and for true)
- `waves/wave_0.json: placements[0]: ufo placement y 100 is outside its band 188 to 440`
- `waves/wave_0.json: placements[0].type 'comet' is not a drifter type (meteorite, satellite, chain_lightning, fireball, coin, floating_island, planet, ufo)`
- `waves/wave_0.json: placements[2]: meteorite has no seed`

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters and waves contracts' DRA-104 Impact tables expect until the view, the UFO's tuning file and the QA tasks exist.

## Out of scope
- `game/core/waves.py`, `game/core/run.py`, the drifters (task DRA-104-01), `game/app/`, tests, wave files, `tools/`.
