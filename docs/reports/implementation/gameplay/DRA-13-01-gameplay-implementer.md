Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the world scroll and distance counter, and reword two stale docstrings, from `docs/contracts/DRA-13/tasks/DRA-13-01-gameplay-implementer.md` (Architect), against `docs/contracts/DRA-13/DRA-13-scroll.md`.
2. **Delivered:**
   - `game/core/scroll.py` (new): six constants, frozen `Scroll` with `distance_px` and `meters`, `start_scroll()`, `step_scroll()`. Logger `core.scroll`. Stdlib only.
   - `game/core/ship.py`: docstrings only (module docstring, `_stop_at_top_line`). Top line is a ceiling; floor respawn still marked TEMPORARY.
   - `game/core/world.py`: module docstring only (no camera, fixed screen, screen px).
3. **Checks:** all from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: pass (pygame-ce 2.5.8).
   - `python -m py_compile core/scroll.py core/ship.py core/world.py`: clean.
   - `tests/check.sh lint`: pass. `tests/check.sh core`: pass, 9 tests (existing ship tests). No `noqa`.
   - Acceptance check:
     `python -c "from core.scroll import start_scroll, step_scroll; s = start_scroll(); [s := step_scroll(s) for _ in range(30)]; print(s.distance_px, s.meters); [s := step_scroll(s) for _ in range(100)]; print(round(s.distance_px, 2), s.meters)"`
     Output: `0.0 0` then `110.0 11`.
   - Log and determinism: 40 ticks with DEBUG on, run twice. Both print one line `core.scroll scroll start tick=31` and `Scroll(ticks=40, scrolled_ticks=10) 1`. Identical.
   - Grep of `game/core/` for sleep, threading, asyncio, pygame.display/event/key, random.random(, .mp3, .wav: no hits.
4. **Assumptions:** None beyond the contract.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-13/tasks/DRA-13-01-gameplay-implementer.md`. Left alone: `game/app/` (Integration Engineer wires `start_scroll`/`step_scroll`), tests.
7. **Status:** done.

## Decisions
- No update-order choice: the step is two counters, no physics.
- `ticks <= SCROLL_START_DELAY` returns early, so the log sits only on the moving branch and fires when `scrolled_ticks == 1` (tick 31).
- `SCROLL_PER_TICK` is computed from `SCROLL_BASE * LEVEL_1_SCROLL_MULT`, never a bare 1.1.
- Sources: `SCROLL_BASE` and `SCROLL_START_DELAY` are guess values (03-world-and-camera.md). The multiplier, `DISTANCE_START` and `PX_PER_METER` are locked.
- Distance is `scrolled_ticks * SCROLL_PER_TICK`, one multiplication, so meter boundaries stay exact (contract Rationale).
