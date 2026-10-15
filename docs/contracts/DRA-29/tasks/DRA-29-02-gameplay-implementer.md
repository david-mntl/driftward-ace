Feature: DRA-29
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/objects.md#interface
Status: done
Linear: DRA-31

## Do
Build the level table, the shared object base, the tuning records, the registry, the spawner and the meteorite. Needs task DRA-29-01 (`core/collision.py`, `TOP_SIDE_SPEED`) done first.

Everything below is exactly the matching block of `docs/contracts/systems/objects.md`, Interface, with the behavior in its Rules:
- `game/core/levels.py` (new): `LEVEL_COUNT`, `HAZARD_SPEED_MULT`, `TIMER_MULT`, `LEVEL_STARTS_M`, `check_level`, `hazard_speed_mult`, `timer_mult`, `level_at`. Values from 08-difficulty.md, level table (Hazard speed locked, Timer × guess). `LEVEL_STARTS_M = (0,)`: Levels 2 to 8 are TBD (DF-05). Raises `ValueError` naming the level outside 1 to 8.
- `game/core/objects/base.py` (new): `GRAZE_MARGIN = 14` (06-scoring.md, locked); the enums `ObjectType` (one member, `METEORITE = "meteorite"`), `Phase` and `TouchEffect`; `TickContext`; `Birth`; the abstract `Specialty` (interface only: `enabled`, abstract `update`, `effect_on_ship` returning None); the abstract `GameObject` with its fields, defaults and field docs, the concrete `current_hitbox`, `graze_zone`, `is_off_screen`, `warning_center` and classmethod `born`, the abstract classmethod `default_y` and the abstract `update`, `effect_on_touch` and `may_hit_ship`; and the helper `tick_warning`. `hit_ship` is only a recorded fact; the base gives `may_hit_ship` no default and has no "hits once" rule (LD-06 is open). `GameObject` and `Specialty` are `@dataclass(frozen=True, slots=True, kw_only=True)` and inherit `ABC`. No zero-argument `super()` (slots).
- `game/core/objects/tuning.py` (new): `VariantTuning`, `ObjectTypeTuning`, `PlaytestSwitches` (both switches default True), `ObjectTuning`. Records only, no checks: the app checks the files (`systems/app.md`, Tuning loader) and core trusts them.
- `game/core/objects/registry.py` (new): `register_object` (raises `TypeError` for an abstract class or one with no `object_type`, `ValueError` for a duplicate type), `available_objects`, `object_class` (raises `ValueError` for an unregistered type). Messages as in the contract.
- `game/core/objects/spawner.py` (new): `Placement` and `spawn_object`, steps 1 to 8 of the contract's Rules, Spawner, with the three error messages (no tuning for the type, unknown variant naming the variant and the type, level outside 1 to 8). The switches beat `as_level`. Entry warnings are never scaled.
- `game/core/objects/meteorite.py` (new): `Meteorite`, registered with `@register_object`, `object_type = ObjectType.METEORITE`, no new fields, the base `born`. `default_y(height) = -height / 2`. `update`: `tick_warning` in WARNING; in ACTIVE `y += speed` and `ticks_in_phase + 1`, `x` unchanged; unchanged in GONE. `effect_on_touch()` is HIT. `may_hit_ship()` is `not self.hit_ship`: the meteorite-only stand-in (scope report DRA-29, Stand-ins), documented as such in its docstring.
- `game/core/objects/__init__.py` (new): a package docstring and one import of `core.objects.meteorite`, so the class registers when anything in `core.objects` is imported.
- Imports: stdlib and `core` only. Never pygame, `ui` or `app`. No frame time, no randomness, no run mode. No log lines in these modules (each module with code still has its `log` logger).
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint`, `typecheck` and `core` before handoff. Every existing core test must still pass.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Circle
from core.objects.base import ObjectType, TickContext
from core.objects.registry import available_objects
from core.objects.spawner import Placement, spawn_object
from core.objects.tuning import ObjectTuning, ObjectTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn
def v(w): return VariantTuning(width=w, height=w, hitbox=(Circle(0, 0, w / 2),))
met = ObjectTypeTuning(variants={'small': v(20), 'medium': v(28), 'big': v(40)}, default_variant='medium', speed_ratio=0.75, entry_warning_ticks=30)
tuning = ObjectTuning(objects={ObjectType.METEORITE: met}, switches=PlaytestSwitches())
print(sorted(t.value for t in available_objects()))
m = spawn_object(Placement(ObjectType.METEORITE, x=320.0), 1, tuning)
print(m.variant, m.y, round(m.speed, 3), m.phase.value, m.current_hitbox())
ctx = TickContext(ship=spawn())
for _ in range(29): m = m.update(ctx)
print(m.phase.value, m.y)
m = m.update(ctx)
print(m.phase.value, m.y, len(m.current_hitbox()))
m = m.update(ctx)
print(round(m.y, 3), m.x)
print(round(spawn_object(Placement(ObjectType.METEORITE, x=0.0, as_level=8), 1, tuning).speed, 3))
try:
    spawn_object(Placement(ObjectType.METEORITE, x=0.0, variant='huge'), 1, tuning)
except ValueError as err:
    print(err)
"
```
It prints seven lines:
- `['meteorite']`: the meteorite registered itself.
- `medium -14.0 4.935 warning ()`: default variant, default start y (−28 ÷ 2), Level 1 speed 0.75 × 6.58, born in its warning with no hitbox.
- `warning -14.0`: still warning after 29 updates, not moving.
- `active -14.0 1`: the 30th update makes it appear, where it was placed, with one hitbox shape.
- `-9.065 320.0`: then it falls straight down by its speed.
- `7.008`: placed as Level 8, its speed is × 1.42.
- `unknown variant 'huge' for object type 'meteorite'`.
Put the command and its output in the implementation report.

## Out of scope
- `core/collision.py` and the ship hitbox (task DRA-29-01). Any change to `core/ship.py` beyond reading `TOP_SIDE_SPEED`.
- `Run.objects`, `add_objects`, hits, drops and the lifecycle log lines (task DRA-29-03).
- Any specialty behavior, coins, `TouchEffect.COLLECT` handling, other objects, graze scoring, object-vs-object or wall collisions.
- Reading tuning files (the app does it). Tests (task DRA-29-07). Views (tasks DRA-29-05, DRA-29-06).
