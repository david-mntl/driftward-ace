Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-29-01 (Architect): the hitbox shapes and overlap test in `core/collision.py`, and the ship's inverted-T hitbox and `TOP_SIDE_SPEED` in `core/ship.py`.
2. **Delivered:**
   - `game/core/collision.py` (new): `Circle`, `Box`, `Shape`, `Hitbox`, `place_hitbox`, `hitboxes_overlap`, `grow_hitbox`, plus private helpers per shape pair.
   - `game/core/ship.py` (changed, additions only): `TOP_SIDE_SPEED`, `HITBOX_BAR_W`, `HITBOX_FOOT_H`, `SHIP_HITBOX`, `ship_hitbox`, the `core.collision` import, and the module docstring now names the hitbox.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile` on both files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `check.sh typecheck`: PASS (mypy strict, 25 files). `check.sh core`: 35 passed (all existing core tests).
   - Acceptance, from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "..."` with the command from the task file. Output:
     ```
     6.58
     False True
     False True
     ```
   - Determinism: ran it twice, outputs identical (diff empty). Also printed the spawned ship hitbox: bar `Box(320, 240, 12, 32)`, foot `Box(320, 250, 32, 12)`, and `hitboxes_overlap((), ship)` is False.
   - Grep of `game/core/*.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-29/tasks/DRA-29-01-gameplay-implementer.md`. Left alone: `core/levels.py`, `core/objects/`, `core/run.py`, UI and tests (other DRA-29 tasks).
7. **Status:** done.

## Decisions
- Overlap uses squared distances for circle tests so the strict `<` has no square root: a rock whose edge exactly touches the bar (14 px above it) gives 196 < 196, False. Source: objects.md, Rules, Collision.
- Circle-box finds the box point nearest the circle's center by clamping, then compares squared distance with r squared. Strict, as the contract says.
- Shape dispatch is `isinstance` in one small function, with one helper per pair. No class hierarchy or registry: the contract fixes two frozen dataclasses and a union.
- `collision.py` has its `log` logger as game/CONTEXT.md requires but logs nothing, as the contract says.
- `TOP_SIDE_SPEED` is computed from `THRUST_SIDE` and `DRAG_X`; `SHIP_HITBOX` from `SHIP_W`, `SHIP_H`, `HITBOX_BAR_W`, `HITBOX_FOOT_H`. No bare numbers. Values 12 and 12 are `guess` in 04-ship.md, hitbox.
- `SHIP_HITBOX` is a tuple of frozen boxes, so the `Final` constant can't be mutated.
