Feature: DRA-62
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: done
Linear: DRA-70

## Read in the contract
- drifters.md: Purpose.
- drifters.md: Diagram: the class diagram, the life of one drifter, the birth flowchart, Coin (the pixel map and drawn parts) and the coin timeline.
- drifters.md: Interface, `game/core/drifters/base.py`: the import line, `DrifterType.COIN`, `TouchEffect.COLLECT`, `TickContext.scroll_step_px`, `Drifter.parked`, `collect_points`, `collect_popup`, and the paragraph after the block (the DRA-62 sentences).
- drifters.md: Interface, `game/core/drifters/tuning.py`: the `speed_ratio` and `entry_warning_ticks` comments.
- drifters.md: Interface, `game/core/drifters/spawner.py`: the `spawn_drifter` comment.
- drifters.md: Interface, `game/core/drifters/coin.py` (all of it) and `game/core/drifters/__init__.py`.
- drifters.md: Rules: The base (Phase; Parked and moving; Per-tick facts; Collect); Spawner (step 4 with Parked, step 8); Coin (all of it); Tuning files (The coin's file, for what the loader will hand over); Logging.
- drifters.md: Impact, the DRA-62 table. Rationale, the DRA-62 lines.
- run.md: Interface, `game/core/popup.py` (all of it).

## Builds
- `game/core/popup.py` (new)
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/tuning.py` (changed: docstrings only)
- `game/core/drifters/spawner.py` (changed)
- `game/core/drifters/coin.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.drifters.base import DrifterType, TickContext
from core.drifters.coin import CoinTypeExtra, CoinVariantExtra, coin_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn
extra = CoinTypeExtra(body_height=10, ring_width=22, ring_height=8, glint_size=2, glint_left=3, glint_top=3, popup_ticks=60, popup_rise_per_tick=0.5)
variants = {n: VariantTuning(width=12.0, height=20.0, hitbox=coin_hitbox(12, 10), extra=CoinVariantExtra(points=p, glint=g)) for n, p, g in (('common', 50, False), ('rare', 100, True))}
tuning = DrifterTuning(drifters={DrifterType.COIN: DrifterTypeTuning(variants=variants, default_variant='common', speed_ratio=0.0, entry_warning_ticks=0, extra=extra)}, switches=PlaytestSwitches())
coin = spawn_drifter(Placement(DrifterType.COIN, x=320.0), 8, tuning)
print(coin.phase.value, coin.y, coin.speed, coin.effect_on_touch().value, coin.graze_zone())
moved = coin.update(TickContext(ship=spawn(), scroll_step_px=1.1)).update(TickContext(ship=spawn()))
print(round(moved.y, 2), moved.x, len(moved.drawn_parts()))
print(coin.collect_points(), coin.collect_popup())
try:
    spawn_drifter(Placement(DrifterType.COIN, x=320.0, speed=2.0), 1, tuning)
except ValueError as error:
    print(error)
"
```
It prints four lines:
- `active -10.0 0.0 collect ()`: born ACTIVE with no warning, just above the top edge, no speed even at Level 8, a pickup with no graze zone.
- `-8.9 320.0 2`: it moved with the scroll step and not without one, never sideways, and has two drawn parts.
- `50 PointsPopup(x=320.0, start_y=-10.0, points=50, lifetime_ticks=60, rise_per_tick=0.5, age_ticks=0)`.
- `coin has no speed`.

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass. In `core` and `ui`, the only failures are the two the contract's DRA-62 Impact table expects until the view and `game/tuning/drifters/coin.json` exist (`test_collision.py` naming `coin`, `test_drifter_registry.py`); every other existing test passes unchanged.

## Out of scope
- `game/core/run.py` and `game/core/scroll.py`: the collect step, the popups in the run and `scroll_step_px` are task DRA-62-02.
- The coin's view and the popup's view (tasks DRA-62-03 and DRA-62-04).
- `game/app/`, `game/tuning/` (the coin's file is content, named by the Director), tests.
- Sound, final art, waves, graze, any change to the other drifters.
