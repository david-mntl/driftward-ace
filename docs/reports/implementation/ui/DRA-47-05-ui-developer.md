Status: ready-for-review
Created by: ui-developer

1. **Task:** `docs/contracts/DRA-47/tasks/DRA-47-05-ui-developer.md` (architect): draw the entry warning from `warning_copy()`, sized on the copy's width.
2. **Delivered:** `game/ui/drifters/entry_warning.py` (changed: `_build_image` and `_draw_copy`, plus docstrings).
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/drifters/entry_warning.py`: clean.
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy` (the task's command, unchanged). Output:
     ```
     [('copy', 80.0, 0.5, 1.0)] True
     [('small', 20.0, 0.5, 1.0)] True
     ```
   - `game/tests/check.sh lint`: pass (ruff check and format, 51 files).
   - `game/tests/check.sh ui`: 16 passed, 1 failed: `test_drifter_registry.py::test_drifter_lists_match_everywhere` (extra `'chain_lightning'` in core). This is the failure the task allows until DRA-47-06.
   - `game/tests/check.sh typecheck`: fails with 17 errors, all in `tests/core/test_collision.py` and `app/tuning.py` (the new `Line` shape in unions). None in `game/ui/`. Those files are not mine (test and app/core lane).
   - The draw only reads the drifter and writes the surface and the module's image dict. Drifters are not touched.
   - Grep of `entry_warning.py` for sleep, threading, asyncio, display, event, key, image.load, mixer, `random.random(`, mp3, wav: no hits. Grep of `game/core/` for `ui` imports: no hits.
4. **Assumptions:** The cache key stays `(uid, drifter_type, variant, tilt)`, as the contract says. It does not include the copy's width. The copy depends only on the drifter's own fields, which `uid` and `variant` fix. The tilt still comes from the drifter, not from the copy (contract: `obj.warning_tilt_degrees()`).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-47/tasks/DRA-47-05-ui-developer.md`. Left alone: `chain_lightning_view.py` (DRA-47-06, which will fix the registry test), `shapes.py`, and the typecheck errors in `app/tuning.py` and `tests/core/test_collision.py` (owned by the Gameplay Implementer, Integration Engineer and QA).
7. **Status:** done.

## Decisions
- `_build_image` calls `drifter.warning_copy()` once. The copy's width gives `R`; the copy is what the view draws. Source: drifters.md, Presentation, Entry warning (DRA-47).
- `_draw_copy` takes the copy and the tilt as arguments, so the tilt (from the drifter) and the copy (from `warning_copy()`) stay separate. The turn layer is renamed `layer` so it no longer shadows the copy.
- Spikes still use `drifter.uid` as the seed. Contract: `random.Random(obj.uid)`.
- No new constants. Every value is unchanged.
