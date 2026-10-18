Status: ready-for-review
Created by: ui-developer

1. **Task:** `docs/contracts/DRA-39/tasks/DRA-39-02-ui-developer.md`, from the Architect: add brightness to drifter views, `dim_color`, the tilted entry-warning copy and the meteorite dim.
2. **Delivered:**
   - `game/ui/drifters/registry.py`: `DrifterView` takes `brightness`; new `dim_color`; `render_drifter` passes `drifter.brightness()` in ACTIVE.
   - `game/ui/drifters/entry_warning.py`: cache key gains `warning_tilt_degrees()`; new `_draw_copy` turns the copy when the tilt is not 0; the copy is always drawn at brightness 1.0.
   - `game/ui/drifters/meteorite_view.py`: `render_meteorite` takes `brightness` and draws in `dim_color(METEORITE_COLOR, brightness)`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `py_compile` on `game/ui/drifters/*.py`: clean.
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy` (the command is in the task file, run verbatim). Output:
     ```
     (140, 140, 140)
     (105, 105, 105)
     (45, 83, 165)
     True
     ```
   - `game/tests/check.sh lint`: pass (ruff check, ruff format, 47 files).
   - `game/tests/check.sh ui`: pass, 17 passed.
   - `game/tests/check.sh typecheck`: 18 errors, all in `tests/core/test_run_drifters.py` and `tests/core/test_drifters.py` (`hit_ship`, `type-abstract`), the test files the drifters.md Impact names. None in `game/ui/` or `game/core/`.
   - Grep of `game/ui/` for sleep, threading, asyncio, display, event, key, image.load, mixer, `random.random(`, .mp3, .wav: no hits. Grep of `game/core/` for imports of `ui`: no hits.
   - The views read core state and write none. The ship-state and moved-state checks (5) are covered by the dim run above: the same rock with `rehit_ticks_left=5` draws (105, 105, 105) instead of (140, 140, 140).
4. **Assumptions:** The tilt-0 path draws straight on the image as before, so existing warning images are unchanged. A turned copy is rotated about the image's middle pixel, which is the surface center, since the image side is odd.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-39/tasks/DRA-39-02-ui-developer.md`. Left alone: `game/ui/shapes.py`, `game/ui/debug_overlay.py`, the satellite view (DRA-39-04), and the failing core test files (QA owns them).
7. **Status:** done.

## Decisions
- `dim_color` lives in `registry.py`, as the contract's Interface places it. `meteorite_view.py` imports it from there. `entry_warning.py` still imports `DrifterView` only under `TYPE_CHECKING`, so there is no import cycle.
- `dim_color` uses `math.floor(channel * brightness + 0.5)`, the contract's half-up rule.
- The warning copy always uses brightness 1.0: a drifter still warning has never hit. Source: drifters.md, Presentation, Brightness.
- The tilt joins the cache key as a float, as drifters.md, Pre-rendered says. The turned copy is drawn on its own SRCALPHA surface first, so rotating never moves the glow or spikes. Sign: `pygame.transform.rotate` takes degrees counterclockwise, matching `warning_tilt_degrees()`.
- Numbers and colors are unchanged: every constant is still the one drifters.md gives on its line.
