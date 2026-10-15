Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the object views: the view registry, the shared entry warning and the placeholder meteorite. Task `docs/contracts/DRA-29/tasks/DRA-29-05-ui-developer.md`, from the Architect.
2. **Delivered:**
   - `/workspace/game/ui/objects/__init__.py` (new): package docstring, one import of `ui.objects.meteorite_view`.
   - `/workspace/game/ui/objects/registry.py` (new): `ObjectView`, `register_view`, `registered_views`, `render_object`.
   - `/workspace/game/ui/objects/entry_warning.py` (new): the six constants, `draw_entry_warning`, and `drop_entry_warning` (see Assumptions).
   - `/workspace/game/ui/objects/meteorite_view.py` (new): `METEORITE_COLOR`, `render_meteorite`.
3. **Checks** (from `/workspace/game`):
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile ui/objects/*.py`: clean.
   - `tests/check.sh lint`: PASS (ruff check and format). `tests/check.sh typecheck`: PASS (mypy strict, 37 files). `tests/check.sh ui`: 11 passed.
   - Acceptance command, exact text from the task (run as a script from `game/` with `PYTHONPATH=.`, scratchpad `acc.py`, same body). Output:
     ```
     ['meteorite'] (160.0, 10.0) (140, 140, 140) True 76
     True True True
     (140, 140, 140) 308 0
     ```
     Line 1: warning at the top edge, grey copy (76 px, near 80) on glow. Line 2: all ink in x 150..170, rows 0..20. Line 3: active grey disc of radius 10 (308 px, near 314), no glow.
   - Follows the state: moving the object to x 300 moves the warning (pixel (300, 10) turns grey). ACTIVE draws a disc at (x, y) and no glow. GONE draws nothing (surface all black). A second view for METEORITE raises `ValueError: view for object type 'meteorite' is already registered`.
   - Core untouched: `repr` of the object identical before and after drawing. Two draws of the same state give identical pixels. The warning cache holds 1 entry while WARNING and 0 after the first ACTIVE draw.
   - Grep of `game/ui/objects` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for ui imports: no hits.
   - Screenshots (outside the repo): `/tmp/claude-1000/-workspace/c95abc97-1f22-42a3-a4b4-1aa1c00ef104/scratchpad/warning.png` and `.../active.png`.
   - Only noise: ALSA "cannot find card" lines from `pygame.init()` in the sandbox.
4. **Assumptions:**
   - The contract Interface has no way to drop a cache entry, but `render_object` must drop it on the first ACTIVE frame. I added one public function, `drop_entry_warning(obj)`, in `entry_warning.py`, which `render_object` calls. The cache dict stays private in that module. If the Architect wants the Interface exact, the contract needs this name added.
   - `render_object` looks the view up before it checks the phase, so an unregistered type raises in every phase, GONE included.
   - The spike width 1 is written inline, since the task lists exactly six constants.
   - `ObjectView` is a `type` alias (Python 3.12), used as a plain `Callable` alias by every caller.
   - The app task says it calls `ui.objects.render_object`. The contract keeps `__init__.py` to a docstring and one import, so `render_object` is imported from `ui.objects.registry`.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-29/tasks/DRA-29-05-ui-developer.md`. I left `game/ui/debug_overlay.py` alone (task DRA-29-06) and `game/app/` (Integration Engineer).
7. **Status:** done.

## Decisions
- Circular import: `registry` imports `entry_warning` at runtime, and `entry_warning` needs `ObjectView` only for a type hint. It imports it under `TYPE_CHECKING` with `from __future__ import annotations`. No runtime cycle.
- `ui/objects/__init__.py` mirrors `core/objects/__init__.py`: a docstring and one `import ... as ...` line, no logger. Importing `ui.objects.registry` runs it first, so `meteorite_view` always registers.
- The warning image is built by `_build_image`: glow, spikes, then the object's own view at `ENTRY_WARNING_SCALE` on the image, centered at its middle pixel. The same `view` callable draws the copy, so no skin is named in the warning code.
- Spikes use `math.tau` for the angle range. Order of random calls is count, then angle, then length per spike, as the contract says.
- Blit uses `image.get_rect(center=round(warning_center()))`. For an odd side, the rect center is the middle pixel, so the warning's center lands on the rounded point.
- Sources: constants and their sources are in the docstrings of `entry_warning.py` (07-objects.md entry_warning values, guess; `GLOW_RATIO` is the contract's placeholder choice, see objects.md Rationale) and `meteorite_view.py` (objects/01-meteorite.md, placeholder_look, guess).
- The module-level dicts `_VIEWS` and `_IMAGES` are the registry and the cache the contract asks for. They hold no game state: views and images that depend only on their key.

## Review fix 2026-10-15: docs/reports/review/DRA-29-05-ui-developer.md

1. **Task:** Answer round 1 of the review (findings 1 and 2) for DRA-29-05. Asked by the `/implement` skill.
2. **Delivered:**
   - `/workspace/game/ui/objects/entry_warning.py` (changed): six constants now `Final[...]`, `Final` imported.
   - `/workspace/game/ui/objects/meteorite_view.py` (changed): `METEORITE_COLOR` now `Final[...]`, `Final` imported.
   - This section.
3. **Checks** (from `/workspace/game`):
   - `python -c "import pygame; assert pygame.IS_CE"`: passes. `python -m py_compile ui/objects/*.py`: clean.
   - `ruff check .`: all checks passed. `ruff format --check .`: 40 files already formatted.
   - `tests/check.sh lint`, `typecheck`, `ui`: all PASS.
   - Acceptance draw run (scratchpad `acc.py`, `PYTHONPATH=.`) prints the same three lines as before: `['meteorite'] (160.0, 10.0) (140, 140, 140) True 76`, `True True True`, `(140, 140, 140) 308 0`.
   - Grep of `game/ui/objects` for the banned names: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** `Final` is the right reading of "every module-level constant is `typing.Final`". It satisfies both the rule and the contract's sample lines, so no conflict is raised.
5. **Documentation differences:** Pending Director approval.
   - Document and section: `docs/contracts/systems/objects.md`, Interface, `game/ui/objects/` block.
   - Difference: `game/ui/objects/entry_warning.py:65` has a public function `drop_entry_warning(obj)` that the Interface does not list. The contract needs it: `render_object` must forget the cached warning image when an object turns ACTIVE, and the Interface gives it no other way to reach the cache in `entry_warning`.
   - Proposed change, under `draw_entry_warning`: `def drop_entry_warning(obj: GameObject) -> None: ...  # forget obj's warning image; nothing when it has none. render_object calls it when it draws obj ACTIVE.`
   - For visibility: `docs/contracts/systems/app.md:517` names `ui.objects.render_object`, but `objects.md` keeps `ui/objects/__init__.py` to one import, so the function lives at `ui.objects.registry.render_object`. The Architect should align `app.md`, or the Integration Engineer imports from `ui.objects.registry`.
   - The code stays as it is until the Director decides. I did not edit any doc.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-29-05-ui-developer.md`. The Director decides the contract line above.
7. **Status:** done for the code. The contract line waits for the Director's approval; it changes no code.

### Decisions
- Finding 2: typed the constants `Final[<type>]` rather than claiming a `ui/` exemption. It costs one import and matches the contract's first paragraph.
- Finding 1: no code change, as the review asks. The request moves to item 5.

### Answers
1. Fixed: this section, item 5. The undocumented `drop_entry_warning` is now a Documentation differences request with the proposed contract line, pending the Director's approval. Code unchanged.
2. Fixed: `game/ui/objects/entry_warning.py:24`, `:27`, `:31`, `:34`, `:37`, `:41` and `game/ui/objects/meteorite_view.py:16`, each constant is now annotated `Final[...]`.
