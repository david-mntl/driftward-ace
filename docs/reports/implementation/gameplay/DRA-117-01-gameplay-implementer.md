Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-117-01, build the graze margin, graze state and per-drifter graze zone on the drifter base (task `docs/contracts/DRA-117/tasks/DRA-117-01-gameplay-implementer.md`, from the Architect).
2. **Delivered:**
   - `game/core/drifters/base.py`: enum `GrazeState` (OUTSIDE, INSIDE, SPENT); `Birth.graze_margin` (last field, default `GRAZE_MARGIN`); `Drifter.graze_margin` and `Drifter.graze_state` (defaults `GRAZE_MARGIN`, OUTSIDE); `graze_zone()` grows the hitbox by `self.graze_margin`; `born_drifter` copies `birth.graze_margin`.
   - `game/core/drifters/tuning.py`: `HazardRules.graze_margin` (default `GRAZE_MARGIN`).
   - `game/core/drifters/spawner.py`: `spawn_drifter` passes `tuning.hazards.graze_margin` to `Birth`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on the three files: clean.
   - `game/tests/check.sh` (full): env, lint, format, typecheck, core, ui all PASS, "QA: pass". No existing test changed result.
   - Smoke run, twice: identical output (compared with `cmp`). Command, from `game/` (script below saved at the scratchpad path, not in the repo):
     `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -I -c "import sys; sys.path.insert(0,'.'); exec(open('<script path>').read())"`
   - Grep of `game/core` for the banned names: hits only in `core/ruff.toml` (the ban rules themselves) and `.wav` matching `core.waves` imports in `wave_files.py` and `run.py` (regex dot). No real use.

   Script:
```python
"""DRA-117-01 smoke: graze margin, graze state and graze zone on the drifter base."""

from dataclasses import replace

from core.collision import Box, Circle
import core.drifters  # registers every drifter
from core.drifters.base import Birth, DrifterType, Phase
from core.drifters.coin import CoinTypeExtra, CoinVariantExtra
from core.drifters.floating_island import IslandShape, IslandTypeExtra, IslandVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)

ROCK = (Circle(0.0, 0.0, 14.0),)  # drifters/01-meteorite.md, medium
COIN_EXTRA = CoinTypeExtra(
    body_height=10, ring_width=22, ring_height=8, glint_size=2,
    glint_left=3, glint_top=3, popup_ticks=60, popup_rise_per_tick=0.5,
)


def tuning(rules: HazardRules) -> DrifterTuning:
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK)},
                default_variant="medium", speed_ratio=0.375, entry_warning_ticks=60,
            ),
            DrifterType.COIN: DrifterTypeTuning(
                variants={"common": VariantTuning(
                    width=12, height=20, hitbox=(Box(0.0, 0.0, 12.0, 10.0),),
                    extra=CoinVariantExtra(points=50, glint=False))},
                default_variant="common", speed_ratio=0.0, entry_warning_ticks=0,
                extra=COIN_EXTRA,
            ),
            DrifterType.FLOATING_ISLAND: DrifterTypeTuning(
                variants={"rectangle": VariantTuning(
                    width=320, height=120, hitbox=(Box(0.0, 0.0, 320.0, 120.0),),
                    extra=IslandVariantExtra(shape=IslandShape.RECTANGLE))},
                default_variant="rectangle", speed_ratio=0.0, entry_warning_ticks=0,
                extra=IslandTypeExtra(arm=40.0),
            ),
        },
        switches=PlaytestSwitches(),
        hazards=rules,
    )


def active_rock(rules: HazardRules):
    rock = spawn_drifter(Placement(DrifterType.METEORITE, 320.0, 100.0), 1, tuning(rules))
    return replace(rock, phase=Phase.ACTIVE, ticks_in_phase=0)


for label, rules in (("default", HazardRules()), ("margin 30", HazardRules(graze_margin=30))):
    rock = active_rock(rules)
    print(label, rock.graze_margin, rock.graze_state, rock.graze_zone())
rock = spawn_drifter(Placement(DrifterType.METEORITE, 320.0, 100.0), 1, tuning(HazardRules()))
print("warning", rock.phase, rock.graze_zone())
for kind in (DrifterType.COIN, DrifterType.FLOATING_ISLAND):
    d = spawn_drifter(Placement(kind, 320.0, 100.0), 1, tuning(HazardRules()))
    print(kind.value, d.phase, d.graze_zone(), d.graze_state)
birth = Birth(
    x=1.0, y=2.0, variant="medium", width=28, height=28, hitbox=ROCK, speed=1.0,
    warning_ticks=60, timer_mult=1.0, specialty_enabled=None, invert=False, variant_extra=None,
    type_extra=None, rehit_cooldown_ticks=180, rehit_dim=0.75, telegraph_min_ticks=45,
)
print("birth", birth.graze_margin)
```
   Output:
```
default 14 GrazeState.OUTSIDE (Circle(cx=320.0, cy=100.0, r=28.0),)
margin 30 30 GrazeState.OUTSIDE (Circle(cx=320.0, cy=100.0, r=44.0),)
warning Phase.WARNING ()
coin Phase.ACTIVE () GrazeState.OUTSIDE
floating_island Phase.ACTIVE () GrazeState.OUTSIDE
birth 14
```
   Reading: default margin 14, zone radius 28 (hitbox 14 + 14). Margin 30: zone radius 44, 30 px wider than the hitbox's 14. WARNING meteorite: zone `()`. Coin and floating island (ACTIVE): zone `()`, state OUTSIDE. `Birth(...)` without `graze_margin` builds, margin 14.
4. **Assumptions:** The smoke builds the coin and island tuning from the values the existing core tests use (coin 12x20, island rectangle 320x120, arm 40). The acceptance check names no values for them, and the result does not depend on them.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-117/tasks/DRA-117-01-gameplay-implementer.md`. Left alone: `core/run.py`, `core/graze.py`, `core/popup.py` (task DRA-117-02), the drifter subclasses, `app/tuning.py` (Integration Engineer loads `graze_margin` from `hazards.json`), tests.
7. **Status:** done.

## Decisions
- `graze_margin` is typed `float` on `Birth`, `Drifter` and `HazardRules`, as the contract says; the default is the `int` constant `GRAZE_MARGIN` (14), so the zone is the same as before with the default.
- `Birth.graze_margin` is the last field, with a default, so every existing `Birth(...)` call still builds.
- `GrazeState` sits before `TouchEffect` in `base.py`, with no logic. The run sets it (task DRA-117-02); no `update` reads it.
- No check on `graze_margin > 0` in core: core trusts the values `app.tuning` checks (`game/CONTEXT.md`, Good practice).
- Sources: `GRAZE_MARGIN` 14 from 06-scoring.md, graze_margin (locked); the margin in tuning from scope report DRA-117, Limits. No new number in code.
