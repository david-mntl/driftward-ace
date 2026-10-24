Status: ready-for-review
Created by: ui-developer

1. **Task:** build the planet's view and register it (`docs/contracts/DRA-96/tasks/DRA-96-04-ui-developer.md`, from the Architect).
2. **Delivered:**
   - `game/ui/drifters/planet_view.py` (new): `render_planet`, `PLANET_BODY_COLOR`, `PLANET_RING_COLOR`, `PLANET_RING_WIDTH`.
   - `game/ui/drifters/__init__.py`: one import line for `planet_view`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on both files: clean.
   - `ruff check .` and `ruff format --check .` from `game/`: no findings. `game/tests/check.sh lint`: PASS. `game/tests/check.sh typecheck`: PASS (75 files, no issues).
   - Acceptance command, run from `game/` exactly as in the task. Output:
     ```
     (140, 70, 200) (140, 70, 200)
     True
     True True
     (0, 0, 0) (0, 0, 0)
     (105, 53, 150) True
     (140, 70, 200) True False
     ```
     All six lines match the task's expected values.
   - Follows the state: moved the planet to y 340 and ticks_in_phase 30, the picture differs from the first. Same state drawn twice gives the same bytes. The drifter's `repr` is identical before and after drawing. One alpha layer built across all draws. A WARNING planet draws a visible copy through `render_drifter`. Screenshot: `/tmp/claude-1000/-workspace/8a87910c-7f35-495d-8e08-03bd44ecf117/scratchpad/planet.png`.
   - Grep of `game/ui/drifters/planet_view.py` and `__init__.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** "scale 1.0" is read as `scale >= 1.0` for the ring and field (the contract says "below 1.0" is body only). The module-level `_LAYERS` dict is the cache the contract asks for (same pattern as the island view's `_IMAGES`). Overlapping inner rings overwrite each other on the layer instead of blending (the contract's layer method); at the file's values they never share a pixel.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-96/tasks/DRA-96-04-ui-developer.md`. Left alone: `registry.py`, `entry_warning.py`, other views, `shapes.py`, `debug_overlay.py`. Typecheck passes now, so the planet tuning file and the registry guard are already in place.
7. **Status:** done.

## Decisions
- Draw order outer ring, inner rings (one blit), body last. Source: contract, Presentation, Planet.
- The view never works out a ring: radius and opacity come from `Planet.inner_rings()`. Alpha is `floor(255 * opacity + 0.5)`; alpha 0 is skipped.
- The alpha layer is keyed by side `2 * (round(pull_radius) + 1) + 1`, built once, cleared each frame, blitted once. Source: contract, Planet, Inner rings; Rationale (DRA-96).
- Colors: (140, 70, 200) body, (180, 120, 255) rings, 1 px width. Source: drifters/08-planet.md placeholder_look (guess), through the contract's constants. All go through `dim_color`, so the field dims with the body.
- Center is rounded once, then every circle uses it. No camera: drifter views take a screen center.

## Review fix 2026-10-22: docs/reports/review/DRA-96-04-ui-developer.md
Fixed: DRA-96-04-F1

1. **Task:** answer review round 1 of DRA-96-04 (one should-fix, a report gap).
2. **Delivered:** this section only. No code changed.
3. **Checks:** run from `/workspace/game` on 2026-10-22.
   - Acceptance command: the command block under "Acceptance check" in `docs/contracts/DRA-96/tasks/DRA-96-04-ui-developer.md`, run as written (`SDL_VIDEODRIVER=dummy python -c "..."`, `from dataclasses import replace` through the last `print`). Output:
     ```
     (140, 70, 200) (140, 70, 200)
     True
     True True
     (0, 0, 0) (0, 0, 0)
     (105, 53, 150) True
     (140, 70, 200) True False
     ```
     All six lines match the task's expected values.
   - `game/tests/check.sh lint`: PASS (ruff check and format, 79 files). `typecheck`: PASS (75 files, no issues).
   - `game/tests/check.sh ui`: PASS, 46 passed. This includes `tests/ui/test_drifter_registry.py` (2 passed), so the planet view registers and `planet.json` loads.
   - `game/tests/check.sh core`: FAIL. One collection error: `tests/core/test_collision.py:1676`, `load_variant_cases` raises `KeyError: 'hitbox'` reading `planet.json`. This matches the DRA-96 Impact row in `docs/contracts/systems/drifters.md:1808` for `game/tests/core/test_collision.py` ("reads `raw["hitbox"]` ... which has neither (an error at collection)"), fixed by task `DRA-96-06-qa-engineer`. No other core failure shown, since collection stops there.
   - Re-ran `ruff`, `py_compile` and the grep checks: unchanged, no hits.
4. **Assumptions:** the earlier line "typecheck passes now, so the planet tuning file and the registry guard are already in place" was an inference. The `ui` result above is the proof for the registry guard and the tuning file. Correction to the first report's Next.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-96-04-ui-developer.md`. Left alone: DRA-96-04-F2 (note, change none).
7. **Status:** done.

## Decisions
- Reported the failing `core` check with its Impact-table row instead of hiding it, as the task's acceptance text allows only expected failures.

## Answers
- DRA-96-04-F1. Fixed: docs/reports/implementation/ui/DRA-96-04-ui-developer.md (this section), acceptance command, output, and `check.sh core` and `ui` results added; the core failure is named and matched to the Impact row at `docs/contracts/systems/drifters.md:1808` (task DRA-96-06).
