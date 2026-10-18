Status: ready-for-review
Created by: ui-developer

1. **Task:** build the fireball view and register it (`docs/contracts/DRA-56/tasks/DRA-56-02-ui-developer.md`, from the Architect).
2. **Delivered:**
   - `game/ui/drifters/fireball_view.py` (new): `FIREBALL_HEAD_COLOR`, `FIREBALL_TAIL_COLOR`, `render_fireball`.
   - `game/ui/drifters/__init__.py` (changed): one import line for `fireball_view`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile` on both files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `typecheck`: PASS (mypy strict, 53 files).
   - `game/tests/check.sh ui`: 34 passed, 1 failed: `test_drifter_registry.py::test_drifter_lists_match_everywhere`, as the task expects until `game/tuning/drifters/fireball.json` exists (the diff names `fireball` as the extra item).
   - Acceptance command, the task's script run from `game/` (saved as a file in the scratchpad and run with `PYTHONPATH=.`, same code):
     ```
     True
     (255, 140, 0) (200, 160, 0) (0, 0, 0)
     (191, 105, 0) (150, 120, 0)
     (200, 160, 0) (0, 0, 0)
     True True
     False True
     ```
     All six lines match the task.
   - Follows the state: moving the fireball 40 px in core moved the head pixel (100,100 became black, 140,100 orange). `repr` of the drifter is identical before and after a draw. Two draws of the same state give identical bytes.
   - Screenshot: `/tmp/claude-1000/-workspace/6d0200a8-6d16-44cc-a909-cf947d64e667/scratchpad/fireball.png`.
   - Grep of the two files for sleep, threading, asyncio, display, event, key, image.load, mixer, `random.random(`, .mp3, .wav: no hits. Grep of `game/core/` for `ui` imports: no hits.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-56/tasks/DRA-56-02-ui-developer.md`. Left alone: `entry_warning.py`, `registry.py`, `shapes.py`, the debug overlay (out of scope). `game/tuning/drifters/fireball.json` is still missing, so the registry guard test fails until it exists.
7. **Status:** done.

## Decisions
- Same shape as `satellite_view.py`: a private `_two_circles` check (raises the contract's TypeError text) and a `_placed` helper that scales the offsets and moves them to `center`, so the full-size look sits on the debug outlines.
- Draw order: tail first, head on top. Source: contract, Presentation, Fireball.
- Both colors go through `dim_color` with `brightness`, so the head and tail dim together in the re-hit cooldown.
- Colors (255, 140, 0) and (200, 160, 0): drifters/06-fireball.md, placeholder_look (guess), named as constants by the contract.
- The warning copy and its tilt need no code here: the view draws whatever `warning_copy().hitbox` holds, and `entry_warning.py` turns it.
