Feature: DRA-111
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-111/impact.md
Status: open
Linear: DRA-114

## Read in the contract
- systems/drifters/electric-ball/core.md: Diagram, Interface, Rules
- systems/drifters/shared/base.md: Entering, Leaving, Re-hit cooldown, Timers
- systems/drifters/shared/spawner-registry-tuning.md: Spawner
- systems/run.md: A playing tick, Logging

## Builds
- `game/tests/core/test_electric_ball.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-111-01

## Not in the contract
- Like `test_ufo.py`, the new file builds its own `DrifterTuning` for the electric ball (and a meteorite where a test needs one) from the GDD values at the top of the file, the way `app.tuning` builds it, and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.
## Test
- It is born in WARNING with the shared entry warning at its x against the top edge; x is required; with no y its ball touches the top edge from above; a placed y is kept; `invert` changes nothing. Rules: Start; Warning; Born.
- A specialty, a seed, the wrong variant extra and the wrong type extra are refused, each with its message, in the contract's order. Rules: Born; Placement fields.
- It falls by its speed on every ACTIVE tick, x unchanged, and never reads the ship or the scroll; it doesn't move while warning. Rules: Update.
- The cycle, tick for tick, over two whole cycles with the ball on screen (a placed y or a slow speed): charge for exactly the charge length from the state it appears, fire for exactly the fire length, then charge again. Rules: Cycle; Diagram.
- Rays and outline level on each cycle tick: one ray at the start, one more each part, never past `charge_rays`, all of them for the last part at Level 1 and Level 8; the outline level is the ray count's share. Rules: Charge rays; Outline level.
- Ball on screen is the strict box test at each of the four edges. Rules: Ball on screen.
- While the ball is off screen the cycle keeps counting, but no ray shows, the outline level is 0 and nothing fires. Rules: Shown only with the ball; Fires.
- No hitbox in WARNING, in GONE and while charging; the circle placed on the ball while it fires with the ball on screen; none on the first firing state the ball is off screen. The graze zone exists only while it fires. Rules: Hitbox now; Fires; Touch.
- Drawn parts: the ball's box alone while the ball is off screen, the ball's box and the pulse box while it is on. Rules: Drawn parts.
- The timeline from a top start at Level 1: appears touching the top edge, on screen from the next state, fires once from mid-screen, and is dropped by the run on the first state its ball is fully below the floor, during that fire, with its `drifter gone` line; never dropped before it has entered. Rules: Diagram; Leaving.
- Level scaling: speed × the level's hazard speed; the charge × Timer ×, rounded up, never below `telegraph_min` (also with a tuning charge under the floor); the fire, the radius, the sizes and the ray values unchanged; with the switches off, Level 1 values; a placement speed changes only the speed. Rules: Scales; Spawner.
- `telegraph_ticks` gives the type's charge, and None without its type values. Rules: For wave_check.
- `electric_ball_hitbox` is one circle on the center; `check_electric_ball_variant` accepts the GDD values and refuses a pulse radius at or below half the ball with its message. Rules: Hitbox; Tuning checks.
- In the run: a ship sitting on the ball while it charges is not hit; a ship inside the circle on the first firing state is hit: one life, the cooldown starts, it dims, keeps falling and keeps its cycle; no second hit until the cooldown ends; no hit while the ship is invulnerable, and the circle keeps firing. Rules: Touch; Hitting again; run.md, A playing tick.
- It logs `drifter spawn`, `drifter active`, `drifter touch ... effect=hit` per hit and `drifter gone`, and nothing from `core.drifters`. Rules: run.md, Logging.
- `update` never mutates its input; the same state and context give the same result. Rules: Update.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures are cleared, with `test_electric_ball.py` in the `core` step and all its tests passing.

## Out of scope
- The ship against every variant (task DRA-111-04); wave files and the telegraph guard (task DRA-111-05).
- wave_check and its tests (`tools/wave_check/`, the main session). The view.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
