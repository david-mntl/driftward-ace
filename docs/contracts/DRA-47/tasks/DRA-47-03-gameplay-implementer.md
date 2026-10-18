Feature: DRA-47
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-50

## Read in the contract
- Interface, `game/core/drifters/base.py`: `DrifterType.CHAIN_LIGHTNING`.
- Interface, `game/core/drifters/chain_lightning.py` and `game/core/drifters/__init__.py`.
- Rules, Chain lightning (all of it).
- Rules, The base: Birth, Start, Entering, Leaving, Re-hit cooldown, Warning copy, Warning settle, Timers.
- Diagram: Chain lightning cycle and Chain lightning timeline.
- Rationale: the DRA-47 bullets from "Nodes in units of `node_spacing`" to "A top-start chain fires once at Level 1".

## Builds
- `game/core/drifters/base.py` (changed: the `CHAIN_LIGHTNING` member)
- `game/core/drifters/chain_lightning.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
DRA-47-01, DRA-47-02

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.drifters.base import DrifterType, TickContext
from core.drifters.chain_lightning import ChainLayout, ChainLightningTypeExtra, ChainLightningVariantExtra, InvertMirror, chain_hitbox, layout_size
from core.drifters.registry import available_drifters
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import add_drifters, start_run
def layout(nodes, arcs, mirror='left_right'): return ChainLayout(nodes=tuple((x * 128, y * 128) for x, y in nodes), arcs=arcs, invert_mirror=InvertMirror(mirror))
flat = layout(((-0.5, 0.0), (0.5, 0.0)), ((0, 1),))
tri = layout(((-0.5, 0.4330127), (0.0, -0.4330127), (0.5, 0.4330127)), ((0, 1), (1, 2), (2, 0)), 'top_bottom')
def variant(l):
    w, h = layout_size(l.nodes, 12)
    return VariantTuning(width=w, height=h, hitbox=chain_hitbox(l.nodes, l.arcs, 12, 6), extra=ChainLightningVariantExtra(layout=l))
extra = ChainLightningTypeExtra(node_size=12, arc_width=6, charge_ticks=120, fire_ticks=120, charge_rays=4, ray_length=6, ray_width=1, warning_layout=tri)
chain = DrifterTypeTuning(variants={'pair_flat': variant(flat), 'trio_triangle': variant(tri)}, default_variant='pair_flat', speed_ratio=0.375, entry_warning_ticks=60, extra=extra)
tuning = DrifterTuning(drifters={DrifterType.CHAIN_LIGHTNING: chain}, switches=PlaytestSwitches())
print(sorted(t.value for t in available_drifters()))
run = add_drifters(start_run(), [Placement(DrifterType.CHAIN_LIGHTNING, x=320.0)], tuning)
c = run.drifters[0]
print(c.variant, c.y, c.width, c.height, c.warning_center(), c.warning_copy().width, c.current_hitbox())
ctx = TickContext(ship=run.ship)
seen = []
for tick in range(1, 261):
    c = c.update(ctx).mark_entered()
    if tick in (60, 90, 120, 150, 179, 180, 259):
        seen.append((tick, round(c.y), c.is_firing(), c.charge_ray_count(), c.firing_arcs(), len(c.current_hitbox())))
print(seen)
print(c.is_off_screen())
t = spawn_drifter(Placement(DrifterType.CHAIN_LIGHTNING, x=320.0, variant='trio_triangle', invert=True, as_level=8), 1, tuning)
print([tuple(round(v, 2) for v in n) for n in t.nodes], t.charge_ticks, t.fire_ticks, round(t.speed, 2))
try:
    spawn_drifter(Placement(DrifterType.CHAIN_LIGHTNING), 1, tuning)
except ValueError as err:
    print(err)
"
```
It prints six lines:
- `['chain_lightning', 'meteorite', 'satellite']`: the chain lightning registered itself.
- `pair_flat -6.0 140.0 12.0 (256.0, 70.0) 140.0 ()`: default variant, just above the top edge, warning above the left node (a tie), sized on the triangle, no hitbox while warning.
- `[(60, -6, False, 1, (), 0), (90, 68, False, 2, (), 0), (120, 142, False, 3, (), 0), (150, 216, False, 4, (), 0), (179, 288, False, 4, (), 0), (180, 290, True, 0, (0,), 3), (259, 485, True, 0, (0,), 3)]`: the contract's timeline: four ray steps, then the arc and both nodes hit.
- `True`: dropped on the next state, every node below the floor.
- `[(-64.0, -55.43), (0.0, 55.43), (64.0, -55.43)] 84 120 3.5`: the inverted triangle points down; at Level 8 the charge is 84, the fire stays 120, the speed is × 1.42.
- `chain_lightning placement needs x`

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. `core -k "not collision"` passes. `ui` fails only in `test_drifter_registry.py` (no chain lightning view or tuning file yet), and `typecheck` only where task DRA-47-01 lists, until tasks DRA-47-04, DRA-47-06 and DRA-47-07, the data file and integration.

## Out of scope
- The chain lightning view, the warning drawing and line drawing (tasks DRA-47-04 to DRA-47-06).
- `game/tuning/drifters/chain_lightning.json` and its loader in `game/app/` (content and the Integration Engineer).
- Graze scoring, waves, ship-relative placement, the electric ball (scope report DRA-47, Out).
- Any test file.
