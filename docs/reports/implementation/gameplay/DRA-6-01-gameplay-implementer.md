Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the ship's state, its one-tick step and the screen geometry, from `docs/contracts/DRA-6/tasks/DRA-6-01-gameplay-implementer.md` (Architect), against `docs/contracts/DRA-6/DRA-6-ship.md` and `docs/contracts/DRA-6/DRA-6-world.md`.
2. **Delivered:**
   - `game/core/world.py`: `SCREEN_W`, `SCREEN_H`, `TOP_LINE_RATIO`, `TOP_LINE_Y`. Constants only, no imports, no logger.
   - `game/core/ship.py`: the ten constants, `Wall`, `Thrust`, `Ship`, `spawn() -> Ship`, `step(ship, thrust) -> Ship`. Logger `core.ship`.
3. **Checks:** all run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: pass, pygame-ce 2.5.8.
   - `python -m py_compile core/world.py core/ship.py`: clean.
   - `game/tests/check.sh lint` (ruff check + ruff format --check): `QA: pass`. No `noqa`, `ruff.toml` untouched.
   - Acceptance check:
     ```
     python -c "from core.ship import spawn, step, Thrust; s = spawn(); [s := step(s, Thrust(up=True)) for _ in range(300)]; print(s.y, s.vy)"
     ```
     Output: `184.0 0.0`. Top edge 184 - 16 = 168 = `TOP_LINE_Y`.
   - Smoke run, headless, with DEBUG logging switched on in the command only:
     ```
     SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "
     import logging, sys; logging.basicConfig(level=logging.DEBUG, format='%(name)s %(message)s', stream=sys.stdout)
     from core.ship import spawn, step, Thrust, Ship
     s = spawn()
     for _ in range(60): s = step(s, Thrust())
     print('60 no input:', s)
     s = spawn()
     for _ in range(400): s = step(s, Thrust(right=True, up=True))
     print('400 right+up:', s)
     s = Ship(x=10.0, y=491.0, vx=-3.0, vy=5.5); print('wall+floor:', step(s, Thrust()), 'input:', s)
     print('all keys:', step(spawn(), Thrust(True, True, True, True)))"
     ```
     Results:
     - 60 ticks, no input: y 240 to 478.2, vy held at `FALL_CAP` 5.5, x 320, no log line. The ship fell.
     - 400 ticks Right+Up: one `top line stop x=383.21 y=184.00`, then one `wall hit side=right x=624.00 y=184.00`, nothing after. Ends at (624.0, 184.0), vx 0, vy 0, `wall='right'`, `at_top_line=True`. Contact logs once, not per tick.
     - Wall and floor in one tick: `wall hit side=left x=16.00 y=496.50`, then `respawn from x=16.00 y=496.50`. Returns (320.0, 240.0) at rest. The input ship is unchanged.
     - All four keys: vx 0.0, vy 0.16 (gravity only). Opposite keys cancel.
     - Separate run, not in the command above: 200 ticks Down gave three `respawn from x=320.00 y=497.10` lines, one per fall.
   - Determinism: the smoke run twice, outputs compared with `cmp`: identical. No randomness or clock in `step`.
   - Grep `game/core/` for `time.sleep|threading|asyncio|pygame|random|.mp3|.wav|print(|except`: one hit, the module docstring of `ship.py` saying it never reads randomness. No code hit.
4. **Assumptions:**
   - Logging uses the ship after the clamps and before the respawn reset (`moved` in `step`). The contract says "the returned ship" for the wall line, but also says a wall hit and a respawn in one tick log both lines, wall first. The returned ship after a respawn has `wall=None`, so only the pre-reset ship satisfies both sentences.
   - Imports are `from core.world import ...`, the same top-level package style `app/` uses (`from app.settings import ...`). `logging.getLogger(__name__)` then names the logger `core.ship`.
   - All physics values are `guess` in the GDD (04-ship.md, 03-world-and-camera.md). Only `fall_respawn` and `top_line_ratio` are locked.
5. **Documentation differences:** None.
6. **Next:**
   - Implementation Reviewer: review `game/core/world.py` and `game/core/ship.py` against task `docs/contracts/DRA-6/tasks/DRA-6-01-gameplay-implementer.md`.
   - Left alone on purpose: `game/app/settings.py` still has `SCREEN_SIZE = (640, 480)`. The world contract's Rationale moves screen size to `core/world.py`, with the app change listed under Impact in the DRA-5 contract. That change is in `game/app/`, which is the Integration Engineer's. `game/core/.gitkeep` is kept (no deletes).
7. **Status:** done.

## Decisions
- **Update order:** the contract fixes it (04-ship.md, rule 2): thrust, gravity, drag, fall cap, move, walls, top line, floor. `step` follows it as written.
- **Structure:** `step` composes four small private pure helpers (`_accelerate`, `_clamp_to_walls`, `_stop_at_top_line`, `_is_below_floor`) and one log helper. The public Interface is exactly the contract's. No pattern beyond that; a state machine or strategy would add nothing for one ship with one behavior.
- **Thrust applied literally:** left subtracts, right adds, up subtracts, down adds, each as its own `if`, in the contract's order. Opposite keys cancel through that, not through a `right - left` sum, so the float results match the contract's arithmetic step for step.
- **Plain floats, no pygame:** the agent standards ask for `pygame.Vector2` and `FRect`, but the contract and task forbid importing pygame in `core/ship.py`. The contract wins. `Ship` holds `x`, `y`, `vx`, `vy` floats, so there is no int truncation.
- **Constant annotations:** written as the contract gives them (`SHIP_W: int = 32`), not `Final[int]`, to match the Interface exactly and the style of `app/settings.py`. Each has a docstring with its GDD source.
- **Walls:** left edge below 0 sets x to `SHIP_W / 2`; right edge past `SCREEN_W` sets x to `SCREEN_W - SHIP_W / 2`; vx = 0; no bounce. Source: 03-world-and-camera.md, rule 6; 01-vision.md, locked decision 3.
- **Top line (TEMPORARY, DRA-6):** triggers only on `y - SHIP_H / 2 < TOP_LINE_Y`, so a ship resting on the line isn't re-clamped. Marked temporary in its docstring. Source: scope report DRA-6, Limits.
- **Floor (TEMPORARY, DRA-6):** `y - SHIP_H / 2 >= SCREEN_H` returns `spawn()`. Marked temporary in its docstring. Source: scope report DRA-6, Limits; 05-lives-and-damage.md, fall_respawn.
- **`TOP_LINE_Y`:** `round(SCREEN_H * TOP_LINE_RATIO)`, never a bare 168. Source: DRA-6-world.md, Rules.
- **Numbers:** every value comes from the contract's Interface lines, each matching its GDD row: 04-ship.md Values (ship_w, ship_h, gravity, thrust_side, thrust_up, thrust_down, drag_x, fall_cap); 03-world-and-camera.md Values (screen_w, screen_h, top_line_ratio, ship_start); 05-lives-and-damage.md (fall_respawn). No tuning file exists yet; the contract keeps these in `core/ship.py` for DRA-6.
