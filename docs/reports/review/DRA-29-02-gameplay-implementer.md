Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the implementation report `docs/reports/implementation/gameplay/DRA-29-02-gameplay-implementer.md` (`core/levels.py` and the `core/objects/` package: base, tuning, registry, spawner, meteorite). The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-29-02-gameplay-implementer.md` (this file).
3. **Checks:** I only read the code. I ran nothing.
   - I compared the seven delivered files line by line with `docs/contracts/systems/objects.md` (Interface: `levels.py`, `base.py`, `tuning.py`, `registry.py`, `spawner.py`, `meteorite.py`, `__init__.py`; Rules: Levels, The base, Registry, Spawner, Meteorite, Logging; Rationale), the task's Do list, both schemas in `docs/contracts/schemas/`, `08-difficulty.md`, `06-scoring.md` (graze_margin), `objects/01-meteorite.md`, `01-vision.md`, `game/CONTEXT.md` and `game/ruff.toml`.
   - I traced the acceptance script by hand. `TOP_SIDE_SPEED` = 0.42 × 0.94 / 0.06 = 6.58; × 0.75 = 4.935. Default y −28 / 2 = −14. 29 updates give `ticks_in_phase` 29 in WARNING; the 30th gives 30 ≥ 30, so ACTIVE with 0 at y −14 and one placed circle. One more update: −14 + 4.935 = −9.065, x 320. Level 8: 4.935 × 1.42 = 7.0077, rounds to 7.008. `'huge'` hits the unknown-variant message. All seven claimed lines follow from the code.
   - Reading for bans: no pygame, `ui` or `app` import, no randomness, frame time, sleep, thread, `await`, `print` or log call in any of the seven files.
4. **Assumptions:** "35 passed", ruff and mypy results can't be confirmed by reading; QA runs them. I took the PEP 695 type parameters as equivalent to the contract's `TypeVar` form, as the implementer's Decisions say.
5. **Documentation differences:** One contract break in the code, finding 1: `spawn_object` treats an empty-string `Placement.variant` as unset, where `docs/contracts/systems/objects.md`, Rules, Spawner, step 2 uses the default variant only "when None". I propose no document change; the code should follow the contract.
6. **Next:** Gameplay Implementer, Review fix mode, on this file. Open: 1 must-fix, 1 should-fix, 3 notes.
7. **Status:** done.

## Findings
1. **must-fix** `game/core/objects/spawner.py:59`: `variant_name = placement.variant or type_tuning.default_variant` falls back to the default variant for `variant=""` too. The contract uses the default only when the variant is None; any other name not in the tuning raises `unknown variant '<name>' for object type '<type>'`. `""` can never be a variant name (schema pattern `^[a-z][a-z0-9_]*$`), so a placement that sends it is a mistake, and the code hides it. The implementer listed this as Assumption 4, but the contract does answer it. Rule: spawner step 2, and never fall back to a default on bad input. Source: `docs/contracts/systems/objects.md`, Rules, Spawner, step 2 and Rationale ("Silently ignoring it would hide a wave mistake"); `docs/contracts/schemas/object-tuning.schema.json`, `variant_name`; `game/CONTEXT.md`, Error handling. Change: `type_tuning.default_variant if placement.variant is None else placement.variant`, the same `is None` form as lines 63 and 67, and drop Assumption 4 from the report.
2. **should-fix** `game/core/objects/base.py:30`: `METEORITE = "meteorite"` has no member doc. The contract's Interface gives it the source `# objects/01-meteorite.md` and asks the code to document each field with its comment. The `Phase` and `TouchEffect` members in the same file are documented. Rule: the code documents each field with the contract's comment. Source: `docs/contracts/systems/objects.md`, Interface, `base.py` block and the paragraph after it. Change: add a one-line docstring under the member naming `objects/01-meteorite.md`.
3. **note** `game/core/objects/registry.py:17`, `game/core/objects/base.py:246`: `register_object` and `tick_warning` use PEP 695 type parameters instead of the contract's `TypeVar`. The bound and the signatures are the same, and the implementer's Decisions explain why (ruff UP047, target py312). The report's Documentation differences says "None" while this is a wording difference from the contract text. Rule: Interface matches exactly. Source: `docs/contracts/systems/objects.md`, Interface, `registry.py` and `base.py` blocks. Change: none. The Architect may update the two comments at close-out.
4. **note** `game/core/objects/spawner.py:21`: `BASE_LEVEL: Final[int] = 1` is a public module name the Interface doesn't list. It names "Level 1 values" from 08-difficulty.md, rule 5, so the number traces, and the Decisions explain it. Rule: no added name beyond the Interface. Source: `docs/contracts/systems/objects.md`, Interface, `spawner.py` block. Change: none.
5. **note** `game/core/levels.py:50`: `level_at` returns at least 1 for negative meters, and counting starts ≤ meters gives the highest level only while `LEVEL_STARTS_M` is ascending. Meters never go below 0 and the table's starts rise by level, so neither case can happen today. Rule: the highest level whose start is ≤ meters. Source: `08-difficulty.md`, rule 1; `docs/contracts/systems/objects.md`, Rules, Levels. Change: none.

