Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the implementation report `docs/reports/implementation/gameplay/DRA-29-01-gameplay-implementer.md` (`core/collision.py` new; hitbox and `TOP_SIDE_SPEED` added to `core/ship.py`). The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-29-01-gameplay-implementer.md` (this file).
3. **Checks:** I only read the code. I ran nothing.
   - I compared `game/core/collision.py` and `game/core/ship.py` line by line with `docs/contracts/systems/objects.md` (Interface, `core/collision.py` block; Rules, Collision; Logging) and `docs/contracts/systems/ship.md` (Interface, Rules: Values and Hitbox, Impact), the task's Do list, `04-ship.md` (hitbox, derived values, rule 8), `06-scoring.md` rule 3, `07-objects.md` rule 8, decision-log row 35, `game/CONTEXT.md` and `game/ruff.toml`.
   - I traced the acceptance script by hand. `0.42 × 0.94 / 0.06 = 6.58`. Spawned T: bar x 314 to 326, y 224 to 256; foot x 304 to 336, y 244 to 256. Rock at (320, 210), r 14: nearest bar point (320, 224), 196 < 196 is False; at (320, 211): 169 < 196 is True. Rock at (344, 230): bar nearest (326, 230), 324; foot nearest (336, 244), 64 + 196 = 260; both are not < 196, so False. Grown to r 28 (784): True. All three claimed lines match the code.
   - Grep-level reading of both files: no pygame, `ui` or `app` import, no randomness, frame time, sleep, thread, `print` or log call in the new code.
4. **Assumptions:** Without a diff, I can't confirm that nothing else in `ship.py` changed. I checked that every existing constant, `Wall`, `Thrust`, `Ship`, `spawn`, `step`, its helpers, `is_below_floor` and both log lines match `systems/ship.md` exactly. The only other change is the added module-docstring paragraph the task asks for.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: run task DRA-29-07 against the implementation report and this review. 0 must-fix, 0 should-fix, 1 note.
7. **Status:** done.

## Findings
1. **note** `game/core/ship.py:57-58`: the `TOP_SIDE_SPEED` docstring says "(about 6.58)" and "Recompute when THRUST_SIDE or DRAG_X changes." The constant itself is computed, so it recomputes on its own; only the "about 6.58" in the text would go stale. A reader could take the sentence to mean the value needs a manual update. Rule: docstrings say what the name and types can't, plainly. Source: game/CONTEXT.md, Docstrings; `systems/ship.md`, Rules, Values ("computed ... never written as a bare 6.58"). Change: none. A later task that touches the file may reword it to "the 6.58 in this text" or drop the number.

## Checklist
1. Interface matches exactly: **pass**. `Circle(cx, cy, r)` and `Box(cx, cy, w, h)` are frozen, slotted, with the contract's field meanings (`collision.py:17-45`). `Shape`, `Hitbox`, `place_hitbox`, `hitboxes_overlap` and `grow_hitbox` have the contract's names, parameters and return types (`collision.py:48-77`). `TOP_SIDE_SPEED`, `HITBOX_BAR_W`, `HITBOX_FOOT_H`, `SHIP_HITBOX` and `ship_hitbox(ship) -> Hitbox` match `systems/ship.md` (`ship.py:56-71`, `189-194`). Every added helper is private.
2. UI/core split: **pass**. `collision.py` imports stdlib only. `ship.py` adds only `core.collision` (`ship.py:19`).
3. Fixed 60 Hz tick: **pass** (n/a in substance). No timers; nothing reads time.
4. Randomness: **pass**. None. `any(...)` over both hitboxes returns the same bool in any order.
5. Browser rules: **pass**. No blocking call, sleep, thread, await, audio or path.
6. Numbers trace: **pass**. 12 and 12 are `04-ship.md`, hitbox (guess), as the report says. `TOP_SIDE_SPEED` and `SHIP_HITBOX` are built from constants, never bare numbers (`systems/ship.md`, Rules, Values). The literals left are geometry (`/ 2`, `2 * margin`).
7. Pillars and locked decisions: **pass**. The T stays inside the 32 × 32 square, so walls (no bounce), top line and floor are untouched. Strict overlap keeps the hitbox no bigger than what is seen (`07-objects.md`, rule 8; `objects.md`, Rationale).
8. Smells: **pass**. Short functions, nesting depth 2 at most (`collision.py:94-102`), no duplicated blocks, no dead code, no module-level game state, every function annotated and documented.
9. Decisions: **pass**. All six match the code: squared distances with strict `<` (`collision.py:110`, `124`), clamping for circle–box (`collision.py:120-121`), `isinstance` dispatch with one helper per pair, an unused `log` as the contract requires, constants built from constants, and `SHIP_HITBOX` as a tuple of frozen boxes.
10. Report claims match the files: **pass**. The acceptance output and the spawned boxes `Box(320, 240, 12, 32)` and `Box(320, 250, 32, 12)` follow from the code. The ruff, mypy and "35 passed" results can't be confirmed by reading. QA runs them.

## For QA
- Strict touch on every pair: circle tangent to the bar top, the bar side, the foot side and the foot's outer corner gives False; 1 px further in gives True. Box–box sharing only an edge or only a corner gives False.
- Circle whose center is inside a box gives True (nearest point is the center, distance 0).
- An empty hitbox on either side of `hitboxes_overlap` gives False; `place_hitbox((), x, y)` and `grow_hitbox((), m)` return `()`.
- `place_hitbox` and `grow_hitbox` return new shapes and leave the input tuple unchanged; `grow_hitbox` keeps centers and adds `2 × margin` to a box's w and h.
- `ship_hitbox` of a wall-clamped or top-line ship: the T's outer edges equal the ship's 32 × 32 edges (left edge 0 at the left wall, top edge `TOP_LINE_Y` at the ceiling).
