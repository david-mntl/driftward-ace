Feature: DRA-111
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-111/impact.md
Status: done
Linear: DRA-112

## Read in the contract
- systems/drifters/electric-ball/core.md: Diagram, Interface, Rules
- systems/drifters/electric-ball/rationale.md: Rationale
- systems/drifters/shared/base-interface.md: ELECTRIC_BALL, scale_telegraph, born_drifter, tick_warning
- systems/drifters/shared/base.md: Drawn parts, Leaving, Timers
- systems/drifters/shared/spawner-registry-tuning.md: Spawner, How to add a drifter

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/electric_ball.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report builds the electric ball's tuning in code from the GDD values, the way `app.tuning` builds it (`electric-ball/core.md`, Tuning), and prints:
- one placed with x and no y at Level 1, state by state from its birth through one whole charge and the fire until the run would drop it: phase, y, `is_charging()`, `is_firing()`, `ball_on_screen()`, `pulse_fires()`, `charge_ray_count()`, `outline_level()` and `current_hitbox()`. The rows follow the Electric ball timeline in the Diagram, and the first state with no hitbox after the fire is the first one whose ball is fully below the floor;
- one with a placed y at Level 1 and a slow placement speed, through two whole cycles: charge, fire, charge, fire, on the ticks the Cycle rule gives;
- one at Level 8: its charge is the GDD's Level 8 charge (drifters/10-electric-ball.md, rule 10), its fire unchanged; and one with a tuning charge low enough that the floor applies;
- the refusals, each with its message: no x, a specialty, a seed, the wrong variant extra, the wrong type extra; `check_electric_ball_variant` at and above half the ball; and a placement with `invert` printing the same states as the one without.

Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects from DRA-111-01; every other existing test passes unchanged.

## Out of scope
- The view (task DRA-111-02), `game/app/` (the loader is the Integration Engineer's), the tuning file and the debug rows (content), tests.
- Any change to the other drifters, `core/collision.py`, `core/levels.py`, `core/drifters/tuning.py`, `core/drifters/spawner.py`, `core/run.py`, `core/wave_files.py` or `tools/`.
