Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-117-01-gameplay-implementer (graze margin, graze state and per-drifter graze zone on the drifter base), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-117-01-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (env, lint, format, typecheck, core, ui all PASS). Every existing test keeps its result.
   - Acceptance check reproduced with an inline run (the implementation report's script, plus a second script run on the real tuning files with the hazards loader stubbed to `HazardRules()` / `graze_margin=30`; scripts in the scratchpad, not saved in `game/tests/`):
     - default `HazardRules()`: meteorite `graze_margin` 14, `graze_state` OUTSIDE, zone `Circle(r=28)` (hitbox 14 + 14).
     - `HazardRules(graze_margin=30)`: margin 30, OUTSIDE, zone radius 44 (30 wider than the hitbox's 14).
     - WARNING meteorite: zone `()`. Coin and floating island (ACTIVE): zone `()`, state OUTSIDE.
     - `Birth(...)` built without `graze_margin`: builds, margin 14.
   - Edge cases, margins 14, 30 and 0.5, all nine drifter types spawned through `spawn_drifter`, then 500 `update` ticks each with the ship far away:
     - every drifter carries the tuned margin on every tick (subclass `born` for satellite, chain lightning, UFO, electric ball included).
     - zone equals `grow_hitbox(current_hitbox(), margin)` on every tick for HIT drifters, `()` otherwise: 0 mismatches. Chain lightning has a zone on 135 ticks (firing only). Electric ball first firing tick 180: circle r=64, zone r=94 at margin 30. Coin, island: `()` always.
     - `graze_state` stays OUTSIDE through `update` for all types. A drifter set to SPENT stays SPENT after `update` (`replace` carries it over).
     - Margin 0.5 and 14 grow as expected. Margin 0 gives a zone equal to the hitbox (core trusts `app.tuning`'s check, per the implementer's decision).
     - Same inputs twice (electric ball, margin 30, 300 ticks): identical.
   - Review `For QA` list: all five lines checked above.
4. **Assumptions:** The hazards loader is outside this task, so I stubbed `app.tuning._load_hazards` in the inline runs to build a full tuning.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Note for the Integration Engineer: `game/tuning/hazards.json` already holds `"graze_margin": 14`, and `app.tuning` does not know that field yet. `load_tuning()` raises `tuning/hazards.json: graze_margin is not a known field`, so the game does not start until the loader reads it (`docs/contracts/DRA-117/impact.md`, `game/app/tuning.py`, `systems/app/tuning-loader.md`). The tuning file edit and the loader change are outside this task (Out of scope: `game/app/`, tuning files). No existing test reaches it, so `check.sh` passes.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
