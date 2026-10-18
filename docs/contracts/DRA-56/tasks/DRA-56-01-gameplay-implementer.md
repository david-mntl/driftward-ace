Feature: DRA-56
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-57

## Read in the contract
- Interface, `game/core/drifters/base.py`: `DrifterType.FIREBALL`, `drawn_parts`, `is_partly_on_screen`, `is_off_screen`, and the note under the block (DRA-56).
- Interface, `game/core/drifters/fireball.py` and `game/core/drifters/__init__.py`.
- Rules, The base: Drawn parts, Entering, Leaving, Warning place, Warning tilt, Warning copy, Birth, Start, Re-hit cooldown.
- Rules, Fireball (all of it). Rules, Spawner (steps 4 and 7).
- Diagram: the Fireball sketch, the start table and the Fireball timeline.
- Rationale: the DRA-56 bullets from "`drawn_parts()` in the base" to "A fireball dropped later than its head alone allows".

## Builds
- `game/core/drifters/base.py` (changed: the `FIREBALL` member, `drawn_parts`, the two screen tests through it, the `Box` import)
- `game/core/drifters/fireball.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.drifters.base import DrifterType, TickContext
from core.drifters.fireball import FireballTypeExtra, fireball_hitbox
from core.drifters.registry import available_drifters
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import start_run
def variant(w): return VariantTuning(width=w, height=w, hitbox=fireball_hitbox(w, 0.5, 35.0, False))
fire = DrifterTypeTuning(variants={'small': variant(21.0), 'big': variant(32.0)}, default_variant='small', speed_ratio=0.47, entry_warning_ticks=60, extra=FireballTypeExtra(angle_degrees=35.0, tail_ratio=0.5))
tuning = DrifterTuning(drifters={DrifterType.FIREBALL: fire}, switches=PlaytestSwitches())
def circles(h): return ' '.join(f'{c.cx:.2f},{c.cy:.2f},{c.r:.2f}' for c in h)
def boxes(h): return ' '.join(f'{b.cx:.2f},{b.cy:.2f},{b.w:.2f}' for b in h)
F = DrifterType.FIREBALL
print(sorted(t.value for t in available_drifters()))
for p in (Placement(F), Placement(F, variant='big', invert=True), Placement(F, x=125.0), Placement(F, y=120.0), Placement(F, y=200.0, invert=True)):
    f = spawn_drifter(p, 1, tuning)
    print(f.variant, f'{f.x:.2f} {f.y:.2f}', '%.2f %.2f' % f.warning_center(), f'{f.warning_tilt_degrees():.1f}', f'{f.velocity_x:.4f} {f.velocity_y:.4f}')
small = spawn_drifter(Placement(F), 1, tuning)
big = spawn_drifter(Placement(F, variant='big', invert=True), 1, tuning)
print(circles(small.hitbox), '|', circles(big.hitbox))
print(boxes(small.drawn_parts()), '|', boxes(big.drawn_parts()))
copy = small.warning_copy()
print(f'{copy.width:.2f} {copy.height:.2f}', circles(copy.hitbox), copy.phase.value)
f = spawn_drifter(Placement(F, x=125.0), 1, tuning)
ctx = TickContext(ship=start_run().ship)
seen = []
for tick in range(1, 263):
    f = f.update(ctx).mark_entered()
    if tick in (60, 258, 261, 262):
        seen.append((tick, f.phase.value, f.has_entered, f'{f.x:.2f}', f'{f.y:.2f}', f.is_off_screen()))
print(seen)
l8 = spawn_drifter(Placement(F, as_level=8), 1, tuning)
print(f'{l8.speed:.2f} {l8.velocity_x:.2f} {l8.velocity_y:.2f} {l8.angle_degrees:.1f}')
try:
    spawn_drifter(Placement(F, specialty_enabled=True), 1, tuning)
except ValueError as err:
    print(err)
"
```
It prints twelve lines:
- `['chain_lightning', 'fireball', 'meteorite', 'satellite']`: the fireball registered itself.
- `small 0.00 -10.50 12.00 12.00 35.0 1.7738 2.5333`: the default corner, warning in the top-left corner.
- `big 640.00 -16.00 628.00 12.00 -35.0 -1.7738 2.5333`: `invert`, the top-right corner, flying left.
- `small 125.00 -10.50 125.00 12.00 35.0 1.7738 2.5333`: along the top.
- `small -10.50 120.00 12.00 120.00 35.0 1.7738 2.5333`: the left wall.
- `small 650.50 200.00 628.00 200.00 -35.0 -1.7738 2.5333`: the right wall.
- `0.00,0.00,10.50 -9.03,-12.90,5.25 | 0.00,0.00,16.00 13.77,-19.66,8.00`: head, then the tail touching it from behind, mirrored with `invert`.
- `0.00,-10.50,24.00 -9.03,-23.40,13.50 | 640.00,-16.00,35.00 653.77,-35.66,19.00`: one drawn box per circle.
- `21.00 31.50 0.00,5.25,10.50 0.00,-10.50,5.25 warning`: the warning copy, laid straight down.
- `[(60, 'active', True, '125.00', '-10.50', False), (258, 'active', True, '476.22', '491.10', False), (261, 'active', True, '481.54', '498.70', False), (262, 'active', True, '483.32', '501.23', True)]`: the head is below the floor on 258, but the tail still shows; off only on 262.
- `4.39 2.52 3.60 35.0`: Level 8 speeds it up, the angle stays.
- `fireball has no specialty`

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass. `core -k "not collision"` passes. `core` fails only in `test_collision.py`'s ship test naming `fireball`, and `ui` only in `test_drifter_registry.py`, until task DRA-56-02, task DRA-56-03 and `game/tuning/drifters/fireball.json` exist.

## Out of scope
- The fireball view (task DRA-56-02).
- `game/tuning/drifters/fireball.json` and its loader, the debug spawn rows (content and the Integration Engineer).
- Graze scoring, trail and sprite art, sound, waves (scope report DRA-56, Out).
- Any change to the meteorite, the satellite, the chain lightning or `core/run.py`.
- Any test file.
