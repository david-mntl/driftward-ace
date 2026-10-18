Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the fireball core and the base `drawn_parts` hook, task `docs/contracts/DRA-56/tasks/DRA-56-01-gameplay-implementer.md`. Asked by the `/implement` skill on the report `docs/reports/implementation/gameplay/DRA-56-01-gameplay-implementer.md`.
2. **Delivered:** `docs/reports/review/DRA-56-01-gameplay-implementer.md`.
3. **Checks:** Read `game/core/drifters/base.py`, `game/core/drifters/fireball.py` and `game/core/drifters/__init__.py` against `docs/contracts/systems/drifters.md` (Interface for base, fireball and `__init__`; Rules for the base, the fireball and spawner steps 4 and 7; the DRA-56 Rationale), `docs/design/gdd/drifters/06-fireball.md`, `game/CONTEXT.md`, `game/ruff.toml` and `game/core/ruff.toml`. Worked the acceptance numbers by hand: velocities 1.7738 and 2.5333, tail offsets (-9.03, -12.90) and (13.77, -19.66), drawn boxes 24, 13.5, 35 and 19, the warning copy 21 × 31.5, and the leave timeline (tail box top 479.05 on tick 261, 481.58 on tick 262). All match the report's output. Ran nothing.
4. **Assumptions:** `SCREEN_H` is 480, as the task's expected timeline implies. Notes on code outside this task's Builds are recorded with no change, since the task's lane forbids fixing them here.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Three notes, none asking for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-56-01-F1 | note | game/core/drifters/fireball.py:161 | no action |
| DRA-56-01-F2 | note | game/core/drifters/fireball.py:134 | no action |
| DRA-56-01-F3 | note | game/core/drifters/base.py:306 | no action |

### DRA-56-01-F1
`drawn_parts()` skips any non-`Circle` shape without a word. The hitbox only ever comes from `fireball_hitbox` or `warning_copy`, so nothing is skipped today, and the Assumptions say so. If it ever happened, the error would stay hidden (`game/CONTEXT.md`, Error handling: "Never swallow an error"). Change: none.

### DRA-56-01-F2
`Fireball.update` is line for line the same as `Satellite.update` (`game/core/drifters/satellite.py:94`). The contract gives each drifter its own `update`, and a shared helper would touch the satellite, which is out of scope. Change: none.

### DRA-56-01-F3
The base `warning_copy` docstring still says "at half size" and "Its width also sizes the warning". The contract (Rules, The base, Warning copy) says the copy is scaled to `ENTRY_WARNING_COPY_SIZE` and "does not size the warning". This text predates DRA-56 and isn't in this task's Builds. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: F1, F2, F3
9. pass
10. pass

## For QA
- A fireball from the top-left corner: it's removed only once the tail's box has passed the floor (ACTIVE n 202, not n 198), never while the tail still shows.
- `invert` with a side entry at a set y: it starts at x 650.5, warns at (628, y) and flies down and to the left.
- The meteorite, the satellite and the chain lightning enter and leave on exactly the same ticks as before the `drawn_parts` change.
- The warning copy turns +35° with the head pointing down and to the right, and -35° with `invert`.
- A fireball crossing a side wall or another drifter flies straight through, with no bounce and no stop.
