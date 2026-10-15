Feature: DRA-29
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md#rules
Status: done
Linear: DRA-32

## Do
Put objects into the run: they enter through `add_objects`, update every playing tick, hit the ship under the existing lives rules, and leave when they are off screen. Needs tasks DRA-29-01 and DRA-29-02 done first.

In `game/core/run.py`, from `docs/contracts/systems/run.md`, Interface, Rules, Logging and Impact:
- `Run` gains `objects: tuple[GameObject, ...] = ()` and `next_uid: int = 1`, each documented, and the property `level` (`core.levels.level_at(scroll.meters)`).
- `step_run`, a playing tick, in the contract's nine steps: step 3 updates every object with `TickContext(ship=run.ship)`; steps 4 to 6 are the existing wait, ship, scroll and fall rules, unchanged; step 7 is the hit, only when step 6 found no fall; step 8 drops objects that are GONE or off screen; step 9 sets `held`.
  - Hit: the touching objects are ACTIVE, `effect_on_touch()` HIT, `may_hit_ship()` True, and their `current_hitbox()` overlaps `ship_hitbox(ship)`. The run never reads `hit_ship` to decide; it asks `may_hit_ship()` (LD-06 is open; the "hits once" rule is the meteorite's own). Not protected and at least one touching: one life lost, every touching object gets `hit_ship = True` (the fact), `invuln_ticks_left = INVULN_TICKS`, the ship and `waiting` unchanged. On the last life: game over as the contract gives it, the ship stays where it was hit. Protected: nothing, nothing marked.
  - The game-over tick is unchanged: objects freeze with everything else. A retry returns `start_run()`, so no objects and `next_uid` 1.
- `add_objects(run, placements, tuning) -> Run` (new): returns `run` unchanged at game over or with no placements; otherwise spawns each placement with `spawn_object(placement, run.level, tuning)`, sets its `uid` from `next_uid` (`dataclasses.replace`), appends them in order, and returns the run with the new `objects` and `next_uid`. Errors from `spawn_object` rise.
- Logging on `core.run`: the four new DEBUG lines `object spawn`, `object active`, `object touch` and `object gone`, with the exact formats and the order inside a tick given in the contract's Logging section. `life lost` and `game over` also log for a hit. Nothing for a hazard passing through an invulnerable ship. Every existing line stays as it is.
- No change to `core/ship.py`, `core/scroll.py`, `core/world.py` or `core/objects/`.
- Expected test result: every existing test in `tests/core/test_run.py` and `tests/core/test_ship.py` still passes unchanged. Their runs have no objects. Don't edit tests.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint`, `typecheck` and `core` before handoff.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Circle
from core.objects.base import ObjectType
from core.objects.spawner import Placement
from core.objects.tuning import ObjectTuning, ObjectTypeTuning, PlaytestSwitches, VariantTuning
from core.run import add_objects, start_run, step_run
from core.ship import Thrust
def v(w): return VariantTuning(width=w, height=w, hitbox=(Circle(0, 0, w / 2),))
met = ObjectTypeTuning(variants={'small': v(20), 'medium': v(28), 'big': v(40)}, default_variant='medium', speed_ratio=0.75, entry_warning_ticks=30)
tuning = ObjectTuning(objects={ObjectType.METEORITE: met}, switches=PlaytestSwitches())
up = Thrust(up=True)
r = add_objects(start_run(), [Placement(ObjectType.METEORITE, x=320.0, y=184.0)], tuning)
for _ in range(29): r = step_run(r, up)
print(r.lives, r.objects[0].uid, r.objects[0].phase.value)
r = step_run(r, up)
print(r.lives, r.invulnerable, r.objects[0].hit_ship, r.ship.x, r.ship.y)
for _ in range(200): r = step_run(r, up)
print(r.lives, len(r.objects), r.next_uid)
"
```
It prints three lines:
- `3 1 warning`: the meteorite placed on the ship's spot (Up holds the ship on the top line at y 184) is still warning after 29 ticks and can't hit.
- `2 True True 320.0 184.0`: on the 30th tick it appears, and that is a hit: one life lost, invulnerable, the meteorite marked, the ship not moved.
- `2 0 2`: it falls away and is dropped below the floor; no second life lost.
Put the command and its output in the implementation report.

## Out of scope
- The objects, the spawner, collision and levels (tasks DRA-29-01 and DRA-29-02).
- Graze counting or scoring, coins and `COLLECT`, specialties, the life-lost feedback (flash, breaking heart, burst), object-vs-object or wall collisions, level progression.
- Loading tuning files, the debug test spawn list and the frame loop (`game/app/`, Integration Engineer).
- Tests (task DRA-29-08). Views.
