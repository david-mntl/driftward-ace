Feature: DRA-29
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/objects.md#interface
Status: done
Linear: DRA-30

## Do
Build the hitbox shapes and their overlap test, and give the ship its inverted-T hitbox and its top sideways speed.
- `game/core/collision.py` (new), exactly the `core/collision.py` block of `docs/contracts/systems/objects.md`, Interface, and its Rules, Collision:
  - `Circle(cx, cy, r)` and `Box(cx, cy, w, h)`, frozen, slotted dataclasses, each field documented with its unit and meaning. `Shape = Circle | Box`, `Hitbox = tuple[Shape, ...]`.
  - `place_hitbox(hitbox, x, y)`, `hitboxes_overlap(a, b)`, `grow_hitbox(hitbox, margin)`. Overlap is strict: shapes that only touch at an edge or a point don't overlap. Circle–circle, box–box and circle–box as the contract gives them. An empty hitbox overlaps nothing.
  - Stdlib only. Pure: no logging lines, no randomness. The module still has its `log` logger (game/CONTEXT.md, Logging).
- `game/core/ship.py`, from `docs/contracts/systems/ship.md`, Interface, Rules (Hitbox) and Impact:
  - `TOP_SIDE_SPEED: Final[float] = THRUST_SIDE * DRAG_X / (1 - DRAG_X)` (04-ship.md, derived values).
  - `HITBOX_BAR_W: Final[int] = 12`, `HITBOX_FOOT_H: Final[int] = 12` (04-ship.md, hitbox, guess).
  - `SHIP_HITBOX: Final[Hitbox]`: the bar `Box(cx=0, cy=0, w=HITBOX_BAR_W, h=SHIP_H)` and the foot `Box(cx=0, cy=SHIP_H / 2 - HITBOX_FOOT_H / 2, w=SHIP_W, h=HITBOX_FOOT_H)`, built from the constants, never bare numbers.
  - `ship_hitbox(ship: Ship) -> Hitbox`: `place_hitbox(SHIP_HITBOX, ship.x, ship.y)`. Pure, no logging.
  - Each new constant documented with its unit and source, as the existing ones are. The module docstring names the hitbox.
  - Nothing else changes: every existing constant, `Thrust`, `Ship`, `spawn`, `step`, `is_below_floor` and both log lines stay exactly as they are.
- Follow game/CONTEXT.md: module logger, type hints on every function, docstrings, no `print`, no broad `except`. Run `game/tests/check.sh lint`, `game/tests/check.sh typecheck` and `game/tests/check.sh core` before handoff. Every existing core test must still pass.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Circle, place_hitbox, hitboxes_overlap, grow_hitbox
from core.ship import spawn, ship_hitbox, TOP_SIDE_SPEED
ship = ship_hitbox(spawn())
def rock(x, y): return place_hitbox((Circle(0, 0, 14),), x, y)
print(round(TOP_SIDE_SPEED, 2))
print(hitboxes_overlap(ship, rock(320, 210)), hitboxes_overlap(ship, rock(320, 211)))
print(hitboxes_overlap(ship, rock(344, 230)), hitboxes_overlap(ship, grow_hitbox(rock(344, 230), 14)))
"
```
It prints three lines:
- `6.58`: the ship's top sideways speed (0.42 × 0.94 / 0.06).
- `False True`: a medium rock whose bottom just touches the top of the ship's bar doesn't overlap; one pixel lower, it does.
- `False True`: a rock beside the ship, in the empty corner of the T, doesn't touch it, but its graze zone (grown by 14) does.
Put the command and its output in the implementation report.

## Out of scope
- `core/levels.py`, `core/objects/` (task DRA-29-02) and the run (task DRA-29-03).
- The ship view and `ui/shapes.py` (task DRA-29-04).
- Tests (task DRA-29-07).
- Any change to the ship's physics, walls, top line, floor or log lines.
