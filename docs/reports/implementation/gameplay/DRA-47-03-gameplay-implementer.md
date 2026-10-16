Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-47/tasks/DRA-47-03-gameplay-implementer.md`, from the Architect: the chain lightning drifter, its `DrifterType` member and its registration.
2. **Delivered:**
   - `game/core/drifters/chain_lightning.py` (new): `InvertMirror`, `ChainLayout`, `ChainLightningVariantExtra`, `ChainLightningTypeExtra`, `mirrored_nodes`, `layout_size`, `chain_hitbox`, `ChainLightning`.
   - `game/core/drifters/base.py` (changed): `DrifterType.CHAIN_LIGHTNING`.
   - `game/core/drifters/__init__.py` (changed): imports `chain_lightning`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: ok (pygame-ce 2.5.8). `py_compile` clean on the three files.
   - `ruff check game`, `ruff format --check game`, `game/tests/check.sh lint`: pass.
   - Acceptance smoke, from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <the task's command>` (the command saved to a scratch file outside the repo, content identical). Output, six lines as the task expects, run twice, identical:
     ```
     ['chain_lightning', 'meteorite', 'satellite']
     pair_flat -6.0 140.0 12.0 (256.0, 70.0) 140.0 ()
     [(60, -6, False, 1, (), 0), (90, 68, False, 2, (), 0), (120, 142, False, 3, (), 0), (150, 216, False, 4, (), 0), (179, 288, False, 4, (), 0), (180, 290, True, 0, (0,), 3), (259, 485, True, 0, (0,), 3)]
     True
     [(-64.0, -55.43), (0.0, 55.43), (64.0, -55.43)] 84 120 3.5
     chain_lightning placement needs x
     ```
   - `game/tests/check.sh core --ignore=tests/core/test_collision.py`: 78 passed. `check.sh core -k "not collision"` does NOT pass, see Next.
   - `check.sh typecheck`: 18 errors, all in files DRA-47-01 already lists: `app/tuning.py` (4), `ui/shapes.py` (1), `tests/core/test_collision.py` (13). None in `core/`.
   - `check.sh ui`: 1 failure, `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no view or tuning loader yet), as the task expects.
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no code hit.
4. **Assumptions:** `current_hitbox()` picks its shapes from `self.hitbox` (arc `i` is index `i`, node `n` is index `len(arcs) + n`, the order `chain_hitbox` builds), rather than rebuilding them. A chain built by `born` always has that layout. `warning_copy()` and `warning_center()` fall back to the chain itself when `warning_layout` is None (a chain not built by `born`).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-47/tasks/DRA-47-03-gameplay-implementer.md`.
   - The task says `core -k "not collision"` passes. It does not, and not because of this code: adding the `CHAIN_LIGHTNING` member makes `tests/core/test_collision.py` (`load_variant_cases`, line ~383) read `game/tuning/drifters/chain_lightning.json` and fail on `raw["hitbox"]` at collection (the chain lightning file has no per-variant hitbox). The whole module errors, so pytest stops with "1 error". Test task DRA-47-07 (QA Engineer) owns that branch. The rest of core passes (78) with that file ignored. I left the test alone.
   - Left alone: `app/tuning.py`, `ui/`, `tests/`, the tuning data file.
7. **Status:** done.

## Decisions
- Update order: the meteorite's. WARNING counts down with `tick_warning`; ACTIVE does `y += speed` then `ticks_in_phase + 1`. `ctx` is never read.
- Cycle: `ticks_in_phase % (charge_ticks + fire_ticks)` is the only state; no second counter. Ray count is `1 + cycle_tick * charge_rays // charge_ticks`, integer math. Source: contract, Rules, Cycle and Charge rays.
- `born` recomputes the hitbox from the mirrored nodes with `chain_hitbox` (the spawner's `birth.hitbox` is the un-inverted one). `width` and `height` stay as born: mirroring keeps the box. `charge_ticks` uses `scale_telegraph`; `fire_ticks` is never scaled. Every value comes from `Birth`; no number is in the module.
- On-screen test per node is the strict square test, like `is_partly_on_screen`. An arc fires only while both its nodes pass it. The hitbox holds the firing lines, then the circles of nodes that end a firing arc, in node order.
- `settle_warning`: `min` over (squared distance, node x, index), so ties go to the smaller x, then the lower index. Source: contract, Warning node.
- `warning_center`: radius is half the warning copy's width; both axes clamp by that radius around the settled node's center (or the chain's own center before settling). `warning_copy` is `replace(self, nodes, arcs, width, height, hitbox)` in the warning layout; it is computed on each call (a few arithmetic ops), nothing cached, so the drifter stays plain frozen state.
- `Point` and `ArcNodes` are PEP 695 `type` aliases, as the contract writes them. No `Final` constants were needed: the module holds no module-level values.
- Registration: the class is registered by `@register_drifter`; `__init__` imports the module so it registers with the package.
