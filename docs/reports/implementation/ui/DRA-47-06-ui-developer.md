Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the chain lightning view and register it (`docs/contracts/DRA-47/tasks/DRA-47-06-ui-developer.md`, Architect).
2. **Delivered:**
   - `game/ui/drifters/chain_lightning_view.py` (new): `render_chain_lightning`, `CHAIN_NODE_COLOR`, `CHAIN_RAY_COLOR`, `CHAIN_ARC_COLOR`, `FIRST_RAY_DEGREES`.
   - `game/ui/drifters/__init__.py`: one import line for the new view.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on both files: clean.
   - `game/tests/check.sh lint`: pass (ruff check and format). `check.sh ui`: pass, 17 passed, including `test_drifter_registry.py`.
   - `check.sh typecheck`: 17 errors, all in `app/tuning.py` and `tests/core/test_collision.py` (`Line` read as a box). Those are files the drifters.md Impact lists for later tasks. None in `game/ui/`.
   - Acceptance command, run from `game/` (copied from the task, `SDL_VIDEODRIVER=dummy`). Output:
     ```
     (0, 220, 255) (0, 0, 0) True False
     True True
     (220, 240, 255) (0, 0, 0) False
     (165, 180, 191) (0, 165, 191)
     ```
     It matches the four expected lines.
   - Follows the state and leaves core alone: the draw run changes `ticks_in_phase` and `rehit_ticks_left` and the picture changes as the contract says. At scale 0.5 the node is at 3 px radius (pixel (68, 100) cyan, (68, 103) black). `repr(chain)` is identical before and after a draw. A non-chain drifter raises `TypeError("render_chain_lightning draws a ChainLightning")`.
   - Grep of the two files for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `game.ui` / `ui` imports: no hits.
4. **Assumptions:** The contract's Interface names the parameter `obj`. The `DrifterView` type and the other views use `drifter`, so I used `drifter` to match the registry. Registration is positional, so nothing breaks. I added `FULL_TURN_DEGREES` (360.0) as a named constant rather than a magic number.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-47/tasks/DRA-47-06-ui-developer.md`. Left alone: `game/ui/shapes.py`, `game/ui/drifters/entry_warning.py`, `game/ui/debug_overlay.py`, `game/app/tuning.py` and the tests with the typecheck errors.
7. **Status:** done.

## Decisions
- Draw order: bands, then nodes, then rays. The nodes cover the band ends and the rays sit on top. Source: contract, Presentation, Chain lightning.
- Placed node positions are worked out once per call from `drifter.nodes` and `center` (offsets times `scale`), then shared by the three draw helpers. No position is stored.
- The view reads `firing_arcs()` and `charge_ray_count()` from core. It computes no timer or rule.
- Bands use `ui.shapes.draw_shape` with a `Line` of thickness `arc_width * scale`. Nodes use `pygame.draw.circle` and rays `pygame.draw.line`, as the contract says.
- Colors are the three contract constants (GDD placeholder_look, guess), all dimmed through `dim_color`. Ray angles start at `FIRST_RAY_DEGREES` (GDD ray_length, guess) and spread evenly over `charge_rays`. The ray and node sizes come from the chain's fields, which come from the tuning file.
- Hitbox shapes are not read. The bands come from `arcs` and `nodes`, so the warning copy (WARNING phase: no band, no ray) draws as nodes only with no extra code.
