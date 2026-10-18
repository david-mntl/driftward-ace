Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the satellite's placeholder view and register it, task `docs/contracts/DRA-39/tasks/DRA-39-04-ui-developer.md` (Architect).
2. **Delivered:**
   - `game/ui/drifters/satellite_view.py` (new): `SATELLITE_BODY_COLOR`, `SATELLITE_PANEL_COLOR`, `render_satellite`, registered for `DrifterType.SATELLITE`.
   - `game/ui/drifters/__init__.py` (changed): one import line for `satellite_view`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on both files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `game/tests/check.sh ui`: PASS, 17 tests, including the guard test `test_drifter_registry.py` (`game/tuning/drifters/satellite.json` exists).
   - `game/tests/check.sh typecheck`: FAIL, 18 errors, all in `game/tests/core/test_run_drifters.py` and `game/tests/core/test_drifters.py` (the removed `hit_ship` field, an abstract class). None in `game/ui/`. I did not touch tests.
   - Acceptance command from the task, run from `game/` (copied to a scratch file, run with `PYTHONPATH=game`). Output:
     ```
     [(240, 240, 240), (60, 110, 220), (240, 240, 240), (0, 0, 0)]
     [(180, 180, 180), (45, 83, 165)]
     True True
     ```
     All three lines match the task. Warning copy of the angled, inverted satellite sits at the right wall and runs down to the left.
   - Follows the state: moving the satellite to x=300 puts the white body at (300, 50). Drawing the same drifter again leaves `repr(drifter)` identical, so core is untouched. A one-box hitbox raises `TypeError`.
   - Grep of the two files for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `ui` imports: no hits.
   - Screenshot (scratch, not in repo): `/tmp/claude-1000/-workspace/7afa0fd4-0a91-41b9-8ad0-ce7f629d38a8/scratchpad/sat.png`.
4. **Assumptions:** None beyond the contract. Debug-mode run of a crossing satellite is not done: it needs the Integration Engineer to wire DRA-39 in `app` (`docs/contracts/systems/app.md`). I did not check that wiring.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-39/tasks/DRA-39-04-ui-developer.md`. The debug-mode check waits on the Integration Engineer. The 18 typecheck errors in the core tests need the Gameplay Implementer or QA Engineer (outside my lane).
7. **Status:** done.

## Decisions
- Draw order: panel bar first, body on top. Source: contract, Presentation, Satellite.
- Each box is placed by `_placed` (center plus offset times scale, size times scale), then drawn with `ui.shapes.draw_shape`, so the full-size look matches the debug outlines. No offset math elsewhere.
- Colors (240, 240, 240) and (60, 110, 220): contract Interface, drifters/02-satellite.md placeholder_look (guess). Dimmed only through `dim_color`.
- `_two_boxes` raises `TypeError` for anything but two `Box` shapes, as the contract says. It returns body then panel, the order of the tuning file.
- The view reads only `drifter.hitbox`. It never reads `width`, `height`, phase or tilt; the entry warning code handles the tilt.
