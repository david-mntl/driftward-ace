Feature: DRA-62
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/scroll.md, docs/contracts/systems/drifters.md
Status: open
Linear: DRA-71

## Read in the contract
- run.md: Purpose.
- run.md: Diagram: the one-tick flowchart (steps 3, 3a, 5a), the score flowchart and timeline, the popup timeline.
- run.md: Interface, `game/core/run.py`: the import lines, `coin_points` and `popups`, the `start_run` comment. Interface, `game/core/popup.py` (to read; built by DRA-62-01).
- run.md: Rules: Values (the popup sentence); the step-number note; steps 3, 3a, 5a, 9; the "If nothing happened" line; a game-over tick; Score (Coin points, Never goes down, Game over); Other rules (the game-over tick line); Logging (`drifter touch`, the order line, the "Nothing else" line).
- run.md: Impact, the DRA-62 table. Rationale, the DRA-62 lines.
- scroll.md: Interface, `scroll_step_px`. Rules, The next step's movement. Rationale, the DRA-62 line.
- drifters.md: Rules, The base (Per-tick facts; Collect) and Coin (Collected).

## Builds
- `game/core/scroll.py` (changed)
- `game/core/run.py` (changed)

## Depends on
DRA-62-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.drifters.base import DrifterType
from core.drifters.coin import CoinTypeExtra, CoinVariantExtra, coin_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import start_run, step_run
from core.scroll import Scroll, scroll_step_px, start_scroll
from core.ship import Thrust
extra = CoinTypeExtra(body_height=10, ring_width=22, ring_height=8, glint_size=2, glint_left=3, glint_top=3, popup_ticks=60, popup_rise_per_tick=0.5)
variants = {'common': VariantTuning(width=12.0, height=20.0, hitbox=coin_hitbox(12, 10), extra=CoinVariantExtra(points=50, glint=False))}
tuning = DrifterTuning(drifters={DrifterType.COIN: DrifterTypeTuning(variants=variants, default_variant='common', speed_ratio=0.0, entry_warning_ticks=0, extra=extra)}, switches=PlaytestSwitches())
coin = spawn_drifter(Placement(DrifterType.COIN, x=320.0, y=240.0), 1, tuning)
print(scroll_step_px(start_scroll()), scroll_step_px(Scroll(ticks=30)))
waiting = step_run(replace(start_run(), waiting=True, drifters=(coin,)), Thrust())
print(waiting.coin_points, len(waiting.drifters), len(waiting.popups))
run = step_run(replace(start_run(), drifters=(coin,), invuln_ticks_left=30), Thrust())
print(run.coin_points, run.score, len(run.drifters), run.popups[0].y)
for _ in range(59):
    run = step_run(run, Thrust())
print(len(run.popups), run.popups[0].y if run.popups else None)
run = step_run(run, Thrust())
print(len(run.popups))
"
```
It prints five lines:
- `0.0 1.1`: no scroll step before the start delay ends, 1.1 px after.
- `0 1 0`: a ship standing in the respawn wait collects nothing; the coin stays.
- `50 50 0 240.0`: an invulnerable ship collects the coin on the first tick; it pays, it is gone, and its popup starts at its center.
- `1 210.5`: 59 ticks later the popup is still there, 29.5 px higher.
- `0`: one tick later it is gone.

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass. In `core`, the existing tests pass unchanged apart from the `test_collision.py` coin case the contract's DRA-62 Impact table expects until `game/tuning/drifters/coin.json` and task DRA-62-05 exist.

## Out of scope
- Anything in `game/core/drifters/` or `game/core/popup.py` (task DRA-62-01).
- Views, `game/app/`, `game/tuning/`, tests.
- Any change to steps 1, 2, 4, 6, 7, 8 and 10, to `add_drifters`, to `step_scroll` or to how meters are counted.
- Sound, graze, waves, a coin count anywhere.
