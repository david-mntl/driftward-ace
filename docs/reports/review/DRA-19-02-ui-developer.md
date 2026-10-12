Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-19-02 (UI Developer): the debug overlay shows `0.00`, never `-0.00`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-19-02-ui-developer.md` (this file). Reviewed: `game/ui/debug_overlay.py`.
3. **Checks:** Read by hand against `docs/contracts/DRA-19/tasks/DRA-19-02-ui-developer.md`, `docs/contracts/DRA-6/DRA-6-debug-overlay.md` (v2), `docs/reports/scope/DRA-19.md`, 10-ui.md (`debug_overlay*` rows), 15-tech-constraints.md, `game/CONTEXT.md`, `game/ruff.toml`. Grepped `game/` for `.2f` and `-0.00`: the overlay is the only display format, and no test expects `-0.00`. Counted UI tests: 5 in `test_hud.py` + 3 in `test_error_screen.py` = 8, which matches the claimed "8 passed". Nothing run.
4. **Assumptions:** The diff is limited to lines 68-71 and 81, as the report says. I can't see the previous version, so I checked that constants, layout, color, font and `overlay_text_bottom()` match the contract as written.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, `docs/reports/implementation/ui/DRA-19-02-ui-developer.md`. 0 must-fix. One note: the `z` format option has not yet been run in the browser runtime.
7. **Status:** done.

## Findings
1. **note** `game/ui/debug_overlay.py:81`: `f"{name} {value:z.2f}"` needs Python 3.11+. Only desktop 3.12 has run it. The Decisions note says "Not run under the pygbag runtime". The contract's Rationale relies on `.devcontainer/Dockerfile:2`, which says pygbag 0.9.x runs CPython 3.12 in the browser. If the browser runtime were older, every overlay draw would raise `ValueError` and debug mode would go straight to the error screen. Normal mode would not be affected. Rule: a desktop run doesn't count. Source: 15-tech-constraints.md, rule 6 and Edge cases. Change: none to the code. Confirm in a browser debug build (`debug=1`) that the overlay draws.

## Checklist
1. Interface matches the contract: **pass**. The signatures, the three constants and their values, and the imports (`pygame`, `core.ship`, `core.world`, no `app`) match DRA-6-debug-overlay.md, Interface.
2. UI/core split: **pass**. The view only reads `ship.x/y/vx/vy` and `core.world` constants. It doesn't mutate them or read the run mode. The rounding change is display only, and `core.ship` is untouched, as the task's Out of scope asks.
3. Fixed 60 Hz tick: **n/a**. There is no timing in the view.
4. Randomness: **n/a**.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio or outside path. See finding 1 for the browser runtime check.
6. Numbers trace to the GDD or tuning: **pass**. `OVERLAY_COLOR`, `OVERLAY_FONT_SIZE` and `OVERLAY_MARGIN` cite 10-ui.md (guess). The two-decimal format cites `debug_overlay_layout`. `z` cites scope report DRA-19, item 3.
7. Pillars and locked decisions: **n/a**. The change is a debug-only display change. No movement, walls or hazards.
8. Smells: **pass**. There is no duplication, no dead code and no magic number. Every function has type hints. The `@cache` font is a contract-approved cache (Presentation; 15-tech-constraints.md rule 5), not game state.
9. Decisions present and matching the code: **pass**. "Used the `z` format option" matches line 81. "No constants, layout or tests were changed" matches the contract values and the 8-test count. The `draw_debug_overlay` docstring (line 36) still says only "two decimals", which stays true, so leaving it as is follows the task's "if it does" clause.
10. Report claims match the files: **pass**. Line 81 (~87 chars) and line 68 (~95 chars) are under the 100-char limit in `ruff.toml`, so the lint claim is plausible. The claimed 8 UI tests match the count. The acceptance image is saved in the scratchpad, outside the repo, as the task asks. The format check results (`-0.001` gives `0.00`, `-0.26` gives `-0.26`) are correct under PEP 682.

## For QA
- Browser debug build (`debug=1`): the overlay draws with no `ValueError` in the console. This confirms the runtime supports `z`.
- In debug mode, thrust Left and then let go: once vx decays, it reads `vx 0.00`, never `vx -0.00`.
- A real negative still shows its minus. For example, while climbing, `vy` shows something like `vy -0.26`.
- The HUD still sits below the overlay with no overlap. `overlay_text_bottom()` is unchanged, but `0.00` is narrower than `-0.00`, so look at it once.