## Checklist
1. Interface matches exactly: **finding** (2, 3, 4). Every name, field, default, parameter and return in the seven Interface blocks is present and matches. `GameObject` and `Specialty` are `frozen, slots, kw_only` and inherit `ABC` (`base.py:102-119`); `TickContext`, `Birth`, `Placement` are frozen and slotted; the tuning records are frozen, slotted, `kw_only`, both switches default True (`tuning.py:53-57`). `Meteorite` adds no field (`meteorite.py:18-21`). `__init__.py` holds a docstring and one import.
2. UI/core split: **pass**. Imports are stdlib, `core.collision`, `core.ship`, `core.world`, `core.levels` and `core.objects.*` only.
3. Fixed 60 Hz tick: **pass**. The warning counts ticks (`base.py:252-255`); the meteorite moves by `speed` per update (`meteorite.py:33`).
4. Randomness: **pass**. None. The registry dict decides no outcome; `available_objects` returns a frozenset.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio or path.
6. Numbers trace: **finding** (1). Level rows match `08-difficulty.md` exactly (`levels.py:13-22`); `GRAZE_MARGIN` 14 is `06-scoring.md`, locked; speed and sizes come from tuning and `TOP_SIDE_SPEED`. The empty-string fallback at `spawner.py:59` is a fallback default.
7. Pillars and locked decisions: **pass**. An object has no hitbox until its warning has shown `warning_ticks` states (`base.py:169-170`, `253`). The meteorite falls straight down with x unchanged. No weapon, wall or ship-control code is touched.
8. Smells: **pass**. Short functions, nesting depth 1, no duplicated blocks, no dead code, full type hints. The one module-level state, `_CLASSES` (`registry.py:13`), is the registry the contract requires, private and written only by `register_object`.
9. Decisions: **pass**. All eight match the code, including switches beating `as_level` after `check_level` (`spawner.py:63-66`), unscaled entry warnings (`spawner.py:77`), `update` returning `self` in GONE (`meteorite.py:34`) and no zero-argument `super()`.
10. Report claims match the files: **pass**. The acceptance output, the registry error messages and `level 9 is outside 1 to 8` follow from the code. Assumption 4 is covered by finding 1.

## For QA
- `spawn_object` with `variant=""`: after the fix it raises `unknown variant '' for object type 'meteorite'`.
- `hazard_speed_scaling` False with `as_level=8` gives speed 4.935; `as_level=9` or run level 0 still raises `level 9 is outside 1 to 8` (or 0) with either switch off.
- `specialty_enabled=True` raises `meteorite has no specialty`; False and None spawn normally.
- `entry_warning_ticks` 1: one WARNING state, then ACTIVE on the first update. A medium meteorite is first off screen at ACTIVE tick 103 (y ≈ 494.3), never at the top.
- `warning_center` for a medium at x 5, y −14 gives (14, 14); importing only `core.objects.spawner` already lists `meteorite` in `available_objects()`.

## Re-check 2026-10-15
1. **Task:** Re-check the answers to findings 1 and 2 in the `## Review fix 2026-10-15` section of `docs/reports/implementation/gameplay/DRA-29-02-gameplay-implementer.md`. The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-29-02-gameplay-implementer.md` (line 1 and this section).
3. **Checks:** I only read the code. I ran nothing. I read `game/core/objects/spawner.py:48-83` and `game/core/objects/base.py:27-31`, the two places the fix names, against `docs/contracts/systems/objects.md`, Rules, Spawner, step 2 and the `base.py` Interface block. With `variant=""`, line 60 keeps `""`, `variants.get("")` is None, and line 64 raises `unknown variant '' for object type 'meteorite'`. With `variant=None` the default variant is used as before, so the acceptance trace is unchanged. The fix moved the later lines down by two; the `as_level` and `y` lines are now 65 and 69. No new problem found.
4. **Assumptions:** The lint, typecheck and smoke results in the fix section can't be confirmed by reading; QA runs them.
5. **Documentation differences:** None. The contract break in finding 1 is closed.
6. **Next:** QA Engineer, on `docs/reports/implementation/gameplay/DRA-29-02-gameplay-implementer.md`. Open: 0 must-fix, 0 should-fix, 3 notes (3, 4, 5; each asks for no change).
7. **Status:** done.

1. closed. `game/core/objects/spawner.py:59-61` uses `type_tuning.default_variant if placement.variant is None else placement.variant`; `""` now reaches the unknown-variant error. Assumption 4 is withdrawn in the fix section.
2. closed. `game/core/objects/base.py:31` adds `"""Source: objects/01-meteorite.md."""` under `METEORITE`.
